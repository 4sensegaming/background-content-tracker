# Background Content Tracker: browseable message dialogs
# Copyright (C) 2026 Lukáš Hosnedl
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

import contextlib
import json
import os
from html import escape
from typing import TYPE_CHECKING

import addonHandler
import api
import globalVars
import gui
import ui
import wx
from gui.message import HtmlMessageDialog

from . import addonConfig
from .notifier import describe, relativeTime
from .targets import Change, TrackedTarget, sortChanges

if TYPE_CHECKING:
	from gettext import gettext as _  # noqa: TC004

addonHandler.initTranslation()

_HISTORY_SCRIPT = """
function bctAdd(times, before, id, heading, text) {
	for (var key in times) {
		var entry = document.getElementById(key);
		if (entry) {
			var shown = entry.getElementsByTagName("h2")[0];
			if (shown.textContent !== times[key]) {
				shown.textContent = times[key];
			}
		}
	}
	var added = document.createElement("div");
	added.id = id;
	var h2 = document.createElement("h2");
	h2.textContent = heading;
	var pre = document.createElement("pre");
	pre.textContent = text;
	added.appendChild(h2);
	added.appendChild(pre);
	document.getElementById("bctChanges").insertBefore(added, before ? document.getElementById(before) : null);
}
var start = document.getElementById("bctStart");
if (start) {
	start.focus();
}
"""


class BrowseableDialog(HtmlMessageDialog):
	def __init__(self, title: str, body: str):
		"""
		@param title: The window title.
		@param body: The HTML of the message.
		"""
		with open(os.path.join(globalVars.appDir, "message.html"), encoding="utf-8") as f:
			page = f.read().replace("{{TITLE}}", escape(title)).replace("{{MESSAGE}}", body)
		super().__init__(None, page, title, buttons=None)
		self.addButton(
			wx.ID_COPY,
			# Translators: the button copying the text of a browseable message to the clipboard.
			label=_("&Copy"),
			callback=lambda evt: self._copy(),
			closesDialog=False,
		)
		self.registerAction("copy", self._copy)

	def _copy(self):
		api.copyToClip(self._messageControl.GetPageText())
		# Translators: announced when the text of a browseable message is copied to the clipboard.
		ui.message(_("Copied to clipboard"))

	def present(self):
		gui.mainFrame.prePopup()
		self.Show()
		gui.mainFrame.postPopup()


def _entryId(change: Change) -> str:
	"""
	The HTML id of one change in the history dialog.
	@param change: The change.
	@returns: The id.
	"""
	return f"bct{change.serial}"


def _entryHtml(change: Change, start: bool) -> str:
	"""
	The HTML of one change in the history dialog.
	@param change: The change.
	@param start: Whether the dialog opens at this change.
	@returns: The heading with the change's time, followed by its text.
	"""
	startAttributes = ' id="bctStart" tabindex="-1"' if start else ""
	return (
		f'<div id="{_entryId(change)}"><h2{startAttributes}>{escape(relativeTime(change.time))}</h2>'
		f"<pre>{escape(change.text)}</pre></div>"
	)


class HistoryDialog(BrowseableDialog):
	def __init__(self, target: TrackedTarget, serial: int):
		"""
		@param target: The target whose recent changes the dialog shows.
		@param serial: The serial number of the change the dialog opens at.
		"""
		self.target = target
		self._order = str(addonConfig.get("historySorting"))
		self._history = list(target.history)
		entries = "".join(
			_entryHtml(change, change.serial == serial) for change in sortChanges(self._history, self._order)
		)
		heading = escape(describe(target.roleText(), target.name, True, ()))
		super().__init__(
			# Translators: the title of the dialog showing a target's recent changes.
			_("Recent changes"),
			f'<h1>{heading}</h1>\n<div id="bctChanges">{entries}</div>\n<script>{_HISTORY_SCRIPT}</script>',
		)

	def addChange(self, change: Change):
		"""
		Show a change found while the dialog is open, and bring the times of the others up to date.
		@param change: The new change.
		"""
		self._history.append(change)
		ordered = sortChanges(self._history, self._order)
		index = ordered.index(change)
		before = _entryId(ordered[index + 1]) if index + 1 < len(ordered) else None
		times = {_entryId(shown): relativeTime(shown.time) for shown in self._history}
		arguments = ", ".join(
			json.dumps(value)
			for value in (times, before, _entryId(change), relativeTime(change.time), change.text)
		)
		with contextlib.suppress(RuntimeError):
			self._messageControl.RunScript(f"bctAdd({arguments});")


_historyDialogs: list[HistoryDialog] = []


def showHelp(heading: str, commands: list[str]):
	"""
	Show the overlay help in a browseable message.
	@param heading: The heading above the commands.
	@param commands: One line per command.
	"""
	items = "\n".join(f"\t<li>{escape(line)}</li>" for line in commands)
	BrowseableDialog(
		# Translators: the title of the dialog showing the overlay help.
		_("Background Content Tracker"),
		f"<h1>{escape(heading)}</h1>\n<ul>\n{items}\n</ul>",
	).present()


def showHistory(target: TrackedTarget, serial: int):
	"""
	Show a target's recent changes, at one of them.
	@param target: The target.
	@param serial: The serial number of the change to open at.
	"""
	dialog = HistoryDialog(target, serial)
	_historyDialogs.append(dialog)
	dialog.present()


def changeRecorded(target: TrackedTarget, change: Change):
	"""
	Add a new change to the open history dialogs of its target.
	@param target: The target that changed.
	@param change: The change recorded.
	"""
	_historyDialogs[:] = [dialog for dialog in _historyDialogs if dialog]
	for dialog in _historyDialogs:
		if dialog.target is target:
			dialog.addChange(change)
