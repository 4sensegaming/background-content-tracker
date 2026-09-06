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
from html import escape

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
from scriptHandler import script

from . import addonConfig
from . import menu as menuModule
from . import settings as settingsModule
from .monitor import Monitor
from .notifier import Notifier
from .overlay import Overlay
from .targets import TargetRegistry, objectIdentity

addonHandler.initTranslation()


def _helpDocument(heading, commands):
	"""The overlay help as HTML: a heading, then the commands as a list.

	A fragment rather than a whole document, because that is what
	:func:`ui.browseableMessage` asks for: it drops the fragment into NVDA's own
	``message.html`` template, which supplies the document, its title and its
	styling. The fragment is sanitised on the way in (``nh3.clean``, which keeps
	headings and lists), and every translated string is escaped here, so a
	translation containing an ampersand or an angle bracket cannot break the
	markup or lose a character to it.

	Real markup rather than preformatted text is what makes the dialog navigable:
	browse mode can jump to the heading with H and move through the commands with
	I, one list item at a time, instead of meeting one undifferentiated block.
	"""
	items = u"\n".join(u"\t<li>{0}</li>".format(escape(line)) for line in commands)
	return u"<h1>{0}</h1>\n<ul>\n{1}\n</ul>".format(escape(heading), items)


class _InputGesturesAtCategory(InputGesturesDialog):
	"""NVDA's Input Gestures dialog, opened with one category already selected.

	NVDA offers no supported way to open the dialog *at* a category, so an add-on
	has to arrange it for itself. Subclassing is how it gets a say in the dialog's
	construction: ``popupSettingsDialog`` passes its extra arguments straight to
	the class it instantiates, so the category travels in as a keyword argument
	and the dialog is ours before it is ever shown. The Check Input Gestures
	add-on takes the same route to open the dialog on a search term.

	Selecting the category rather than typing it into the dialog's filter box is
	deliberate. The filter matches script descriptions only, never category
	names, so filtering by this add-on's category would find it solely by the
	accident of the add-on's name occurring inside its own command descriptions —
	in every translation, in perpetuity. Selecting the node needs no such
	coincidence, and it leaves the rest of the tree in place to be navigated
	instead of hiding every other category behind a filter.
	"""

	def __init__(self, parent, category="", *args, **kwargs):
		super(_InputGesturesAtCategory, self).__init__(parent, *args, **kwargs)
		if category:
			self._selectCategory(category)

	def _selectCategory(self, category):
		"""Expand and select the category named ``category``, if it is there.

		Best-effort by design: the gesture tree is not a supported interface, so a
		future NVDA may rearrange it out from under this. A failure therefore
		costs the selection and nothing else — the dialog is up either way, on
		whichever category it opened at.
		"""
		try:
			for index, categoryVM in enumerate(self.gesturesVM.filteredGestures):
				if categoryVM.displayName != category:
					continue
				item = self.tree.GetItemByIndex((index,))
				self.tree.Expand(item)
				self.tree.SelectItem(item)
				return
		except Exception:
			log.debugWarning("Could not select the input gesture category", exc_info=True)


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
		# Which targets are persisted depends on "Remember targets", so the list
		# is re-written whenever the settings panel changes it.
		addonConfig.registerSaveHook(self._saveRememberedTargets)
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
		addonConfig.unregisterSaveHook(self._saveRememberedTargets)
		addonConfig.terminate()
		super(GlobalPlugin, self).terminate()

	# --- persistence of remembered targets ----------------------------------
	def _saveRememberedTargets(self):
		"""Persist the targets to be remembered, each with its own local settings.

		Only targets whose effective "Remember targets" is on are written, whether
		that is the global setting or the target's own: a one-time target is not
		meant to outlive the session, so neither it nor its local settings are
		stored at all. A target's overrides travel inside its own entry and never
		touch the global keys, so what one target was told is never mistaken for
		what everything else should do.

		Because the deciding is done here rather than on the loading side, the
		list is also re-written whenever the settings panel changes "Remember
		targets" (see the save hook registered in ``__init__``): ticking the box
		stores the targets already being tracked there and then, instead of
		waiting for the list to next change.
		"""
		settings = addonConfig.snapshot()
		data = []
		for target in self.registry:
			if not target.setting("rememberTargets", settings):
				continue
			identity = target.identity
			if not identity and target.obj is not None:
				identity = objectIdentity(target.obj)
			if not identity:
				continue
			entry = {"identity": identity, "kind": target.kind}
			if target.overrides:
				entry["overrides"] = dict(target.overrides)
			data.append(entry)
		try:
			# notify=False: this write is itself what the save hooks do, and must
			# not set them off again.
			addonConfig.setMany({"savedTargets": json.dumps(data)}, notify=False)
		except Exception:
			log.debugWarning("Could not save remembered targets", exc_info=True)

	def _loadRememberedTargets(self):
		"""Restore the saved targets, as detached entries to be relocated later."""
		raw = addonConfig.get("savedTargets") or ""
		if not raw:
			return
		try:
			data = json.loads(raw)
		except Exception:
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
			# Judged per entry rather than by the global setting alone: a target
			# can be remembered on its own account, and a list left by an older
			# version of the add-on — which stored every target and filtered here —
			# is still read exactly as it was meant to be.
			if not overrides.get("rememberTargets", settings["rememberTargets"]):
				continue
			self.registry.addDetached(identity, entry.get("kind", "window"), overrides)

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

	# --- the press-again-to-do-more rule ------------------------------------
	# A command that has more to offer on a second press speaks first and leaves a
	# press pending. The overlay stays open across commands anyway, so the second
	# press is captured there rather than reaching the app; what the pending press
	# decides is only whether it counts as a repeat. It is matched on the command
	# *and* its target, so 2 followed by 3 is two first presses, not a repeat.
	def _isSecondPress(self, pendingKind, uid):
		"""True if this press repeats the one still pending, within the timeout."""
		return (
			self._pendingKind == pendingKind
			and self._pendingUid == uid
			and (time.time() - self._pendingTime) <= addonConfig.get("overlayTimeout")
		)

	def _awaitSecondPress(self, pendingKind, uid):
		"""Record this press, so an identical one right after it counts as the second."""
		self._pendingKind = pendingKind
		self._pendingUid = uid
		self._pendingTime = time.time()

	def cancelPendingPress(self):
		"""Forget a press that was waiting to be repeated.

		Called by the overlay when a key that is no command at all is pressed:
		the sequence has been broken, so the next press starts afresh rather than
		pairing up with one from before the interruption.
		"""
		self._pendingKind = None

	# --- overlay command implementations ------------------------------------
	def help(self):
		"""Speak the overlay help; on a second press, open it in a browseable dialog.

		Spoken, it is the heading followed by one line per command. Shown, it is
		that same content as HTML in NVDA's own browseable message dialog — the
		one the formatting information is shown in — with the heading marked up as
		a level 1 heading and each command as an item of an unordered list.

		:func:`ui.browseableMessage` is deliberately called rather than any dialog
		class directly. It is the stable public API across the versions this
		add-on supports: it presents the old HTML dialog up to NVDA 2026.2 and the
		modernised, WebView-based one from 2026.3 onwards, without this add-on
		having to know which, and it is also what refuses to open a browseable
		message on a secure screen. Reaching past it for a specific dialog class
		would trade both of those away for nothing.
		"""
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
			# Translators: overlay help line for the S key.
			_("S: open the add-on settings"),
			# Translators: overlay help line for the I key.
			_("I: open the add-on input gestures"),
		]
		if self._isSecondPress(("help", None), None):
			self._pendingKind = None
			self.overlay.handOff()
			# The dialog title reuses the add-on name, an existing message, rather
			# than minting a new one.
			ui.browseableMessage(
				_helpDocument(heading, commands),
				_("Background Content Tracker"),
				isHtml=True,
			)
		else:
			ui.message(u"\n".join([heading] + commands))
			self._awaitSecondPress(("help", None), None)

	def _toggle(self, obj, kind, overrides=None):
		self._pendingKind = None
		if obj is None:
			return
		existing = self.registry.findByObject(obj)
		if existing is not None:
			self.registry.remove(existing)
			self.notifier.announceStopped(existing)
		else:
			target = self.registry.add(obj, kind, overrides)
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
		if self._isSecondPress(pendingKind, target.uid):
			# Second identical press within the window: move the focus.
			self._pendingKind = None
			self._focus(target)
		else:
			self.notifier.speakInfo(target)
			self._awaitSecondPress(pendingKind, target.uid)

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
		# Wherever the focus is going, it is not staying here: the overlay must
		# stop capturing before the user starts typing at the target. Silent when
		# this was invoked from the target menu instead of the overlay.
		self.overlay.handOff()
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

	def openSettings(self):
		"""Open NVDA's Settings dialog on this add-on's category.

		Put on screen from the main thread through ``wx.CallAfter``, as every one
		of NVDA's own commands that opens a dialog does.
		"""
		self._pendingKind = None
		self.overlay.handOff()
		wx.CallAfter(
			gui.mainFrame.popupSettingsDialog,
			NVDASettingsDialog,
			settingsModule.BCTSettingsPanel,
		)

	def openInputGestures(self):
		"""Open NVDA's Input Gestures dialog on this add-on's category."""
		self._pendingKind = None
		self.overlay.handOff()
		wx.CallAfter(self._showInputGestures)

	@blockAction.when(blockAction.Context.SECURE_MODE)
	def _showInputGestures(self):
		"""Put the dialog on screen. Main thread only.

		The secure-screen block is stated here because this opens the dialog
		itself instead of going through NVDA's menu command, which is where NVDA
		states it. Opening Input Gestures on a secure screen was removed from
		NVDA deliberately, as a security fix, and bypassing the menu command must
		not quietly bring it back.
		"""
		gui.mainFrame.popupSettingsDialog(
			_InputGesturesAtCategory,
			category=self.scriptCategory,
		)

	def openMenu(self):
		self._pendingKind = None
		self.overlay.handOff()
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
	def startTracking(self, obj, kind, overrides=None):
		"""Start tracking ``obj``, optionally with local settings of its own.

		``overrides`` maps keys of :data:`addonConfig.LOCAL_KEYS` to this
		target's own values for them; anything left out is inherited from the
		global configuration. They are handed to the registry rather than set
		afterwards because the monitor reads them in ``onAdded``, which decides
		there and then whether to hold the target to its window title.
		"""
		if obj is None or self.registry.findByObject(obj) is not None:
			return
		target = self.registry.add(obj, kind, overrides)
		self.monitor.onAdded(target)
		self.notifier.announceTracking(target)
		self._saveRememberedTargets()

	def stopTracking(self, target):
		if self.registry.remove(target):
			self.notifier.announceStopped(target)
			self._saveRememberedTargets()

	def setFocusToTarget(self, target):
		self._focus(target)
