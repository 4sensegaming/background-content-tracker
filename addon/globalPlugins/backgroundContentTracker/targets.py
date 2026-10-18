# Background Content Tracker: tracked targets and the target registry
# Copyright (C) 2026 Lukáš Hosnedl
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

import itertools
import locale
import threading
import time
from collections import OrderedDict
from collections.abc import Callable, Iterable, Iterator, Mapping
from typing import Any, NamedTuple

import api
import core
import winUser
from controlTypes import Role, State
from logHandler import log
from NVDAObjects import NVDAObject
from NVDAObjects.IAccessible import getNVDAObjectFromEvent
from winBindings import user32

from . import addonConfig, gecko
from .addonConfig import ConfigValue, Settings

Identity = dict[str, Any]

_SW_RESTORE = 9

_UNREADABLE = object()


def safeCall(func: Callable[[], Any], default: Any = None) -> Any:
	try:
		return func()
	except Exception:  # noqa: BLE001
		return default


def onThisThread(obj: NVDAObject) -> NVDAObject | None:
	event = (
		getattr(obj, "event_windowHandle", None),
		getattr(obj, "event_objectID", None),
		getattr(obj, "event_childID", None),
	)
	if None in event:
		return obj
	return safeCall(lambda: getNVDAObjectFromEvent(*event))


def appNameOf(obj: NVDAObject) -> str:
	return safeCall(lambda: obj.appModule.appName) or ""


def titleOf(obj: NVDAObject) -> str:
	return safeCall(lambda: obj.name) or ""


def _roleNumberOf(obj: NVDAObject) -> int:
	role = safeCall(lambda: obj.role)
	return int(role) if role is not None else 0


_IDENTITY_FIELDS: dict[str, Callable[[NVDAObject], Any]] = {
	"appName": appNameOf,
	"windowClassName": lambda obj: safeCall(lambda: obj.windowClassName) or "",
	"automationID": lambda obj: safeCall(lambda: obj.UIAAutomationId) or "",
	"role": _roleNumberOf,
	"name": titleOf,
}


def objectIdentity(obj: NVDAObject) -> Identity:
	return {field: read(obj) for field, read in _IDENTITY_FIELDS.items()}


def matchesIdentity(identity: Identity, obj: NVDAObject) -> bool:
	if not identity:
		return False
	fields = _IDENTITY_FIELDS
	if fields["appName"](obj) != identity.get("appName"):
		return False
	automationID = identity.get("automationID")
	if automationID and fields["automationID"](obj) == automationID:
		return True
	return all(fields[field](obj) == identity.get(field) for field in ("windowClassName", "role", "name"))


def _collationKey(name: str) -> str:
	folded = name.casefold()
	return safeCall(lambda: locale.strxfrm(folded), folded)


class Change(NamedTuple):
	serial: int
	time: float
	text: str


_changeSerials = itertools.count(1)


def sortChanges(changes: Iterable[Change], order: str) -> list[Change]:
	"""
	Put changes in the order of a history sorting setting.
	@param changes: The changes, oldest first.
	@param order: One of L{addonConfig.HISTORY_SORT_ORDERS}.
	@returns: The changes in that order.
	"""
	if order in ("alphabetical", "reverseAlphabetical"):
		ordered = sorted(changes, key=lambda change: _collationKey(change.text))
	else:
		ordered = list(changes)
	if order in ("newest", "reverseAlphabetical"):
		ordered.reverse()
	return ordered


def windowHandleOf(obj: NVDAObject | None) -> int | None:
	"""
	An object's window, as NVDA stored it when it made the object.
	@param obj: The object, or None.
	@returns: The window handle, or None.
	"""
	return safeCall(lambda: obj.windowHandle) if obj is not None else None


def _rootWindowOf(hwnd: int) -> int:
	"""
	The top-level window a window is in.
	@param hwnd: The window.
	@returns: The top-level window, or the window itself when it cannot be found.
	"""
	return safeCall(lambda: winUser.getAncestor(hwnd, winUser.GA_ROOT)) or hwnd


def isInForegroundApp(obj: NVDAObject | None) -> bool:
	hwnd = windowHandleOf(obj)
	if not hwnd:
		return False
	try:
		foreground = winUser.getForegroundWindow()
		if not foreground:
			return False
		rootOwner = winUser.getAncestor(hwnd, winUser.GA_ROOTOWNER)
		if rootOwner == winUser.getAncestor(foreground, winUser.GA_ROOTOWNER):
			return True
		if winUser.isDescendantWindow(foreground, hwnd) or winUser.isDescendantWindow(foreground, rootOwner):
			return True
		return _isInActiveStoreApp(hwnd)
	except Exception:  # noqa: BLE001
		return False


def isHungWindow(hwnd: int | None) -> bool:
	"""
	Whether the application owning a window has stopped responding.
	@param hwnd: The window, or None.
	@returns: False when there is no window.
	"""
	if not hwnd:
		return False
	root = _rootWindowOf(hwnd)
	return bool(safeCall(lambda: user32.dll.IsHungAppWindow(root), False))


def isChromiumWindow(hwnd: int) -> bool:
	"""
	Whether a window is in the top-level window of a Chromium-based application.
	@param hwnd: The window.
	@returns: False also when the class of its top-level window cannot be read.
	"""
	className = safeCall(lambda: winUser.getClassName(_rootWindowOf(hwnd))) or ""
	return className.startswith("Chrome_WidgetWin_")


def sharesRootWindow(first: NVDAObject, second: NVDAObject) -> bool:
	"""
	Whether two objects are in the same top-level window.
	@param first: One object.
	@param second: The other object.
	@returns: True also when either has no window to tell by.
	"""
	firstHwnd = windowHandleOf(first)
	secondHwnd = windowHandleOf(second)
	if not firstHwnd or not secondHwnd:
		return True
	return _rootWindowOf(firstHwnd) == _rootWindowOf(secondHwnd)


def _isInActiveStoreApp(hwnd: int) -> bool:
	if not winUser.getClassName(hwnd).startswith("Windows.UI.Core"):
		return False
	active = winUser.getGUIThreadInfo(0).hwndActive
	return bool(active and winUser.isDescendantWindow(active, hwnd))


FocusState = tuple[NVDAObject | None, list[NVDAObject]]


def currentFocus() -> FocusState:
	return safeCall(api.getFocusObject), list(safeCall(api.getFocusAncestors) or ())


def isReachableWindow(obj: NVDAObject | None) -> bool:
	if obj is None:
		return False
	hwnd = windowHandleOf(obj)
	return not hwnd or isShownWindow(hwnd)


def isShownWindow(hwnd: int) -> bool:
	"""
	Whether a window's top-level window is visible.
	@param hwnd: The window.
	@returns: True also when visibility cannot be read.
	"""
	root = _rootWindowOf(hwnd)
	return safeCall(lambda: winUser.isWindowVisible(root), True) is not False


class TrackedTarget:
	def __init__(
		self,
		uid: int,
		obj: NVDAObject | None,
		kind: str,
		overrides: Mapping[str, bool] | None = None,
	):
		self.uid = uid
		self._objects: tuple[NVDAObject | None, dict[int, NVDAObject]] = (None, {})
		self._objectsLock = threading.Lock()
		self._stateLock = threading.Lock()
		self.obj = obj
		self.kind = kind
		self.overrides: dict[str, bool] = dict(overrides) if overrides else {}
		self.identity: Identity = objectIdentity(obj) if obj is not None else {}
		self.title: str = self.identity.get("name") or ""
		self.wasInForeground = False
		self.lastSeenInForeground = False
		self.tabSelected = True
		self._tabDocument: tuple[NVDAObject, Any] | None = None
		self.ignoredGeneration = 0
		self.trackedTitle: str | None = None
		self.history: tuple[Change, ...] = ()
		self.resetTracking()

	def resetTracking(self):
		self.seenContent: OrderedDict[str, int] = OrderedDict()
		self.seenChars = 0
		self.prevTexts: frozenset[str] = frozenset()
		self.forgetIgnoredControls()
		self.announcedRun = 0
		self.lastChange: tuple[str, float] | None = None
		self.announcedDelta = ""
		self.staleCache = True
		self.shownTab: int | None = None
		self.settleUntil: float | None = None

	def recordChange(self, text: str, when: float) -> Change | None:
		"""
		Add a change to the history, dropping the oldest beyond the history size.
		@param text: The new content.
		@param when: When the change was found, as from time.time().
		@returns: The change recorded, or None while the history is off.
		"""
		with self._stateLock:
			limit = int(addonConfig.snapshot()["historySize"])
			if limit <= 0:
				return None
			change = Change(next(_changeSerials), when, text)
			self.history = (*self.history, change)[-limit:]
			return change

	def trimHistory(self):
		with self._stateLock:
			limit = int(addonConfig.snapshot()["historySize"])
			self.history = self.history[-limit:] if limit > 0 else ()

	def settleFor(self, seconds: float):
		self.settleUntil = time.monotonic() + seconds

	def isSettling(self) -> bool:
		return self.settleUntil is not None and time.monotonic() < self.settleUntil

	@property
	def obj(self) -> NVDAObject | None:
		found, copies = self._objects
		if found is None:
			return None
		thread = threading.get_ident()
		mine = copies.get(thread)
		if mine is not None:
			return mine
		mine = onThisThread(found)
		if mine is None:
			return found
		with self._objectsLock:
			if self._objects[0] is found:
				self._objects = (found, {**self._objects[1], thread: mine})
		return mine

	@obj.setter
	def obj(self, obj: NVDAObject | None):
		with self._objectsLock:
			self._objects = (obj, {} if obj is None else {threading.get_ident(): obj})

	def link(self, obj: NVDAObject, settleSeconds: float) -> bool:
		"""
		Link a target that has no object to one, ready to be tracked from scratch.
		@param obj: The object.
		@param settleSeconds: How long the target settles before changes in it count.
		@returns: Whether the target had no object and took this one.
		"""
		with self._objectsLock:
			if self._objects[0] is not None:
				return False
			self.resetTracking()
			self.wasInForeground = isInForegroundApp(obj)
			self.lastSeenInForeground = self.wasInForeground
			self.settleFor(settleSeconds)
			self._objects = (obj, {threading.get_ident(): obj})
			return True

	def replaceObject(self, obj: NVDAObject) -> bool:
		"""
		Swap in a fresh object for the target, unless it has been let go of meanwhile.
		@param obj: The object.
		@returns: Whether the target is still attached and took the object.
		"""
		with self._objectsLock:
			if self._objects[0] is None:
				return False
			self._objects = (obj, {threading.get_ident(): obj})
			return True

	def detachIf(self, found: NVDAObject) -> bool:
		"""
		Let go of the target's object, unless another has been swapped in meanwhile.
		@param found: The object the target was found to have lost.
		@returns: Whether the target still had that object and let go of it.
		"""
		with self._objectsLock:
			if self._objects[0] is not found:
				return False
			self._objects = (None, {})
			self.seenContent = OrderedDict()
			self.seenChars = 0
			self.prevTexts = frozenset()
			return True

	@property
	def attachedObject(self) -> NVDAObject | None:
		"""The object the target was found as, made on whichever thread found it."""
		return self._objects[0]

	@property
	def isAttached(self) -> bool:
		return self._objects[0] is not None

	def setting(self, key: str, settings: Settings | None = None) -> ConfigValue:
		overrides = self.overrides
		if key in overrides:
			return overrides[key]
		if settings is None:
			settings = addonConfig.snapshot()
		return settings[key]

	def setOverride(self, key: str, value: bool | None):
		overrides = dict(self.overrides)
		if value is None:
			overrides.pop(key, None)
		else:
			overrides[key] = bool(value)
		self.overrides = overrides

	def forgetIgnoredControls(self):
		with self._stateLock:
			self.ignoredTemplates: frozenset[str] = frozenset()
			self.ignoredGeneration += 1

	def learnIgnoredControls(self, templates: frozenset[str], generation: int):
		"""
		Add counters to ignore, unless the ignored ones were forgotten since the sweep that found them.
		@param templates: The counters found.
		@param generation: L{ignoredGeneration} before that sweep.
		"""
		with self._stateLock:
			if self.ignoredGeneration == generation:
				self.ignoredTemplates = self.ignoredTemplates | templates

	def isHeldToItsTitle(self, settings: Settings | None = None) -> bool:
		return self.kind == "window" and bool(self.setting("titleChangeDisappears", settings))

	def isForgottenWhenGone(self, settings: Settings | None = None) -> bool:
		if not self.setting("rememberTargets", settings):
			return True
		return bool(self.setting("forgetOnDisappear", settings))

	def captureTrackedTitle(self):
		with self._stateLock:
			held = self.isAttached and self.isHeldToItsTitle(addonConfig.snapshot())
			self.trackedTitle = self.title if held else None

	@property
	def name(self) -> str:
		return (self.title if self.isAttached else "") or self.identity.get("name") or ""

	@property
	def role(self) -> Role | None:
		remembered = self.identity.get("role")
		return safeCall(lambda: Role(remembered)) if remembered else None

	def roleText(self) -> str:
		role = self.role
		if role is None:
			return ""
		return safeCall(lambda: role.displayString) or ""

	def isAlive(self) -> bool:
		"""
		Whether the target was there at the last check and its window still is.
		@returns: False for a target that is not attached.
		"""
		found = self._objects[0]
		if found is None:
			return False
		hwnd = windowHandleOf(found)
		if hwnd and not winUser.isWindow(hwnd):
			return False
		return isReachableWindow(found)

	def freshObj(self) -> NVDAObject | None:
		"""
		This thread's object of the target, with nothing it read before kept.
		@returns: The object, or None while the target is not attached.
		"""
		obj = self.obj
		if obj is not None:
			safeCall(obj.invalidateCache)
		return obj

	def liveTitle(self) -> str | None:
		obj = self.freshObj()
		if obj is None or not self.isAlive():
			return None
		name = safeCall(lambda: obj.name, _UNREADABLE)
		if name is _UNREADABLE:
			return None
		return name or ""

	def isInForeground(self) -> bool:
		return isInForegroundApp(self._objects[0]) and self.tabSelected

	def updateTabSelected(self):
		"""Note whether a target inside a Firefox page is in the tab Firefox keeps up to date as the one shown."""
		found = self._objects[0]
		obj = self.obj
		if self.kind == "window" or found is None or obj is None or not gecko.isGecko(obj):
			self.tabSelected = True
			return
		cached = self._tabDocument
		active = gecko.isActiveDocument(cached[1]) if cached is not None and cached[0] is found else None
		if active is None:
			document = gecko.tabDocument(obj.IAccessibleObject)
			self._tabDocument = (found, document) if document is not None else None
			active = gecko.isActiveDocument(document) if document is not None else None
		self.tabSelected = active is not False

	def isHung(self) -> bool:
		return isHungWindow(windowHandleOf(self._objects[0]))

	def needsPreview(self) -> bool:
		"""
		Whether the target is in a Chromium window that is out of the foreground but not minimized.
		@returns: False for a target that is not attached or whose application has stopped responding.
		"""
		hwnd = windowHandleOf(self._objects[0])
		if not hwnd or self.lastSeenInForeground or not isChromiumWindow(hwnd) or isHungWindow(hwnd):
			return False
		return not safeCall(lambda: user32.dll.IsIconic(_rootWindowOf(hwnd)), False)

	def canTakeFocus(self) -> bool:
		if self.isHung() or not self.isAlive():
			return False
		if self.kind == "window":
			return True
		obj = self.obj
		states = safeCall(lambda: obj.states) if obj is not None else None
		return not (states and State.INVISIBLE in states)

	def isObject(self, obj: NVDAObject) -> bool:
		"""
		Whether an object is this target's, asking its application only when it is in the same top-level window.
		@param obj: The object.
		@returns: False while the target is not attached.
		"""
		found = self._objects[0]
		if found is None or not sharesRootWindow(found, obj):
			return False
		mine = self.obj
		return mine is not None and bool(safeCall(lambda: mine == obj, False))

	def hasFocus(self, focus: FocusState) -> bool:
		focusObj, ancestors = focus
		if not self.isAttached or focusObj is None:
			return False
		hwnd = windowHandleOf(self._objects[0])
		focusHwnd = windowHandleOf(focusObj)
		if hwnd and focusHwnd:
			root = _rootWindowOf(hwnd)
			if _rootWindowOf(focusHwnd) != root:
				return safeCall(lambda: winUser.getAncestor(focusHwnd, winUser.GA_ROOTOWNER)) == root
			if self.kind == "window":
				return True
		if self.kind == "window":
			return False
		obj = self.obj
		if obj is None:
			return False
		candidates = (focusObj, *reversed(ancestors))
		return any(safeCall(lambda c=candidate: obj == c, False) is True for candidate in candidates)

	def hasReportableChange(self) -> bool:
		if self.lastChange is None:
			return False
		return bool(self.setting("trackForegroundTargets")) or not self.isInForeground()

	def _reactivateWindow(self, obj: NVDAObject):
		hwnd = windowHandleOf(obj)
		if not hwnd or not winUser.isWindow(hwnd):
			return
		topHwnd = safeCall(lambda: winUser.getAncestor(hwnd, winUser.GA_ROOTOWNER)) or hwnd
		try:
			if user32.dll.IsIconic(topHwnd):
				user32.ShowWindow(topHwnd, _SW_RESTORE)
		except Exception:  # noqa: BLE001
			log.debugWarning("Could not restore target window", exc_info=True)
		try:
			winUser.setForegroundWindow(topHwnd)
		except Exception:  # noqa: BLE001
			log.debugWarning("Could not bring target window to the foreground", exc_info=True)

	def setFocus(self, onFailure: Callable[[], None] | None = None) -> bool:
		obj = self.obj
		if obj is None:
			return False
		hwnd = windowHandleOf(obj)
		if hwnd and not winUser.isWindow(hwnd):
			return False
		self._reactivateWindow(obj)
		if self.kind != "window" and gecko.isGecko(obj):
			document = gecko.tabDocument(obj.IAccessibleObject)
			if document is not None and not gecko.isInSelectedTab(document):
				gecko.selectTab(document)
		core.callLater(250, self._doSetFocus, obj, onFailure)
		return True

	def _doSetFocus(self, obj: NVDAObject, onFailure: Callable[[], None] | None = None):
		try:
			obj.setFocus()
		except Exception:  # noqa: BLE001
			log.debugWarning("Could not set focus to target", exc_info=True)
			if onFailure is not None:
				onFailure()


class TargetRegistry:
	MAX_SLOTS = 10

	def __init__(self):
		self._targets: list[TrackedTarget] = []
		self._nextUid = 1
		self._lock = threading.RLock()

	def __iter__(self) -> Iterator[TrackedTarget]:
		with self._lock:
			return iter(list(self._targets))

	def __contains__(self, target: object) -> bool:
		with self._lock:
			return target in self._targets

	def __len__(self) -> int:
		with self._lock:
			return len(self._targets)

	def _newUid(self) -> int:
		uid = self._nextUid
		self._nextUid += 1
		return uid

	def add(
		self,
		obj: NVDAObject,
		kind: str,
		overrides: Mapping[str, bool] | None,
		prepare: Callable[[TrackedTarget], None],
	) -> TrackedTarget:
		"""
		Start tracking an object.
		@param obj: The object.
		@param kind: What the object was taken as, such as "window".
		@param overrides: The target's own settings.
		@param prepare: Readies the new target before the list holds it.
		@returns: The target.
		"""
		with self._lock:
			target = TrackedTarget(self._newUid(), obj, kind, overrides)
		prepare(target)
		with self._lock:
			self._targets.append(target)
		return target

	def addDetached(
		self,
		identity: Identity,
		kind: str,
		overrides: Mapping[str, bool] | None = None,
	) -> TrackedTarget:
		with self._lock:
			target = TrackedTarget(self._newUid(), None, kind, overrides)
			target.identity = identity or {}
			self._targets.append(target)
			return target

	def remove(self, target: TrackedTarget) -> bool:
		with self._lock:
			if target in self._targets:
				self._targets.remove(target)
				return True
			return False

	def clear(self):
		with self._lock:
			self._targets = []

	def findByObject(self, obj: NVDAObject | None) -> TrackedTarget | None:
		if obj is None:
			return None
		with self._lock:
			candidates = list(self._targets)
		for target in candidates:
			if target.isObject(obj):
				return target
		return None

	def sortedTargets(self, order: str) -> list[TrackedTarget]:
		with self._lock:
			ordered = list(self._targets)
		reverse = order in ("newest", "recentlyChanged", "reverseAlphabetical")
		if order in ("recentlyChanged", "leastRecentlyChanged"):

			def changed(target: TrackedTarget) -> float:
				lastChange = target.lastChange
				if lastChange is None or not (target.isAttached and target.hasReportableChange()):
					return 0.0
				return lastChange[1]

			ordered.sort(key=changed)
		elif order in ("alphabetical", "reverseAlphabetical"):
			ordered.sort(key=lambda target: _collationKey(target.name))
		if reverse:
			ordered.reverse()
		return ordered

	def slots(self) -> list[TrackedTarget]:
		return self.sortedTargets(str(addonConfig.get("slotSorting")))[: self.MAX_SLOTS]

	def slot(self, index: int) -> TrackedTarget | None:
		slots = self.slots()
		if 0 <= index < len(slots):
			return slots[index]
		return None

	def newest(self) -> TrackedTarget | None:
		with self._lock:
			return self._targets[-1] if self._targets else None

	def liveTargets(self) -> list[TrackedTarget]:
		with self._lock:
			return [t for t in self._targets if t.isAttached]

	def detachedTargets(self) -> list[TrackedTarget]:
		with self._lock:
			return [t for t in self._targets if not t.isAttached]
