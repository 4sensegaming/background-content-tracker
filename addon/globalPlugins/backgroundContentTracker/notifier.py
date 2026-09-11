# Background Content Tracker: spoken and beeped notifications
# Copyright (C) 2026 Lukáš Hosnedl
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

import time
from collections.abc import Sequence
from typing import TYPE_CHECKING

import addonHandler
import core
import speech
import tones
import ui
from logHandler import log
from speech.priorities import Spri

from . import addonConfig
from .targets import TrackedTarget

if TYPE_CHECKING:
	from gettext import gettext as _  # noqa: TC004
	from gettext import ngettext  # noqa: TC004

addonHandler.initTranslation()

_UNPROMPTED_DELAY_MS = 400

_SAME_TARGET_INTERVALS = 5

_NAMED_RESTORED_LIMIT = 5

Extras = Sequence[str | None]


def _describe(roleText: str, name: str, includeType: bool, extras: Extras) -> str:
	if includeType and roleText:
		base = f"{roleText}: {name}" if name else roleText
	else:
		base = name or roleText
	parts = [base] if base else []
	parts.extend([piece for piece in extras if piece])
	return ", ".join(parts)


def _notFound() -> str:
	# Translators: shown in the target menu, and spoken on demand, for a target
	# that does not currently exist (e.g. a remembered target not yet reopened).
	return _("not found")


def _noChanges() -> str:
	# Translators: shown in the target menu, and spoken on demand, for a target
	# that has not changed since it was added, or is being looked at right now.
	return _("no changes yet")


def relativeTime(when: float | None) -> str:
	if not when:
		return _noChanges()
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
	hours = mins // 60
	# Translators: relative time in hours. {n} is the number of hours.
	return ngettext("{n} hour ago", "{n} hours ago", hours).format(n=hours)


class Notifier:
	def __init__(self):
		self._lastChange: tuple[int, float] | None = None

	def _announce(self, text: str, unprompted: bool, priority: Spri):
		if not unprompted:
			ui.message(text)
			return
		core.callLater(_UNPROMPTED_DELAY_MS, ui.message, text, priority)

	def _describeTarget(
		self,
		target: TrackedTarget,
		extras: Extras = (),
		typeSetting: str = "announceTargetType",
	) -> str:
		return _describe(target.roleText(), target.name, bool(addonConfig.get(typeSetting)), extras)

	def _announceTarget(self, template: str, target: TrackedTarget, unprompted: bool):
		self._announce(template.format(target=self._describeTarget(target)), unprompted, Spri.NEXT)

	def announceTracking(self, target: TrackedTarget, unprompted: bool = False):
		# Translators: announced when tracking starts, e.g. "Tracking window: Claude".
		self._announceTarget(_("Tracking {target}"), target, unprompted)

	def announceRestored(self, attached: Sequence[TrackedTarget], total: int):
		found = len(attached)
		if not found:
			# Translators: announced at start-up or on resuming tracking when none of
			# the remembered targets are there.
			text = _("No remembered targets found")
			self._announce(text, unprompted=True, priority=Spri.NORMAL)
			return
		named = found < _NAMED_RESTORED_LIMIT
		names = ", ".join(target.name or target.roleText() for target in attached)
		if found >= total and named:
			text = ngettext(
				# Translators: announced at start-up or on resuming tracking when every
				# remembered target has been found, and there are few enough to name.
				# {n} is how many there are, {names} their names, separated by commas.
				"Found {n} remembered target: {names}",
				"Found {n} remembered targets: {names}",
				found,
			).format(n=found, names=names)
		elif found >= total:
			# Translators: announced at start-up or on resuming tracking when every
			# remembered target has been found. {n} is how many there are.
			text = ngettext("Found {n} remembered target", "Found {n} remembered targets", found)
			text = text.format(n=found)
		elif named:
			# Translators: announced at start-up or on resuming tracking when only some
			# of the remembered targets have been found; the rest are still being looked
			# for. {found} is how many are being tracked, {total} how many there are,
			# {names} the names of the ones found, separated by commas.
			text = _("Found {found} of {total} remembered targets: {names}")
			text = text.format(found=found, total=total, names=names)
		else:
			# Translators: announced at start-up or on resuming tracking when only some
			# of the remembered targets have been found; the rest are still being looked
			# for. {found} is how many are being tracked, {total} how many there are.
			text = _("Found {found} of {total} remembered targets")
			text = text.format(found=found, total=total)
		self._announce(text, unprompted=True, priority=Spri.NORMAL)

	def announceStopped(self, target: TrackedTarget, unprompted: bool = False):
		# Translators: announced when tracking stops, e.g. "Stopped tracking listbox: Message list".
		self._announceTarget(_("Stopped tracking {target}"), target, unprompted)

	def announceDisappeared(self, target: TrackedTarget):
		# Translators: announced when a remembered target disappears and is kept in the
		# list to be tracked again once it reappears, e.g. "Target disappeared: Claude".
		self._announceTarget(_("Target disappeared: {target}"), target, unprompted=True)

	def announceChange(self, target: TrackedTarget, delta: str):
		if addonConfig.get("changeBeep"):
			self.beep()
		if not addonConfig.get("changeAnnounce"):
			return
		now = time.monotonic()
		window = _SAME_TARGET_INTERVALS * int(addonConfig.get("trackingInterval"))
		last = self._lastChange
		sameRun = last is not None and last[0] == target.uid and now - last[1] < window
		self._lastChange = (target.uid, now)
		if not addonConfig.get("announceChangedContent"):
			text = self._describeTarget(target)
		elif sameRun:
			text = delta
		else:
			text = self._describeTarget(target, [delta])
		if not text:
			return
		if target.setting("interruptSpeech"):
			speech.cancelSpeech()
		ui.message(text)

	def speakInfo(self, target: TrackedTarget):
		if not target.isAlive():
			ui.message(self._describeTarget(target, [_notFound()]))
			return
		if not target.hasReportableChange():
			ui.message(self._describeTarget(target, [_noChanges()]))
			return
		content = target.lastDelta if addonConfig.get("announceChangedContent") else None
		desc = self._describeTarget(target, [content])
		if desc:
			ui.message(desc)

	def menuDescription(self, target: TrackedTarget) -> str:
		if not target.isAlive():
			return self._describeTarget(target, [_notFound()], "menuTargetType")
		reportable = target.hasReportableChange()
		extras: list[str] = []
		if addonConfig.get("menuTimeSinceChange"):
			extras.append(relativeTime(target.lastChangeTime if reportable else None))
		if addonConfig.get("menuChangedContent") and reportable and target.lastDelta:
			extras.append(target.lastDelta)
		return self._describeTarget(target, extras, "menuTargetType")

	def beep(self):
		try:
			tones.beep(addonConfig.get("beepPitch"), addonConfig.get("beepDuration"))
		except Exception:  # noqa: BLE001
			log.debugWarning("Beep failed", exc_info=True)

	def noTargetInSlot(self, slotNumber: int):
		# Translators: announced when a number key addresses an empty slot, e.g. "No target in slot 2".
		ui.message(_("No target in slot {slot}").format(slot=slotNumber))

	def allCleared(self):
		# Translators: announced when the whole target list is cleared at once.
		ui.message(_("All targets cleared"))

	def noTargets(self):
		# Translators: announced when a command needs a target and none is being tracked.
		ui.message(_("No targets"))

	def focusFailed(self):
		# Translators: announced when "Set focus" cannot move the focus to a target (e.g. its window is gone).
		ui.message(_("Could not move focus to the target"))

	def alreadyFocused(self):
		# Translators: announced when a second press would move the focus to a target that already has it.
		ui.message(_("The target already has the focus"))

	def paused(self):
		# Translators: announced when background content tracking is paused.
		ui.message(_("Tracking paused"))

	def resumed(self):
		# Translators: announced when background content tracking is resumed.
		ui.message(_("Tracking resumed"))
