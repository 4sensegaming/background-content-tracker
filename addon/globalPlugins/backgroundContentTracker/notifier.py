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

_NAMED_RESTORED_LIMIT = 5

Extras = Sequence[str | None]


def describe(roleText: str, name: str, includeType: bool, extras: Extras) -> str:
	"""
	Describe a target, e.g. "Window: Claude, 3 minutes ago".
	@param roleText: The target's type.
	@param name: The target's name.
	@param includeType: Whether the type is part of the description.
	@param extras: What follows the name; empty pieces are left out.
	@returns: The description.
	"""
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


def _pausedNote() -> str | None:
	"""
	The note that ends target information while tracking is paused.
	@returns: The note, or None while tracking is enabled.
	"""
	if addonConfig.get("enabled"):
		return None
	# Translators: added to the end of a target's item in the target menu and of its
	# information spoken on demand while background content tracking is paused.
	return _("Tracking paused")


def _sentence(text: str) -> str:
	"""
	End a spoken announcement with a full stop, unless it already ends a sentence.
	@param text: The announcement.
	@returns: The announcement as a sentence.
	"""
	return text if text.endswith((".", "!", "?", "…")) else f"{text}."


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


def _speakAll(texts: Sequence[str], priority: Spri):
	"""
	Speak announcements one after another.
	@param texts: The announcements, in the order they are spoken.
	@param priority: Their speech priority.
	"""
	for text in texts:
		ui.message(text, priority)


class Notifier:
	def _announce(self, texts: Sequence[str], unprompted: bool, priority: Spri):
		"""
		Speak announcements one after another, at once or after a short delay.
		@param texts: The announcements, in the order they are spoken.
		@param unprompted: Whether they come unasked, which delays them.
		@param priority: The speech priority of delayed announcements.
		"""
		if not unprompted:
			for text in texts:
				ui.message(text)
			return
		core.callLater(_UNPROMPTED_DELAY_MS, _speakAll, texts, priority)

	def _describeTarget(
		self,
		target: TrackedTarget,
		extras: Extras = (),
		typeSetting: str = "announceTargetType",
	) -> str:
		return describe(target.roleText(), target.name, bool(addonConfig.get(typeSetting)), extras)

	def _announceTarget(self, template: str, target: TrackedTarget, unprompted: bool):
		self._announce([template.format(target=self._describeTarget(target))], unprompted, Spri.NEXT)

	def announceTracking(self, target: TrackedTarget, unprompted: bool = False):
		# Translators: announced when tracking starts, e.g. "Tracking window: Claude."
		self._announceTarget(_("Tracking {target}."), target, unprompted)

	def announceTrackingInForeground(self, target: TrackedTarget):
		"""
		Announce a target just added to be read even while its own application is in the foreground.
		@param target: The target added.
		"""
		self._announceTarget(
			# Translators: announced when tracking starts for a target added to be read even while
			# its own application is in the foreground, e.g. "Tracking window: Claude even in the foreground."
			_("Tracking {target} even in the foreground."),
			target,
			unprompted=False,
		)

	def announceRestored(self, attached: Sequence[TrackedTarget], total: int):
		found = len(attached)
		if not found:
			# Translators: announced at start-up or on resuming tracking when none of
			# the remembered targets are there.
			text = _("No remembered targets found.")
			self._announce([text], unprompted=True, priority=Spri.NORMAL)
			return
		named = found < _NAMED_RESTORED_LIMIT
		names = ", ".join(self._describeTarget(target) for target in attached)
		if found >= total and named:
			text = ngettext(
				# Translators: announced at start-up or on resuming tracking when every
				# remembered target has been found, and there are few enough to name.
				# {n} is how many there are, {names} their names, each with its type if
				# announced (e.g. "window: Claude"), separated by commas.
				"Found {n} remembered target: {names}.",
				"Found {n} remembered targets: {names}.",
				found,
			).format(n=found, names=names)
		elif found >= total:
			# Translators: announced at start-up or on resuming tracking when every
			# remembered target has been found. {n} is how many there are.
			text = ngettext("Found {n} remembered target.", "Found {n} remembered targets.", found)
			text = text.format(n=found)
		elif named:
			# Translators: announced at start-up or on resuming tracking when only some
			# of the remembered targets have been found; the rest are still being looked
			# for. {found} is how many are being tracked, {total} how many there are,
			# {names} the names of the ones found, each with its type if announced
			# (e.g. "window: Claude"), separated by commas.
			text = _("Found {found} of {total} remembered targets: {names}.")
			text = text.format(found=found, total=total, names=names)
		else:
			# Translators: announced at start-up or on resuming tracking when only some
			# of the remembered targets have been found; the rest are still being looked
			# for. {found} is how many are being tracked, {total} how many there are.
			text = _("Found {found} of {total} remembered targets.")
			text = text.format(found=found, total=total)
		self._announce([text], unprompted=True, priority=Spri.NORMAL)

	def announceStopped(self, target: TrackedTarget, unprompted: bool = False):
		# Translators: announced when tracking stops, e.g. "Stopped tracking list: Message list."
		texts = [_("Stopped tracking {target}.").format(target=self._describeTarget(target))]
		if target.setting("rememberTargets"):
			# Translators: announced right after "Stopped tracking" when the target was remembered.
			texts.append(_("Target forgotten."))
		self._announce(texts, unprompted, Spri.NEXT)

	def announceDisappeared(self, target: TrackedTarget):
		# Translators: announced when a remembered target disappears and is kept in the
		# list to be tracked again once it reappears, e.g. "Target disappeared: Claude."
		self._announceTarget(_("Target disappeared: {target}."), target, unprompted=True)

	def announceChange(self, target: TrackedTarget, delta: str, sameTarget: bool, speak: bool = True):
		"""
		Beep and speak a change in a target, as the settings ask.
		@param target: The target that changed.
		@param delta: The new content of the target.
		@param sameTarget: Whether the change announced before this one was in the same target.
		@param speak: Whether the change may be spoken at all.
		"""
		if addonConfig.get("changeBeep"):
			self.beep()
		if not (speak and addonConfig.get("changeAnnounce")):
			return
		if not addonConfig.get("announceChangedContent"):
			text = _sentence(self._describeTarget(target))
		elif sameTarget and not addonConfig.get("repeatTargetName"):
			text = delta
		else:
			text = self._describeTarget(target, [delta])
		if not text:
			return
		if target.setting("interruptSpeech"):
			speech.cancelSpeech()
		ui.message(text)

	def speakInfo(self, target: TrackedTarget):
		paused = _pausedNote()
		if not target.isAlive():
			ui.message(_sentence(self._describeTarget(target, [_notFound(), paused])))
			return
		if not target.hasReportableChange():
			ui.message(_sentence(self._describeTarget(target, [_noChanges(), paused])))
			return
		lastChange = target.lastChange
		content = (
			lastChange[0] if lastChange is not None and addonConfig.get("announceChangedContent") else None
		)
		desc = self._describeTarget(target, [content, paused])
		if desc:
			ui.message(desc if content and paused is None else _sentence(desc))

	def menuDescription(self, target: TrackedTarget) -> str:
		paused = _pausedNote()
		if not target.isAlive():
			return self._describeTarget(target, [_notFound(), paused], "menuTargetType")
		lastChange = target.lastChange if target.hasReportableChange() else None
		extras: list[str | None] = []
		if addonConfig.get("menuTimeSinceChange"):
			extras.append(relativeTime(lastChange[1] if lastChange is not None else None))
		if addonConfig.get("menuChangedContent") and lastChange is not None and lastChange[0]:
			extras.append(lastChange[0])
		extras.append(paused)
		return self._describeTarget(target, extras, "menuTargetType")

	def beep(self):
		try:
			tones.beep(addonConfig.get("beepPitch"), addonConfig.get("beepDuration"))
		except Exception:  # noqa: BLE001
			log.debugWarning("Beep failed", exc_info=True)

	def noTargetInSlot(self, slotNumber: int):
		# Translators: announced when a number key addresses an empty slot, e.g. "No target in slot 2."
		ui.message(_("No target in slot {slot}.").format(slot=slotNumber))

	def allCleared(self):
		# Translators: announced when the whole target list is cleared at once.
		ui.message(_("All targets cleared."))

	def noTargets(self):
		# Translators: announced when a command needs a target and none is being tracked.
		ui.message(_("No targets."))

	def noTargetsToTrack(self):
		# Translators: announced at start-up or on resuming tracking when the target list is empty.
		self._announce([_("No targets to track.")], unprompted=True, priority=Spri.NORMAL)

	def focusFailed(self):
		# Translators: announced when "Set focus" cannot move the focus to a target (e.g. its window is gone).
		ui.message(_("Could not set focus."))

	def remembered(self):
		# Translators: announced right after "Tracking" when the target was added to be remembered.
		ui.message(_("Target remembered."))

	def alreadyFocused(self):
		# Translators: announced when a second press would move the focus to a target that already has it.
		ui.message(_("This target already has focus."))

	def paused(self):
		# Translators: announced when background content tracking is paused.
		ui.message(_("Tracking paused."))

	def resumed(self):
		# Translators: announced when background content tracking is resumed.
		ui.message(_("Tracking resumed."))
