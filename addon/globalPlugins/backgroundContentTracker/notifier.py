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


def _notFound():
	"""The trailing piece describing a target that is not there.

	A function rather than a constant so that it is translated when it is used,
	not once when this module is imported.
	"""
	# Translators: shown in the target menu, and spoken on demand, for a target
	# that does not currently exist (e.g. a remembered target not yet reopened).
	return _("not found")


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
		# Queued rather than interrupting: an application coming back can bring
		# several remembered targets with it, and an interrupting message would
		# leave only the last of them audible.
		ui.message(_("Tracking {target}").format(target=desc), speechPriority=Spri.NEXT)

	def announceRestored(self, found, total):
		"""Report the remembered targets restored at start-up, in one message.

		They are counted rather than named: ten of them named one after another,
		over NVDA's own start-up speech, is a recital of things the user already
		knows they asked to be remembered. What is worth hearing is whether they
		are all back, and the numbers say that in a breath. Any that turn up later
		announce themselves as usual.
		"""
		if not found:
			self.noTargets()
			return
		if found >= total:
			# Translators: announced at start-up when every remembered target has been
			# found. {n} is how many there are.
			text = ngettext("Tracking {n} remembered target", "Tracking {n} remembered targets", found)
			ui.message(text.format(n=found), speechPriority=Spri.NEXT)
			return
		# Translators: announced at start-up when only some of the remembered targets
		# have been found; the rest are still being looked for. {found} is how many
		# are being tracked, {total} how many there are.
		text = _("Tracking {found} of {total} remembered targets")
		ui.message(text.format(found=found, total=total), speechPriority=Spri.NEXT)

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

		A target that is not there at all is reported as not found. This is the
		usual state of a remembered target whose window has not been opened yet:
		it holds the slot, but there is nothing behind it, and reporting it as
		merely unchanged would suggest the opposite.

		A target the user is looking at right now, or one that has not changed since
		it was baselined, has nothing new to report, so we say so explicitly rather
		than replay a delta cached during an earlier spell in the background.
		"""
		if not target.isAlive():
			desc = _describe(target.roleText(), target.name, addonConfig.get("announceTargetType"), [_notFound()])
			ui.message(desc)
			return
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

		A target that is not there is shown as not found, in place of both the time
		and the content: neither says anything about a target that does not exist,
		and "no changes yet" would say the wrong thing about one. It is still listed,
		because a target that is not there can still be stopped, have its own
		settings changed, or simply be waited for.

		A target the user is looking at right now shows "no changes yet": the delta
		the monitor cached belongs to an earlier background spell, not to now.
		"""
		if not target.isAlive():
			return _describe(target.roleText(), target.name, addonConfig.get("menuTargetType"), [_notFound()])
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
