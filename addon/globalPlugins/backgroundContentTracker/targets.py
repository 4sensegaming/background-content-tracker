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
from collections import OrderedDict

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


def titleOf(obj):
	"""The object's current title (its name), or "".

	Read live from the object rather than taken from the identity descriptor,
	which records the title the target was *added* with: telling those two apart
	is the whole point of "Consider changed title a disappeared target".
	"""
	return _safe(lambda: obj.name) or ""


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
	Both make an exception for a target whose "Track even foreground targets" is
	on, which is read and announced wherever it is.

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

	def __init__(self, uid, obj, kind, overrides=None):
		#: Unique, monotonically increasing id. Also encodes insertion order.
		self.uid = uid
		#: The live NVDAObject, or ``None`` when the target is detached (gone).
		self.obj = obj
		#: How the target was added: "window", "focus", "mouse" or "navigator".
		self.kind = kind
		#: This target's own values for the settings in
		#: :data:`addonConfig.LOCAL_KEYS`. Holds only the ones actually
		#: overridden: every other setting is inherited from the global
		#: configuration, so one the user changes later still moves this target.
		#: Rebound wholesale by :meth:`setOverride`, never mutated in place,
		#: because it is written on the main thread and read on the monitor one.
		self.overrides = dict(overrides) if overrides else {}
		#: Identity descriptor captured at creation, for re-location/persistence.
		self.identity = objectIdentity(obj) if obj is not None else {}
		self.createdTime = time.time()
		#: Every text this target is known to hold, mapped to how many copies of
		#: it are known: the multiset the monitor's change detection asks its one
		#: question of ("four copies now, three known, so one is new"). It records
		#: content rather than structure, so a control that merely slides around
		#: the tree as content arrives above it cannot be mistaken for something
		#: new. Ordered least recently seen first, which is the order the size
		#: caps evict in. Mutated in place by the monitor thread, which is the
		#: only thread that ever touches it.
		self.seenContent = OrderedDict()
		#: Total length of the keys of ``seenContent``, kept alongside it so the
		#: cache can be capped by weight without measuring it every poll.
		self.seenChars = 0
		#: The texts the previous sweep found. Not a cache and never consulted for
		#: change detection: it exists so that "Ignore repeatedly changing
		#: controls" can tell a control that replaced itself (its old text is gone
		#: this sweep) from a log that appended a line (its old lines are all
		#: still there).
		self.prevTexts = frozenset()
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
		#: Whether the target's application was in the foreground at the previous
		#: check. Only the previous state: what the monitor does about it depends
		#: on whether the target is tracked in the foreground as well.
		self.wasInForeground = False
		#: Whether the cache predates a spell the monitor did not read — because
		#: the user was in the target's application, or because the target was
		#: added while they were there. Such a sweep is folded into the cache
		#: silently instead of being diffed, so that nothing which happened while
		#: nobody was looking is announced afterwards.
		self.staleCache = False
		#: The window title this target was added with, or ``None``. Only ever
		#: set for a target that :meth:`isHeldToItsTitle` — that is, a whole
		#: window, while "Consider changed title a disappeared target" is on; a
		#: window that no longer carries it is then treated as gone rather than as
		#: merely changed. ``None`` for the entire life of anything else, a single
		#: control included: a title is not part of what such a target is.
		self.trackedTitle = None

	def setting(self, key, settings=None):
		"""The effective value of a local setting: this target's, or the global.

		``settings`` is a configuration snapshot. The monitor thread always has
		one to hand and passes it, because reading NVDA's live configuration
		belongs on the main thread; callers on the main thread can leave it out.
		"""
		if key in self.overrides:
			return self.overrides[key]
		if settings is None:
			settings = addonConfig.snapshot()
		return settings[key]

	def setOverride(self, key, value):
		"""Give this target its own value for a setting, or drop the override.

		A ``value`` of ``None`` removes the override, so the target inherits the
		global setting again. The dictionary is rebound rather than modified in
		place: it is written here on the main thread and read on the monitor one.
		"""
		overrides = dict(self.overrides)
		if value is None:
			overrides.pop(key, None)
		else:
			overrides[key] = bool(value)
		self.overrides = overrides

	def isHeldToItsTitle(self, settings=None):
		"""Whether this target is held to the window title it was added with.

		True only for a whole window with "Consider changed title a disappeared
		target" in force — its own value for the option where it has one, the
		global otherwise. A title says nothing about what a single control *is*,
		so the option is neither offered for one in the target menu nor consulted
		for one anywhere: this is the single statement of that rule, and the three
		places that care about a tracked title all ask it rather than restating it.

		Note this asks whether a title *should* be held to, not whether one has
		been recorded: a window added before the option was switched on globally
		answers True and still has no :attr:`trackedTitle` to be held to.

		``settings`` is a configuration snapshot, as for :meth:`setting`.
		"""
		return self.kind == "window" and bool(self.setting("titleChangeDisappears", settings))

	def captureTrackedTitle(self, settings=None):
		"""Take, or drop, the title this target is held to, as things stand now.

		Called wherever the answer may have just moved: when the target is added
		or re-attached, and when "Consider changed title a disappeared target" is
		switched for it, on the target itself or globally. A target that is not
		held to a title keeps none, and neither does one with no object to read a
		title from — a detached target takes its title when it re-attaches.

		Switching the option off therefore drops the title, and switching it back
		on takes the title the window carries *then*, not the one it carried
		before: a rename that happened while the option was off is not one the
		user asked to be told about, and holding the target to the older title
		would report it as gone the moment the option came back on.

		``settings`` is a configuration snapshot, as for :meth:`setting`.
		"""
		self.trackedTitle = (
			titleOf(self.obj)
			if self.obj is not None and self.isHeldToItsTitle(settings)
			else None
		)

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

		False before the target has changed at all since it was baselined, and —
		unless it is tracked in the foreground — false while the target is in the
		foreground, because the user is looking at it and any delta the monitor
		cached belongs to an earlier spell in the background. In both cases the
		query commands and the menu report "no changes" instead. A target tracked
		in the foreground is read while the user is there, so its cached delta
		describes what is on screen now and is reported like any other.
		"""
		if self.lastChangeTime is None:
			return False
		return self.setting("trackForegroundTargets") or not self.isInForeground()

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

	def add(self, obj, kind, overrides=None):
		with self._lock:
			target = TrackedTarget(self._newUid(), obj, kind, overrides)
			self._targets.append(target)
			return target

	def addDetached(self, identity, kind, overrides=None):
		with self._lock:
			target = TrackedTarget(self._newUid(), None, kind, overrides)
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
