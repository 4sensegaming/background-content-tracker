# Background Content Tracker: spoken and beeped notifications
# Copyright (C) 2026 Lukáš Hosnedl
# This file is covered by the GNU General Public License, version 2.
# See the file COPYING.txt for more details.

"""Everything the user hears. All wording here is translatable; control-type
(role) names are taken from NVDA itself and are therefore already localised.

The messages here are of two kinds. One answers a keypress, and is spoken as it
stands. The other the add-on raises on its own account — the start-up report of
what was remembered, and a target found or lost while the user is doing
something else — and arrives in the middle of NVDA's own speech, at a moment
nobody chose. :meth:`Notifier._announce` is where that second kind is fitted
around NVDA, and every method below says which kind its message is.
"""

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
	# NVDA puts the translation lookups into this module's namespace at run time,
	# which a type checker reading the source has no way of knowing. This says what
	# they will be; nothing is imported when the add-on is actually running, which
	# is what the suppression below records.
	from gettext import gettext as _  # noqa: TC004
	from gettext import ngettext  # noqa: TC004

addonHandler.initTranslation()

#: How long a message the add-on raised itself is held back before it is spoken,
#: in milliseconds. Long enough for a window arriving at or leaving the front to
#: have been dealt with, short enough that the message still belongs to it.
_UNPROMPTED_DELAY_MS = 400

#: How many tracking intervals a change announcement goes on following the
#: previous one about the same target, without naming the target again.
_SAME_TARGET_INTERVALS = 5

#: The trailing pieces that go after a target's name in a description. A piece
#: that came to nothing is passed as it was worked out and dropped here, so
#: that a caller never has to decide whether it has anything to add.
Extras = Sequence[str | None]


def _describe(roleText: str, name: str, includeType: bool, extras: Extras) -> str:
	"""Build a target description such as "window: Claude, 3 minutes ago".

	``extras`` is a list of already-formatted trailing pieces (time, content);
	empty pieces are dropped.
	"""
	if includeType and roleText:
		base = f"{roleText}: {name}" if name else roleText
	else:
		base = name or roleText
	parts = [base] if base else []
	parts.extend([piece for piece in extras if piece])
	return ", ".join(parts)


def _notFound() -> str:
	"""The trailing piece describing a target that is not there.

	A function rather than a constant so that it is translated when it is used,
	not once when this module is imported.
	"""
	# Translators: shown in the target menu, and spoken on demand, for a target
	# that does not currently exist (e.g. a remembered target not yet reopened).
	return _("not found")


def relativeTime(when: float | None) -> str:
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


class Notifier:
	"""Turns registry/monitor events into speech and beeps, per the settings."""

	def __init__(self):
		#: The target the last change announcement was about, as its uid, and
		#: ``time.monotonic()`` of that announcement; ``None`` before the first.
		self._lastChange: tuple[int, float] | None = None

	def _announce(self, text: str, unprompted: bool, priority: Spri):
		"""Say ``text``, kept out of NVDA's way where the add-on raised it itself.

		A message answering a keypress is spoken as it stands: the keypress has
		just stopped whatever NVDA was saying, so there is nothing to fit around
		and nothing to wait for.

		One the add-on raised on its own account arrives while NVDA is busy with
		something the user did ask for, and ``priority`` says how it should sit
		with that — waiting for NVDA to finish, or being let in at the end of the
		current sentence, after which NVDA carries on where it left off. Those are
		the two settings NVDA gives a web page's polite and assertive live
		regions, and they behave here exactly as they do there.

		The wait in front of both is for something else. What most often puts a
		target in or out of reach is a window arriving at or leaving the front,
		and NVDA answers a window coming to the front by throwing away everything
		it has queued to be spoken, whatever priority it carries. A message raised
		in the moment before that is not outranked but discarded: it reaches the
		log and the speech viewer, and is never heard. Waiting lets the change of
		window go by first, so the message is queued behind what NVDA says about
		it instead of into what is about to be dropped.
		"""
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
		"""``target`` described for the user, per the settings that shape it.

		Every message this class produces is the same three questions — what the
		target is called, whether its control type belongs in front of that, and
		what trailing pieces go after it — so they are asked in one place. Which
		setting decides the control type is the only thing that varies: the spoken
		messages follow "Target type", the target menu follows its own.
		"""
		return _describe(target.roleText(), target.name, bool(addonConfig.get(typeSetting)), extras)

	def announceTracking(self, target: TrackedTarget, unprompted: bool = False):
		desc = self._describeTarget(target)
		# Translators: announced when tracking starts, e.g. "Tracking window: Claude".
		text = _("Tracking {target}").format(target=desc)
		self._announce(text, unprompted, Spri.NEXT)

	def announceRestored(self, found: int, total: int):
		"""Report the remembered targets restored at start-up, in one message.

		They are counted rather than named: ten of them named one after another,
		over NVDA's own start-up speech, is a recital of things the user already
		knows they asked to be remembered. What is worth hearing is whether they
		are all back, and the numbers say that in a breath. Any that turn up later
		announce themselves as usual.
		"""
		if not found:
			self.noTargets(unprompted=True)
			return
		if found >= total:
			# Translators: announced at start-up when every remembered target has been
			# found. {n} is how many there are.
			text = ngettext("Found {n} remembered target", "Found {n} remembered targets", found)
			self._announce(text.format(n=found), unprompted=True, priority=Spri.NORMAL)
			return
		# Translators: announced at start-up when only some of the remembered targets
		# have been found; the rest are still being looked for. {found} is how many
		# are being tracked, {total} how many there are.
		text = _("Found {found} of {total} remembered targets")
		self._announce(text.format(found=found, total=total), unprompted=True, priority=Spri.NORMAL)

	def announceStopped(self, target: TrackedTarget, unprompted: bool = False):
		desc = self._describeTarget(target)
		# Translators: announced when tracking stops, e.g. "Stopped tracking listbox: Message list".
		text = _("Stopped tracking {target}").format(target=desc)
		self._announce(text, unprompted, Spri.NEXT)

	def announceChange(self, target: TrackedTarget, delta: str):
		"""A change was detected in ``target``; ``delta`` is the new content.

		The target is not named when the previous change announcement was about
		this same target and came less than :data:`_SAME_TARGET_INTERVALS`
		tracking intervals ago: nothing else has been heard in between, so the
		content can only belong to the target that was just named. Every change so
		announced starts the count again, so a steady run of them stays unnamed for
		as long as it lasts. Where the content is not announced the name is all
		there is to say, and is said every time.

		With "Interrupt previous speech when announcing a change" in force for the
		target, whatever NVDA is saying is cancelled first, rather than having the
		announcement wait its turn behind it.
		"""
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
			ui.message(self._describeTarget(target, [_notFound()]))
			return
		if not target.hasReportableChange():
			# Translators: on-demand target info when there is nothing new to report.
			ui.message(self._describeTarget(target, [_("no changes yet")]))
			return
		content = target.lastDelta if addonConfig.get("announceChangedContent") else None
		desc = self._describeTarget(target, [content])
		if desc:
			ui.message(desc)

	def menuDescription(self, target: TrackedTarget) -> str:
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
		# A tone that could not be played is not worth an error, and there is
		# nothing to be done about it beyond saying nothing.
		except Exception:  # noqa: BLE001
			log.debugWarning("Beep failed", exc_info=True)

	def noTargetInSlot(self, slotNumber: int):
		# Translators: announced when a number key addresses an empty slot, e.g. "No target in slot 2".
		ui.message(_("No target in slot {slot}").format(slot=slotNumber))

	def allCleared(self):
		# Translators: announced when the whole target list is cleared at once.
		ui.message(_("All targets cleared"))

	def noTargets(self, unprompted: bool = False):
		# Translators: announced (on resume and at start-up) when there are no valid targets.
		text = _("No remembered targets found")
		self._announce(text, unprompted, Spri.NORMAL)

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
