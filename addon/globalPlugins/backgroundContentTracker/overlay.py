# Background Content Tracker: the layered-command overlay
# Copyright (C) 2026 Lukáš Hosnedl
# This file is covered by the GNU General Public License, version 2.
# See the file COPYING.txt for more details.

"""A focus-safe "virtual overlay" that captures the command keys pressed after
the prefix gesture.

It is implemented with ``inputCore.manager._captureFunc`` — the same input
capture hook NVDA itself uses for Input Help.

The overlay is a **mode**, not a one-shot prompt. It takes the capture once, when
it opens, and keeps it across command after command until one of exactly three
things ends it:

* the user presses escape;
* the timeout elapses with no key pressed;
* a command hands the focus somewhere else — a dialog, the target menu, or a
  tracked target — and closes the overlay itself, so that the keys the user
  types there are not swallowed here.

Anything else leaves it open, a mistyped key included: that only says so and
waits for the next one. Closing over a mistake would cost the user the command
they actually meant to give, and they would have to press the prefix again to
get back to where they already were.

Every one of those endings is announced the same way, through :meth:`Overlay._end`
— never interrupting, because the announcement rides alongside a window
appearing and being announced, and it belongs after that rather than across it.

THREADING CONTRACT (this is critical, read before editing):

``_captureFunc`` is invoked *inline* by ``inputCore.manager.executeGesture``,
which NVDA calls from ``keyboardHandler.internal_keyDownEvent`` — and that runs
on the dedicated ``winInputHook`` thread servicing a ``WH_KEYBOARD_LL`` low-level
keyboard hook. A low-level hook callback must return promptly: while it has not
returned, Windows stops delivering keyboard input. Therefore :meth:`_capture`
must never touch wx (timers, menus), speech (``ui.message``, ``tones.beep``), or
any NVDAObject/COM API (``api.get*Object``) — doing so blocks the hook thread and
freezes all keyboard input system-wide. NVDA's own ``_inputHelpCaptor`` follows
exactly this discipline: it only queues a function and returns.

So :meth:`_capture` does the bare minimum on the hook thread — read the already
computed key name and hand off via ``queueHandler.queueFunction`` — while
:meth:`_handleKey` does the real work on the main thread. Timers are created and
stopped on the main thread only.
"""

import contextlib

import addonHandler
import core
import inputCore
import queueHandler
import ui
from keyboardHandler import KeyboardInputGesture
from logHandler import log
from speech.priorities import Spri

from . import addonConfig

addonHandler.initTranslation()

#: Maps a number-row/number-pad digit key name to a 0-based slot index.
_DIGIT_KEYS = {"1": 0, "2": 1, "3": 2, "4": 3, "5": 4, "6": 5, "7": 6, "8": 7, "9": 8, "0": 9}

#: The four commands that start or stop tracking something, and the source each
#: one takes its target from. They are the only commands that take modifiers of
#: their own: shift and control each switch on one of the target's local settings.
_TOGGLE_KEYS = {
	"w": "window",
	"f": "focus",
	"m": "mouse",
	"n": "navigator",
}

#: How long to hold back the closing announcement when a command has taken the
#: focus elsewhere. Long enough for the window it opened to have claimed the
#: focus and for NVDA to have begun announcing it, so that this queues behind
#: that announcement instead of being cut off by it. NVDA's own
#: ``ui.delayedMessage`` is no use here: its delay is one millisecond, meant only
#: to clear a UI change that has already happened.
_HANDOFF_ANNOUNCE_DELAY_MS = 400


class Overlay:
	"""Owns the open/close/timeout mechanics and routes each captured key."""

	def __init__(self, controller):
		#: The object implementing the command methods (the GlobalPlugin).
		self.controller = controller
		self._armed = False
		self._timer = None
		self._prevCapture = None
		#: Bumped by every open and every close, so that a timer or a queued key
		#: press belonging to a previous overlay session is ignored.
		self._session = 0
		#: A single, stable bound method. ``self._capture`` creates a *new* bound
		#: method object on every attribute access, so an ``is`` comparison
		#: against it would never match and the capture would never be released.
		self._captureRef = self._capture

	# --- main thread: opening and closing ------------------------------------
	def open(self):
		"""Open the overlay. Called from the prefix script, on the main thread."""
		if self._armed:
			self._restartTimer()  # a second prefix press just restarts the timeout
			return
		self._prevCapture = inputCore.manager._captureFunc
		self._session += 1
		self._armed = True
		inputCore.manager._captureFunc = self._captureRef
		self._restartTimer()
		# Translators: announced when the command overlay opens. "H" is the help key.
		ui.message(_("Background Content Tracker, H for help"))

	def close(self):
		"""Close the overlay silently. Used on plugin termination."""
		self._session += 1  # any timer or queued key still to come is now stale
		self._cancelTimer()
		self._releaseCapture()

	def dismiss(self):
		"""Close the overlay at the user's request: escape, or the timeout."""
		self._end(0)

	def handOff(self):
		"""Close the overlay because a command is taking the focus elsewhere.

		Called by every command that puts a dialog or the target menu on the
		screen, or moves the focus to a tracked target. Those same commands are
		also reachable from the target menu, with no overlay involved at all,
		which is why this says nothing when nothing is open.
		"""
		self._end(_HANDOFF_ANNOUNCE_DELAY_MS)

	def _end(self, announceDelayMs):
		"""Close an open overlay and announce it. Silent if it is not open."""
		if not self._armed:
			return
		self.close()
		# Translators: announced when the command overlay closes.
		text = _("Overlay closed")
		# Queued, never interrupting: when a command closed the overlay, this
		# rides alongside NVDA announcing whatever that command opened, and
		# talking over it would tell the user the one thing they did not need.
		if announceDelayMs:
			core.callLater(announceDelayMs, ui.message, text, Spri.NORMAL)
		else:
			ui.message(text, speechPriority=Spri.NORMAL)

	# --- main thread: the timeout --------------------------------------------
	def _restartTimer(self):
		"""(Re)start the inactivity timeout. Every command press earns a full one."""
		self._cancelTimer()
		timeoutMs = int(addonConfig.get("overlayTimeout")) * 1000
		self._timer = core.callLater(timeoutMs, self._onTimeout, self._session)

	def _cancelTimer(self):
		if self._timer is not None:
			# A timer that has already fired refuses to be stopped, and that is
			# exactly the case where there is nothing left to stop.
			with contextlib.suppress(Exception):
				self._timer.Stop()
			self._timer = None

	def _onTimeout(self, session):
		self._timer = None
		if session != self._session:
			return  # a later session owns the overlay now
		self.dismiss()

	# --- safe from any thread (plain attribute assignment only) --------------
	def _releaseCapture(self):
		self._armed = False
		# Reached from the keyboard hook thread as well, where nothing may be
		# allowed to raise; giving the capture back is best effort either way.
		with contextlib.suppress(Exception):
			if inputCore.manager._captureFunc is self._captureRef:
				inputCore.manager._captureFunc = self._prevCapture
		self._prevCapture = None

	# --- KEYBOARD HOOK THREAD: must be fast and non-blocking ------------------
	def _capture(self, gesture):
		"""Capture one command key. See the threading contract above: absolutely
		no wx, speech or NVDAObject/COM access may happen here.

		The capture is *not* given up per key. The overlay is a mode, so it stays
		installed for as long as the overlay is open and is released in exactly
		one place, :meth:`_releaseCapture`.
		"""
		try:
			if not isinstance(gesture, KeyboardInputGesture):
				return True  # let non-keyboard input pass; keep capturing
			if not self._armed:
				# The overlay closed underneath us; make sure we let go of input.
				self._releaseCapture()
				return True
			if gesture.isModifier:
				# A modifier on its own is nobody's command. Let it through and
				# say nothing: it is half of a keystroke, not a mistyped one.
				return True
			# These are plain strings NVDA has already computed on this thread in
			# order to look the gesture up; reading them is cheap and safe.
			key = (gesture.mainKeyName or "").lower()
			mods = tuple(sorted(modifier.lower() for modifier in gesture.modifierNames))
			queueHandler.queueFunction(
				queueHandler.eventQueue,
				self._handleKey,
				key,
				mods,
				self._session,
				_immediate=True,
			)
		except Exception:
			log.exception("Error in overlay capture function")
			self._releaseCapture()
		return False  # swallow the key

	# --- main thread: running the command ------------------------------------
	def _handleKey(self, key, mods, session):
		"""Run one captured command. Queued onto the main thread by _capture()."""
		if session != self._session:
			return  # belongs to a previous overlay session
		self._cancelTimer()
		if key == "escape" and not mods:
			self.dismiss()
			return
		try:
			recognised = self._dispatch(key, mods)
		except Exception:
			# A command that failed is still a command, and the overlay must not
			# be left holding the keyboard with no timeout to end it.
			log.exception("Error running an overlay command")
			recognised = True
		if not recognised:
			# Not a command, so it cannot be the second half of a double press
			# either: whatever was waiting to be repeated is forgotten, rather
			# than left to pair up with a press two keys later.
			self.controller.cancelPendingPress()
			# Translators: announced when a key pressed in the overlay is not one of its commands.
			ui.message(_("Unknown command, press H for help."))
		if self._armed:
			# Still open, so keep it open: the command did not hand the focus on.
			self._restartTimer()

	def _dispatch(self, key, mods):
		"""Route a captured key to a command.

		Returns True if it was a recognised command, False for anything else,
		which is reported and otherwise changes nothing.
		"""
		# Accept the number pad as well as the number row.
		if key.startswith("numpad"):
			suffix = key[len("numpad") :]
			if suffix in _DIGIT_KEYS:
				key = suffix
			elif suffix == "enter":
				key = "enter"
		mods = set(mods)
		c = self.controller

		if mods == {"control"} and key in _DIGIT_KEYS:
			c.stopSlot(_DIGIT_KEYS[key])
			return True
		if key in _TOGGLE_KEYS and not mods - {"control", "shift"}:
			# Held with one of these, the command still does exactly what it does
			# on its own; the modifiers only say what the target it adds is to be
			# given. Shift asks for this one target to be remembered, control for
			# it to be read even while it is in the foreground — each the local
			# form of the global setting of the same name, set on the target as it
			# is added rather than afterwards in the target menu. A press that
			# stops tracking has no target to give anything to, and the modifiers
			# are simply spent: they never reach an existing target.
			overrides = {}
			if "shift" in mods:
				overrides["rememberTargets"] = True
			if "control" in mods:
				overrides["trackForegroundTargets"] = True
			c.toggleSource(_TOGGLE_KEYS[key], overrides)
			return True
		if mods:
			return False  # any other modifier combination is not a command

		if key == "h":
			c.help()
		elif key == "t":
			c.openMenu()
		elif key == "p":
			c.togglePause()
		elif key == "s":
			c.openSettings()
		elif key == "i":
			c.openInputGestures()
		elif key in _DIGIT_KEYS:
			c.slotInfo(_DIGIT_KEYS[key])
		elif key in ("space", "enter"):
			c.newestInfo()
		elif key == "backspace":
			c.stopNewest()
		elif key == "delete":
			c.clearAll()
		else:
			return False
		return True
