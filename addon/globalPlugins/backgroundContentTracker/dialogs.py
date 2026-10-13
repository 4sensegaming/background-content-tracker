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
from .addonConfig import ChangedKeys, Settings
from .notifier import describe, relativeTime
from .targets import Change, TrackedTarget, sortChanges

if TYPE_CHECKING:
	from gettext import gettext as _  # noqa: TC004

addonHandler.initTranslation()

_HISTORY_SCRIPT = """
function bctEntry(entry) {
	var added = document.createElement("li");
	added.id = entry[0];
	if (entry[1] !== null && entry[2] !== null) {
		var h2 = document.createElement("h2");
		h2.appendChild(document.createTextNode(entry[1]));
		added.appendChild(h2);
	} else if (entry[1] !== null) {
		added.appendChild(document.createTextNode(entry[1]));
	}
	if (entry[2] !== null) {
		var pre = document.createElement("pre");
		pre.appendChild(document.createTextNode(entry[2]));
		added.appendChild(pre);
	}
	return added;
}
function bctFill(entries) {
	var changes = document.getElementById("bctChanges");
	while (changes.firstChild) {
		changes.removeChild(changes.firstChild);
	}
	for (var i = 0; i < entries.length; i++) {
		changes.appendChild(bctEntry(entries[i]));
	}
}
function bctTimes(times) {
	for (var key in times) {
		var entry = document.getElementById(key);
		if (entry) {
			var shown = entry.firstChild;
			if (shown.nodeType === 1) {
				shown = shown.firstChild;
			}
			if (shown.nodeValue !== times[key]) {
				shown.nodeValue = times[key];
			}
		}
	}
}
function bctAdd(dropped, times, before, entry) {
	var changes = document.getElementById("bctChanges");
	for (var i = 0; i < dropped.length; i++) {
		var gone = document.getElementById(dropped[i]);
		if (gone) {
			changes.removeChild(gone);
		}
	}
	bctTimes(times);
	changes.insertBefore(bctEntry(entry), before ? document.getElementById(before) : null);
}
"""

_HISTORY_KEYS = frozenset({"menuTimeSinceChange", "menuChangedContent", "historySorting", "historySize"})

Entry = tuple[str, str | None, str | None]

_open: dict[str, "BrowseableDialog"] = {}


def historyParts(settings: Settings | None = None) -> tuple[bool, bool]:
	"""
	What an entry in a target's history shows.
	@param settings: The settings to go by, or None for the current ones.
	@returns: Whether the time of each change is shown, and whether its content is.
	"""
	if settings is None:
		settings = addonConfig.snapshot()
	return bool(settings["menuTimeSinceChange"]), bool(settings["menuChangedContent"])


def hasHistory(target: TrackedTarget, settings: Settings | None = None) -> bool:
	"""
	Whether a target's history can be browsed.
	@param target: The target.
	@param settings: The settings to go by, or None for the current ones.
	@returns: False also while its entries would show nothing.
	"""
	return bool(target.history) and any(historyParts(settings))


def entryParts(change: Change, parts: tuple[bool, bool]) -> tuple[str | None, str | None]:
	"""
	What the entry of one change in a target's history shows.
	@param change: The change.
	@param parts: What entries show, as from L{historyParts}.
	@returns: The relative time of the change and its content, each None when not shown.
	"""
	showTime, showContent = parts
	return relativeTime(change.time) if showTime else None, change.text if showContent else None


def _shown(chapter: str) -> "BrowseableDialog | None":
	"""
	The open browseable dialog for a chapter of the documentation.
	@param chapter: The chapter F1 opens in the dialog.
	@returns: The dialog, or None when none is shown.
	"""
	dialog = _open.get(chapter)
	return dialog if dialog and dialog.IsShown() else None


def helpAt(focus: NVDAObject) -> Callable[[], str] | None:
	"""
	Whether F1 at the focus belongs to an open browseable dialog, judged by window handles alone.
	@param focus: The focus.
	@returns: What gives the chapter of the documentation F1 opens, or None when F1 is not the add-on's.
	"""
	root = winUser.getAncestor(focus.windowHandle, winUser.GA_ROOT)
	for chapter, dialog in tuple(_open.items()):
		if dialog._handle == root:
			return lambda: chapter
	return None


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
		self._chapter = chapter
		_open[chapter] = self
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
		if evt.GetWindow().GetHandle() == self._handle and _open.get(self._chapter) is self:
			del _open[self._chapter]
		evt.Skip()

	def _copy(self):
		api.copyToClip(self._messageControl.GetPageText())
		# Translators: announced when the text of a browseable message is copied to the clipboard.
		ui.message(_("Copied to clipboard."))

	def present(self):
		gui.mainFrame.prePopup()
		if self.IsShown():
			self.Raise()
		else:
			self.Show()
		gui.mainFrame.postPopup()


def _entryId(change: Change) -> str:
	"""
	The HTML id of one change in the history dialog.
	@param change: The change.
	@returns: The id.
	"""
	return f"bct{change.serial}"


def _entry(change: Change, parts: tuple[bool, bool]) -> Entry:
	"""
	One change as the history dialog's script takes it.
	@param change: The change.
	@param parts: What entries show, as from L{historyParts}.
	@returns: Its HTML id, then its relative time and its content, each None when not shown.
	"""
	return (_entryId(change), *entryParts(change, parts))


class HistoryDialog(BrowseableDialog):
	def __init__(self, target: TrackedTarget):
		"""
		@param target: The target whose recent changes the dialog shows.
		"""
		self.target = target
		self._history = list(target.history)
		heading = escape(
			describe(target.roleText(), target.name, bool(addonConfig.get("menuTargetType")), ())
		)
		super().__init__(
			# Translators: the title of the dialog showing a target's recent changes.
			_("Recent changes"),
			f'<h1>{heading}</h1>\n<ul id="bctChanges"></ul>\n<script>{_HISTORY_SCRIPT}</script>',
			documentation.HISTORY,
		)
		self._draw()
		self._timer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, lambda evt: self._tick(), self._timer)
		self._timer.Start(1000)
		addonConfig.registerChangeHook(self._onSettingsChanged)

	def _onDestroy(self, evt: wx.WindowDestroyEvent):
		"""
		Stop updating the dialog once it is gone.
		@param evt: The destroy event, also sent for the dialog's controls.
		"""
		if evt.GetWindow().GetHandle() == self._handle:
			self._timer.Stop()
			addonConfig.unregisterChangeHook(self._onSettingsChanged)
		super()._onDestroy(evt)

	def isUpdating(self) -> bool:
		"""
		Whether the dialog follows the target's history while open.
		@returns: The target's own setting.
		"""
		return bool(self.target.setting("updateOpenHistory"))

	def _ordered(self) -> list[Change]:
		"""
		The changes shown, in the order of the history sorting setting.
		@returns: The changes.
		"""
		return sortChanges(self._history, str(addonConfig.get("historySorting")))

	def _draw(self):
		parts = historyParts()
		self._run("bctFill", [_entry(change, parts) for change in self._ordered()])

	def _tick(self):
		if historyParts()[0] and self.isUpdating():
			self._run("bctTimes", self._times())

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

	def sync(self):
		"""Show the target's history as it is now, putting a single new change in its place."""
		previous = self._history
		shown = {change.serial for change in previous}
		self._history = list(self.target.history)
		kept = {change.serial for change in self._history}
		new = [change for change in self._history if change.serial not in shown]
		if not new and kept == shown:
			return
		if len(new) != 1:
			self._draw()
			return
		parts = historyParts()
		dropped = [_entryId(change) for change in previous if change.serial not in kept]
		ordered = self._ordered()
		index = ordered.index(new[0])
		before = _entryId(ordered[index + 1]) if index + 1 < len(ordered) else None
		self._run("bctAdd", dropped, self._times() if parts[0] else {}, before, _entry(new[0], parts))

	def _onSettingsChanged(self, changed: ChangedKeys):
		"""
		Redraw the changes as the settings now ask, or close once there is no history to show.
		@param changed: The settings that changed.
		"""
		if not changed & _HISTORY_KEYS:
			return
		if not hasHistory(self.target):
			self.Close(force=True)
			return
		if self.isUpdating():
			self._history = list(self.target.history)
		else:
			self._history = self._history[-int(addonConfig.get("historySize")) :]
		self._draw()


def _shownHistory() -> HistoryDialog | None:
	"""
	The open history dialog.
	@returns: The dialog, or None when none is shown.
	"""
	dialog = _shown(documentation.HISTORY)
	return dialog if isinstance(dialog, HistoryDialog) else None


def showHelp(heading: str, commands: list[str]):
	"""
	Show the overlay help in a browseable message.
	@param heading: The heading above the commands.
	@param commands: One line per command.
	"""
	dialog = _shown(documentation.KEYSTROKES)
	if dialog is None:
		items = "\n".join(f"\t<li>{escape(line)}</li>" for line in commands)
		dialog = BrowseableDialog(
			# Translators: the title of the dialog showing the overlay help.
			_("Background Content Tracker"),
			f"<h1>{escape(heading)}</h1>\n<ul>\n{items}\n</ul>",
			documentation.KEYSTROKES,
		)
	dialog.present()


def showHistory(target: TrackedTarget):
	"""
	Show a target's recent changes.
	@param target: The target.
	"""
	dialog = _shownHistory() or HistoryDialog(target)
	dialog.present()


def historyOpenFor(target: TrackedTarget) -> bool:
	"""
	Whether the history dialog is open for a target.
	@param target: The target.
	@returns: False also while it is open for another target.
	"""
	dialog = _shownHistory()
	return dialog is not None and dialog.target is target


def closeHistory(target: TrackedTarget | None = None):
	"""
	Close the history dialog.
	@param target: Close it only while it is open for this target, or None to close it whatever its target.
	"""
	dialog = _shownHistory()
	if dialog is not None and (target is None or dialog.target is target):
		dialog.Close(force=True)


def changeRecorded(target: TrackedTarget):
	"""
	Bring the history dialog up to date with a change recorded in its target, unless it is not updating.
	@param target: The target that changed.
	"""
	dialog = _shownHistory()
	if dialog is not None and dialog.target is target and dialog.isUpdating():
		dialog.sync()
