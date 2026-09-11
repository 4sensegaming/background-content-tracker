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

import contextlib
import json
import time
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
from .targets import TargetRegistry, TrackedTarget, currentFocus, objectIdentity, safeCall

if TYPE_CHECKING:
	# NVDA puts the translation lookup into this module's namespace at run time,
	# which a type checker reading the source has no way of knowing. This says
	# what it will be; nothing is imported when the add-on is actually running,
	# which is what the suppression below records.
	from gettext import gettext as _  # noqa: TC004

addonHandler.initTranslation()

#: The four places a target can be taken from, each with the call that names
#: whatever is there right now. Stated once because three things address the
#: same four sources: the overlay's W, F, M and N keys, the target menu's
#: start-tracking items, and the ``kind`` every target carries for the rest of
#: its life. The order is the order the menu offers them in.
_SOURCES: dict[str, Callable[[], NVDAObject | None]] = {
	"window": api.getForegroundObject,
	"focus": api.getFocusObject,
	"mouse": api.getMouseObject,
	"navigator": api.getNavigatorObject,
}

#: What a press still waiting to be repeated was: the command, and which
#: target it named where it named one. Matched whole, so that a press on one
#: slot followed by a press on another is two first presses, not a repeat.
PendingKind = tuple[str, int | None]


def _helpDocument(heading: str, commands: Sequence[str]) -> str:
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
	items = "\n".join(f"\t<li>{escape(line)}</li>" for line in commands)
	return f"<h1>{escape(heading)}</h1>\n<ul>\n{items}\n</ul>"


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

	def __init__(self, parent: wx.Window, category: str = "", *args: Any, **kwargs: Any):
		super().__init__(parent, *args, **kwargs)
		if category:
			self._selectCategory(category)

	def _selectCategory(self, category: str):
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
		# The gesture tree is not a supported interface; a future NVDA rearranging
		# it costs the selection and nothing else.
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
		# The monitor drops targets that disappear and takes up ones that come
		# back, so the saved list has to be written out again when it does.
		self.monitor = Monitor(self.registry, self.notifier, self._saveRememberedTargets)
		self.overlay = Overlay(self)
		# State for the "press a number again to move focus" behaviour.
		self._pendingKind: PendingKind | None = None
		self._pendingUid: int | None = None
		self._pendingTime = 0.0
		NVDASettingsDialog.categoryClasses.append(settingsModule.BCTSettingsPanel)
		# Some global settings need something done to the targets that already
		# exist the moment they are switched; see ``_onSettingsChanged``.
		addonConfig.registerChangeHook(self._onSettingsChanged)
		self._loadRememberedTargets()
		self.monitor.start()

	def terminate(self):
		try:
			self.monitor.stop()
		# NVDA is going down either way; whatever the monitor made of being asked
		# to stop, the rest of this still has to run.
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

	# --- reacting to a change of the global settings ------------------------
	def _onSettingsChanged(self, changed: ChangedKeys):
		"""Bring the existing targets into line with a global setting that moved.

		Registered with :func:`addonConfig.registerChangeHook`, so it hears about
		a global changing however it changed — the settings panel being saved, or
		a configuration profile being switched to — and only about the keys that
		genuinely moved. Both of the things done here are the wrong thing to do to
		a target on a save that changed nothing about it.

		Everything not named here is read live, by the monitor or the notifier, and
		so needs nothing done to it when it changes.
		"""
		if "titleChangeDisappears" in changed:
			self._recaptureTrackedTitles()
		if "ignoreCounters" in changed:
			self._forgetIgnoredControls()
		if "rememberTargets" in changed:
			self._dropUnkeptDetachedTargets()
			self._saveRememberedTargets()

	def _recaptureTrackedTitles(self):
		"""Re-take every inheriting target's tracked title after a global switch.

		The title a window is held to is taken once, when the target is added, so
		switching "Consider changed title a disappeared target" on globally would
		otherwise do nothing at all for the targets already being tracked: they
		would carry no title to be held to, and would go on being reported as
		merely changed for the rest of their lives. Switching it off leaves them
		holding a title nothing consults. Either way the targets have to be taken
		round again, which is what this does.

		A target with its own value for the option is left alone: the global has
		not moved *it*, and re-taking its title would quietly re-baseline a window
		that has already renamed itself — the very thing it is being watched for.
		Only the targets that inherit the option are the ones the global changed.
		"""
		for target in self.registry:
			if "titleChangeDisappears" in target.overrides:
				continue
			target.captureTrackedTitle()

	def _forgetIgnoredControls(self):
		"""Let every inheriting target's counters be heard again after a global switch.

		What a target has silenced was decided by "Ignore counters, steppers and
		timers", so moving that option globally has to un-decide it: switching off
		must let those controls be announced again, and switching on again must
		start from what they do next. A target with its own value for the option
		is left alone, exactly as for a changed title: the global has not moved
		*it*.
		"""
		for target in self.registry:
			if "ignoreCounters" in target.overrides:
				continue
			target.forgetIgnoredControls()

	def _dropUnkeptDetachedTargets(self):
		"""Drop the entries that are gone and are no longer being kept.

		A target that has disappeared stays in the list only to be found again,
		and only "Remember targets" asks for that (see
		:meth:`.TrackedTarget.isForgottenWhenGone`). Switching it off — globally,
		or on one target in the target menu — therefore leaves such an entry with
		nothing on its way to find it, so it goes rather than sitting there
		reading "not found" for the rest of the session.

		Silent: the user was told the target was gone when it went, and this only
		settles what became of the entry afterwards.
		"""
		settings = addonConfig.snapshot()
		for target in self.registry:
			if target.obj is None and not target.setting("rememberTargets", settings):
				self.registry.remove(target)

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
		targets" (see ``_onSettingsChanged``): ticking the box stores the targets
		already being tracked there and then, instead of waiting for the list to
		next change.
		"""
		settings = addonConfig.snapshot()
		data: list[dict[str, Any]] = []
		for target in self.registry:
			if not target.setting("rememberTargets", settings):
				continue
			identity = target.identity
			if not identity and target.obj is not None:
				identity = objectIdentity(target.obj)
			if not identity:
				continue
			entry: dict[str, Any] = {"identity": identity, "kind": target.kind}
			if target.overrides:
				entry["overrides"] = dict(target.overrides)
			data.append(entry)
		try:
			# notify=False: this write is itself what the change hooks do, and
			# must not set them off again.
			addonConfig.setMany({"savedTargets": json.dumps(data)}, notify=False)
		# A list that could not be written is a list that is not remembered; it is
		# no reason to fail the command that changed it.
		except Exception:  # noqa: BLE001
			log.debugWarning("Could not save remembered targets", exc_info=True)

	def _loadRememberedTargets(self):
		"""Restore the saved targets, as detached entries to be relocated later."""
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
			# Judged per entry rather than by the global setting alone: a target
			# can be remembered on its own account, and a list left by an older
			# version of the add-on — which stored every target and filtered here —
			# is still read exactly as it was meant to be.
			if not overrides.get("rememberTargets", settings["rememberTargets"]):
				continue
			self.registry.addDetached(identity, entry.get("kind", "window"), overrides)

	# --- the single, rebindable prefix gesture ------------------------------
	@script(
		description=_(
			# Translators: the description of the main command, shown in Input Gestures.
			"Opens the Background Content Tracker command overlay: press and release it, then press a command key (H for help)"
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
	def _isSecondPress(self, pendingKind: PendingKind, uid: int | None) -> bool:
		"""True if this press repeats the one still pending, within the timeout.

		It is the overlay's own timeout, so a press stays pending exactly as long
		as the overlay it was given in stays open — an overlay set never to time
		out keeps it pending for as long as the user holds it open, and a fresh
		opening clears it either way.
		"""
		timeout = int(addonConfig.get("overlayTimeout"))
		return (
			self._pendingKind == pendingKind
			and self._pendingUid == uid
			and (timeout <= 0 or (time.time() - self._pendingTime) <= timeout)
		)

	def _awaitSecondPress(self, pendingKind: PendingKind, uid: int | None):
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
			ui.message("\n".join([heading] + commands))
			self._awaitSecondPress(("help", None), None)

	def toggleSource(self, kind: str, overrides: Mapping[str, bool] | None = None):
		"""Start, or stop, tracking whatever one of :data:`_SOURCES` names now.

		``kind`` is the source's key, which is also the kind the target keeps.
		``overrides`` are the local settings the target is to be given, and are
		spent where this press stops tracking instead: there is no new target for
		them to be given to, and they never reach an existing one.
		"""
		self._pendingKind = None
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

	def _infoOrFocus(self, pendingKind: PendingKind, target: TrackedTarget):
		if self._isSecondPress(pendingKind, target.uid):
			# Second identical press within the window: move the focus, unless it
			# cannot go there or is there already, which the target menu settles
			# the same way by not offering Set focus at all.
			self._pendingKind = None
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

	def _focusResolved(self, target: TrackedTarget, found: bool):
		"""Focus a target once its object is known to be current. Main thread only."""
		if not found:
			self.notifier.focusFailed()
			return
		if not target.setFocus(self.notifier.focusFailed):
			self.notifier.focusFailed()

	def stopSlot(self, index: int):
		self._pendingKind = None
		target = self.registry.slot(index)
		if target is None:
			self.notifier.noTargetInSlot(index + 1)
			return
		self.stopTracking(target)

	def stopNewest(self):
		self._pendingKind = None
		target = self.registry.newest()
		if target is None:
			self.notifier.noTargets()
			return
		self.stopTracking(target)

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
			if not self._anythingToTrack():
				self.notifier.noTargets()
		else:
			self.notifier.paused()

	def _anythingToTrack(self) -> bool:
		"""Whether anything is tracked, or is still waiting to be found.

		A remembered target that is not there yet counts: the monitor looks for it
		on every poll and takes it up the moment it appears, so calling that
		nothing to track would be wrong. Resuming is exactly when it would be:
		nothing is looked for while tracking is paused, so at that moment every
		remembered target that was not already attached is still detached.
		"""
		settings = addonConfig.snapshot()
		return any(
			target.obj is not None or target.setting("rememberTargets", settings) for target in self.registry
		)

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
		# Capture the current-location sources and the focus now, before the menu
		# takes the focus.
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
				continue  # the same control under two of the four sources
			seen.append(obj)
			sources.append((kind, obj))
		return sources

	# --- actions invoked from the menu --------------------------------------
	def startTracking(
		self,
		obj: NVDAObject | None,
		kind: str,
		overrides: Mapping[str, bool] | None = None,
	):
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

	def stopTracking(self, target: TrackedTarget):
		if self.registry.remove(target):
			self.notifier.announceStopped(target)
			self._saveRememberedTargets()

	def setFocusToTarget(self, target: TrackedTarget):
		self._focus(target)

	def setTargetOverride(self, target: TrackedTarget, key: str, value: bool):
		"""Give one target its own value for a local setting. Main thread only.

		Invoked from the check items in a target's Target settings submenu, so the
		change takes effect the moment it is made: the monitor reads a target's
		settings on every poll, and the saved target list is re-written here rather
		than waiting for the target list itself to next change — the target may
		have just been told to be remembered, or told not to be.
		"""
		target.setOverride(key, value)
		if key == "titleChangeDisappears":
			# The one local setting that is not read live: the title a target is
			# held to is taken when the target is added, so switching the option
			# here has to take (or drop) it now, exactly as a change of the global
			# does for every target that inherits it.
			target.captureTrackedTitle()
		elif key == "ignoreCounters":
			# Likewise for what the target has learned about its counters: the
			# option decided it, so moving the option has to un-decide it.
			target.forgetIgnoredControls()
		elif key == "rememberTargets" and not value:
			# Told not to be remembered. If it is one of the entries left behind by
			# a target that disappeared, nothing will look for it now, so it goes.
			self._dropUnkeptDetachedTargets()
		self._saveRememberedTargets()
