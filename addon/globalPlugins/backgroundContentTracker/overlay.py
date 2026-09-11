# Background Content Tracker: the layered-command overlay
# Copyright (C) 2026 Lukáš Hosnedl
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

import contextlib
from collections.abc import Callable
from typing import TYPE_CHECKING

import addonHandler
import core
import inputCore
import queueHandler
import ui
import wx
from keyboardHandler import KeyboardInputGesture
from logHandler import log
from speech.priorities import Spri

from . import addonConfig

if TYPE_CHECKING:
	from gettext import gettext as _  # noqa: TC004

	from . import GlobalPlugin

addonHandler.initTranslation()

CaptureFunc = Callable[[inputCore.InputGesture], bool]

_DIGIT_KEYS = {"1": 0, "2": 1, "3": 2, "4": 3, "5": 4, "6": 5, "7": 6, "8": 7, "9": 8, "0": 9}

_TOGGLE_KEYS = {
	"w": "window",
	"f": "focus",
	"m": "mouse",
	"n": "navigator",
}

_HANDOFF_ANNOUNCE_DELAY_MS = 400


class Overlay:
	def __init__(self, controller: "GlobalPlugin"):
		self.controller = controller
		self._armed = False
		self._timer: wx.CallLater | None = None
		self._prevCapture: CaptureFunc | None = None
		self._session = 0
		self.keyCount = 0
		self._captureRef = self._capture

	def open(self):
		self.keyCount += 1
		if self._armed:
			self._restartTimer()
			return
		self._prevCapture = inputCore.manager._captureFunc
		self._session += 1
		self._armed = True
		inputCore.manager._captureFunc = self._captureRef
		self._restartTimer()
		# Translators: announced when the command overlay opens.
		ui.message(_("Overlay opened"))
		if not addonConfig.get("enabled"):
			self.controller.notifier.paused()

	def close(self):
		self._session += 1
		self._cancelTimer()
		self._releaseCapture()

	def dismiss(self):
		self._end(0)

	def handOff(self):
		self._end(_HANDOFF_ANNOUNCE_DELAY_MS)

	def _end(self, announceDelayMs: int):
		if not self._armed:
			return
		self.close()
		# Translators: announced when the command overlay closes.
		text = _("Overlay closed")
		if announceDelayMs:
			core.callLater(announceDelayMs, ui.message, text, Spri.NORMAL)
		else:
			ui.message(text, speechPriority=Spri.NORMAL)

	def _restartTimer(self):
		self._cancelTimer()
		timeout = int(addonConfig.get("overlayTimeout"))
		if timeout <= 0:
			return
		self._timer = core.callLater(timeout * 1000, self._onTimeout, self._session)

	def _cancelTimer(self):
		if self._timer is not None:
			with contextlib.suppress(Exception):
				self._timer.Stop()
			self._timer = None

	def _onTimeout(self, session: int):
		self._timer = None
		if session != self._session:
			return
		self.dismiss()

	def _releaseCapture(self):
		self._armed = False
		with contextlib.suppress(Exception):
			if inputCore.manager._captureFunc is self._captureRef:
				inputCore.manager._captureFunc = self._prevCapture
		self._prevCapture = None

	def _capture(self, gesture: inputCore.InputGesture) -> bool:
		try:
			if not isinstance(gesture, KeyboardInputGesture):
				return True
			if not self._armed:
				self._releaseCapture()
				return True
			if gesture.isModifier:
				return True
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
		return False

	def _handleKey(self, key: str, mods: tuple[str, ...], session: int):
		if session != self._session:
			return
		self.keyCount += 1
		self._cancelTimer()
		if key == "escape" and not mods:
			self.dismiss()
			return
		try:
			recognised = self._dispatch(key, mods)
		except Exception:
			log.exception("Error running an overlay command")
			recognised = True
		if not recognised:
			ui.message(
				_(
					# Translators: announced when a key pressed in the overlay is not one of its commands.
					"Unknown command. Press H once for help, twice to display the help as a browseable message."
				)
			)
		if self._armed:
			self._restartTimer()

	def _dispatch(self, key: str, mods: tuple[str, ...]) -> bool:
		if key.startswith("numpad"):
			suffix = key[len("numpad") :]
			if suffix in _DIGIT_KEYS:
				key = suffix
			elif suffix == "enter":
				key = "enter"
		held = set(mods)
		c = self.controller

		if held == {"control"} and key in _DIGIT_KEYS:
			c.stopSlot(_DIGIT_KEYS[key])
			return True
		if key in _TOGGLE_KEYS and not held - {"control", "shift"}:
			overrides: dict[str, bool] = {}
			if "shift" in held:
				overrides["rememberTargets"] = True
			if "control" in held:
				overrides["trackForegroundTargets"] = True
			c.toggleSource(_TOGGLE_KEYS[key], overrides)
			return True
		if held:
			return False

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
