# Background Content Tracker: the settings panel
# Copyright (C) 2026 Lukáš Hosnedl
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

import contextlib
from typing import TYPE_CHECKING

import addonHandler
import tones
import ui
import wx
from gui import guiHelper, nvdaControls
from gui.settingsDialogs import SettingsPanel

from . import addonConfig, documentation

if TYPE_CHECKING:
	from gettext import gettext as _  # noqa: TC004

addonHandler.initTranslation()

_CHAPTERS = {
	"enabled": "enable-tracking-checkbox-enabled-by-default",
	"trackingInterval": "tracking-interval-edit-1-by-default",
	"changesAtOnce": "changes-to-announce-at-once-background-targets-only-edit-5-by-default",
	"historySize": "keep-history-of-recent-changes-per-target-edit-50-by-default",
	"overlayTimeout": "overlay-timeout-edit-10-by-default",
	"trackForegroundTargets": "track-even-foreground-targets-checkbox-disabled-by-default",
	"slotSorting": "target-sorting",
	"menuSorting": "target-sorting",
	"historySorting": "target-sorting",
	"rememberTargets": "remember-targets-checkbox-disabled-by-default",
	"forgetOnDisappear": "forget-remembered-targets-when-they-disappear-checkbox-disabled-by-default",
	"ignoreProgressBars": "ignore-progress-bars-checkbox-enabled-by-default",
	"ignoreCounters": "ignore-counters-steppers-and-timers-checkbox-enabled-by-default",
	"titleChangeDisappears": "consider-changed-title-a-disappeared-target-checkbox-disabled-by-default",
	"ignoreGenericControls": "ignore-known-generic-controls-checkbox-enabled-by-default",
	"ignoreFocusedControl": "ignore-the-focused-control-when-tracking-the-foreground-window-checkbox-enabled-by-default",
	"changeBeep": "beep-checkbox-enabled-by-default",
	"changeAnnounce": "announce-checkbox-enabled-by-default",
	"interruptSpeech": "interrupt-previous-speech-when-announcing-a-new-change-checkbox-disabled-by-default",
	"repeatTargetName": "repeat-target-name-for-consecutive-changes-in-the-same-target-checkbox-enabled-by-default",
	"beepDuration": "duration-edit-50-by-default",
	"beepPitch": "pitch-edit-440-by-default",
	"announceTargetType": "target-type-checkbox-enabled-by-default",
	"announceChangedContent": "changed-content-checkbox-enabled-by-default",
	"menuTargetType": "target-type-checkbox-enabled-by-default_1",
	"menuTimeSinceChange": "time-since-last-change-checkbox-enabled-by-default",
	"menuChangedContent": "changed-content-checkbox-enabled-by-default_1",
}


class BCTSettingsPanel(SettingsPanel):
	# Translators: the title of the add-on's category in NVDA's Settings dialog.
	title = _("Background Content Tracker")

	trackForegroundCb: wx.CheckBox
	ignoreFocusedCb: wx.CheckBox
	beepCb: wx.CheckBox
	announceCb: wx.CheckBox
	interruptCb: wx.CheckBox
	repeatNameCb: wx.CheckBox
	durationCtrl: nvdaControls.SelectOnFocusSpinCtrl
	pitchCtrl: nvdaControls.SelectOnFocusSpinCtrl
	testButton: wx.Button
	annTypeCb: wx.CheckBox
	annContentCb: wx.CheckBox
	_bound: dict[str, wx.CheckBox | nvdaControls.SelectOnFocusSpinCtrl]
	_sortRadios: dict[str, tuple[wx.RadioBox, tuple[str, ...]]]
	_chapters: dict[int, str]

	def _group(
		self, helper: guiHelper.BoxSizerHelper, label: str
	) -> tuple[wx.StaticBox, guiHelper.BoxSizerHelper]:
		box = wx.StaticBox(self, label=label)
		return box, helper.addItem(guiHelper.BoxSizerHelper(box, sizer=wx.StaticBoxSizer(box, wx.VERTICAL)))

	def _checkBox(
		self,
		helper: guiHelper.BoxSizerHelper,
		parent: wx.Window,
		key: str,
		label: str,
	) -> wx.CheckBox:
		checkBox = helper.addItem(wx.CheckBox(parent, label=label))
		checkBox.SetValue(bool(addonConfig.get(key)))
		self._bound[key] = checkBox
		return checkBox

	def _spinCtrl(
		self,
		helper: guiHelper.BoxSizerHelper,
		key: str,
		label: str,
		minimum: int,
		maximum: int,
	) -> nvdaControls.SelectOnFocusSpinCtrl:
		spinCtrl = helper.addLabeledControl(
			label,
			nvdaControls.SelectOnFocusSpinCtrl,
			min=minimum,
			max=maximum,
			initial=addonConfig.get(key),
		)
		self._bound[key] = spinCtrl
		return spinCtrl

	def _sortRadio(
		self,
		helper: guiHelper.BoxSizerHelper,
		key: str,
		label: str,
		labels: dict[str, str],
		orders: tuple[str, ...],
	):
		"""
		Add the radio buttons of one sorting setting.
		@param helper: Where the radio buttons go.
		@param key: The setting.
		@param label: The label of the radio buttons.
		@param labels: The label of each order.
		@param orders: The orders the setting offers.
		"""
		radio = helper.addItem(
			wx.RadioBox(
				self,
				label=label,
				choices=[labels[order] for order in orders],
				majorDimension=1,
				style=wx.RA_SPECIFY_COLS,
			)
		)
		radio.SetSelection(orders.index(str(addonConfig.get(key))))
		self._sortRadios[key] = (radio, orders)

	def makeSettings(self, settingsSizer: wx.Sizer):
		self._bound = {}
		self._sortRadios = {}
		sHelper = guiHelper.BoxSizerHelper(self, sizer=settingsSizer)

		# Translators: master switch; enables or disables all tracking.
		self._checkBox(sHelper, self, "enabled", _("Enable &tracking"))
		self._spinCtrl(
			sHelper,
			"trackingInterval",
			# Translators: how often, in seconds, targets are queried for changes
			# (0 means only display changes in the target menu, never announce them).
			_("Tracking &interval (seconds, 0 means never announce, only display in target menu)"),
			0,
			3600,
		)
		self._spinCtrl(
			sHelper,
			"changesAtOnce",
			# Translators: how many consecutive changes to one target to announce in a
			# row before you have to refocus it (0 means announce every change). A target
			# the user is currently working in is never limited.
			_("Changes to announce at &once (background targets only, 0 means always announce every change)"),
			0,
			100,
		)
		self._spinCtrl(
			sHelper,
			"historySize",
			# Translators: how many recent changes the target menu keeps for each target (0 means none).
			_("Keep &history of recent changes per target (0 means no history)"),
			0,
			1000,
		)
		self._spinCtrl(
			sHelper,
			"overlayTimeout",
			# Translators: how many seconds of inactivity close the command overlay
			# (0 means the overlay stays open until it is closed by a command or escape).
			_("&Overlay timeout (seconds, 0 means never time out)"),
			0,
			120,
		)
		self.trackForegroundCb = self._checkBox(
			sHelper,
			self,
			"trackForegroundTargets",
			# Translators: also track a target while its own application is in the foreground.
			_("Trac&k even foreground targets"),
		)
		self.trackForegroundCb.Bind(wx.EVT_CHECKBOX, self._onDependencyChanged)

		targetLabels = {
			# Translators: a target order; the most recently added target comes first.
			"newest": _("Newest target first"),
			# Translators: a target order; the target added longest ago comes first.
			"oldest": _("Oldest target first"),
			# Translators: a target order; the target that changed last comes first.
			"recentlyChanged": _("Most recently changed target first"),
			# Translators: a target order; the target that changed longest ago comes first.
			"leastRecentlyChanged": _("Least recently changed target first"),
			# Translators: a target order; targets by name, A to Z.
			"alphabetical": _("Alphabetically, A to Z"),
			# Translators: a target order; targets by name, Z to A.
			"reverseAlphabetical": _("Alphabetically, Z to A"),
		}
		changeLabels = {
			**targetLabels,
			# Translators: an order of a target's recent changes; the most recent change comes first.
			"newest": _("Newest change first"),
			# Translators: an order of a target's recent changes; the oldest change comes first.
			"oldest": _("Oldest change first"),
		}
		self._sortRadio(
			sHelper,
			"slotSorting",
			# Translators: the order the targets take the ten number slots in.
			_("Target slot sorting"),
			targetLabels,
			addonConfig.SORT_ORDERS,
		)
		self._sortRadio(
			sHelper,
			"menuSorting",
			# Translators: the order the targets are listed in, in the target menu.
			_("Target menu sorting"),
			targetLabels,
			addonConfig.SORT_ORDERS,
		)
		self._sortRadio(
			sHelper,
			"historySorting",
			# Translators: the order a target's recent changes are listed in, in the target menu.
			_("Change history sorting"),
			changeLabels,
			addonConfig.HISTORY_SORT_ORDERS,
		)

		# Translators: keep the target list between NVDA restarts and re-attach on reappearance.
		self._checkBox(sHelper, self, "rememberTargets", _("&Remember targets"))
		self._checkBox(
			sHelper,
			self,
			"forgetOnDisappear",
			# Translators: automatically drop remembered targets that no longer exist.
			_("&Forget remembered targets when they disappear"),
		)

		# Translators: group of options refining how whole-window targets are announced.
		windowBox, windowGroup = self._group(sHelper, _("Window tracking behavior"))
		# Translators: suppress announcements of progress bar controls in a window.
		self._checkBox(windowGroup, windowBox, "ignoreProgressBars", _("Ignore &progress bars"))
		self._checkBox(
			windowGroup,
			windowBox,
			"ignoreCounters",
			# Translators: suppress a control that does nothing but count (e.g. a timer).
			_("Ignore c&ounters, steppers and timers"),
		)
		self._checkBox(
			windowGroup,
			windowBox,
			"titleChangeDisappears",
			# Translators: treat a window that renames itself as a target that has disappeared.
			_("Consider c&hanged title a disappeared target"),
		)
		self._checkBox(
			windowGroup,
			windowBox,
			"ignoreGenericControls",
			# Translators: suppress standard controls such as Minimize, OK or Cancel buttons in a window.
			_("Ignore kno&wn generic controls"),
		)
		self.ignoreFocusedCb = self._checkBox(
			windowGroup,
			windowBox,
			"ignoreFocusedControl",
			# Translators: suppress announcements of the control the user is typing in.
			_("Ignore the focu&sed control when tracking the foreground window"),
		)

		# Translators: group of options controlling what happens on a change.
		changeBox, changeGroup = self._group(sHelper, _("When target changes"))
		# Translators: play a tone when the target changes.
		self.beepCb = self._checkBox(changeGroup, changeBox, "changeBeep", _("&Beep"))
		self.beepCb.Bind(wx.EVT_CHECKBOX, self._onDependencyChanged)
		# Translators: speak an announcement when the target changes.
		self.announceCb = self._checkBox(changeGroup, changeBox, "changeAnnounce", _("&Announce"))
		self.announceCb.Bind(wx.EVT_CHECKBOX, self._onDependencyChanged)
		self.interruptCb = self._checkBox(
			changeGroup,
			changeBox,
			"interruptSpeech",
			# Translators: cancel whatever NVDA is saying to speak a change announcement at once.
			_("I&nterrupt previous speech when announcing a new change"),
		)
		self.repeatNameCb = self._checkBox(
			changeGroup,
			changeBox,
			"repeatTargetName",
			# Translators: say the target's name in every change announcement, even when the same
			# target changes several times in a row.
			_("Repeat target na&me for consecutive changes in the same target"),
		)

		# Translators: group of options for the beep, available when Beep is on.
		beepBox, beepGroup = self._group(sHelper, _("Beep parameters"))
		# Translators: how long the beep lasts, in milliseconds.
		self.durationCtrl = self._spinCtrl(beepGroup, "beepDuration", _("D&uration (ms)"), 1, 30000)
		# Translators: the frequency of the beep, in hertz.
		self.pitchCtrl = self._spinCtrl(beepGroup, "beepPitch", _("&Pitch (Hz)"), 20, 20000)
		# Translators: plays a test beep with the current parameters.
		self.testButton = beepGroup.addItem(wx.Button(beepBox, label=_("&Test")))
		self.testButton.Bind(wx.EVT_BUTTON, self._onTest)

		# Translators: group choosing what a change announcement contains.
		annBox, annGroup = self._group(sHelper, _("Include in change announcement"))
		# Translators: include the target type (role) in change announcements.
		self.annTypeCb = self._checkBox(annGroup, annBox, "announceTargetType", _("Target t&ype"))
		# Translators: include the changed content in change announcements.
		self.annContentCb = self._checkBox(annGroup, annBox, "announceChangedContent", _("Changed &content"))

		# Translators: group choosing what a target menu description contains.
		menuBox, menuGroup = self._group(sHelper, _("Include in menu descriptions"))
		# Translators: include the target type (role) in menu descriptions.
		self._checkBox(menuGroup, menuBox, "menuTargetType", _("Targe&t type"))
		# Translators: include the time since the last change in menu descriptions.
		self._checkBox(menuGroup, menuBox, "menuTimeSinceChange", _("Time since last chan&ge"))
		# Translators: include the changed content in menu descriptions.
		self._checkBox(menuGroup, menuBox, "menuChangedContent", _("Changed cont&ent"))

		# Translators: sets every option on this panel back to its default value.
		restoreButton = sHelper.addItem(wx.Button(self, label=_("Restore &default add-on settings")))
		restoreButton.Bind(wx.EVT_BUTTON, self._onRestoreDefaults)

		self._chapters = {control.GetId(): _CHAPTERS[key] for key, control in self._bound.items()}
		for key, (radio, _orders) in self._sortRadios.items():
			self._chapters[radio.GetId()] = _CHAPTERS[key]
		self._chapters[self.testButton.GetId()] = "test-button"
		self.GetTopLevelParent().Bind(wx.EVT_CHAR_HOOK, self._onCharHook)

		self._updateDependentControls()

	def _onCharHook(self, evt: wx.KeyEvent):
		if evt.GetKeyCode() != wx.WXK_F1 or evt.HasAnyModifiers() or not self.IsShown():
			evt.Skip()
			return
		chapter = documentation.GLOBAL_SETTINGS
		window = wx.Window.FindFocus()
		while window:
			if window.GetId() in self._chapters:
				chapter = self._chapters[window.GetId()]
				break
			window = window.GetParent()
		documentation.openChapter(chapter)

	def _onDependencyChanged(self, evt: wx.CommandEvent):
		self._updateDependentControls()

	def _updateDependentControls(self):
		self.ignoreFocusedCb.Enable(self.trackForegroundCb.IsChecked())
		beepOn = self.beepCb.IsChecked()
		for control in (self.durationCtrl, self.pitchCtrl, self.testButton):
			control.Enable(beepOn)
		announceOn = self.announceCb.IsChecked()
		for control in (self.interruptCb, self.repeatNameCb, self.annTypeCb, self.annContentCb):
			control.Enable(announceOn)

	def _onRestoreDefaults(self, evt: wx.CommandEvent):
		for key, control in self._bound.items():
			default = addonConfig.DEFAULTS[key]
			if isinstance(control, wx.CheckBox):
				control.SetValue(bool(default))
			else:
				control.SetValue(int(default))
		for key, (radio, orders) in self._sortRadios.items():
			radio.SetSelection(orders.index(str(addonConfig.DEFAULTS[key])))
		self._updateDependentControls()
		# Translators: announced when the add-on's settings panel is set back to the default values.
		ui.message(_("Default settings restored"))

	def _onTest(self, evt: wx.CommandEvent):
		with contextlib.suppress(Exception):
			tones.beep(self.pitchCtrl.GetValue(), self.durationCtrl.GetValue())

	def onSave(self):
		values: dict[str, addonConfig.ConfigValue] = {
			key: control.GetValue() for key, control in self._bound.items()
		}
		for key, (radio, orders) in self._sortRadios.items():
			values[key] = orders[radio.GetSelection()]
		addonConfig.setMany(values)
