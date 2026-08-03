# Background Content Tracker: spoken and beeped notifications
# Copyright (C) 2026 Lukáš Hosnedl
# This file is covered by the GNU General Public License, version 2.
# See the file COPYING.txt for more details.

"""Everything the user hears. All wording here is translatable; control-type
(role) names are taken from NVDA itself and are therefore already localised.
"""

import time

import addonHandler
import tones
import ui
from logHandler import log
from speech.priorities import Spri

from . import addonConfig

addonHandler.initTranslation()


def _describe(roleText, name, includeType, extras):
	"""Build a target description such as "window: Claude, 3 minutes ago".

	``extras`` is a list of already-formatted trailing pieces (time, content);
	empty pieces are dropped.
	"""
	if includeType and roleText:
		base = u"{role}: {name}".format(role=roleText, name=name) if name else roleText
	else:
		base = name or roleText
	parts = [base] if base else []
	parts.extend([piece for piece in extras if piece])
	return u", ".join(parts)


def relativeTime(when):
	"""A human, translatable "x ago" string for the target menu."""
	if not when:
		# Translators: shown in the target menu when a target has not changed yet.
		return _("no changes yet")
	secs = int(time.time() - when)
	if secs < 5:
		# Translators: relative time for a change that has only just happened.
		return _("just now")
	if secs < 60:
		# Translators: relative time in seconds. {n} is the number of seconds.
		return ngettext("{n} second ago", "{n} seconds ago", secs).format(n=secs)
	mins = secs // 60
	if mins < 60:
		# Translators: relative time in minutes. {n} is the number of minutes.
		return ngettext("{n} minute ago", "{n} minutes ago", mins).format(n=mins)
	# Hours is the largest unit we distinguish; older changes keep counting in hours.
	hours = mins // 60
	# Translators: relative time in hours. {n} is the number of hours.
	return ngettext("{n} hour ago", "{n} hours ago", hours).format(n=hours)


class Notifier(object):
	"""Turns registry/monitor events into speech and beeps, per the settings."""

	def announceTracking(self, target):
		desc = _describe(target.roleText(), target.name, addonConfig.get("announceTargetType"), [])
		# Translators: announced when tracking starts, e.g. "Tracking window: Claude".
		# Queued rather than interrupting: several remembered targets are
		# re-attached in a quick loop at start-up, and an interrupting message
		# would leave only the last one audible.
		ui.message(_("Tracking {target}").format(target=desc), speechPriority=Spri.NEXT)

	def announceStopped(self, target):
		desc = _describe(target.roleText(), target.name, addonConfig.get("announceTargetType"), [])
		# Translators: announced when tracking stops, e.g. "Stopped tracking listbox: Message list".
		ui.message(_("Stopped tracking {target}").format(target=desc))

	def announceChange(self, target, delta):
		"""A change was detected in ``target``; ``delta`` is the new content."""
		if addonConfig.get("changeBeep"):
			self.beep()
		if not addonConfig.get("changeAnnounce"):
			return
		content = delta if addonConfig.get("announceChangedContent") else None
		desc = _describe(target.roleText(), target.name, addonConfig.get("announceTargetType"), [content])
		if desc:
			ui.message(desc)

	def speakInfo(self, target):
		"""On-demand information about a target (the number/space/enter keys).

		A target the user is looking at right now, or one that has not changed since
		it was baselined, has nothing new to report, so we say so explicitly rather
		than replay a delta cached during an earlier spell in the background.
		"""
		if not target.hasReportableChange():
			# Translators: on-demand target info when there is nothing new to report.
			desc = _describe(target.roleText(), target.name, addonConfig.get("announceTargetType"), [_("no changes yet")])
			ui.message(desc)
			return
		content = target.lastDelta if addonConfig.get("announceChangedContent") else None
		desc = _describe(target.roleText(), target.name, addonConfig.get("announceTargetType"), [content])
		if desc:
			ui.message(desc)

	def menuDescription(self, target):
		"""The text of a target's item in the target menu.

		A target the user is looking at right now shows "no changes yet": the delta
		the monitor cached belongs to an earlier background spell, not to now.
		"""
		reportable = target.hasReportableChange()
		extras = []
		if addonConfig.get("menuTimeSinceChange"):
			extras.append(relativeTime(target.lastChangeTime if reportable else None))
		if addonConfig.get("menuChangedContent") and reportable and target.lastDelta:
			extras.append(target.lastDelta)
		return _describe(target.roleText(), target.name, addonConfig.get("menuTargetType"), extras)

	def beep(self):
		try:
			tones.beep(addonConfig.get("beepPitch"), addonConfig.get("beepDuration"))
		except Exception:
			log.debugWarning("Beep failed", exc_info=True)

	def noTargetInSlot(self, slotNumber):
		# Translators: announced when a number key addresses an empty slot, e.g. "No target in slot 2".
		ui.message(_("No target in slot {slot}").format(slot=slotNumber))

	def allCleared(self):
		# Translators: announced when the whole target list is cleared at once.
		ui.message(_("All targets cleared"))

	def noTargets(self):
		# Translators: announced (on resume and at start-up) when there are no valid targets.
		ui.message(_("No targets to track"))

	def focusFailed(self):
		# Translators: announced when "Set focus" cannot move the focus to a target (e.g. its window is gone).
		ui.message(_("Could not move focus to the target"))

	def paused(self):
		# Translators: announced when background content tracking is paused.
		ui.message(_("Background content tracking disabled"))

	def resumed(self):
		# Translators: announced when background content tracking is resumed.
		ui.message(_("Background content tracking enabled"))
