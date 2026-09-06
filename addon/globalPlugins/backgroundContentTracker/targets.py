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
from winBindings import user32

from . import addonConfig

#: ``ShowWindow``'s "restore" command: show the window, and put it back to its
#: previous size and position if it is minimised. Stated here because NVDA's
#: ``winUser`` names neither this constant nor a ``ShowWindow`` to pass it to;
#: the call itself goes through ``winBindings``, which is where NVDA binds it.
_SW_RESTORE = 9


#: Handed to :func:`safeCall` as the default where a property that legitimately
#: answers ``None`` has to be told from one that could not be read at all.
_UNREADABLE = object()


def safeCall(func, default=None):
	"""Call ``func`` and return its result, or ``default`` on any exception.

	Reading properties of a dead or cross-process accessible object frequently
	raises, so almost every access in this add-on goes through this. The catch is
	deliberately as wide as it is: the accessibility APIs raise ``COMError``,
	``OSError``, ``AttributeError`` and more besides, and a property that cannot be
	read is never worth taking the add-on down for. This is the one place that
	blanket catch is written, which is why it is the one place it is excused.
	"""
	try:
		return func()
	except Exception:  # noqa: BLE001
		return default


def appNameOf(obj):
	"""The object's application name, or "".

	Split out of :func:`objectIdentity` because it is the one field cheap enough
	to rule a whole window out with: one cross-process read against the six a full
	descriptor costs.
	"""
	return safeCall(lambda: obj.appModule.appName) or ""


def titleOf(obj):
	"""The object's current title (its name), or "".

	Read live from the object rather than taken from the identity descriptor,
	which records the title the target was *added* with: telling those two apart
	is the whole point of "Consider changed title a disappeared target".
	"""
	return safeCall(lambda: obj.name) or ""


def objectIdentity(obj):
	"""Return a JSON-serialisable identity descriptor for an NVDAObject.

	Used both to recognise the same target again after it disappears and
	reappears, and to persist remembered targets across NVDA restarts.
	"""
	role = safeCall(lambda: obj.role)
	return {
		"appName": appNameOf(obj),
		"windowClassName": safeCall(lambda: obj.windowClassName) or "",
		"windowControlID": safeCall(lambda: obj.windowControlID) or 0,
		"role": int(role) if role is not None else 0,
		"name": safeCall(lambda: obj.name) or "",
		"automationID": safeCall(lambda: obj.UIAAutomationId) or "",
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
	shares its root owner. A Store app is not caught by any of that at all, and is
	asked about separately; see :func:`_isInActiveStoreApp`.

	A wrong answer here is not symmetrical. Calling a background target foreground
	costs an announcement that waits until the user leaves; calling a foreground
	one background makes the add-on read out the very application the user is
	working in, which is the one thing it promises never to do.
	"""
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
	# A window that cannot be placed is background: see the note above on which
	# way round it is safe to be wrong.
	except Exception:  # noqa: BLE001
		return False


def _isInActiveStoreApp(hwnd):
	"""Whether ``hwnd`` belongs to the Store app the user is working in.

	A UWP or WinUI window is not a descendant of the foreground window and does
	not share its root owner, so every test above calls it background while the
	user is typing in it. NVDA meets the same problem in ``shouldAcceptEvent``
	and settles it the same way (its #6713): such a window is always the active
	window of the input thread, or a descendant of it.

	Asked only once the cheap tests have all said no, because that is the whole
	of its cost — two local window-manager calls, no cross-process traffic — and
	because it can only ever turn a "no" into a "yes".
	"""
	if not winUser.getClassName(hwnd).startswith("Windows.UI.Core"):
		return False
	active = winUser.getGUIThreadInfo(0).hwndActive
	return bool(active and winUser.isDescendantWindow(active, hwnd))


class TrackedTarget:
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
		#: change detection: it exists so that "Ignore counters, steppers and
		#: timers" can tell a control that replaced itself (its old text is gone
		#: this sweep) from a log that appended a line (its old lines are all
		#: still there).
		self.prevTexts = frozenset()
		#: Templates (text with numeric runs collapsed) of the controls this
		#: target has been caught counting: ones that changed in nothing but their
		#: numbers. They are silenced from the moment they are recognised until
		#: the target is re-baselined or the option that recognises them moves.
		#: Rebound wholesale, never added to in place: the monitor thread writes
		#: it as it learns, and the main thread empties it when the option moves.
		self.ignoredTemplates = frozenset()
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
		#: the user was in the target's application, or because the target has not
		#: been baselined yet. Such a sweep is folded into the cache silently
		#: instead of being diffed, so that nothing which happened while nobody was
		#: looking is announced afterwards.
		#:
		#: True from the outset, because a target is in the registry — and so in
		#: front of the monitor thread — from the moment it is constructed, a moment
		#: before :meth:`.Monitor.onAdded` is reached. A poll landing in between
		#: would otherwise diff a whole window against an empty cache and read all
		#: of it out as new content.
		self.staleCache = True
		#: The window title this target was added with, or ``None``. Only ever
		#: set for a target that :meth:`isHeldToItsTitle` — that is, a whole
		#: window, while "Consider changed title a disappeared target" is on; a
		#: window that no longer carries it is then treated as gone rather than as
		#: merely changed. ``None`` for the entire life of anything else, a single
		#: control included: a title is not part of what such a target is.
		self.trackedTitle = None
		#: When this target may next be looked for while it is detached, as a
		#: ``time.time()``, and how long the wait after another failure. Zero for
		#: both means "at the next relocation pass", which is where every target
		#: starts and what attaching puts it back to. The policy behind them is
		#: the monitor's (:meth:`.Monitor._deferRelocate`), and so is the thread:
		#: nothing else ever writes them.
		self.nextRelocate = 0.0
		self.relocateDelay = 0.0

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

	def forgetIgnoredControls(self):
		"""Forget which of this target's controls were found to be counting.

		Called wherever "Ignore counters, steppers and timers" moves for this
		target — on the target itself, or globally for a target that inherits it.
		What is silenced was decided by the option, so the option moving has to
		un-decide it: switching off has to let those controls be heard again, and
		switching on again has to start watching from what they do next rather
		than from what they were caught doing before.
		"""
		self.ignoredTemplates = frozenset()

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

	def isForgottenWhenGone(self, settings=None):
		"""Whether this target is dropped from the list once it disappears.

		"Forget remembered targets when they disappear" only ever qualifies
		"Remember targets". Keeping a target that is gone is worth something only
		while something is going to look for it again, and looking for it again is
		exactly what "Remember targets" asks for: a target that is not remembered
		would sit in the list reading "not found" for the rest of the session with
		nothing on its way to find it. It is therefore always dropped, whatever
		the forgetting option says — which is also why that option is offered,
		here and in the settings panel, only while "Remember targets" is on.

		Both options are read per target, so one target may be kept where the
		global settings would drop it, and the other way round.

		``settings`` is a configuration snapshot, as for :meth:`setting`.
		"""
		if not self.setting("rememberTargets", settings):
			return True
		return bool(self.setting("forgetOnDisappear", settings))

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
			titleOf(self.obj) if self.obj is not None and self.isHeldToItsTitle(settings) else None
		)

	@property
	def name(self):
		"""The target's display name, falling back to the remembered name."""
		current = safeCall(lambda: self.obj.name) if self.obj is not None else None
		return current or self.identity.get("name") or ""

	@property
	def role(self):
		if self.obj is not None:
			return safeCall(lambda: self.obj.role)
		return None

	def roleText(self):
		"""NVDA's own localised name for the control type, e.g. "window"."""
		role = self.role
		if role is None:
			return ""
		return safeCall(lambda: role.displayString) or ""

	def isAlive(self):
		"""Whether the underlying object still exists and is reachable."""
		obj = self.obj
		if obj is None:
			return False
		hwnd = safeCall(lambda: obj.windowHandle)
		if hwnd and not winUser.isWindow(hwnd):
			return False
		# Touch a cheap property to detect a dead COM object. The sentinel is what
		# tells a name that is legitimately ``None`` from one that could not be read.
		return safeCall(lambda: obj.name, _UNREADABLE) is not _UNREADABLE

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

		The restore and the activation are guarded separately, because they fail
		separately and a window that cannot be restored is still worth raising.
		Under one guard, a failure of the first silently cost the second as well.
		"""
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
		hwnd = safeCall(lambda: obj.windowHandle)
		if hwnd and not winUser.isWindow(hwnd):
			return False
		self._reactivateWindow(obj)
		core.callLater(250, self._doSetFocus, obj, onFailure)
		return True

	def _doSetFocus(self, obj, onFailure=None):
		"""Issue the deferred focus call for a control target. Main thread only."""
		try:
			obj.setFocus()
		except Exception:  # noqa: BLE001
			log.debugWarning("Could not set focus to target", exc_info=True)
			if onFailure is not None:
				onFailure()


class TargetRegistry:
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
			self._targets = []

	def findByObject(self, obj):
		if obj is None:
			return None
		with self._lock:
			candidates = list(self._targets)
		for target in candidates:
			if target.obj is not None and safeCall(lambda t=target: t.obj == obj, False):
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
