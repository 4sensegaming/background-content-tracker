# Background Content Tracker: the target menu
# Copyright (C) 2026 Lukáš Hosnedl
# This file is covered by the GNU General Public License, version 2.
# See the file COPYING.txt for more details.

"""Builds and shows the target menu (the prefix followed by "t"): a real wx
pop-up menu listing the tracked targets (each a submenu with Stop tracking, Set
focus and the target's own settings), then the targets that can be started from
the current location, and finally Stop tracking all targets. The current-location
sources are captured before the menu is shown, because showing it takes the focus
to the menu.
"""

import addonHandler
import gui
import wx
from logHandler import log

addonHandler.initTranslation()


def showTargetMenu(plugin, sources):
	"""Entry point, invoked (via ``wx.CallAfter``) on the main thread."""
	try:
		_buildAndShow(plugin, sources)
	except Exception:
		log.error("Error showing the target menu", exc_info=True)


def _startLabel(kind, obj):
	name = ""
	try:
		name = obj.name or ""
	except Exception:
		name = ""
	if not name:
		try:
			name = obj.role.displayString
		except Exception:
			name = ""
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


def _localSettingItems(target):
	"""This target's local settings, as (key, menu label), in display order.

	One entry per key of :data:`addonConfig.LOCAL_KEYS`, ordered as in the
	settings panel rather than as in that tuple, so the two read alike — except
	that the window tracking ones are offered for a whole-window target only. The
	monitor ignores every one of them unless the target is a window, so on a
	control they would be switches wired to nothing.

	Those are labelled with the settings panel's own words: they read the same
	wherever they are set. The remaining three are worded for the one target they
	act on here, rather than for every target at once as the panel's wording has
	it.

	Built on each call rather than held in a module-level constant, because the
	labels are translated at the moment they are built and the user can change
	NVDA's language without restarting the add-on.
	"""
	items = []
	if target.kind == "window":
		items.extend((
			# Translators: suppress announcements of progress bar controls in a window.
			("ignoreProgressBars", _("Ignore &progress bars")),
			# Translators: suppress repeated announcements of the same control (e.g. a timer).
			("ignoreRepeatedControls", _("Ignore &repeatedly changing controls")),
			# Translators: treat a window that renames itself as a target that has disappeared.
			("titleChangeDisappears", _("Consider c&hanged title a disappeared target")),
			# Translators: suppress announcements of the control the user is typing in.
			("ignoreFocusedControl", _("Ignore focu&sed control")),
		))
	items.extend((
		# Translators: submenu item; read this one target while its own application is in the foreground.
		("trackForegroundTargets", _("Read this target even when in foreground")),
		# Translators: submenu item; keep this one target between NVDA restarts and re-attach it on reappearance.
		("rememberTargets", _("Remember this target")),
		# Translators: submenu item; automatically drop this one target once it no longer exists.
		("forgetOnDisappear", _("Forget this target when it disappears")),
	))
	return items


def _appendSettingsSubmenu(submenu, plugin, target, bind):
	"""Append this target's own copy of the local settings, as check items.

	Each box shows the setting's *effective* value — the target's own where it has
	one, the global everywhere else — so what is ticked is what the target actually
	does, whether or not it has ever been given an opinion of its own. Ticking or
	unticking one gives the target its own value there and then, and only for that
	setting: everything left alone goes on following the global.

	The new value is worked out when the item is chosen rather than read back off
	the menu item, because by then the menu is being torn down.

	Which settings are offered depends on the target; see
	:func:`_localSettingItems`.
	"""
	settingsMenu = wx.Menu()
	for key, label in _localSettingItems(target):
		item = settingsMenu.AppendCheckItem(wx.ID_ANY, label)
		item.Check(bool(target.setting(key)))
		bind(item, lambda k=key, t=target: plugin.setTargetOverride(t, k, not t.setting(k)))
	# Translators: submenu of a target's menu, holding that target's own settings.
	submenu.AppendSubMenu(settingsMenu, _("Target settings"))


def _buildAndShow(plugin, sources):
	registry = plugin.registry
	notifier = plugin.notifier
	menu = wx.Menu()
	boundIds = []

	def bind(item, func):
		gui.mainFrame.Bind(wx.EVT_MENU, lambda evt: func(), item)
		boundIds.append(item.GetId())

	# Currently tracked targets first, honouring the Target sorting setting.
	trackedCount = 0
	for target in registry.sortedTargets():
		trackedCount += 1
		submenu = wx.Menu()
		# Translators: submenu item that stops tracking a single target.
		stopItem = submenu.Append(wx.ID_ANY, _("Stop tracking"))
		bind(stopItem, lambda t=target: plugin.stopTracking(t))
		# Translators: submenu item that moves the focus to a target.
		focusItem = submenu.Append(wx.ID_ANY, _("Set focus"))
		bind(focusItem, lambda t=target: plugin.setFocusToTarget(t))
		_appendSettingsSubmenu(submenu, plugin, target, bind)
		menu.AppendSubMenu(submenu, notifier.menuDescription(target))

	# Then the targets that can be started from the current location.
	if sources:
		if trackedCount:
			menu.AppendSeparator()
		for kind, obj in sources:
			item = menu.Append(wx.ID_ANY, _startLabel(kind, obj))
			bind(item, lambda o=obj, k=kind: plugin.startTracking(o, k))

	# Finally, stop tracking everything.
	if trackedCount:
		menu.AppendSeparator()
		# Translators: menu item that stops tracking every target at once.
		allItem = menu.Append(wx.ID_ANY, _("Stop tracking all targets"))
		bind(allItem, lambda: plugin.clearAll())

	if menu.GetMenuItemCount() == 0:
		notifier.noTargets()
		menu.Destroy()
		return

	gui.mainFrame.prePopup()
	try:
		gui.mainFrame.PopupMenu(menu)
	finally:
		gui.mainFrame.postPopup()
		for itemId in boundIds:
			try:
				gui.mainFrame.Unbind(wx.EVT_MENU, id=itemId)
			except Exception:
				pass
		menu.Destroy()
