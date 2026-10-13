# Background Content Tracker: browseable message dialogs
# Copyright (C) 2026 Lukáš Hosnedl
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

import contextlib
import json
import os
from collections.abc import Callable
from html import escape
from typing import TYPE_CHECKING

import addonHandler
import api
import globalVars
import gui
import ui
import winUser
import wx
from gui.message import HtmlMessageDialog
from NVDAObjects import NVDAObject

from . import addonConfig, documentation
from .notifier import describe, relativeTime
from .targets import Change, TrackedTarget, sortChanges

if TYPE_CHECKING:
	from gettext import gettext as _  # noqa: TC004

addonHandler.initTranslation()

_HISTORY_SCRIPT = """
function bctTimes(times) {
	for (var key in times) {
		var entry = document.getElementById(key);
		if (entry) {
			var shown = entry.getElementsByTagName("h2")[0];
			if (shown.textContent !== times[key]) {
				shown.textContent = times[key];
			}
		}
	}
}
function bctAdd(times, before, id, heading, text) {
	bctTimes(times);
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
	start.scrollIntoView();
}
"""


_openChapters: dict[int, str] = {}


def helpAt(focus: NVDAObject) -> Callable[[], str] | None:
	"""
	Whether F1 at the focus belongs to an open browseable dialog, judged by window handles alone.
	@param focus: The focus.
	@returns: What gives the chapter of the documentation F1 opens, or None when F1 is not the add-on's.
	"""
	chapter = _openChapters.get(winUser.getAncestor(focus.windowHandle, winUser.GA_ROOT))
	if chapter is None:
		return None
	return lambda: chapter


class BrowseableDialog(HtmlMessageDialog):
	def __init__(self, title: str, body: str, chapter: str):
		"""
		@param title: The window title.
		@param body: The HTML of the message.
		@param chapter: The chapter of the documentation F1 opens.
		"""
		with open(os.path.join(globalVars.appDir, "message.html"), encoding="utf-8") as f:
			page = f.read().replace("{{TITLE}}", escape(title)).replace("{{MESSAGE}}", body)
		super().__init__(None, page, title, buttons=None)
		self._handle = self.GetHandle()
		_openChapters[self._handle] = chapter
		self.Bind(wx.EVT_WINDOW_DESTROY, self._onDestroy)
		self.addButton(
			wx.ID_COPY,
			# Translators: the button copying the text of a browseable message to the clipboard.
			label=_("&Copy"),
			callback=lambda evt: self._copy(),
			closesDialog=False,
		)
		self.registerAction("copy", self._copy)

	def _onDestroy(self, evt: wx.WindowDestroyEvent):
		if evt.GetWindow() is self:
			_openChapters.pop(self._handle, None)
		evt.Skip()

	def _copy(self):
		api.copyToClip(self._messageControl.GetPageText())
		# Translators: announced when the text of a browseable message is copied to the clipboard.
		ui.message(_("Copied to clipboard."))

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
	startAttributes = ' id="bctStart"' if start else ""
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
			documentation.HISTORY,
		)
		self._timer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, lambda evt: self._run("bctTimes", self._times()), self._timer)
		self._timer.Start(1000)

	def _onDestroy(self, evt: wx.WindowDestroyEvent):
		"""
		Stop updating the times once the dialog is gone.
		@param evt: The destroy event, also sent for the dialog's controls.
		"""
		if evt.GetWindow() is self:
			self._timer.Stop()
		super()._onDestroy(evt)

	def _times(self) -> dict[str, str]:
		"""
		The time of every change shown.
		@returns: The relative time of each change, by its HTML id.
		"""
		return {_entryId(shown): relativeTime(shown.time) for shown in self._history}

	def _run(self, function: str, *arguments: object):
		"""
		Call a function of the page's script.
		@param function: The function's name.
		@param arguments: Its arguments, passed as JSON.
		"""
		with contextlib.suppress(RuntimeError):
			self._messageControl.RunScript(
				f"{function}({', '.join(json.dumps(value) for value in arguments)});"
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
		self._run("bctAdd", self._times(), before, _entryId(change), relativeTime(change.time), change.text)


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
		documentation.KEYSTROKES,
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
