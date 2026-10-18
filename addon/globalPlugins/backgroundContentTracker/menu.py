# Background Content Tracker: the target menu
# Copyright (C) 2026 Lukáš Hosnedl
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

import contextlib
import ctypes
from collections.abc import Callable, Mapping, Sequence
from ctypes import wintypes
from typing import TYPE_CHECKING

import addonHandler
import gui
import winUser
import wx
from logHandler import log
from NVDAObjects import NVDAObject

from . import addonConfig, dialogs, documentation
from .settings import WINDOW_SETTINGS, sharedSettingLabels
from .targets import FocusState, TrackedTarget, safeCall, sortChanges

if TYPE_CHECKING:
	from gettext import gettext as _  # noqa: TC004

	from . import GlobalPlugin

addonHandler.initTranslation()

Source = tuple[str, NVDAObject]
Bind = Callable[[wx.MenuItem, Callable[[], None], str], None]

_MN_GETHMENU = 0x01E1
_MF_BYPOSITION = 0x0400
_MF_HILITE = 0x0080
_getMenuState = ctypes.WINFUNCTYPE(wintypes.UINT, wintypes.HMENU, wintypes.UINT, wintypes.UINT)(
	("GetMenuState", ctypes.windll.user32)
)
_getSubMenu = ctypes.WINFUNCTYPE(wintypes.HMENU, wintypes.HMENU, ctypes.c_int)(
	("GetSubMenu", ctypes.windll.user32)
)
_getMenuItemCount = ctypes.WINFUNCTYPE(ctypes.c_int, wintypes.HMENU)(
	("GetMenuItemCount", ctypes.windll.user32)
)
_getMenuItemID = ctypes.WINFUNCTYPE(wintypes.UINT, wintypes.HMENU, ctypes.c_int)(
	("GetMenuItemID", ctypes.windll.user32)
)

_openChapters: Mapping[int, str] | None = None


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


def helpAt(focus: NVDAObject) -> Callable[[], str] | None:
	"""
	Whether F1 at the focus belongs to the open target menu, judged by window handles alone.
	@param focus: The focus.
	@returns: What gives the chapter of the documentation F1 opens, or None when F1 is not the add-on's.
	"""
	chapters = _openChapters
	if chapters is None or focus.windowClassName != "#32768":
		return None
	hwnd = focus.windowHandle
	return lambda: _highlightedChapter(
		hwnd, {itemId & 0xFFFF: chapter for itemId, chapter in chapters.items()}
	)


def _highlightedChapter(hwnd: int, chapters: Mapping[int, str]) -> str:
	"""
	The chapter of the item highlighted in a menu window: that of the submenu it opens, or else that of the menu.
	@param hwnd: The menu window.
	@param chapters: The chapter of each item bound, by the low word of its id.
	@returns: The chapter.
	"""
	hMenu = winUser.sendMessage(hwnd, _MN_GETHMENU, 0, 0)
	submenu = None
	for position in range(_getMenuItemCount(hMenu)):
		if _getMenuState(hMenu, position, _MF_BYPOSITION) & _MF_HILITE:
			submenu = _getSubMenu(hMenu, position)
			break
	return _menuChapter(submenu or hMenu, chapters) or documentation.TARGET_MENU


def _menuChapter(hMenu: int, chapters: Mapping[int, str]) -> str | None:
	"""
	The chapter of a menu, which is that of the items in it.
	@param hMenu: The menu.
	@param chapters: The chapter of each item bound, by the low word of its id.
	@returns: The chapter, or None for a menu with no item bound.
	"""
	for position in range(_getMenuItemCount(hMenu)):
		chapter = chapters.get(_getMenuItemID(hMenu, position) & 0xFFFF)
		if chapter is not None:
			return chapter
	return None


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
	shared = sharedSettingLabels()
	items: list[tuple[str, str]] = []
	announcing = addonConfig.get("changeAnnounce")
	if announcing:
		items.append(("interruptSpeech", shared["interruptSpeech"]))
	if int(addonConfig.get("historySize")) > 0:
		items.append(("updateOpenHistory", shared["updateOpenHistory"]))
		if announcing:
			items.append(("announceWithHistoryOpen", shared["announceWithHistoryOpen"]))
	if target.kind == "window":
		items.extend((key, shared[key]) for key in WINDOW_SETTINGS)
	items.append(
		# Translators: submenu item; read this one target while its own application is in the foreground.
		("trackForegroundTargets", _("Trac&k this target even in the foreground")),
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
		("rememberTargets", _("&Remember this target")),
	)
	if target.setting("rememberTargets"):
		items.append(
			# Translators: submenu item; drop this one remembered target once it no longer exists.
			("forgetOnDisappear", _("&Forget this target when it disappears")),
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
	submenu.AppendSubMenu(settingsMenu, _("Target &settings"))


def _targetSubmenu(
	plugin: "GlobalPlugin",
	target: TrackedTarget,
	focus: FocusState,
	bind: Bind,
	deferred: list[Callable[[], None]] | None = None,
) -> wx.Menu:
	"""
	Build the submenu of one target.
	@param plugin: The add-on, which carries out the chosen item.
	@param target: The target the submenu acts on.
	@param focus: The current focus, deciding whether "Set focus" is offered.
	@param bind: Binds each item to what it does.
	@param deferred: Receives what fills the history submenu, to be run later, or None to fill it now.
	@returns: The submenu.
	"""
	submenu = wx.Menu()
	# Translators: submenu item that stops tracking a single target.
	stopItem = submenu.Append(wx.ID_ANY, _("Stop &tracking"))
	bind(stopItem, lambda: plugin.stopTracking(target), documentation.TARGET_MENU)
	if target.canTakeFocus() and not target.hasFocus(focus):
		# Translators: submenu item that moves the focus to a target.
		focusItem = submenu.Append(wx.ID_ANY, _("Set &focus"))
		bind(focusItem, lambda: plugin.setFocusToTarget(target), documentation.TARGET_MENU)
	_appendSettingsSubmenu(submenu, plugin, target, bind)
	if dialogs.hasHistory(target):
		_appendHistorySubmenu(submenu, target, bind, deferred)
	return submenu


def _appendHistorySubmenu(
	submenu: wx.Menu,
	target: TrackedTarget,
	bind: Bind,
	deferred: list[Callable[[], None]] | None,
):
	"""
	Add the submenu listing a target's recent changes.
	@param submenu: The target's submenu.
	@param target: The target.
	@param bind: Binds each item to what it does.
	@param deferred: Receives what fills the submenu, to be run later, or None to fill it now.
	"""
	historyMenu = wx.Menu()

	def fill():
		parts = dialogs.historyParts()
		for change in sortChanges(target.history, str(addonConfig.get("historySorting"))):
			label = ", ".join(part for part in dialogs.entryParts(change, parts) if part is not None)
			item = historyMenu.Append(wx.ID_ANY, _plain(label))
			bind(item, lambda: dialogs.showHistory(target), documentation.HISTORY)

	if deferred is None:
		fill()
	else:
		deferred.append(fill)
	# Translators: submenu of a target's menu, listing the target's recent changes.
	submenu.AppendSubMenu(historyMenu, _("&Recent changes"))


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


def _popUp(menu: wx.Menu, chapters: Mapping[int, str], deferred: list[Callable[[], None]] | None = None):
	"""
	Show a menu until it closes, then unbind its items and destroy it.
	@param menu: The menu to show.
	@param chapters: The ids of the items bound in it, with the chapter of the documentation F1 opens on each.
	@param deferred: What fills submenus, run when the first submenu opens.
	"""
	global _openChapters

	def fillDeferred(evt: wx.MenuEvent):
		evt.Skip()
		if evt.GetMenu() is not menu and deferred:
			for fill in deferred:
				fill()
			deferred.clear()

	_openChapters = chapters
	gui.mainFrame.Bind(wx.EVT_MENU_OPEN, fillDeferred)
	gui.mainFrame.prePopup()
	try:
		gui.mainFrame.PopupMenu(menu)
	finally:
		gui.mainFrame.postPopup()
		gui.mainFrame.Unbind(wx.EVT_MENU_OPEN, handler=fillDeferred)
		_openChapters = None
		for itemId in chapters:
			with contextlib.suppress(Exception):
				gui.mainFrame.Unbind(wx.EVT_MENU, id=itemId)
		menu.Destroy()


def _buildAndShow(plugin: "GlobalPlugin", sources: Sequence[Source], focus: FocusState):
	notifier = plugin.notifier
	menu = wx.Menu()
	chapters: dict[int, str] = {}
	bind = _binder(chapters)
	deferred: list[Callable[[], None]] = []

	tracked = plugin.registry.sortedTargets(str(addonConfig.get("menuSorting")))
	for target in tracked:
		menu.AppendSubMenu(
			_targetSubmenu(plugin, target, focus, bind, deferred), _plain(notifier.menuDescription(target))
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
		allItem = menu.Append(wx.ID_ANY, _("Stop tracking &all targets"))
		bind(allItem, lambda: plugin.clearAll(), documentation.TARGET_MENU)

	if not (tracked or sources):
		notifier.noTargets()
		menu.Destroy()
		return

	_popUp(menu, chapters, deferred)
