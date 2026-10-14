# Background Content Tracker: the change-detection and caching engine
# Copyright (C) 2026 Lukáš Hosnedl
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Change detection. A sweep is compared with a multiset of every text the target
is known to hold, so content that only moved in the tree is never new. Only a
whole sweep that found content may lower a count: a truncated one has not seen
the rest, and a minimised Chromium window reads as empty.
"""

import contextlib
import ctypes
import re
import threading
import time
from collections import Counter, deque
from collections.abc import Callable, Generator, Mapping, Sequence
from typing import TYPE_CHECKING, Any, NamedTuple

import addonHandler
import api
import appModuleHandler
import oleacc
import queueHandler
import textInfos
import winUser
from controlTypes import Role, State
from editableText import EditableText
from logHandler import log
from NVDAObjects import NVDAObject, NVDAObjectTextInfo
from NVDAObjects.IAccessible import IAccessible
from NVDAObjects.UIA import UIATextInfo
from NVDAObjects.UIA.web import UIAWebTextInfo
from NVDAObjects.window import Window
from winBindings import user32

from . import addonConfig, dialogs, gecko
from . import targets as targetsMod
from .addonConfig import Settings
from .notifier import Notifier
from .preview import PreviewWindow
from .targets import Identity, TargetRegistry, TrackedTarget, onThisThread, safeCall, sharesRootWindow

if TYPE_CHECKING:
	from gettext import gettext as _  # noqa: TC004

addonHandler.initTranslation()

Entry = tuple[str, str]

_HIDDEN_STATES = frozenset((State.INVISIBLE, State.OFFSCREEN))
_INVISIBLE_STATES = frozenset((State.INVISIBLE,))

POLL_INTERVAL = 1.0
PREVIEW_WAIT = 0.25
SETTLE_SECONDS = 10.0
MAX_NODES = 1000
MAX_TEXT_CHARS = 10000
MAX_DEPTH = 50
_RAW_TEXT_LIMIT = MAX_TEXT_CHARS * 4
MAX_CACHE_ENTRIES = 100000
MAX_CACHE_CHARS = 20 * 1000 * 1000
_OBJECT_REPLACEMENT = "￼"


def _hasOwnText(obj: NVDAObject) -> bool:
	return safeCall(lambda: obj.TextInfo is not NVDAObjectTextInfo, False) is True


def _ownText(obj: NVDAObject) -> str:
	"""
	An object's own text, of which L{_readableText} keeps the end.
	@param obj: The object.
	@returns: Only the end of UI Automation text outside web content, which jumps there in one call,
	the whole of any other text, or an empty string when it cannot be read.
	"""

	def read() -> str:
		info = obj.makeTextInfo(textInfos.POSITION_ALL)
		if isinstance(info, UIATextInfo) and not isinstance(info, UIAWebTextInfo):
			info.collapse(end=True)
			info.move(textInfos.UNIT_CHARACTER, -_RAW_TEXT_LIMIT, endPoint="start")
		return info.text

	return safeCall(read, "") or ""


def _labelOf(obj: NVDAObject, withValue: bool = True) -> str:
	return _joinLabel(safeCall(lambda: obj.name), safeCall(lambda: obj.value) if withValue else None)


def _joinLabel(name: object, value: object) -> str:
	parts = (name, value)
	return " ".join(part for part in parts if isinstance(part, str) and part and not part.isspace())


_BASE_GET_CHILD = NVDAObject.getChild
_BASE_CHILD_COUNT = NVDAObject._get_childCount


def _hasFastChildAccess(obj: NVDAObject) -> bool:
	cls = type(obj)
	return (
		getattr(cls, "getChild", None) is not _BASE_GET_CHILD
		and getattr(cls, "_get_childCount", None) is not _BASE_CHILD_COUNT
	)


def _childrenOf(obj: NVDAObject, limit: int, fromEnd: bool = True) -> tuple[list[NVDAObject], int]:
	"""At most ``limit`` children, from the end or the start, and the child index of the first."""
	if limit <= 0:
		return [], 0
	if _hasFastChildAccess(obj):
		count = safeCall(lambda: int(obj.childCount), -1)
		if count == 0:
			return [], 0
		if count > limit:
			indices = range(count - 1, count - limit - 1, -1) if fromEnd else range(limit)
			picked: list[NVDAObject] = []
			for index in indices:
				child = safeCall(lambda i=index: obj.getChild(i))
				if child is None:
					break
				picked.append(child)
			if picked:
				if not fromEnd:
					return picked, 0
				picked.reverse()
				return picked, count - len(picked)
	children: list[NVDAObject] | None = safeCall(lambda: list(obj.children or []))
	if children is None:
		return [], 0
	if len(children) <= limit:
		return children, 0
	if not fromEnd:
		return children[:limit], 0
	return children[-limit:], len(children) - limit


def _cleanText(text: str) -> str:
	if not text:
		return ""
	if _OBJECT_REPLACEMENT in text:
		text = text.replace(_OBJECT_REPLACEMENT, "")
	return " ".join(text.split())


def _readableText(raw: str) -> str:
	if not raw:
		return ""
	if len(raw) > _RAW_TEXT_LIMIT:
		raw = raw[-_RAW_TEXT_LIMIT:]
	text = _cleanText(raw)
	return text[-MAX_TEXT_CHARS:] if len(text) > MAX_TEXT_CHARS else text


def _isProgressBar(obj: NVDAObject) -> bool:
	return safeCall(lambda: obj.role == Role.PROGRESSBAR, False) is True


def _isPresented(obj: NVDAObject | None, dormant: bool) -> bool:
	"""
	Whether a control is shown.
	@param obj: The control, or None.
	@param dormant: Whether it is in a Firefox page Firefox does not keep up to date as the one shown,
	where everything is off screen.
	@returns: True also when its states cannot be read.
	"""
	if obj is None:
		return True
	states = safeCall(lambda: obj.states)
	if not states:
		return True
	return not (states & (_INVISIBLE_STATES if dormant else _HIDDEN_STATES))


_FRAME_ROLES = frozenset((Role.TITLEBAR, Role.MENUBAR))
# MB_GetString indices of OK, Cancel, Abort, Retry, Yes, No, Close and Continue.
_MESSAGE_BOX_BUTTONS = (0, 1, 2, 3, 5, 6, 7, 10)


def _labelKey(label: str) -> str:
	return " ".join(label.replace("&", "").split()).strip("<> ").casefold()


def _windowsButtonLabels() -> list[str]:
	getString = ctypes.WinDLL("user32").MB_GetString
	getString.restype = ctypes.c_wchar_p
	getString.argtypes = (ctypes.c_uint,)
	return [label for index in _MESSAGE_BOX_BUTTONS if (label := getString(index))]


def _genericButtonLabels() -> frozenset[str]:
	labels: list[str] = list(safeCall(_windowsButtonLabels, []))
	for english, translated in (
		# Translators: a dialog's OK button, never announced while "Ignore known generic controls" is on.
		("OK", _("OK")),
		# Translators: a dialog's Cancel button, never announced while "Ignore known generic controls" is on.
		("Cancel", _("Cancel")),
		# Translators: a button closing a window or dialog, never announced while "Ignore known generic
		# controls" is on.
		("Close", _("Close")),
		# Translators: a dialog's Abort button, never announced while "Ignore known generic controls" is on.
		("Abort", _("Abort")),
		# Translators: a dialog's Retry button, never announced while "Ignore known generic controls" is on.
		("Retry", _("Retry")),
		# Translators: a dialog's Continue button, never announced while "Ignore known generic controls" is on.
		("Continue", _("Continue")),
		# Translators: a wizard's button moving to its next page, never announced while "Ignore known
		# generic controls" is on.
		("Next", _("Next")),
		# Translators: a wizard's button moving to its previous page, never announced while "Ignore known
		# generic controls" is on.
		("Previous", _("Previous")),
		# Translators: a wizard's button moving to its previous page, never announced while "Ignore known
		# generic controls" is on.
		("Back", _("Back")),
		# Translators: a wizard's button closing it on its last page, never announced while "Ignore known
		# generic controls" is on.
		("Finish", _("Finish")),
		# Translators: a button declining an offer or a prompt for now, never announced while "Ignore known
		# generic controls" is on.
		("Not now", _("Not now")),
		# Translators: a dialog's Yes button, never announced while "Ignore known generic controls" is on.
		("Yes", _("Yes")),
		# Translators: a dialog's No button, never announced while "Ignore known generic controls" is on.
		("No", _("No")),
		# Translators: a window's title bar button, never announced while "Ignore known generic controls" is on.
		("Minimize", _("Minimize")),
		# Translators: a window's title bar button, never announced while "Ignore known generic controls" is on.
		("Maximize", _("Maximize")),
		# Translators: the title bar button of a maximized window, never announced while "Ignore known
		# generic controls" is on.
		("Restore", _("Restore")),
	):
		labels += (english, translated)
	return frozenset(_labelKey(label) for label in labels)


_GENERIC_BUTTON_LABELS = _genericButtonLabels()


def _isGenericControl(obj: NVDAObject, text: str) -> bool:
	role = safeCall(lambda: obj.role)
	if role == Role.MENUBAR:
		return True
	if role == Role.BUTTON and _labelKey(text) in _GENERIC_BUTTON_LABELS:
		return True
	if role not in (Role.BUTTON, Role.MENUITEM):
		return False
	return safeCall(lambda: obj.parent.role) in _FRAME_ROLES


def _focusedValues(focusObj: NVDAObject) -> frozenset[str]:
	"""
	The values of a focused control and of the controls in it, as read now.
	@param focusObj: This thread's copy of the focused control.
	@returns: Each value, and each with its control's name; none for a document.
	"""
	safeCall(focusObj.invalidateCache)
	if safeCall(lambda: focusObj.role) == Role.DOCUMENT:
		return frozenset()
	values: set[str] = set()
	budget = MAX_NODES
	pending = [focusObj]
	while pending and budget > 0:
		obj = pending.pop()
		budget -= 1
		value = safeCall(lambda o=obj: o.value)
		text = _readableText(value) if isinstance(value, str) else ""
		if text:
			values.add(text)
			values.add(_readableText(_joinLabel(safeCall(lambda o=obj: o.name), value)))
		children, _firstIndex = _childrenOf(obj, budget)
		pending.extend(children)
	return frozenset(values)


_WORD = re.compile(r"\w+")
_TYPING_SLACK = 20
_MIN_KEPT = 8


def _wordsOf(text: str) -> str:
	return " ".join(_WORD.findall(text))


def _longestPrefixIn(text: str, value: str) -> int:
	low, high = 0, len(text)
	while low < high:
		middle = (low + high + 1) // 2
		if text[:middle] in value:
			low = middle
		else:
			high = middle - 1
	return low


def _longestSuffixIn(text: str, value: str) -> int:
	low, high = 0, len(text)
	while low < high:
		middle = (low + high + 1) // 2
		if text[len(text) - middle :] in value:
			low = middle
		else:
			high = middle - 1
	return low


def _joinsNear(head: str, tail: str, value: str) -> bool:
	if not head or not tail:
		return head + tail in value
	start = value.find(head)
	while start != -1:
		end = start + len(head)
		if value.find(tail, end, end + _TYPING_SLACK + len(tail)) != -1:
			return True
		start = value.find(head, start + 1)
	return False


def _isEditOf(text: str, value: str) -> bool:
	"""Whether ``text`` is part of ``value`` but for one run of up to ``_TYPING_SLACK`` characters.

	A sweep catches a field being typed in between the two reads of its value, a few
	keystrokes away from both, and not part of either unless the typing is at the end.
	"""
	if text in value:
		return True
	size = len(text)
	head = _longestPrefixIn(text, value)
	tail = _longestSuffixIn(text, value)
	if head + tail < max(size - _TYPING_SLACK, _MIN_KEPT):
		return False
	least = size - _TYPING_SLACK
	for t in range(min(tail, size - head), max(least - head, 0) - 1, -1):
		kept = head + t
		if kept < _MIN_KEPT or size - kept > kept:
			break
		if _joinsNear(text[:head], text[size - t :], value):
			return True
	for h in range(min(head, size - tail), max(least - tail, 0) - 1, -1):
		kept = h + tail
		if kept < _MIN_KEPT or size - kept > kept:
			break
		if _joinsNear(text[:h], text[size - tail :], value):
			return True
	return False


def _isTyped(text: str, typed: frozenset[str], typedWords: frozenset[str]) -> bool:
	if any(_isEditOf(text, value) for value in typed):
		return True
	words = _wordsOf(text)
	return bool(words) and any(_isEditOf(words, value) for value in typedWords)


class _Sweep(NamedTuple):
	entries: list[Entry]
	whole: bool
	nodes: dict[str, NVDAObject]
	dormant: frozenset[str]
	shownTab: int | None


class _Frame:
	"""A control the sweep is inside of, with what is left of its children."""

	def __init__(
		self,
		obj: NVDAObject,
		key: str,
		depth: int,
		dormant: bool | None,
		children: list[NVDAObject],
		firstIndex: int,
		looked: bool,
	):
		"""
		@param obj: The control.
		@param key: Its key in the sweep.
		@param depth: How deep it is under where the sweep starts.
		@param dormant: Whether it is in a Firefox page Firefox does not keep up to date as the one shown,
		or None outside any Firefox page.
		@param children: Its children the sweep reads.
		@param firstIndex: The child index of the first of them.
		@param looked: Whether the sweep looked into the control at all.
		"""
		self.obj = obj
		self.key = key
		self.depth = depth
		self.dormant = dormant
		self.children = children
		self.firstIndex = firstIndex
		self.looked = looked
		self.next = len(children) - 1
		self.gotText = False


class _Sweeper:
	def __init__(self, ignoreProgressBars: bool):
		"""
		@param ignoreProgressBars: Whether to skip progress bars below where the sweep starts.
		"""
		self.ignoreProgressBars = ignoreProgressBars
		self.budget = MAX_NODES
		self.whole = True
		self.entries: list[Entry] = []
		self.nodes: dict[str, NVDAObject] = {}
		self.dormant: set[str] = set()
		self.gecko = False
		self.selectedPanelID: int | None = None
		self.panelsID: int | None = None

	def run(self, root: NVDAObject) -> _Sweep:
		"""
		Read the controls under a control, in post-order, children last first.
		@param root: Where the sweep starts.
		@returns: What the sweep read.
		"""
		stack: list[_Frame] = []
		first = self._enter(root, "", 0, self._prepare(root), None)
		if first is not None:
			stack.append(first)
		while stack:
			frame = stack[-1]
			if frame.next >= 0 and self.budget > 0:
				child = frame.children[frame.next]
				childKey = f"{frame.key}/{frame.firstIndex + frame.next}"
				frame.next -= 1
				entered = self._enter(child, childKey, frame.depth + 1, frame.dormant, frame)
				if entered is not None:
					stack.append(entered)
				continue
			if frame.next >= 0:
				self.whole = False
			stack.pop()
			if self._finish(frame, not stack) and stack:
				stack[-1].gotText = True
		self.entries.reverse()
		return _Sweep(self.entries, self.whole, self.nodes, frozenset(self.dormant), self.selectedPanelID)

	def _prepare(self, root: NVDAObject) -> bool | None:
		"""
		Find out what a sweep of a Firefox window or page has to know before it starts.
		@param root: Where the sweep starts.
		@returns: Whether it is in a Firefox page Firefox does not keep up to date as the one shown,
		or None outside any Firefox page.
		"""
		if not gecko.isGecko(root):
			return None
		self.gecko = True
		acc = safeCall(lambda: root.IAccessibleObject)
		document = gecko.tabDocument(acc) if acc is not None else None
		if document is not None:
			return gecko.isActiveDocument(document) is False
		hwnd = targetsMod.windowHandleOf(root)
		windowAcc = gecko.windowRoot(hwnd) if hwnd else None
		selected = gecko.selectedDocument(windowAcc) if windowAcc is not None else None
		panel = gecko.tabPanel(selected) if selected is not None else None
		panels = gecko.parentOf(panel) if panel is not None else None
		if panels is not None:
			self.selectedPanelID = gecko.uniqueID(panel)
			self.panelsID = gecko.uniqueID(panels)
		return None

	def _enter(
		self,
		obj: NVDAObject,
		key: str,
		depth: int,
		dormant: bool | None,
		parent: _Frame | None,
	) -> _Frame | None:
		"""
		Start reading a control.
		@param obj: The control.
		@param key: Its key in the sweep.
		@param depth: How deep it is under where the sweep starts.
		@param dormant: As its parent is.
		@param parent: The control it is a child of, or None where the sweep starts.
		@returns: The control with the children to read, or None when it gives nothing.
		"""
		if self.budget <= 0:
			self.whole = False
			return None
		if self.gecko and dormant is None:
			role = safeCall(lambda: obj.IAccessibleRole)
			if role == oleacc.ROLE_SYSTEM_PROPERTYPAGE and self._isOtherTabPanel(obj, parent):
				return None
			if role == oleacc.ROLE_SYSTEM_DOCUMENT:
				dormant = safeCall(lambda: gecko.isActiveDocument(obj.IAccessibleObject)) is False
		self.budget -= 1
		if parent is not None and self.ignoreProgressBars and _isProgressBar(obj):
			return None
		looked = depth < MAX_DEPTH and self.budget > 0
		if not looked:
			self.whole = False
		children, firstIndex = _childrenOf(obj, self.budget) if looked else ([], 0)
		if firstIndex:
			self.whole = False
		return _Frame(obj, key, depth, dormant, children, firstIndex, looked)

	def _isOtherTabPanel(self, obj: NVDAObject, parent: _Frame | None) -> bool:
		"""
		Whether a control is the tab panel of a Firefox tab other than the selected one.
		@param obj: The control.
		@param parent: The control it is a child of, or None where the sweep starts.
		@returns: False when the selected tab is not known.
		"""
		if self.selectedPanelID is None or self.panelsID is None or parent is None:
			return False
		parentObj = parent.obj
		if safeCall(lambda: parentObj.IA2UniqueID) != self.panelsID:
			return False
		return safeCall(lambda: obj.IA2UniqueID) != self.selectedPanelID

	def _finish(self, frame: _Frame, isRoot: bool) -> bool:
		"""
		Add a control once its children are read: its label if they gave text, else its own text.
		@param frame: The control.
		@param isRoot: Whether the sweep started at it.
		@returns: Whether the control or any control under it gave text.
		"""
		obj = frame.obj
		text = ""
		trustOwnText = frame.looked and (not frame.children or (frame.firstIndex == 0 and self.budget > 0))
		if not frame.gotText and trustOwnText and _hasOwnText(obj):
			text = _readableText(_ownText(obj))
		if not text and not (isRoot and frame.children):
			isFieldOverText = frame.gotText and isinstance(obj, EditableText)
			text = _readableText(_labelOf(obj, withValue=not isFieldOverText))
		if not text:
			return frame.gotText
		self.entries.append((frame.key, text))
		self.nodes[frame.key] = obj
		if frame.dormant:
			self.dormant.add(frame.key)
		return True


def _sweepEntries(root: NVDAObject, ignoreProgressBars: bool = False) -> _Sweep:
	"""
	Read the text of every control of a target.
	A node whose children gave text adds only its label; only a mute subtree falls
	back to the node's own text, so nothing is read as one blob. Children are walked
	last first, so a sweep cut short keeps the end, where new content arrives.
	In Firefox, a window reads only the tab it shows, and a page in a tab Firefox does
	not keep up to date as the one shown counts as on screen.
	@param root: The target's object.
	@param ignoreProgressBars: Whether to skip progress bars below the target.
	@returns: ``(key, text)`` per control in document order, whether no cap cut the sweep short,
	key to control, the keys in Firefox pages not kept up to date, and the unique ID of the tab
	panel a Firefox window shows, or None.
	"""
	return _Sweeper(ignoreProgressBars).run(root)


def _isDarkSweep(entries: Sequence[Entry], cache: Mapping[str, int]) -> bool:
	return len(entries) <= 1 < len(cache)


_NUMBER_RUN = re.compile(r"\d(?:[\d.,:\u00a0\u0020]*\d)?")
_NUMBER_SENTINEL = "\uf8ff"


def _templateOf(text: str) -> str:
	return _NUMBER_RUN.sub(_NUMBER_SENTINEL, text)


def _cutsWord(text: str, index: int) -> bool:
	return 0 < index < len(text) and bool(_WORD.match(text[index - 1])) and bool(_WORD.match(text[index]))


def _stripAnnounced(delta: str, announced: str) -> str:
	"""``delta`` without the lines ``announced`` said, nor the start of a line that grew from one."""
	if not announced:
		return delta
	heard = {line for line in announced.split("\n") if line}
	longestFirst = sorted(heard, key=len, reverse=True)
	kept: list[str] = []
	for line in delta.split("\n"):
		rest = line
		while rest and rest not in heard:
			grownFrom = next(
				(old for old in longestFirst if rest.startswith(old) and not _cutsWord(rest, len(old))),
				None,
			)
			if grownFrom is None:
				break
			rest = rest[len(grownFrom) :].lstrip()
		if rest and rest not in heard:
			kept.append(rest)
	return "\n".join(kept)


def _joinSurfaced(surfaced: Sequence[Entry]) -> str:
	kept: list[str] = []
	chain: list[Entry] = []
	for key, text in surfaced:
		while chain and not key.startswith(chain[-1][0] + "/"):
			chain.pop()
		if any(text in ancestorText for _, ancestorText in chain):
			continue
		chain.append((key, text))
		kept.append(text)
	return "\n".join(kept).strip()


def _topLevelWindows() -> list[int]:
	"""
	The handles of every top-level window, frontmost first.
	@returns: The window handles.
	"""
	found: list[int] = []

	def collect(hwnd: int | None, lParam: int) -> bool:
		if hwnd:
			found.append(hwnd)
		return True

	user32.EnumWindows(user32.WNDENUMPROC(collect), 0)
	return found


def _windowObject(hwnd: int) -> NVDAObject | None:
	"""
	The object of a top-level window, made as the desktop makes its children.
	@param hwnd: The window.
	@returns: The object, or None when it cannot be made.
	"""

	def make() -> NVDAObject:
		kwargs = {"windowHandle": hwnd}
		apiClass = Window.findBestAPIClass(kwargs, relation="parent")
		return apiClass(**kwargs)

	return safeCall(make)


class Monitor:
	def __init__(
		self,
		registry: TargetRegistry,
		notifier: Notifier,
		preview: PreviewWindow,
		onListChanged: Callable[[], None] | None = None,
	):
		"""
		@param registry: The targets.
		@param notifier: Announces what the monitor finds.
		@param preview: Keeps covered Chromium windows drawn while they are read.
		@param onListChanged: Called when the target list changes on its own.
		"""
		self.registry = registry
		self.notifier = notifier
		self._preview = preview
		self._onListChanged = onListChanged
		self._thread: threading.Thread | None = None
		self._stop = threading.Event()
		self._wake = threading.Event()
		self._lastAnnouncedUid: int | None = None
		self._focusCopy: tuple[NVDAObject, NVDAObject] | None = None

	def start(self):
		if self._thread is not None:
			return
		self._stop.clear()
		self._thread = threading.Thread(
			name="BackgroundContentTracker._monitorThread",
			target=self._run,
			daemon=True,
		)
		self._thread.start()

	def stop(self):
		self._stop.set()
		self._wake.set()
		self._thread = None

	def wake(self):
		"""Look for missing remembered targets now instead of at the next regular pass."""
		self._wake.set()

	def _callOnMainThread(self, func: Callable[..., object], *args: Any, **kwargs: Any):
		if self._stop.is_set():
			return
		immediate = kwargs.pop("immediate", False)
		queueHandler.queueFunction(
			queueHandler.eventQueue, self._unlessStopped, func, *args, _immediate=immediate, **kwargs
		)

	def _unlessStopped(self, func: Callable[..., object], *args: Any, **kwargs: Any):
		"""
		Run what the monitor queued, unless it has been stopped since.
		@param func: What to run, with its arguments.
		"""
		if not self._stop.is_set():
			func(*args, **kwargs)

	def _notifyListChanged(self):
		if self._onListChanged is not None:
			self._callOnMainThread(self._onListChanged)

	def _refreshIdentity(self, target: TrackedTarget, obj: NVDAObject) -> bool:
		newIdentity = targetsMod.objectIdentity(obj)
		target.title = newIdentity["name"]
		if newIdentity == target.identity:
			return False
		target.identity = newIdentity
		return True

	def onAdded(self, target: TrackedTarget):
		target.resetTracking()
		target.wasInForeground = target.isInForeground()
		target.lastSeenInForeground = target.wasInForeground
		target.captureTrackedTitle()

	def link(self, target: TrackedTarget, obj: NVDAObject) -> bool:
		"""
		Link a target that has no object to one found for it.
		@param target: The target.
		@param obj: The object.
		@returns: Whether the target had no object and took this one.
		"""
		if not target.link(obj, SETTLE_SECONDS):
			return False
		if self._refreshIdentity(target, obj):
			self._notifyListChanged()
		target.captureTrackedTitle()
		return True

	def waitingTargetFor(self, obj: NVDAObject) -> TrackedTarget | None:
		"""
		The remembered target waiting for an object like this one to appear.
		@param obj: The object.
		@returns: The target, or None.
		"""
		if targetsMod.isHungWindow(targetsMod.windowHandleOf(obj)):
			return None
		settings = addonConfig.snapshot()
		for target in self.registry.detachedTargets():
			if (
				target.setting("rememberTargets", settings)
				and targetsMod.matchesIdentity(target.identity, obj)
				and self._keptItsTitle(target, obj, settings)
			):
				return target
		return None

	def _run(self):
		sinceLast = 0.0
		lastTick = time.monotonic()
		wasEnabled = False
		while True:
			self._wake.clear()
			if self._stop.is_set():
				return
			try:
				settings = addonConfig.snapshot()
				enabled = bool(settings["enabled"])
				report = enabled and not wasEnabled
				wasEnabled = enabled
				if enabled:
					self._checkPresence(settings, report)
				now = time.monotonic()
				elapsed = now - lastTick
				if elapsed + 1e-6 >= POLL_INTERVAL:
					lastTick = now
					if enabled:
						interval = int(settings["trackingInterval"])
						effective = POLL_INTERVAL if interval <= 0 else max(interval, POLL_INTERVAL)
						sinceLast += elapsed
						due = sinceLast + 1e-6 >= effective
						if due:
							sinceLast = 0.0
						with self._drawnWhileRead(due):
							self._settlePass(settings)
							if due:
								self._checkContent(settings, announce=interval != 0)
			except Exception:
				log.exception("Error in Background Content Tracker poll")
			self._wake.wait(max(0.0, POLL_INTERVAL - (time.monotonic() - lastTick)))
			if self._stop.is_set():
				return

	@contextlib.contextmanager
	def _drawnWhileRead(self, due: bool) -> Generator[None]:
		"""
		Keep covered Chromium windows drawn while this tick reads any target in one.
		@param due: Whether this tick checks every target's content, not only that of settling ones.
		"""
		read = [target for target in self.registry.liveTargets() if due or target.isSettling()]
		if not any(target.needsPreview() for target in read):
			yield
			return
		self._preview.show()
		try:
			self._stop.wait(PREVIEW_WAIT)
			yield
		finally:
			self._preview.hide()

	def _checkPresence(self, settings: Settings, report: bool):
		remembered = [
			target
			for target in self.registry.detachedTargets()
			if target.setting("rememberTargets", settings)
		]
		self._relocatePass(remembered, settings, announce=not report)
		dropped: set[TrackedTarget] = set()
		for target in self.registry.liveTargets():
			if self._stop.is_set():
				return
			if target.isHung():
				continue
			found = target.attachedObject
			if found is None:
				continue
			title = target.liveTitle()
			if title is not None and self._keptItsTitle(target, title, settings):
				target.title = title
				target.updateTabSelected()
				target.lastSeenInForeground = target.isInForeground()
				continue
			if self._handleDisappeared(target, settings, found):
				dropped.add(target)
		if not report:
			return
		kept = [
			target
			for target in self.registry
			if target not in dropped and target.setting("rememberTargets", settings)
		]
		if kept:
			found = [target for target in kept if target.isAttached]
			self._callOnMainThread(self.notifier.announceRestored, found, len(kept))
		else:
			self._callOnMainThread(self._reportEmptyList)

	def _reportEmptyList(self):
		if not len(self.registry):
			self.notifier.noTargetsToTrack()

	def _checkContent(self, settings: Settings, announce: bool):
		for target in self.registry.liveTargets():
			if self._stop.is_set():
				return
			if target.isSettling():
				continue
			self._checkTargetContent(target, settings, announce)

	def _settlePass(self, settings: Settings):
		"""Re-take the baseline of a target just attached to, every second until a sweep
		reveals nothing the one before it did not, so a window still opening is not taken
		for a window that has just filled itself with new content.
		"""
		for target in self.registry.liveTargets():
			if self._stop.is_set():
				return
			if target.isSettling():
				self._checkTargetContent(target, settings, announce=False)

	def _checkTargetContent(self, target: TrackedTarget, settings: Settings, announce: bool):
		obj = target.freshObj()
		if obj is None or target.isHung():
			return
		isWindow = target.kind == "window"
		ignorePB = bool(target.setting("ignoreProgressBars", settings)) and isWindow
		inForeground = target.lastSeenInForeground
		if inForeground != target.wasInForeground:
			target.announcedRun = 0
		target.wasInForeground = inForeground
		if inForeground and not target.setting("trackForegroundTargets", settings):
			target.staleCache = True
			return
		focusObj = None
		typedBefore: frozenset[str] = frozenset()
		if inForeground and isWindow and target.setting("ignoreFocusedControl", settings):
			focusObj = self._focusIn(obj)
			if focusObj is not None:
				typedBefore = _focusedValues(focusObj)
		ignoredGeneration = target.ignoredGeneration
		sweep = _sweepEntries(obj, ignorePB)
		counts = Counter(text for _, text in sweep.entries)
		dark = _isDarkSweep(sweep.entries, target.seenContent)
		if sweep.shownTab != target.shownTab:
			target.shownTab = sweep.shownTab
			target.staleCache = True
		if target.staleCache:
			texts = frozenset(counts)
			self._absorb(target, counts, sweep.whole, dark)
			target.staleCache = target.isSettling() and not texts <= target.prevTexts
			target.prevTexts = texts
			if not target.staleCache:
				target.settleUntil = None
			return
		delta = self._collectDelta(
			target, sweep, counts, isWindow, settings, focusObj, typedBefore, ignoredGeneration
		)
		self._absorb(target, counts, sweep.whole, dark)
		target.prevTexts = frozenset(counts)
		if not delta:
			return
		when = time.time()
		target.lastChange = (delta, when)
		if target.recordChange(delta, when) is not None:
			self._callOnMainThread(dialogs.changeRecorded, target)
		if not announce:
			return
		sameTarget = self._lastAnnouncedUid == target.uid
		if not sameTarget:
			target.announcedRun = 0
		cap = int(settings["changesAtOnce"])
		if cap and not inForeground and target.announcedRun >= cap:
			return
		spoken = _stripAnnounced(delta, target.announcedDelta)
		if not spoken:
			return
		target.announcedDelta = delta
		target.announcedRun += 1
		self._lastAnnouncedUid = target.uid
		self._callOnMainThread(self._announceChange, target, spoken, sameTarget, immediate=True)

	def _announceChange(self, target: TrackedTarget, spoken: str, sameTarget: bool):
		"""
		Announce a change in a target still tracked, unless it has come to the foreground meanwhile.
		@param target: The target that changed.
		@param spoken: The new content to announce.
		@param sameTarget: Whether the change announced before this one was in the same target.
		"""
		if target not in self.registry:
			return
		if not target.setting("trackForegroundTargets") and target.isInForeground():
			return
		speak = bool(target.setting("announceWithHistoryOpen")) or not dialogs.historyOpenFor(target)
		self.notifier.announceChange(target, spoken, sameTarget, speak)

	def _focusIn(self, root: NVDAObject) -> NVDAObject | None:
		"""
		The focused control, if it is inside the window of ``root``, made once per focus change.
		@param root: The tracked window.
		@returns: This thread's copy of the focused control, or None.
		"""
		focus = safeCall(api.getFocusObject)
		if focus is None or not sharesRootWindow(focus, root):
			return None
		cached = self._focusCopy
		if cached is not None and cached[0] is focus:
			return cached[1]
		copy = onThisThread(focus) or focus
		self._focusCopy = (focus, copy)
		return copy

	def _collectDelta(
		self,
		target: TrackedTarget,
		sweep: _Sweep,
		counts: Mapping[str, int],
		isWindow: bool,
		settings: Settings,
		focusObj: NVDAObject | None,
		typedBefore: frozenset[str],
		ignoredGeneration: int,
	) -> str:
		cache = target.seenContent
		nodes = sweep.nodes
		outstanding: dict[str, int] = {}
		for text, seen in counts.items():
			known = cache.get(text, 0)
			if seen > known:
				outstanding[text] = seen - known
		if not outstanding:
			return ""
		picked: list[Entry] = []
		for key, text in reversed(sweep.entries):
			left = outstanding.get(text)
			if left:
				outstanding[text] = left - 1
				picked.append((key, text))
		picked.reverse()
		if focusObj is not None:
			typed = typedBefore | _focusedValues(focusObj)
			if typed:
				typedWords = frozenset(_wordsOf(value) for value in typed)
				picked = [(key, text) for key, text in picked if not _isTyped(text, typed, typedWords)]
				if not picked:
					return ""
		picked = [(key, text) for key, text in picked if _isPresented(nodes.get(key), key in sweep.dormant)]
		if isWindow and target.setting("ignoreGenericControls", settings):
			picked = [(key, text) for key, text in picked if not _isGenericControl(nodes[key], text)]
		if not picked:
			return ""
		if not (isWindow and target.setting("ignoreCounters", settings)):
			return _joinSurfaced(picked)

		ignored = target.ignoredTemplates
		vanished: set[str] = set()
		for text in target.prevTexts:
			if text not in counts:
				vanished.add(_templateOf(text))

		surfaced: list[Entry] = []
		learned: set[str] = set()
		for key, text in picked:
			template = _templateOf(text)
			if template == text:
				surfaced.append((key, text))
				continue
			if template in ignored:
				continue
			if template in vanished:
				learned.add(template)
				continue
			surfaced.append((key, text))
		if learned:
			target.learnIgnoredControls(frozenset(learned), ignoredGeneration)
		return _joinSurfaced(surfaced)

	def _absorb(self, target: TrackedTarget, counts: Mapping[str, int], whole: bool, dark: bool):
		cache = target.seenContent
		trustAbsence = whole and not dark
		if trustAbsence:
			for gone in [text for text in cache if text not in counts]:
				target.seenChars -= len(gone)
				del cache[gone]
		for text, seen in counts.items():
			known = cache.get(text)
			if known is None:
				cache[text] = seen
				target.seenChars += len(text)
				continue
			if seen > known or trustAbsence:
				cache[text] = seen
			cache.move_to_end(text)
		while cache and (len(cache) > MAX_CACHE_ENTRIES or target.seenChars > MAX_CACHE_CHARS):
			evicted, _count = cache.popitem(last=False)
			target.seenChars -= len(evicted)

	def _keptItsTitle(self, target: TrackedTarget, title: str | NVDAObject, settings: Settings) -> bool:
		if not target.isHeldToItsTitle(settings):
			return True
		if target.trackedTitle is None:
			return True
		if not isinstance(title, str):
			title = targetsMod.titleOf(title)
		return title == target.trackedTitle

	def _handleDisappeared(self, target: TrackedTarget, settings: Settings, found: NVDAObject) -> bool:
		"""
		Let go of a gone target and say what became of it, unless it has been found again meanwhile.
		@param target: The target.
		@param settings: The settings.
		@param found: The object the target was found to have lost.
		@returns: Whether the target was dropped.
		"""
		if not target.detachIf(found):
			return False
		forget = target.isForgottenWhenGone(settings)
		if forget:
			announce = not target.lastSeenInForeground or bool(target.setting("rememberTargets", settings))
			self._callOnMainThread(self._dropGone, target, announce)
		elif not target.lastSeenInForeground:
			self._callOnMainThread(self._whileTracked, target, self.notifier.announceDisappeared, target)
		return forget

	def _dropGone(self, target: TrackedTarget, announce: bool):
		"""
		Remove a target that is gone, unless it has been removed meanwhile.
		@param target: The target.
		@param announce: Whether to say that it stopped being tracked.
		"""
		if not self.registry.remove(target):
			return
		dialogs.closeHistory(target)
		if announce:
			self.notifier.announceStopped(target, unprompted=True)
		if self._onListChanged is not None:
			self._onListChanged()

	def _whileTracked(self, target: TrackedTarget, func: Callable[..., object], *args: Any, **kwargs: Any):
		"""
		Run something about a target only if it is still in the list.
		@param target: The target.
		@param func: What to run, with its arguments.
		"""
		if target in self.registry:
			func(*args, **kwargs)

	def relocate(self, target: TrackedTarget) -> bool:
		obj = self._locate(target.identity, target.kind)
		if obj is None or not target.replaceObject(obj):
			return False
		if self._refreshIdentity(target, obj):
			self._notifyListChanged()
		return True

	def relocateAsync(self, target: TrackedTarget, callback: Callable[[TrackedTarget, bool], None]):
		def run():
			try:
				found = self.relocate(target)
			except Exception:  # noqa: BLE001
				log.debugWarning("Could not relocate target", exc_info=True)
				found = False
			self._callOnMainThread(callback, target, found, immediate=True)

		threading.Thread(
			name="BackgroundContentTracker._relocateThread",
			target=run,
			daemon=True,
		).start()

	def _relocatePass(
		self,
		targets: Sequence[TrackedTarget],
		settings: Settings,
		announce: bool,
	):
		if not targets:
			return
		windows = self._desktopWindows()
		if not windows:
			return
		candidatesByApp: dict[str, list[NVDAObject]] = {}
		for target in targets:
			if self._stop.is_set():
				break
			if not target.identity:
				continue
			appName = target.identity.get("appName") or ""
			candidates = candidatesByApp.get(appName)
			if candidates is None:
				candidates = candidatesByApp[appName] = self._candidateWindows(windows, target.identity)
			obj = self._locateAmong(candidates, target.identity, target.kind)
			if obj is not None and not self._keptItsTitle(target, obj, settings):
				obj = None
			if obj is None:
				continue
			self._attach(target, obj, announce)

	def _desktopWindows(self) -> list[tuple[str, int]]:
		"""
		Every top-level window that is shown and responding, with the name of its application.
		@returns: The application names and window handles, frontmost first.
		"""
		appNames: dict[int, str] = {}
		windows: list[tuple[str, int]] = []
		for hwnd in _topLevelWindows():
			if not targetsMod.isShownWindow(hwnd) or targetsMod.isHungWindow(hwnd):
				continue
			processID = safeCall(lambda h=hwnd: winUser.getWindowThreadProcessID(h)[0], 0)
			if processID not in appNames:
				appNames[processID] = (
					safeCall(lambda p=processID: appModuleHandler.getAppModuleFromProcessID(p).appName) or ""
				)
			windows.append((appNames[processID], hwnd))
		return windows

	def _candidateWindows(
		self,
		windows: Sequence[tuple[str, int]],
		identity: Identity,
	) -> list[NVDAObject]:
		"""
		The windows a target may be in: its application's.
		@param windows: Every top-level window that is shown and responding, with its application's name.
		@param identity: The target's identity.
		@returns: The objects of those windows, in the order given.
		"""
		if not identity:
			return []
		wantedApp = identity.get("appName")
		candidates: list[NVDAObject] = []
		for appName, hwnd in windows:
			if wantedApp and appName != wantedApp:
				continue
			window = _windowObject(hwnd)
			if window is not None:
				candidates.append(window)
		return candidates

	def _locateAmong(
		self,
		candidates: Sequence[NVDAObject],
		identity: Identity,
		kind: str | None = None,
	) -> NVDAObject | None:
		for window in candidates:
			if targetsMod.matchesIdentity(identity, window):
				return window
		if kind == "window":
			return None
		for window in candidates:
			match = self._findInWindow(window, identity)
			if match is not None:
				return match
		return None

	def _findInWindow(self, window: NVDAObject, identity: Identity) -> NVDAObject | None:
		"""
		The control in a window that an identity describes, looked for in every Firefox tab first.
		@param window: The window.
		@param identity: The identity.
		@returns: The control, or None.
		"""
		documents: list[NVDAObject] = []
		if gecko.isGecko(window):
			for acc in gecko.tabDocuments(window.IAccessibleObject):
				document = safeCall(lambda a=acc: IAccessible(IAccessibleObject=a, IAccessibleChildID=0))
				if document is not None:
					documents.append(document)
		for document in documents:
			if targetsMod.matchesIdentity(identity, document):
				return document
		for document in documents:
			match = self._findMatchingDescendant(document, identity)
			if match is not None:
				return match
		return self._findMatchingDescendant(window, identity)

	def _locate(self, identity: Identity, kind: str | None = None) -> NVDAObject | None:
		if not identity:
			return None
		windows = self._desktopWindows()
		return self._locateAmong(self._candidateWindows(windows, identity), identity, kind)

	def _findMatchingDescendant(
		self,
		root: NVDAObject,
		identity: Identity,
		maxNodes: int = 150,
	) -> NVDAObject | None:
		children, _firstIndex = _childrenOf(root, maxNodes, fromEnd=False)
		queue = deque(children)
		examined = 0
		while queue and examined < maxNodes:
			node = queue.popleft()
			examined += 1
			if targetsMod.matchesIdentity(identity, node):
				return node
			children, _firstIndex = _childrenOf(node, maxNodes - examined - len(queue), fromEnd=False)
			queue.extend(children)
		return None

	def _attach(self, target: TrackedTarget, obj: NVDAObject, announce: bool = True):
		if self.link(target, obj) and announce:
			self._callOnMainThread(
				self._whileTracked, target, self.notifier.announceTracking, target, unprompted=True
			)
