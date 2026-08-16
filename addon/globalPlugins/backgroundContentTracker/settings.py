# Background Content Tracker: the settings panel
# Copyright (C) 2026 Lukáš Hosnedl
# This file is covered by the GNU General Public License, version 2.
# See the file COPYING.txt for more details.

"""The "Background Content Tracker" category in NVDA's multi-category Settings
dialog. Options are grouped exactly as in the documentation, dependent controls
are enabled/disabled to match, and values are read from and written to NVDA's
own configuration.
"""

import addonHandler
import wx
from gui import guiHelper, nvdaControls
from gui.settingsDialogs import SettingsPanel

import tones

from . import addonConfig

addonHandler.initTranslation()


class BCTSettingsPanel(SettingsPanel):
	# Translators: the title of the add-on's category in NVDA's Settings dialog.
	title = _("Background Content Tracker")

	def makeSettings(self, settingsSizer):
		sHelper = guiHelper.BoxSizerHelper(self, sizer=settingsSizer)

		# Translators: master switch; enables or disables all tracking.
		self.enabledCb = sHelper.addItem(wx.CheckBox(self, label=_("Enable background content &tracking")))
		self.enabledCb.SetValue(addonConfig.get("enabled"))

		# Group: When target changes -----------------------------------------
		# Translators: group of options controlling what happens on a change.
		changeBox = wx.StaticBox(self, label=_("When target changes"))
		changeGroup = sHelper.addItem(guiHelper.BoxSizerHelper(changeBox, sizer=wx.StaticBoxSizer(changeBox, wx.VERTICAL)))
		# Translators: play a tone when the target changes.
		self.beepCb = changeGroup.addItem(wx.CheckBox(changeBox, label=_("&Beep")))
		self.beepCb.SetValue(addonConfig.get("changeBeep"))
		self.beepCb.Bind(wx.EVT_CHECKBOX, self._onDependencyChanged)
		# Translators: speak an announcement when the target changes.
		self.announceCb = changeGroup.addItem(wx.CheckBox(changeBox, label=_("&Announce")))
		self.announceCb.SetValue(addonConfig.get("changeAnnounce"))
		self.announceCb.Bind(wx.EVT_CHECKBOX, self._onDependencyChanged)
		self.intervalCtrl = changeGroup.addLabeledControl(
			# Translators: how often, in seconds, targets are queried for changes
			# (0 means only display changes in the target menu, never announce them).
			_("Tracking &interval (seconds)"), nvdaControls.SelectOnFocusSpinCtrl,
			min=0, max=3600, initial=addonConfig.get("trackingInterval"),
		)
		self.changesAtOnceCtrl = changeGroup.addLabeledControl(
			# Translators: how many consecutive changes to one target to announce in a
			# row before you have to refocus it (0 means announce every change).
			_("Changes to announce at &once"), nvdaControls.SelectOnFocusSpinCtrl,
			min=0, max=100, initial=addonConfig.get("changesAtOnce"),
		)

		# Group: Window tracking behavior ------------------------------------
		# Translators: group of options refining how whole-window targets are announced.
		windowBox = wx.StaticBox(self, label=_("Window tracking behavior"))
		windowGroup = sHelper.addItem(guiHelper.BoxSizerHelper(windowBox, sizer=wx.StaticBoxSizer(windowBox, wx.VERTICAL)))
		# Translators: suppress announcements of progress bar controls in a window.
		self.ignoreProgressCb = windowGroup.addItem(wx.CheckBox(windowBox, label=_("Ignore &progress bars")))
		self.ignoreProgressCb.SetValue(addonConfig.get("ignoreProgressBars"))
		# Translators: suppress repeated announcements of the same control (e.g. a timer).
		self.ignoreRepeatedCb = windowGroup.addItem(wx.CheckBox(windowBox, label=_("Ignore &repeatedly changing controls")))
		self.ignoreRepeatedCb.SetValue(addonConfig.get("ignoreRepeatedControls"))
		# Translators: treat a window that renames itself as a target that has disappeared.
		self.titleChangeCb = windowGroup.addItem(wx.CheckBox(windowBox, label=_("Consider c&hanged title a disappeared target")))
		self.titleChangeCb.SetValue(addonConfig.get("titleChangeDisappears"))

		# Group: Beep parameters ---------------------------------------------
		# Translators: group of options for the beep, available when Beep is on.
		beepBox = wx.StaticBox(self, label=_("Beep parameters"))
		beepGroup = sHelper.addItem(guiHelper.BoxSizerHelper(beepBox, sizer=wx.StaticBoxSizer(beepBox, wx.VERTICAL)))
		# Translators: how long the beep lasts, in milliseconds.
		self.durationCtrl = beepGroup.addLabeledControl(
			_("D&uration (ms)"), nvdaControls.SelectOnFocusSpinCtrl,
			min=1, max=30000, initial=addonConfig.get("beepDuration"),
		)
		# Translators: the frequency of the beep, in hertz.
		self.pitchCtrl = beepGroup.addLabeledControl(
			_("&Pitch (Hz)"), nvdaControls.SelectOnFocusSpinCtrl,
			min=20, max=20000, initial=addonConfig.get("beepPitch"),
		)
		# Translators: plays a test beep with the current parameters.
		self.testButton = beepGroup.addItem(wx.Button(beepBox, label=_("&Test")))
		self.testButton.Bind(wx.EVT_BUTTON, self._onTest)

		# Group: Include in change announcement -------------------------------
		# Translators: group choosing what a change announcement contains.
		annBox = wx.StaticBox(self, label=_("Include in change announcement"))
		annGroup = sHelper.addItem(guiHelper.BoxSizerHelper(annBox, sizer=wx.StaticBoxSizer(annBox, wx.VERTICAL)))
		# Translators: include the target type (role) in change announcements.
		self.annTypeCb = annGroup.addItem(wx.CheckBox(annBox, label=_("Target t&ype")))
		self.annTypeCb.SetValue(addonConfig.get("announceTargetType"))
		# Translators: include the changed content in change announcements.
		self.annContentCb = annGroup.addItem(wx.CheckBox(annBox, label=_("Changed &content")))
		self.annContentCb.SetValue(addonConfig.get("announceChangedContent"))

		# Group: Include in menu descriptions --------------------------------
		# Translators: group choosing what a target menu description contains.
		menuBox = wx.StaticBox(self, label=_("Include in menu descriptions"))
		menuGroup = sHelper.addItem(guiHelper.BoxSizerHelper(menuBox, sizer=wx.StaticBoxSizer(menuBox, wx.VERTICAL)))
		# Translators: include the target type (role) in menu descriptions.
		self.menuTypeCb = menuGroup.addItem(wx.CheckBox(menuBox, label=_("Targe&t type")))
		self.menuTypeCb.SetValue(addonConfig.get("menuTargetType"))
		# Translators: include the time since the last change in menu descriptions.
		self.menuTimeCb = menuGroup.addItem(wx.CheckBox(menuBox, label=_("Time since last chan&ge")))
		self.menuTimeCb.SetValue(addonConfig.get("menuTimeSinceChange"))
		# Translators: include the changed content in menu descriptions.
		self.menuContentCb = menuGroup.addItem(wx.CheckBox(menuBox, label=_("Changed cont&ent")))
		self.menuContentCb.SetValue(addonConfig.get("menuChangedContent"))

		self.overlayTimeoutCtrl = sHelper.addLabeledControl(
			# Translators: how many seconds of inactivity close the command overlay.
			_("&Overlay timeout (seconds)"), nvdaControls.SelectOnFocusSpinCtrl,
			min=1, max=120, initial=addonConfig.get("overlayTimeout"),
		)

		# Group: Target sorting ----------------------------------------------
		sortChoices = [
			# Translators: target sorting option (the default).
			_("Oldest first"),
			# Translators: target sorting option.
			_("Newest first"),
		]
		self.sortRadio = sHelper.addItem(wx.RadioBox(
			# Translators: label for the target sorting radio buttons.
			self, label=_("Target sorting"), choices=sortChoices,
			majorDimension=1, style=wx.RA_SPECIFY_COLS,
		))
		self.sortRadio.SetSelection(1 if addonConfig.get("targetSorting") == "newest" else 0)

		# Translators: keep the target list between NVDA restarts and re-attach on reappearance.
		self.rememberCb = sHelper.addItem(wx.CheckBox(self, label=_("&Remember targets")))
		self.rememberCb.SetValue(addonConfig.get("rememberTargets"))

		# Translators: automatically drop targets that no longer exist.
		self.forgetCb = sHelper.addItem(wx.CheckBox(self, label=_("&Forget targets when they disappear")))
		self.forgetCb.SetValue(addonConfig.get("forgetOnDisappear"))

		self._updateDependentControls()

	def _onDependencyChanged(self, evt):
		self._updateDependentControls()

	def _updateDependentControls(self):
		beepOn = self.beepCb.IsChecked()
		for control in (self.durationCtrl, self.pitchCtrl, self.testButton):
			control.Enable(beepOn)
		announceOn = self.announceCb.IsChecked()
		for control in (self.annTypeCb, self.annContentCb):
			control.Enable(announceOn)

	def _onTest(self, evt):
		try:
			tones.beep(self.pitchCtrl.GetValue(), self.durationCtrl.GetValue())
		except Exception:
			pass

	def onSave(self):
		# Written in one go: each individual write re-reads every setting into the
		# monitor thread's snapshot, so nineteen separate writes would cost
		# nineteen full re-reads.
		addonConfig.setMany({
			"enabled": self.enabledCb.IsChecked(),
			"changeBeep": self.beepCb.IsChecked(),
			"changeAnnounce": self.announceCb.IsChecked(),
			"trackingInterval": self.intervalCtrl.GetValue(),
			"changesAtOnce": self.changesAtOnceCtrl.GetValue(),
			"ignoreProgressBars": self.ignoreProgressCb.IsChecked(),
			"ignoreRepeatedControls": self.ignoreRepeatedCb.IsChecked(),
			"titleChangeDisappears": self.titleChangeCb.IsChecked(),
			"beepDuration": self.durationCtrl.GetValue(),
			"beepPitch": self.pitchCtrl.GetValue(),
			"announceTargetType": self.annTypeCb.IsChecked(),
			"announceChangedContent": self.annContentCb.IsChecked(),
			"menuTargetType": self.menuTypeCb.IsChecked(),
			"menuTimeSinceChange": self.menuTimeCb.IsChecked(),
			"menuChangedContent": self.menuContentCb.IsChecked(),
			"overlayTimeout": self.overlayTimeoutCtrl.GetValue(),
			"targetSorting": "newest" if self.sortRadio.GetSelection() == 1 else "oldest",
			"rememberTargets": self.rememberCb.IsChecked(),
			"forgetOnDisappear": self.forgetCb.IsChecked(),
		})
