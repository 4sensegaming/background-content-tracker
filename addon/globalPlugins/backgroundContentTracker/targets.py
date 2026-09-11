# Background Content Tracker: tracked targets and the target registry
# Copyright (C) 2026 Lukáš Hosnedl
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

import locale
import threading
import time
from collections import OrderedDict
from collections.abc import Callable, Iterator, Mapping
from typing import Any

import api
import core
import winUser
from controlTypes import Role, State
from logHandler import log
from NVDAObjects import NVDAObject
from NVDAObjects.IAccessible import getNVDAObjectFromEvent
from winBindings import user32

from . import addonConfig
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


def _rootWindowOf(hwnd: int) -> int | None:
	return safeCall(lambda: winUser.getAncestor(hwnd, winUser.GA_ROOT))


def isInForegroundApp(obj: NVDAObject | None) -> bool:
	if obj is None:
		return False
	hwnd = safeCall(lambda: obj.windowHandle)
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
	hwnd = safeCall(lambda: obj.windowHandle)
	if not hwnd:
		return True
	root = _rootWindowOf(hwnd) or hwnd
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
		self.obj = obj
		self.kind = kind
		self.overrides: dict[str, bool] = dict(overrides) if overrides else {}
		self.identity: Identity = objectIdentity(obj) if obj is not None else {}
		self.wasInForeground = False
		self.lastSeenInForeground = False
		self.trackedTitle: str | None = None
		self.resetTracking()

	def resetTracking(self):
		self.seenContent: OrderedDict[str, int] = OrderedDict()
		self.seenChars = 0
		self.prevTexts: frozenset[str] = frozenset()
		self.ignoredTemplates: frozenset[str] = frozenset()
		self.announcedRun = 0
		self.lastDelta = ""
		self.lastChangeTime: float | None = None
		self.announcedDelta = ""
		self.staleCache = True
		self.settleUntil: float | None = None

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

	@property
	def isAttached(self) -> bool:
		return self._objects[0] is not None

	def setting(self, key: str, settings: Settings | None = None) -> ConfigValue:
		if key in self.overrides:
			return self.overrides[key]
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
		self.ignoredTemplates = frozenset()

	def isHeldToItsTitle(self, settings: Settings | None = None) -> bool:
		return self.kind == "window" and bool(self.setting("titleChangeDisappears", settings))

	def isForgottenWhenGone(self, settings: Settings | None = None) -> bool:
		if not self.setting("rememberTargets", settings):
			return True
		return bool(self.setting("forgetOnDisappear", settings))

	def captureTrackedTitle(self, settings: Settings | None = None):
		self.trackedTitle = (
			titleOf(self.obj) if self.obj is not None and self.isHeldToItsTitle(settings) else None
		)

	@property
	def name(self) -> str:
		obj = self.obj
		current = safeCall(lambda: obj.name) if obj is not None else None
		return current or self.identity.get("name") or ""

	@property
	def role(self) -> Role | None:
		obj = self.obj
		if obj is not None:
			return safeCall(lambda: obj.role)
		return None

	def roleText(self) -> str:
		role = self.role
		if role is None:
			return ""
		return safeCall(lambda: role.displayString) or ""

	def isAlive(self) -> bool:
		return self.liveTitle() is not None

	def liveTitle(self) -> str | None:
		obj = self.obj
		if obj is None:
			return None
		hwnd = safeCall(lambda: obj.windowHandle)
		if hwnd and not winUser.isWindow(hwnd):
			return None
		if not isReachableWindow(obj):
			return None
		name = safeCall(lambda: obj.name, _UNREADABLE)
		if name is _UNREADABLE:
			return None
		return name or ""

	def isInForeground(self) -> bool:
		return isInForegroundApp(self.obj)

	def canTakeFocus(self) -> bool:
		obj = self.obj
		if obj is None:
			return False
		hwnd = safeCall(lambda: obj.windowHandle)
		if hwnd:
			root = _rootWindowOf(hwnd) or hwnd
			if safeCall(lambda: user32.dll.IsHungAppWindow(root), False):
				return False
		if not self.isAlive():
			return False
		if self.kind == "window":
			return True
		states = safeCall(lambda: obj.states)
		return not (states and State.INVISIBLE in states)

	def hasFocus(self, focus: FocusState) -> bool:
		obj = self.obj
		focusObj, ancestors = focus
		if obj is None or focusObj is None:
			return False
		hwnd = safeCall(lambda: obj.windowHandle)
		focusHwnd = safeCall(lambda: focusObj.windowHandle)
		root = _rootWindowOf(hwnd) if hwnd else None
		if root and focusHwnd:
			focusRoot = _rootWindowOf(focusHwnd)
			if focusRoot and focusRoot != root:
				return safeCall(lambda: winUser.getAncestor(focusHwnd, winUser.GA_ROOTOWNER)) == root
			if focusRoot and self.kind == "window":
				return True
		if self.kind == "window":
			return False
		candidates = (focusObj, *reversed(ancestors))
		return any(safeCall(lambda c=candidate: obj == c, False) is True for candidate in candidates)

	def hasReportableChange(self) -> bool:
		if self.lastChangeTime is None:
			return False
		return bool(self.setting("trackForegroundTargets")) or not self.isInForeground()

	def _reactivateWindow(self, obj: NVDAObject):
		hwnd = safeCall(lambda: obj.windowHandle)
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
		hwnd = safeCall(lambda: obj.windowHandle)
		if hwnd and not winUser.isWindow(hwnd):
			return False
		self._reactivateWindow(obj)
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

	def _newUid(self) -> int:
		uid = self._nextUid
		self._nextUid += 1
		return uid

	def add(
		self,
		obj: NVDAObject,
		kind: str,
		overrides: Mapping[str, bool] | None = None,
	) -> TrackedTarget:
		with self._lock:
			target = TrackedTarget(self._newUid(), obj, kind, overrides)
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
			if target.obj is not None and safeCall(lambda t=target: t.obj == obj, False):
				return target
		return None

	def sortedTargets(self, order: str) -> list[TrackedTarget]:
		with self._lock:
			ordered = list(self._targets)
		reverse = order in ("newest", "recentlyChanged", "reverseAlphabetical")
		if order in ("recentlyChanged", "leastRecentlyChanged"):

			def changed(target: TrackedTarget) -> float:
				reportable = target.isAttached and target.hasReportableChange()
				return (target.lastChangeTime or 0.0) if reportable else 0.0

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
