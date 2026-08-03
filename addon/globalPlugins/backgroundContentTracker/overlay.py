# Background Content Tracker: the layered-command overlay
# Copyright (C) 2026 Lukáš Hosnedl
# This file is covered by the GNU General Public License, version 2.
# See the file COPYING.txt for more details.

"""A focus-safe "virtual overlay" that captures the single command key pressed
after the prefix gesture.

It is implemented with ``inputCore.manager._captureFunc`` — the same one-shot
input-capture hook NVDA itself uses for Input Help.

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
computed key name, release the capture, and hand off via
``queueHandler.queueFunction`` — while :meth:`_handleKey` does the real work on
the main thread. Timers are created and stopped on the main thread only.
"""

import addonHandler
import core
import inputCore
import queueHandler
import ui
from keyboardHandler import KeyboardInputGesture
from logHandler import log

from . import addonConfig

addonHandler.initTranslation()

#: Maps a number-row/number-pad digit key name to a 0-based slot index.
_DIGIT_KEYS = {"1": 0, "2": 1, "3": 2, "4": 3, "5": 4, "6": 5, "7": 6, "8": 7, "9": 8, "0": 9}


class Overlay(object):
	"""Owns the arm/disarm/timeout mechanics and routes the captured key."""

	def __init__(self, controller):
		#: The object implementing the command methods (the GlobalPlugin).
		self.controller = controller
		self._armed = False
		self._timer = None
		self._prevCapture = None
		#: Incremented on every open, so a late timer or a queued key press
		#: belonging to a previous overlay session is ignored.
		self._session = 0
		#: A single, stable bound method. ``self._capture`` creates a *new* bound
		#: method object on every attribute access, so an ``is`` comparison
		#: against it would never match and the capture would never be released.
		self._captureRef = self._capture

	# --- main thread ---------------------------------------------------------
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
		"""Close the overlay silently (used on plugin termination)."""
		self._cancelTimer()
		self._releaseCapture()

	def _restartTimer(self):
		self._cancelTimer()
		timeoutMs = int(addonConfig.get("overlayTimeout")) * 1000
		self._timer = core.callLater(timeoutMs, self._onTimeout, self._session)

	def _cancelTimer(self):
		if self._timer is not None:
			try:
				self._timer.Stop()
			except Exception:
				pass
			self._timer = None

	def _onTimeout(self, session):
		self._timer = None
		if session != self._session or not self._armed:
			return  # a key was already handled, or this is a stale session
		self._releaseCapture()
		# Translators: announced when the overlay closes on its own or after an invalid key.
		ui.message(_("Overlay closed"))

	def _handleKey(self, key, mods, session):
		"""Run the captured command. Queued onto the main thread by _capture()."""
		if session != self._session:
			return  # belongs to a previous overlay session
		self._cancelTimer()
		if not self._dispatch(key, mods):
			# Translators: announced when the overlay closes on its own or after an invalid key.
			ui.message(_("Overlay closed"))
			return
		# A command that spoke info and is waiting for a confirming second press
		# (e.g. a number key, to then move focus) keeps the overlay open so that
		# second press is captured here rather than leaking to the focused app.
		if getattr(self.controller, "_pendingKind", None) is not None:
			self._rearm()

	def _rearm(self):
		"""Re-open the capture without re-announcing, to await a second press.

		Mirrors :meth:`open` minus the arm-check and the greeting. Bumps the
		session so any timer or queued key from the just-handled press is ignored.
		"""
		self._prevCapture = inputCore.manager._captureFunc
		self._session += 1
		self._armed = True
		inputCore.manager._captureFunc = self._captureRef
		self._restartTimer()

	# --- safe from any thread (plain attribute assignment only) --------------
	def _releaseCapture(self):
		self._armed = False
		try:
			if inputCore.manager._captureFunc is self._captureRef:
				inputCore.manager._captureFunc = self._prevCapture
		except Exception:
			pass
		self._prevCapture = None

	# --- KEYBOARD HOOK THREAD: must be fast and non-blocking ------------------
	def _capture(self, gesture):
		"""Capture the follow-up gesture. See the threading contract above:
		absolutely no wx, speech or NVDAObject/COM access may happen here."""
		try:
			if not isinstance(gesture, KeyboardInputGesture):
				return True  # let non-keyboard input pass; keep waiting
			if not self._armed:
				# The overlay already timed out; make sure we let go of input.
				self._releaseCapture()
				return True
			if gesture.isModifier:
				return True  # ignore lone modifiers; keep waiting for a real key
			# These are plain strings NVDA has already computed on this thread in
			# order to look the gesture up; reading them is cheap and safe.
			key = (gesture.mainKeyName or "").lower()
			mods = tuple(sorted(modifier.lower() for modifier in gesture.modifierNames))
			session = self._session
			self._releaseCapture()
			queueHandler.queueFunction(
				queueHandler.eventQueue,
				self._handleKey,
				key,
				mods,
				session,
				_immediate=True,
			)
		except Exception:
			log.error("Error in overlay capture function", exc_info=True)
			self._releaseCapture()
		return False  # swallow the follow-up key

	# --- main thread ---------------------------------------------------------
	def _dispatch(self, key, mods):
		"""Route a captured key to a command. Returns True if it was a recognised
		command, False for an invalid key (which closes the overlay).
		"""
		# Accept the number pad as well as the number row.
		if key.startswith("numpad"):
			suffix = key[len("numpad"):]
			if suffix in _DIGIT_KEYS:
				key = suffix
			elif suffix == "enter":
				key = "enter"
		mods = set(mods)
		c = self.controller

		if mods == {"control"} and key in _DIGIT_KEYS:
			c.stopSlot(_DIGIT_KEYS[key])
			return True
		if mods:
			return False  # any other modifier combination is not a command

		if key == "h":
			c.help()
		elif key == "w":
			c.toggleWindow()
		elif key == "f":
			c.toggleFocus()
		elif key == "m":
			c.toggleMouse()
		elif key == "n":
			c.toggleNavigator()
		elif key == "t":
			c.openMenu()
		elif key == "p":
			c.togglePause()
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
