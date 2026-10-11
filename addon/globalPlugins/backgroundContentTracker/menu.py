# Background Content Tracker: the target menu
# Copyright (C) 2026 Lukáš Hosnedl
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

import contextlib
from collections.abc import Callable, Mapping, Sequence
from typing import TYPE_CHECKING

import addonHandler
import gui
import wx
from logHandler import log
from NVDAObjects import NVDAObject

from . import addonConfig, dialogs, documentation
from .notifier import relativeTime
from .targets import FocusState, TrackedTarget, safeCall, sortChanges

if TYPE_CHECKING:
	from gettext import gettext as _  # noqa: TC004

	from . import GlobalPlugin

addonHandler.initTranslation()

Source = tuple[str, NVDAObject]
Bind = Callable[[wx.MenuItem, Callable[[], None], str], None]


def showTargetMenu(plugin: "GlobalPlugin", sources: Sequence[Source], focus: FocusState):
	try:
		_buildAndShow(plugin, sources, focus)
	except Exception:
		log.exception("Error showing the target menu")


def showTargetSubmenu(plugin: "GlobalPlugin", target: TrackedTarget, focus: FocusState):
	"""
	Pop up the submenu one target has in the target menu, on its own.
	@param plugin: The add-on, which carries out the chosen item.
	@param target: The target the submenu acts on.
	@param focus: The current focus, deciding whether "Set focus" is offered.
	"""
	try:
		chapters: dict[int, str] = {}
		_popUp(_targetSubmenu(plugin, target, focus, _binder(chapters)), chapters)
	except Exception:
		log.exception("Error showing the target menu")


def _plain(text: str) -> str:
	"""
	Keep the ampersands of a menu label from marking its accelerator.
	@param text: The label.
	@returns: The label as the menu takes it.
	"""
	return text.replace("&", "&&")


def _startLabel(kind: str, obj: NVDAObject) -> str:
	name = safeCall(lambda: obj.name) or safeCall(lambda: obj.role.displayString) or ""
	kindLabels = {
		# Translators: the "window" source in the target menu's start-tracking items.
		"window": _("window"),
		# Translators: the "focus" source in the target menu's start-tracking items.
		"focus": _("focus"),
		# Translators: the "mouse" source in the target menu's start-tracking items.
		"mouse": _("mouse pointer"),
		# Translators: the "navigator object" source in the target menu's start-tracking items.
		"navigator": _("navigator object"),
	}
	kindLabel = kindLabels.get(kind, kind)
	# Translators: a start-tracking item in the target menu, e.g. "Track window: Claude".
	return _("Track {source}: {name}").format(source=kindLabel, name=name)


def _localSettingItems(target: TrackedTarget) -> list[tuple[str, str]]:
	items: list[tuple[str, str]] = []
	if addonConfig.get("changeAnnounce"):
		items.append(
			(
				"interruptSpeech",
				# Translators: cancel whatever NVDA is saying to speak a change announcement at once.
				_("I&nterrupt previous speech when announcing a new change"),
			),
		)
	if target.kind == "window":
		items.extend(
			(
				# Translators: suppress announcements of progress bar controls in a window.
				("ignoreProgressBars", _("Ignore &progress bars")),
				# Translators: suppress a control that does nothing but count (e.g. a timer).
				("ignoreCounters", _("Ignore c&ounters, steppers and timers")),
				# Translators: treat a window that renames itself as a target that has disappeared.
				("titleChangeDisappears", _("Consider c&hanged title a disappeared target")),
				# Translators: suppress standard controls such as Minimize, OK or Cancel buttons in a window.
				("ignoreGenericControls", _("Ignore kno&wn generic controls")),
			)
		)
	items.append(
		# Translators: submenu item; read this one target while its own application is in the foreground.
		("trackForegroundTargets", _("Track this target even in the foreground")),
	)
	if target.kind == "window" and target.setting("trackForegroundTargets"):
		items.append(
			(
				"ignoreFocusedControl",
				# Translators: suppress announcements of the control the user is typing in.
				_("Ignore the focu&sed control"),
			),
		)
	items.append(
		# Translators: submenu item; keep this one target between NVDA restarts and re-attach it on reappearance.
		("rememberTargets", _("Remember this target")),
	)
	if target.setting("rememberTargets"):
		items.append(
			# Translators: submenu item; drop this one remembered target once it no longer exists.
			("forgetOnDisappear", _("Forget this target when it disappears")),
		)
	return items


def _appendSettingsSubmenu(
	submenu: wx.Menu,
	plugin: "GlobalPlugin",
	target: TrackedTarget,
	bind: Bind,
):
	settingsMenu = wx.Menu()
	for key, label in _localSettingItems(target):
		item = settingsMenu.AppendCheckItem(wx.ID_ANY, label)
		item.Check(bool(target.setting(key)))
		bind(
			item,
			lambda k=key, t=target: plugin.setTargetOverride(t, k, not t.setting(k)),
			documentation.TARGET_SETTINGS,
		)
	# Translators: submenu of a target's menu, holding that target's own settings.
	submenu.AppendSubMenu(settingsMenu, _("Target settings"))


def _targetSubmenu(plugin: "GlobalPlugin", target: TrackedTarget, focus: FocusState, bind: Bind) -> wx.Menu:
	"""
	Build the submenu of one target.
	@param plugin: The add-on, which carries out the chosen item.
	@param target: The target the submenu acts on.
	@param focus: The current focus, deciding whether "Set focus" is offered.
	@param bind: Binds each item to what it does.
	@returns: The submenu.
	"""
	submenu = wx.Menu()
	# Translators: submenu item that stops tracking a single target.
	stopItem = submenu.Append(wx.ID_ANY, _("Stop tracking"))
	bind(stopItem, lambda: plugin.stopTracking(target), documentation.TARGET_MENU)
	if target.canTakeFocus() and not target.hasFocus(focus):
		# Translators: submenu item that moves the focus to a target.
		focusItem = submenu.Append(wx.ID_ANY, _("Set focus"))
		bind(focusItem, lambda: plugin.setFocusToTarget(target), documentation.TARGET_MENU)
	_appendSettingsSubmenu(submenu, plugin, target, bind)
	if target.history and addonConfig.get("menuChangedContent"):
		_appendHistorySubmenu(submenu, target, bind)
	return submenu


def _appendHistorySubmenu(submenu: wx.Menu, target: TrackedTarget, bind: Bind):
	"""
	Add the submenu listing a target's recent changes.
	@param submenu: The target's submenu.
	@param target: The target.
	@param bind: Binds each item to what it does.
	"""
	historyMenu = wx.Menu()
	for change in sortChanges(target.history, str(addonConfig.get("historySorting"))):
		item = historyMenu.Append(wx.ID_ANY, _plain(f"{relativeTime(change.time)}, {change.text}"))
		bind(item, lambda serial=change.serial: dialogs.showHistory(target, serial), documentation.HISTORY)
	# Translators: submenu of a target's menu, listing the target's recent changes.
	submenu.AppendSubMenu(historyMenu, _("Recent changes"))


def _binder(chapters: dict[int, str]) -> Bind:
	"""
	Make the function that binds menu items, keeping their ids to unbind once the menu closes.
	@param chapters: Receives the id of every item bound, with the chapter of the documentation F1 opens on it.
	@returns: The binding function.
	"""

	def bind(item: wx.MenuItem, func: Callable[[], None], chapter: str):
		gui.mainFrame.Bind(wx.EVT_MENU, lambda evt: func(), item)
		chapters[item.GetId()] = chapter

	return bind


def _popUp(menu: wx.Menu, chapters: Mapping[int, str]):
	"""
	Show a menu until it closes, then unbind its items and destroy it.
	@param menu: The menu to show.
	@param chapters: The ids of the items bound in it, with the chapter of the documentation F1 opens on each.
	"""
	byMenuId = {itemId & 0xFFFF: chapter for itemId, chapter in chapters.items()}

	def onHelp(evt: wx.HelpEvent):
		documentation.openChapter(byMenuId.get(evt.GetId() & 0xFFFF, documentation.TARGET_MENU))

	gui.mainFrame.Bind(wx.EVT_HELP, onHelp)
	gui.mainFrame.prePopup()
	try:
		gui.mainFrame.PopupMenu(menu)
	finally:
		gui.mainFrame.postPopup()
		gui.mainFrame.Unbind(wx.EVT_HELP, handler=onHelp)
		for itemId in chapters:
			with contextlib.suppress(Exception):
				gui.mainFrame.Unbind(wx.EVT_MENU, id=itemId)
		menu.Destroy()


def _buildAndShow(plugin: "GlobalPlugin", sources: Sequence[Source], focus: FocusState):
	notifier = plugin.notifier
	menu = wx.Menu()
	chapters: dict[int, str] = {}
	bind = _binder(chapters)

	tracked = plugin.registry.sortedTargets(str(addonConfig.get("menuSorting")))
	for target in tracked:
		menu.AppendSubMenu(
			_targetSubmenu(plugin, target, focus, bind), _plain(notifier.menuDescription(target))
		)

	if sources:
		if tracked:
			menu.AppendSeparator()
		for kind, obj in sources:
			item = menu.Append(wx.ID_ANY, _plain(_startLabel(kind, obj)))
			bind(item, lambda o=obj, k=kind: plugin.startTracking(o, k), documentation.TARGET_MENU)

	if tracked:
		menu.AppendSeparator()
		# Translators: menu item that stops tracking every target at once.
		allItem = menu.Append(wx.ID_ANY, _("Stop tracking all targets"))
		bind(allItem, lambda: plugin.clearAll(), documentation.TARGET_MENU)

	if not (tracked or sources):
		notifier.noTargets()
		menu.Destroy()
		return

	_popUp(menu, chapters)
