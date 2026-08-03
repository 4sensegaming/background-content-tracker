# Background Content Tracker: tracked targets and the target registry
# Copyright (C) 2026 Lukáš Hosnedl
# This file is covered by the GNU General Public License, version 2.
# See the file COPYING.txt for more details.

"""The model layer: a :class:`TrackedTarget` wraps one tracked object together
with the cached content used for change detection, and :class:`TargetRegistry`
owns the ordered list of targets and maps it onto the ten numbered slots.

Nothing here speaks or beeps; that is the notifier's job. Nothing here polls;
that is the monitor's job. This keeps the model easy to reason about and test.
"""

import threading
import time

import core
import winUser
from logHandler import log

from . import addonConfig


def _safe(func, default=None):
	"""Call ``func`` and return its result, or ``default`` on any exception.

	Reading properties of a dead or cross-process accessible object frequently
	raises (``COMError`` and friends), so almost every access goes through this.
	"""
	try:
		return func()
	except Exception:
		return default


def appNameOf(obj):
	"""The object's application name, or "".

	Split out of :func:`objectIdentity` because it is the one field cheap enough
	to rule a whole window out with: one cross-process read against the six a full
	descriptor costs.
	"""
	return _safe(lambda: obj.appModule.appName) or ""


def objectIdentity(obj):
	"""Return a JSON-serialisable identity descriptor for an NVDAObject.

	Used both to recognise the same target again after it disappears and
	reappears, and to persist remembered targets across NVDA restarts.
	"""
	role = _safe(lambda: obj.role)
	return {
		"appName": appNameOf(obj),
		"windowClassName": _safe(lambda: obj.windowClassName) or "",
		"windowControlID": _safe(lambda: obj.windowControlID) or 0,
		"role": int(role) if role is not None else 0,
		"name": _safe(lambda: obj.name) or "",
		"automationID": _safe(lambda: obj.UIAAutomationId) or "",
	}


def identitiesMatch(a, b):
	"""Heuristic equality between two identity descriptors."""
	if not a or not b:
		return False
	# A stable automation id within the same app is a strong signal on its own.
	autoA, autoB = a.get("automationID"), b.get("automationID")
	if autoA and autoA == autoB and a.get("appName") == b.get("appName"):
		return True
	# Otherwise require app, window class and role to match, plus the name.
	for field in ("appName", "windowClassName", "role", "name"):
		if a.get(field) != b.get(field):
			return False
	return True


def isInForegroundApp(obj):
	"""Whether the object's window belongs to the foreground application.

	Such targets are neither read nor announced by the monitor: the whole point of
	the add-on is to report what you are *not* currently looking at. The query
	commands use it too, to report "no changes" for a target you are looking at.

	This mirrors NVDA's own foreground test in ``eventHandler.shouldAcceptEvent``.
	A simple "is it the foreground window" comparison is not enough: an owned
	dialog, a popup, or a child window such as the Office ribbon is not the
	foreground window itself, yet it belongs to the foreground application and
	shares its root owner.
	"""
	if obj is None:
		return False
	try:
		hwnd = obj.windowHandle
	except Exception:
		return False
	if not hwnd:
		return False
	try:
		foreground = winUser.getForegroundWindow()
		if not foreground:
			return False
		rootOwner = winUser.getAncestor(hwnd, winUser.GA_ROOTOWNER)
		if rootOwner == winUser.getAncestor(foreground, winUser.GA_ROOTOWNER):
			return True
		return bool(
			winUser.isDescendantWindow(foreground, hwnd)
			or winUser.isDescendantWindow(foreground, rootOwner)
		)
	except Exception:
		return False


class TrackedTarget(object):
	"""One tracked window or control, plus its change-detection state."""

	def __init__(self, uid, obj, kind):
		#: Unique, monotonically increasing id. Also encodes insertion order.
		self.uid = uid
		#: The live NVDAObject, or ``None`` when the target is detached (gone).
		self.obj = obj
		#: How the target was added: "window", "focus", "mouse" or "navigator".
		self.kind = kind
		#: Identity descriptor captured at creation, for re-location/persistence.
		self.identity = objectIdentity(obj) if obj is not None else {}
		self.createdTime = time.time()
		#: Baseline snapshot of the target's whole accessible subtree: one entry
		#: per control, mapping its structural key to its text. The keys tell the
		#: diff which control a text belongs to, the texts tell it what was already
		#: there, so a control that merely slides around the tree as content
		#: arrives is not mistaken for new content. Rebound wholesale, never
		#: mutated in place.
		self.cachedNodes = {}
		#: Templates (text with numeric runs collapsed) of repeatedly-changing
		#: controls already announced, mapped to the poll on which each last
		#: changed. Used to suppress timers and countdowns, and to forget one that
		#: has gone quiet. Reset on re-baseline.
		self.announcedControls = {}
		#: Count of background polls performed for this target. Drives the age-out
		#: of quiet controls in ``announcedControls``; advances every poll, even
		#: ones where nothing changed. Reset when the target is (re-)baselined.
		self.pollTick = 0
		#: Number of consecutive changes already announced for this target since
		#: it was last refocused. Capped by the "Changes to announce at once"
		#: setting; reset on re-baseline.
		self.announcedRun = 0
		#: The most recent surfaced content — the whole current text of the
		#: node(s) that changed, not the bare diff (used by speak-info and the menu).
		self.lastDelta = ""
		#: ``time.time()`` of the last detected change, or ``None``.
		self.lastChangeTime = None
		#: Whether the target's application was in the foreground at the last
		#: check. Used to re-baseline silently when the user switches away.
		self.wasInForeground = False

	@property
	def name(self):
		"""The target's display name, falling back to the remembered name."""
		current = _safe(lambda: self.obj.name) if self.obj is not None else None
		return current or self.identity.get("name") or ""

	@property
	def role(self):
		if self.obj is not None:
			return _safe(lambda: self.obj.role)
		return None

	def roleText(self):
		"""NVDA's own localised name for the control type, e.g. "window"."""
		role = self.role
		if role is None:
			return ""
		return _safe(lambda: role.displayString) or ""

	def isAlive(self):
		"""Whether the underlying object still exists and is reachable."""
		obj = self.obj
		if obj is None:
			return False
		hwnd = _safe(lambda: obj.windowHandle)
		if hwnd and not winUser.isWindow(hwnd):
			return False
		# Touch a cheap property to detect a dead COM object.
		try:
			obj.name
		except Exception:
			return False
		return True

	def isInForeground(self):
		"""Whether this target is currently in the foreground application."""
		return isInForegroundApp(self.obj)

	def hasReportableChange(self):
		"""Whether a manual query should surface a cached change for this target.

		False while the target is in the foreground — the user is looking at it, so
		any delta the monitor cached belongs to an earlier spell in the background —
		and false before the target has changed at all since it was baselined. In
		both cases the query commands and the menu report "no changes" instead.
		"""
		return self.lastChangeTime is not None and not self.isInForeground()

	def _reactivateWindow(self, obj):
		"""Un-minimise and bring the target's top-level window to the foreground.

		Best-effort: the OS may reject foregrounding from a background process, so
		failures here are logged and swallowed rather than treated as fatal.
		"""
		hwnd = _safe(lambda: obj.windowHandle)
		if not hwnd or not winUser.isWindow(hwnd):
			return
		topHwnd = _safe(lambda: winUser.getAncestor(hwnd, winUser.GA_ROOTOWNER)) or hwnd
		try:
			if winUser.user32.IsIconic(topHwnd):
				winUser.showWindow(topHwnd, winUser.SW_RESTORE)
			winUser.user32.SetForegroundWindow(topHwnd)
		except Exception:
			log.debugWarning("Could not reactivate target window", exc_info=True)

	def setFocus(self, onFailure=None):
		"""Move the system focus to this target.

		The top-level window is reactivated first (restored if minimised and
		brought to the foreground), then the focus call itself is deferred so the
		asynchronous restore has settled before it lands — focusing inline would
		land while the window is still iconic and be dropped. Reactivating alone is
		not enough even for a window target: it is ``obj.setFocus()`` that actually
		moves NVDA there, so it is issued for every kind.

		Because the focus call is deferred, its success is only known later and is
		reported through ``onFailure`` (called with no arguments if it fails); the
		bool returned here only says the attempt was scheduled against a live
		object, and a ``False`` return means the object is already gone. Note a
		*stale* control object still passes as live yet focuses nothing — the
		caller re-resolves such objects (see the monitor's ``relocate``) first.
		"""
		obj = self.obj
		if obj is None:
			return False
		hwnd = _safe(lambda: obj.windowHandle)
		if hwnd and not winUser.isWindow(hwnd):
			return False
		self._reactivateWindow(obj)
		core.callLater(250, self._doSetFocus, obj, onFailure)
		return True

	def _doSetFocus(self, obj, onFailure=None):
		"""Issue the deferred focus call for a control target. Main thread only."""
		try:
			obj.setFocus()
		except Exception:
			log.debugWarning("Could not set focus to target", exc_info=True)
			if onFailure is not None:
				onFailure()


class TargetRegistry(object):
	"""The ordered collection of targets, with slot and sort handling.

	Read from two threads: the main thread adds and removes targets, while the
	monitor thread iterates them once a second. Every access to ``_targets`` is
	therefore taken under ``_lock``, and the methods that hand targets out return
	a copy so that a caller can iterate it without holding anything.
	"""

	#: Number keys address at most this many targets; the menu addresses all.
	MAX_SLOTS = 10

	def __init__(self):
		self._targets = []
		self._nextUid = 1
		self._lock = threading.RLock()

	def __len__(self):
		with self._lock:
			return len(self._targets)

	def __iter__(self):
		with self._lock:
			return iter(list(self._targets))

	def _newUid(self):
		uid = self._nextUid
		self._nextUid += 1
		return uid

	def add(self, obj, kind):
		with self._lock:
			target = TrackedTarget(self._newUid(), obj, kind)
			self._targets.append(target)
			return target

	def addDetached(self, identity, kind):
		with self._lock:
			target = TrackedTarget(self._newUid(), None, kind)
			target.identity = identity or {}
			self._targets.append(target)
			return target

	def remove(self, target):
		with self._lock:
			if target in self._targets:
				self._targets.remove(target)
				return True
			return False

	def clear(self):
		with self._lock:
			removed = list(self._targets)
			self._targets = []
			return removed

	def findByObject(self, obj):
		if obj is None:
			return None
		with self._lock:
			candidates = list(self._targets)
		for target in candidates:
			if target.obj is not None and _safe(lambda t=target: t.obj == obj, False):
				return target
		return None

	def sortedTargets(self):
		"""Targets in the order dictated by the Target sorting setting."""
		with self._lock:
			ordered = list(self._targets)
		if addonConfig.get("targetSorting") == "newest":
			ordered.reverse()
		return ordered

	def slots(self):
		"""The (at most ten) targets addressable by the number keys."""
		return self.sortedTargets()[: self.MAX_SLOTS]

	def slot(self, index):
		"""The target in slot ``index`` (0-based), or ``None`` if empty."""
		slots = self.slots()
		if 0 <= index < len(slots):
			return slots[index]
		return None

	def newest(self):
		"""The most recently added target, regardless of sort order."""
		with self._lock:
			if not self._targets:
				return None
			return max(self._targets, key=lambda t: t.uid)

	def liveTargets(self):
		with self._lock:
			return [t for t in self._targets if t.obj is not None]

	def detachedTargets(self):
		with self._lock:
			return [t for t in self._targets if t.obj is None]
