# Background Content Tracker: the target menu
# Copyright (C) 2026 Lukáš Hosnedl
# This file is covered by the GNU General Public License, version 2.
# See the file COPYING.txt for more details.

"""Builds and shows the target menu (the prefix followed by "t"): a real wx
pop-up menu listing the tracked targets (each a submenu with Stop tracking and
Set focus), then the targets that can be started from the current location, and
finally Stop tracking all targets. The current-location sources are captured
before the menu is shown, because showing it takes the focus to the menu.
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
