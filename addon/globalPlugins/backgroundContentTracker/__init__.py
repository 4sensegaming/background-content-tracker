# Background Content Tracker
# An NVDA add-on that tells you when new content appears in a window or control
# you are not focused on.
# Copyright (C) 2026 Lukáš Hosnedl
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

import contextlib
import json
from collections.abc import Callable, Mapping, Sequence
from html import escape
from typing import TYPE_CHECKING, Any

import addonHandler
import api
import globalPluginHandler
import gui
import ui
import wx
from gui import blockAction
from gui.inputGestures import InputGesturesDialog
from gui.settingsDialogs import NVDASettingsDialog
from logHandler import log
from NVDAObjects import NVDAObject
from scriptHandler import script

from . import addonConfig
from . import menu as menuModule
from . import settings as settingsModule
from .addonConfig import ChangedKeys
from .monitor import Monitor
from .notifier import Notifier
from .overlay import Overlay
from .targets import TargetRegistry, TrackedTarget, currentFocus, safeCall

if TYPE_CHECKING:
	from gettext import gettext as _  # noqa: TC004

addonHandler.initTranslation()

_SOURCES: dict[str, Callable[[], NVDAObject | None]] = {
	"window": api.getForegroundObject,
	"focus": api.getFocusObject,
	"mouse": api.getMouseObject,
	"navigator": api.getNavigatorObject,
}

PendingKind = tuple[str, int | None]


def _helpDocument(heading: str, commands: Sequence[str]) -> str:
	items = "\n".join(f"\t<li>{escape(line)}</li>" for line in commands)
	return f"<h1>{escape(heading)}</h1>\n<ul>\n{items}\n</ul>"


class _InputGesturesAtCategory(InputGesturesDialog):
	def __init__(self, parent: wx.Window, category: str = "", *args: Any, **kwargs: Any):
		super().__init__(parent, *args, **kwargs)
		if category:
			self._selectCategory(category)

	def _selectCategory(self, category: str):
		try:
			for index, categoryVM in enumerate(self.gesturesVM.filteredGestures):
				if categoryVM.displayName != category:
					continue
				item = self.tree.GetItemByIndex((index,))
				self.tree.Expand(item)
				self.tree.SelectItem(item)
				return
		except Exception:  # noqa: BLE001
			log.debugWarning("Could not select the input gesture category", exc_info=True)


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	# Translators: the category for this add-on's commands in the Input Gestures
	# dialog, and its title in the Settings dialog.
	scriptCategory = _("Background Content Tracker")

	def __init__(self):
		super().__init__()
		addonConfig.initialize()
		self.registry = TargetRegistry()
		self.notifier = Notifier()
		self.monitor = Monitor(self.registry, self.notifier, self._saveRememberedTargets)
		self.overlay = Overlay(self)
		self._pending: tuple[PendingKind, int | None, int] | None = None
		NVDASettingsDialog.categoryClasses.append(settingsModule.BCTSettingsPanel)
		addonConfig.registerChangeHook(self._onSettingsChanged)
		self._loadRememberedTargets()
		self.monitor.start()

	def terminate(self):
		try:
			self.monitor.stop()
		except Exception:  # noqa: BLE001
			log.debugWarning("Error stopping monitor", exc_info=True)
		with contextlib.suppress(Exception):
			self.overlay.close()
		try:
			NVDASettingsDialog.categoryClasses.remove(settingsModule.BCTSettingsPanel)
		except ValueError:
			pass
		addonConfig.unregisterChangeHook(self._onSettingsChanged)
		addonConfig.terminate()
		super().terminate()

	def _onSettingsChanged(self, changed: ChangedKeys):
		if "titleChangeDisappears" in changed:
			self._recaptureTrackedTitles()
		if "ignoreCounters" in changed:
			self._forgetIgnoredControls()
		if "rememberTargets" in changed:
			self._dropUnkeptDetachedTargets()
			self._saveRememberedTargets()

	def _recaptureTrackedTitles(self):
		for target in self.registry:
			if "titleChangeDisappears" in target.overrides:
				continue
			target.captureTrackedTitle()

	def _forgetIgnoredControls(self):
		for target in self.registry:
			if "ignoreCounters" in target.overrides:
				continue
			target.forgetIgnoredControls()

	def _dropUnkeptDetachedTargets(self):
		settings = addonConfig.snapshot()
		for target in self.registry:
			if not target.isAttached and not target.setting("rememberTargets", settings):
				self.registry.remove(target)

	def _saveRememberedTargets(self):
		settings = addonConfig.snapshot()
		data: list[dict[str, Any]] = []
		for target in self.registry:
			if not target.setting("rememberTargets", settings):
				continue
			entry: dict[str, Any] = {"identity": target.identity, "kind": target.kind}
			if target.overrides:
				entry["overrides"] = dict(target.overrides)
			data.append(entry)
		try:
			addonConfig.setMany({"savedTargets": json.dumps(data)}, notify=False)
		except Exception:  # noqa: BLE001
			log.debugWarning("Could not save remembered targets", exc_info=True)

	def _loadRememberedTargets(self):
		raw = addonConfig.get("savedTargets") or ""
		if not raw:
			return
		try:
			data = json.loads(raw)
		except ValueError:
			return
		if not isinstance(data, list):
			return
		settings = addonConfig.snapshot()
		for entry in data:
			if not isinstance(entry, dict):
				continue
			identity = entry.get("identity")
			if not identity:
				continue
			overrides = addonConfig.sanitizeOverrides(entry.get("overrides"))
			if not overrides.get("rememberTargets", settings["rememberTargets"]):
				continue
			self.registry.addDetached(identity, entry.get("kind", "window"), overrides)

	@script(
		description=_(
			# Translators: the description of the main command, shown in Input Gestures.
			"Opens the Background Content Tracker command overlay: press and release it, then press a command key (H for help)"
		),
		gestures=["kb:NVDA+;"],
	)
	def script_openOverlay(self, gesture):
		self.overlay.open()

	def _isSecondPress(self, pendingKind: PendingKind, uid: int | None) -> bool:
		return self._pending == (pendingKind, uid, self.overlay.keyCount - 1)

	def _awaitSecondPress(self, pendingKind: PendingKind, uid: int | None):
		self._pending = (pendingKind, uid, self.overlay.keyCount)

	def help(self):
		# Translators: heading of the overlay help.
		heading = _("Background Content Tracker commands")
		commands = [
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
			_(
				# Translators: overlay help line for shift and control with W, F, M or N.
				"Add shift to W, F, M or N to remember that one target, control to read it even in the foreground, or both"
			),
			# Translators: overlay help line for the T key.
			_("T: open the target menu"),
			_(
				# Translators: overlay help line for the number keys.
				"1 through 0: speak information about the target in that slot; press again to move focus to it"
			),
			_(
				# Translators: overlay help line for Space and Enter.
				"Space or Enter: speak information about the most recently added target; press again to move focus to it"
			),
			# Translators: overlay help line for Control plus a number.
			_("Control plus a number: stop tracking the target in that slot"),
			# Translators: overlay help line for Backspace.
			_("Backspace: stop tracking the most recently added target"),
			# Translators: overlay help line for Delete.
			_("Delete: stop tracking all targets"),
			# Translators: overlay help line for the P key.
			_("P: pause or resume all tracking"),
			# Translators: overlay help line for the S key.
			_("S: open the add-on settings"),
			# Translators: overlay help line for the I key.
			_("I: open the add-on input gestures"),
			# Translators: overlay help line for the Escape key.
			_("Escape: close the overlay"),
		]
		if self._isSecondPress(("help", None), None):
			self.overlay.handOff()
			ui.browseableMessage(
				_helpDocument(heading, commands),
				_("Background Content Tracker"),
				isHtml=True,
			)
		else:
			ui.message("\n".join([heading] + commands))
			self._awaitSecondPress(("help", None), None)

	def toggleSource(self, kind: str, overrides: Mapping[str, bool] | None = None):
		obj = _SOURCES[kind]()
		if obj is None:
			return
		existing = self.registry.findByObject(obj)
		if existing is not None:
			self.stopTracking(existing)
		else:
			self.startTracking(obj, kind, overrides)

	def slotInfo(self, index: int):
		target = self.registry.slot(index)
		if target is None:
			self.notifier.noTargetInSlot(index + 1)
			return
		self._infoOrFocus(("slot", index), target)

	def newestInfo(self):
		target = self.registry.newest()
		if target is None:
			self.notifier.noTargets()
			return
		self._infoOrFocus(("newest", None), target)

	def _infoOrFocus(self, pendingKind: PendingKind, target: TrackedTarget):
		if self._isSecondPress(pendingKind, target.uid):
			if not target.canTakeFocus():
				self.notifier.focusFailed()
				return
			if target.hasFocus(currentFocus()):
				self.notifier.alreadyFocused()
				return
			self._focus(target)
		else:
			self.notifier.speakInfo(target)
			self._awaitSecondPress(pendingKind, target.uid)

	def _focus(self, target: TrackedTarget):
		self.overlay.handOff()
		if target.kind == "window":
			self._focusResolved(target, True)
			return
		self.monitor.relocateAsync(target, self._focusResolved)

	def _focusResolved(self, target: TrackedTarget, found: bool):
		if not found:
			self.notifier.focusFailed()
			return
		if not target.setFocus(self.notifier.focusFailed):
			self.notifier.focusFailed()

	def stopSlot(self, index: int):
		target = self.registry.slot(index)
		if target is None:
			self.notifier.noTargetInSlot(index + 1)
			return
		self.stopTracking(target)

	def stopNewest(self):
		target = self.registry.newest()
		if target is None:
			self.notifier.noTargets()
			return
		self.stopTracking(target)

	def clearAll(self):
		self.registry.clear()
		self.notifier.allCleared()
		self._saveRememberedTargets()

	def togglePause(self):
		newEnabled = not addonConfig.get("enabled")
		addonConfig.set("enabled", newEnabled)
		if newEnabled:
			self.notifier.resumed()
		else:
			self.notifier.paused()

	def openSettings(self):
		self.overlay.handOff()
		wx.CallAfter(
			gui.mainFrame.popupSettingsDialog,
			NVDASettingsDialog,
			settingsModule.BCTSettingsPanel,
		)

	def openInputGestures(self):
		self.overlay.handOff()
		wx.CallAfter(self._showInputGestures)

	@blockAction.when(blockAction.Context.SECURE_MODE)
	def _showInputGestures(self):
		gui.mainFrame.popupSettingsDialog(
			_InputGesturesAtCategory,
			category=self.scriptCategory,
		)

	def openMenu(self):
		self.overlay.handOff()
		sources = self._captureSources()
		wx.CallAfter(menuModule.showTargetMenu, self, sources, currentFocus())

	def _captureSources(self) -> list[menuModule.Source]:
		sources: list[menuModule.Source] = []
		seen: list[NVDAObject] = []
		for kind, getter in _SOURCES.items():
			obj = getter()
			if obj is None or self.registry.findByObject(obj) is not None:
				continue
			if any(safeCall(lambda p=previous, o=obj: p == o, False) for previous in seen):
				continue
			seen.append(obj)
			sources.append((kind, obj))
		return sources

	def startTracking(
		self,
		obj: NVDAObject | None,
		kind: str,
		overrides: Mapping[str, bool] | None = None,
	):
		if obj is None or self.registry.findByObject(obj) is not None:
			return
		target = self.registry.add(obj, kind, overrides)
		self.monitor.onAdded(target)
		self.notifier.announceTracking(target)
		self._saveRememberedTargets()

	def stopTracking(self, target: TrackedTarget):
		if self.registry.remove(target):
			self.notifier.announceStopped(target)
			self._saveRememberedTargets()

	def setFocusToTarget(self, target: TrackedTarget):
		self._focus(target)

	def setTargetOverride(self, target: TrackedTarget, key: str, value: bool):
		target.setOverride(key, value)
		if key == "titleChangeDisappears":
			target.captureTrackedTitle()
		elif key == "ignoreCounters":
			target.forgetIgnoredControls()
		elif key == "rememberTargets" and not value:
			self._dropUnkeptDetachedTargets()
		self._saveRememberedTargets()
