# Background Content Tracker: Firefox tabs
# Copyright (C) 2026 Lukáš Hosnedl
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

from collections import deque
from typing import Any

import IAccessibleHandler
import oleacc
import winUser
from comInterfaces import IAccessible2Lib as IA2
from NVDAObjects import NVDAObject
from NVDAObjects.IAccessible import IAccessible

from . import targets

_WINDOW_CLASS = "MozillaWindowClass"
_MAX_ANCESTORS = 100
_MAX_PANEL_NODES = 50
_STOP_ROLES = frozenset((oleacc.ROLE_SYSTEM_APPLICATION, oleacc.ROLE_SYSTEM_WINDOW))


def isGecko(obj: NVDAObject) -> bool:
	"""
	Whether an object is read through IAccessible in a Firefox window.
	@param obj: The object.
	@returns: False also when its window cannot be told.
	"""
	if not isinstance(obj, IAccessible):
		return False
	root = targets.safeCall(lambda: winUser.getAncestor(obj.windowHandle, winUser.GA_ROOT))
	return bool(root) and targets.safeCall(lambda: winUser.getClassName(root)) == _WINDOW_CLASS


def _role(acc: Any) -> int | None:
	"""
	An accessible's role, as IAccessible2 or else MSAA gives it.
	@param acc: The accessible.
	@returns: The role number, or None when it cannot be read.
	"""
	role = targets.safeCall(lambda: acc.role()) if isinstance(acc, IA2.IAccessible2) else None
	if not role:
		role = targets.safeCall(lambda: acc.accRole(0))
	return role if isinstance(role, int) else None


def parentOf(acc: Any) -> Any | None:
	"""
	An accessible's parent.
	@param acc: The accessible.
	@returns: The parent, or None.
	"""
	parent = targets.safeCall(lambda: IAccessibleHandler.accParent(acc, 0))
	return parent[0] if parent else None


def _children(acc: Any) -> list[Any]:
	"""
	An accessible's children that are accessibles of their own.
	@param acc: The accessible.
	@returns: The children.
	"""
	count = targets.safeCall(lambda: acc.accChildCount, 0)
	if not isinstance(count, int) or count <= 0:
		return []
	children = targets.safeCall(lambda: IAccessibleHandler.accessibleChildren(acc, 0, count), [])
	return [child for child, childID in children if childID == 0]


def tabDocument(acc: Any) -> Any | None:
	"""
	The document of the tab an accessible is in.
	@param acc: The accessible, which may be the document itself.
	@returns: The topmost document among its ancestors, or None outside a page.
	"""
	found = None
	current = acc
	for _ancestor in range(_MAX_ANCESTORS):
		role = _role(current)
		if role is None or role in _STOP_ROLES:
			break
		if role == oleacc.ROLE_SYSTEM_DOCUMENT:
			found = current
		current = parentOf(current)
		if current is None:
			break
	return found


def isActiveDocument(document: Any) -> bool | None:
	"""
	Whether Firefox keeps a tab's document up to date as the one shown.
	@param document: The tab's document.
	@returns: None when its state cannot be read.
	"""
	state = targets.safeCall(lambda: document.accState(0))
	if not isinstance(state, int):
		return None
	return not state & oleacc.STATE_SYSTEM_OFFSCREEN


def windowRoot(hwnd: int) -> Any | None:
	"""
	The accessible of a window's top-level window.
	@param hwnd: The window.
	@returns: The accessible, or None.
	"""
	root = targets.safeCall(lambda: winUser.getAncestor(hwnd, winUser.GA_ROOT)) or hwnd
	found = targets.safeCall(
		lambda: IAccessibleHandler.accessibleObjectFromEvent(root, winUser.OBJID_CLIENT, 0)
	)
	return found[0] if found else None


def selectedDocument(windowAcc: Any) -> Any | None:
	"""
	The document of a Firefox window's selected tab.
	@param windowAcc: The accessible of the window.
	@returns: The document, or None.
	"""
	found = targets.safeCall(
		lambda: IAccessibleHandler.accNavigate(windowAcc, 0, IAccessibleHandler.NAVRELATION_EMBEDS)
	)
	return found[0] if found else None


def tabPanel(document: Any) -> Any | None:
	"""
	The tab panel a tab's page is shown in.
	@param document: The document of the tab's page.
	@returns: The tab panel, or None.
	"""
	current = parentOf(document)
	for _ancestor in range(_MAX_ANCESTORS):
		if current is None:
			break
		role = _role(current)
		if role is None or role in _STOP_ROLES:
			break
		if role == oleacc.ROLE_SYSTEM_PROPERTYPAGE:
			return current
		current = parentOf(current)
	return None


def _documentIn(panel: Any) -> Any | None:
	"""
	The page shown in a tab panel.
	@param panel: The tab panel.
	@returns: The first document under it, breadth first, or None.
	"""
	pending = deque(_children(panel))
	examined = 0
	while pending and examined < _MAX_PANEL_NODES:
		acc = pending.popleft()
		examined += 1
		if _role(acc) == oleacc.ROLE_SYSTEM_DOCUMENT:
			return acc
		pending.extend(_children(acc))
	return None


def tabDocuments(windowAcc: Any) -> list[Any]:
	"""
	The document of every tab in a Firefox window that has a page loaded.
	@param windowAcc: The accessible of the window.
	@returns: The documents.
	"""
	selected = selectedDocument(windowAcc)
	panel = tabPanel(selected) if selected is not None else None
	panels = parentOf(panel) if panel is not None else None
	if panels is None:
		return []
	documents: list[Any] = []
	for child in _children(panels):
		if _role(child) != oleacc.ROLE_SYSTEM_PROPERTYPAGE:
			continue
		document = _documentIn(child)
		if document is not None:
			documents.append(document)
	return documents


def uniqueID(acc: Any) -> int | None:
	"""
	What tells an accessible from every other one in its window.
	@param acc: The accessible.
	@returns: Its IAccessible2 unique ID, or None.
	"""
	return targets.safeCall(lambda: acc.uniqueID) if isinstance(acc, IA2.IAccessible2) else None


def _labelledBy(acc: Any) -> Any | None:
	"""
	What an accessible is labelled by, as IAccessible2 relates them.
	@param acc: The accessible.
	@returns: The first target of its "labelled by" relation, or None.
	"""

	def find() -> Any | None:
		for index in range(acc.nRelations):
			relation = acc.relation(index)
			if relation.relationType == IAccessibleHandler.RelationType.LABELLED_BY and relation.nTargets:
				return IAccessibleHandler.normalizeIAccessible(relation.target(0))
		return None

	return targets.safeCall(find) if isinstance(acc, IA2.IAccessible2) else None


def isInSelectedTab(document: Any) -> bool:
	"""
	Whether a tab's document is that of its window's selected tab.
	@param document: The tab's document.
	@returns: True also when the selected tab cannot be told.
	"""
	hwnd = targets.safeCall(lambda: document.windowHandle)
	windowAcc = windowRoot(hwnd) if hwnd else None
	selected = selectedDocument(windowAcc) if windowAcc is not None else None
	return selected is None or uniqueID(selected) == uniqueID(document)


def selectTab(document: Any):
	"""
	Select the tab showing a document, if it can be found.
	@param document: The tab's document.
	"""
	panel = tabPanel(document)
	tab = _labelledBy(panel) if panel is not None else None
	if tab is not None:
		targets.safeCall(lambda: tab.accDoDefaultAction(0))
