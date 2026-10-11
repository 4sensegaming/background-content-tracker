# Background Content Tracker: opening the documentation at a chapter
# Copyright (C) 2026 Lukáš Hosnedl
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

import os
import re
import tempfile
from pathlib import Path
from urllib.parse import quote

import addonHandler

KEYSTROKES = "keystrokes"
TARGET_MENU = "the-target-menu"
TARGET_SETTINGS = "target-settings"
HISTORY = "history-of-recent-changes"
GLOBAL_SETTINGS = "global-settings"

_HEADING_ID = re.compile(r'<h[1-6] id="([^"]+)"')


def _headingIds(path: str) -> list[str]:
	"""
	The ids of a readme's headings.
	@param path: The readme in html.
	@returns: The ids, in order.
	"""
	with open(path, encoding="utf-8") as f:
		return _HEADING_ID.findall(f.read())


def openChapter(chapter: str):
	"""
	Open the readme in the user's language in the default web browser, at a chapter.
	@param chapter: The id of the chapter's heading in the English readme.
	"""
	addon = addonHandler.getCodeAddon()
	english = os.path.join(addon.path, "doc", "en", "readme.html")
	path = addon.getDocFilePath() or english
	# Every translation has the English headings in the same order, so a chapter
	# keeps its position; a translation that has drifted is skipped.
	englishIds = _headingIds(english)
	ids = _headingIds(path)
	if len(ids) != len(englishIds):
		path, ids = english, englishIds
	anchor = ids[englishIds.index(chapter)]
	redirect = os.path.join(tempfile.gettempdir(), "backgroundContentTrackerHelp.html")
	url = f"{Path(path).as_uri()}#{quote(anchor)}"
	with open(redirect, "w", encoding="utf-8") as f:
		f.write(f'<!DOCTYPE html><meta charset="utf-8"><meta http-equiv="refresh" content="0;url={url}">')
	os.startfile(redirect)
