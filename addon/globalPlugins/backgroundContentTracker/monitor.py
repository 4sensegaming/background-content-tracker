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
from typing import TYPE_CHECKING, Any

import addonHandler
import api
import appModuleHandler
import queueHandler
import textInfos
import winUser
from controlTypes import Role, State
from editableText import EditableText
from logHandler import log
from NVDAObjects import NVDAObject, NVDAObjectTextInfo
from NVDAObjects.UIA import UIATextInfo
from NVDAObjects.UIA.web import UIAWebTextInfo
from NVDAObjects.window import Window
from winBindings import user32

from . import addonConfig, dialogs
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


def _isPresented(obj: NVDAObject | None) -> bool:
	if obj is None:
		return True
	states = safeCall(lambda: obj.states)
	if not states:
		return True
	return not (states & _HIDDEN_STATES)


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


def _sweepEntries(
	root: NVDAObject,
	ignoreProgressBars: bool = False,
) -> tuple[list[Entry], bool, dict[str, NVDAObject]]:
	"""``(key, text)`` per control in document order, whether no cap cut it short, and key to control.

	A node whose children gave text adds only its label; only a mute subtree falls
	back to the node's own text, so nothing is read as one blob. Children are walked
	last first, so a sweep cut short keeps the end, where new content arrives.
	"""
	entries: list[Entry] = []
	nodes: dict[str, NVDAObject] = {}
	budget = [MAX_NODES]
	whole = [True]

	def visit(obj: NVDAObject, depth: int, key: str, isRoot: bool) -> bool:
		if budget[0] <= 0:
			whole[0] = False
			return False
		budget[0] -= 1
		if not isRoot and ignoreProgressBars and _isProgressBar(obj):
			return False
		looked = depth < MAX_DEPTH and budget[0] > 0
		if not looked:
			whole[0] = False
		children, firstIndex = _childrenOf(obj, budget[0]) if looked else ([], 0)
		if firstIndex:
			whole[0] = False
		gotText = False
		for offset in range(len(children) - 1, -1, -1):
			if budget[0] <= 0:
				whole[0] = False
				break
			childKey = f"{key}/{firstIndex + offset}"
			if visit(children[offset], depth + 1, childKey, False):
				gotText = True
		text = ""
		trustOwnText = looked and (not children or (firstIndex == 0 and budget[0] > 0))
		if not gotText and trustOwnText and _hasOwnText(obj):
			text = _readableText(_ownText(obj))
		if not text and not (isRoot and children):
			isFieldOverText = gotText and isinstance(obj, EditableText)
			text = _readableText(_labelOf(obj, withValue=not isFieldOverText))
		if not text:
			return gotText
		entries.append((key, text))
		nodes[key] = obj
		return True

	visit(root, 0, "", True)
	entries.reverse()
	return entries, whole[0], nodes


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
		queueHandler.queueFunction(queueHandler.eventQueue, func, *args, _immediate=immediate, **kwargs)

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
			self._wake.clear()
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
			title = target.liveTitle()
			if title is not None and self._keptItsTitle(target, title, settings):
				target.title = title
				target.lastSeenInForeground = target.isInForeground()
				continue
			if self._handleDisappeared(target, settings):
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
		obj = target.obj
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
		entries, whole, nodes = _sweepEntries(obj, ignorePB)
		dark = _isDarkSweep(entries, target.seenContent)
		if target.staleCache:
			texts = frozenset(text for _, text in entries)
			self._absorb(target, entries, whole, dark)
			target.staleCache = target.isSettling() and not texts <= target.prevTexts
			target.prevTexts = texts
			if not target.staleCache:
				target.settleUntil = None
			return
		delta = self._collectDelta(target, entries, nodes, isWindow, settings, focusObj, typedBefore)
		self._absorb(target, entries, whole, dark)
		target.prevTexts = frozenset(text for _, text in entries)
		if not delta:
			return
		target.lastDelta = delta
		target.lastChangeTime = time.time()
		if target.recordChange(delta, target.lastChangeTime) is not None:
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
		entries: Sequence[Entry],
		nodes: Mapping[str, NVDAObject],
		isWindow: bool,
		settings: Settings,
		focusObj: NVDAObject | None,
		typedBefore: frozenset[str],
	) -> str:
		cache = target.seenContent
		counts = Counter(text for _, text in entries)
		outstanding: dict[str, int] = {}
		for text, seen in counts.items():
			known = cache.get(text, 0)
			if seen > known:
				outstanding[text] = seen - known
		if not outstanding:
			return ""
		picked: list[Entry] = []
		for key, text in reversed(entries):
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
		picked = [(key, text) for key, text in picked if _isPresented(nodes.get(key))]
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
			target.ignoredTemplates = ignored | learned
		return _joinSurfaced(surfaced)

	def _absorb(self, target: TrackedTarget, entries: Sequence[Entry], whole: bool, dark: bool):
		cache = target.seenContent
		counts = Counter(text for _, text in entries)
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

	def _handleDisappeared(self, target: TrackedTarget, settings: Settings) -> bool:
		"""Let go of a gone target and say what became of it; whether it was dropped."""
		forget = target.isForgottenWhenGone(settings)
		target.obj = None
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
		for target in targets:
			if self._stop.is_set():
				break
			candidates = self._candidateWindows(windows, target.identity)
			obj = self._locateAmong(candidates, target.identity, target.kind)
			if obj is not None and not self._keptItsTitle(target, obj, settings):
				obj = None
			if obj is None:
				continue
			self._attach(target, obj, announce)

	def _desktopWindows(self) -> list[tuple[str, int]]:
		"""
		Every top-level window, with the name of its application.
		@returns: The application names and window handles, frontmost first.
		"""
		appNames: dict[int, str] = {}
		windows: list[tuple[str, int]] = []
		for hwnd in _topLevelWindows():
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
		The windows a target may be in: its application's, visible and responding.
		@param windows: Every top-level window, with its application's name.
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
			if not targetsMod.isShownWindow(hwnd) or targetsMod.isHungWindow(hwnd):
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
			match = self._findMatchingDescendant(window, identity)
			if match is not None:
				return match
		return None

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
