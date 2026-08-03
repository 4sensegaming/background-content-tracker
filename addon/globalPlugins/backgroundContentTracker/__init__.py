# Background Content Tracker
# An NVDA add-on that tells you when new content appears in a window or control
# you are not focused on.
# Copyright (C) 2026 Lukáš Hosnedl
# This file is covered by the GNU General Public License, version 2.
# See the file COPYING.txt for more details.

"""The global plugin: it owns the subsystems (registry, monitor, notifier,
overlay, settings panel), exposes the single rebindable prefix gesture, and
implements every overlay command.
"""

import json
import time

import addonHandler
import api
import globalPluginHandler
import gui
import ui
import wx
from gui.settingsDialogs import NVDASettingsDialog
from logHandler import log
from scriptHandler import script

from . import addonConfig
from . import menu as menuModule
from . import settings as settingsModule
from .monitor import Monitor
from .notifier import Notifier
from .overlay import Overlay
from .targets import TargetRegistry, objectIdentity

addonHandler.initTranslation()


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	# Translators: the category for this add-on's commands in the Input Gestures
	# dialog, and its title in the Settings dialog.
	scriptCategory = _("Background Content Tracker")

	def __init__(self):
		super(GlobalPlugin, self).__init__()
		addonConfig.initialize()
		self.registry = TargetRegistry()
		self.notifier = Notifier()
		self.monitor = Monitor(self.registry, self.notifier)
		self.overlay = Overlay(self)
		# State for the "press a number again to move focus" behaviour.
		self._pendingKind = None
		self._pendingUid = None
		self._pendingTime = 0.0
		gui.settingsDialogs.NVDASettingsDialog.categoryClasses.append(settingsModule.BCTSettingsPanel)
		self._loadRememberedTargets()
		self.monitor.start()

	def terminate(self):
		try:
			self.monitor.stop()
		except Exception:
			log.debugWarning("Error stopping monitor", exc_info=True)
		try:
			self.overlay.close()
		except Exception:
			pass
		try:
			NVDASettingsDialog.categoryClasses.remove(settingsModule.BCTSettingsPanel)
		except ValueError:
			pass
		addonConfig.terminate()
		super(GlobalPlugin, self).terminate()

	# --- persistence of remembered targets ----------------------------------
	def _saveRememberedTargets(self):
		"""Persist the current target list.

		Written whatever "Remember targets" is set to, because the setting is read
		on the *loading* side. Skipping the write while it was off meant that
		turning it on saved nothing until the list next changed: tick the box,
		restart NVDA, and the targets you already had were gone.
		"""
		data = []
		for target in self.registry:
			identity = target.identity
			if not identity and target.obj is not None:
				identity = objectIdentity(target.obj)
			if identity:
				data.append({"identity": identity, "kind": target.kind})
		try:
			addonConfig.set("savedTargets", json.dumps(data))
		except Exception:
			log.debugWarning("Could not save remembered targets", exc_info=True)

	def _loadRememberedTargets(self):
		if not addonConfig.get("rememberTargets"):
			return
		raw = addonConfig.get("savedTargets") or ""
		if not raw:
			return
		try:
			data = json.loads(raw)
		except Exception:
			return
		for entry in data:
			identity = entry.get("identity")
			if identity:
				self.registry.addDetached(identity, entry.get("kind", "window"))

	# --- the single, rebindable prefix gesture ------------------------------
	@script(
		# Translators: the description of the main command, shown in Input Gestures.
		description=_(
			"Opens the Background Content Tracker command overlay: press and "
			"release it, then press a command key (H for help)"
		),
		gestures=["kb:NVDA+;"],
	)
	def script_openOverlay(self, gesture):
		# A fresh opening never continues a press-again-to-focus sequence left over
		# from a previous, already-closed overlay: only the re-arm within a single
		# open (the second press of a genuine double-press) may do that.
		self._pendingKind = None
		self.overlay.open()

	# --- overlay command implementations ------------------------------------
	def help(self):
		self._pendingKind = None
		lines = [
			# Translators: heading of the overlay help.
			_("Background Content Tracker commands:"),
			# Translators: overlay help line for the H key.
			_("H: this help"),
			# Translators: overlay help line for the W key.
			_("W: start or stop tracking the current window"),
			# Translators: overlay help line for the F key.
			_("F: start or stop tracking the focused control"),
			# Translators: overlay help line for the M key.
			_("M: start or stop tracking the control under the mouse pointer"),
			# Translators: overlay help line for the N key.
			_("N: start or stop tracking the navigator object"),
			# Translators: overlay help line for the T key.
			_("T: open the target menu"),
			# Translators: overlay help line for the number keys.
			_("1 through 0: speak information about the target in that slot; press again to move focus to it"),
			# Translators: overlay help line for Space and Enter.
			_("Space or Enter: the most recently added target"),
			# Translators: overlay help line for Control plus a number.
			_("Control plus a number: stop tracking the target in that slot"),
			# Translators: overlay help line for Backspace.
			_("Backspace: stop tracking the most recently added target"),
			# Translators: overlay help line for Delete.
			_("Delete: stop tracking all targets"),
			# Translators: overlay help line for the P key.
			_("P: pause or resume all tracking"),
		]
		ui.message(u"\n".join(lines))

	def _toggle(self, obj, kind):
		self._pendingKind = None
		if obj is None:
			return
		existing = self.registry.findByObject(obj)
		if existing is not None:
			self.registry.remove(existing)
			self.notifier.announceStopped(existing)
		else:
			target = self.registry.add(obj, kind)
			self.monitor.onAdded(target)
			self.notifier.announceTracking(target)
		self._saveRememberedTargets()

	def toggleWindow(self):
		self._toggle(api.getForegroundObject(), "window")

	def toggleFocus(self):
		self._toggle(api.getFocusObject(), "focus")

	def toggleMouse(self):
		self._toggle(api.getMouseObject(), "mouse")

	def toggleNavigator(self):
		self._toggle(api.getNavigatorObject(), "navigator")

	def slotInfo(self, index):
		target = self.registry.slot(index)
		if target is None:
			self._pendingKind = None
			self.notifier.noTargetInSlot(index + 1)
			return
		self._infoOrFocus(("slot", index), target)

	def newestInfo(self):
		target = self.registry.newest()
		if target is None:
			self._pendingKind = None
			self.notifier.noTargets()
			return
		self._infoOrFocus(("newest", None), target)

	def _infoOrFocus(self, pendingKind, target):
		now = time.time()
		timeout = addonConfig.get("overlayTimeout")
		if (
			self._pendingKind == pendingKind
			and self._pendingUid == target.uid
			and (now - self._pendingTime) <= timeout
		):
			# Second identical press within the window: move the focus.
			self._pendingKind = None
			self._focus(target)
		else:
			self.notifier.speakInfo(target)
			self._pendingKind = pendingKind
			self._pendingUid = target.uid
			self._pendingTime = now

	def _focus(self, target):
		"""Move focus to a target, re-resolving a stale control object first.

		A control's cached object goes stale when its app reshapes the tree (the
		control keeps its name and role but its old node is discarded), so it is
		re-located from its identity; if it can no longer be found it is reported
		as gone rather than focused in a stale location. A window keeps a stable
		top-level object and is focused directly, with no lookup at all.

		The lookup is asynchronous: it costs hundreds of cross-process reads, and
		this runs from a keypress, so doing it inline would freeze NVDA for as long
		as it takes. The focus therefore lands a moment later, through
		:meth:`_focusResolved`.
		"""
		if target.kind == "window":
			self._focusResolved(target, True)
			return
		self.monitor.relocateAsync(target, self._focusResolved)

	def _focusResolved(self, target, found):
		"""Focus a target once its object is known to be current. Main thread only."""
		if not found:
			self.notifier.focusFailed()
			return
		if not target.setFocus(self.notifier.focusFailed):
			self.notifier.focusFailed()

	def stopSlot(self, index):
		self._pendingKind = None
		target = self.registry.slot(index)
		if target is None:
			self.notifier.noTargetInSlot(index + 1)
			return
		self.registry.remove(target)
		self.notifier.announceStopped(target)
		self._saveRememberedTargets()

	def stopNewest(self):
		self._pendingKind = None
		target = self.registry.newest()
		if target is None:
			self.notifier.noTargets()
			return
		self.registry.remove(target)
		self.notifier.announceStopped(target)
		self._saveRememberedTargets()

	def clearAll(self):
		self._pendingKind = None
		self.registry.clear()
		self.notifier.allCleared()
		self._saveRememberedTargets()

	def togglePause(self):
		self._pendingKind = None
		newEnabled = not addonConfig.get("enabled")
		addonConfig.set("enabled", newEnabled)
		if newEnabled:
			self.notifier.resumed()
			if not self.registry.liveTargets():
				self.notifier.noTargets()
		else:
			self.notifier.paused()

	def openMenu(self):
		self._pendingKind = None
		# Capture the current-location sources now, before the menu takes focus.
		sources = self._captureSources()
		wx.CallAfter(menuModule.showTargetMenu, self, sources)

	def _captureSources(self):
		sources = []
		seen = []
		candidates = (
			("window", api.getForegroundObject()),
			("focus", api.getFocusObject()),
			("mouse", api.getMouseObject()),
			("navigator", api.getNavigatorObject()),
		)
		for kind, obj in candidates:
			if obj is None or self.registry.findByObject(obj) is not None:
				continue
			duplicate = False
			for previous in seen:
				try:
					if previous == obj:
						duplicate = True
						break
				except Exception:
					pass
			if duplicate:
				continue
			seen.append(obj)
			sources.append((kind, obj))
		return sources

	# --- actions invoked from the menu --------------------------------------
	def startTracking(self, obj, kind):
		if obj is None or self.registry.findByObject(obj) is not None:
			return
		target = self.registry.add(obj, kind)
		self.monitor.onAdded(target)
		self.notifier.announceTracking(target)
		self._saveRememberedTargets()

	def stopTracking(self, target):
		if self.registry.remove(target):
			self.notifier.announceStopped(target)
			self._saveRememberedTargets()

	def setFocusToTarget(self, target):
		self._focus(target)
