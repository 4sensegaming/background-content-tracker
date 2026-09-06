# Background Content Tracker: the change-detection and caching engine
# Copyright (C) 2026 Lukáš Hosnedl
# This file is covered by the GNU General Public License, version 2.
# See the file COPYING.txt for more details.

"""The heart of the add-on, and deliberately built from one mechanism only.

Every tracked target is read on a timer, what it now holds is weighed against
what it is known to have held, and only genuinely new content is announced.
There is no event path: NVDA suppresses accessibility events for windows that
are not in the foreground anyway, so events could only ever have been a latency
optimisation, and they were the source of far worse bugs than the ~1 s of
latency they saved.

Two rules keep the behaviour honest:

* A target is never read, let alone announced, while its application is in the
  foreground (:func:`isInForegroundApp`). The add-on reports what you are *not*
  looking at, so the app you are working in is left completely alone.
* Whenever the cache predates a spell that was never read, the next sweep is
  folded into it silently. Nothing that happened while you were sitting in the
  application can therefore be announced at you when you switch away.

Both rules bend for a target whose "Track even foreground targets" is set: it is
read and announced wherever its application is, and since it is never left
unread, there is nothing stale for it to swallow either. Each of these decisions
is taken per target, through :meth:`.TrackedTarget.setting`, so one target can
differ from the global configuration in any setting that has a local equivalent.

A target read in the foreground says nothing about the control the user is
typing in, unless "Ignore focused control" is off for it: every keystroke moves
that control's text, and hearing your own typing back is not news.

Reading a target means sweeping its **whole accessible subtree**
(:func:`_sweepEntries`): one entry per control, carrying that control's own
text. A window, a chat's message list and a lone edit field all go through
exactly the same sweep, so a list is always read as its individual items and a
document as its individual paragraphs, never as one flat blob. The sweep is
bounded by :data:`MAX_NODES`, :data:`MAX_TEXT_CHARS` and :data:`MAX_DEPTH`, and
only runs for backgrounded targets. It costs tens to hundreds of milliseconds
per window, which is why it runs on the monitor's own thread; see
:class:`Monitor`.

What a sweep is weighed against is a **multiset of content**
(``TrackedTarget.seenContent``): every text the target is known to hold, mapped
to how many copies of it are known. New content is then an arithmetic question —
four copies now where three were known means one is new — with no structure in
it at all, which is what makes a control that merely slid down the tree as
content arrived above it impossible to mistake for something new.

The cache remembers rather than mirrors, and that is what makes the add-on
robust where it used to be silently wrong. Copies are only ever taken *away* by
a sweep in a position to testify that they are gone: one that read the target
whole, and found real content while doing so. A sweep truncated at the node
budget has not seen the top of a long chat log, and a sweep of a window whose
accessibility provider has stopped publishing — minimizing a Chromium window is
the reliable way to produce one — has not seen anything at all. Neither is
allowed to take anything away, so neither can adopt its own blindness as the
truth and then read the whole target back as new content afterwards. See
:meth:`Monitor._absorb`.
"""

import re
import threading
import time
from collections import Counter, OrderedDict

import api
import queueHandler
import textInfos
from NVDAObjects import NVDAObjectTextInfo
from logHandler import log

from . import addonConfig
from . import targets as targetsMod
from .targets import isInForegroundApp

#: The progress bar role, resolved defensively so the module still imports where
#: ``controlTypes`` is unavailable (the offline tests) or has changed shape.
try:
	import controlTypes
	_role = getattr(controlTypes, "Role", None)
	if _role is not None:
		_PROGRESSBAR_ROLE = getattr(_role, "PROGRESSBAR", None)
	else:
		_PROGRESSBAR_ROLE = getattr(controlTypes, "ROLE_PROGRESSBAR", None)
except Exception:
	_PROGRESSBAR_ROLE = None

#: The states that mean a control is not actually being shown to anyone: hidden,
#: or scrolled out of view. They are what NVDA's own ProgressBar behaviour
#: refuses to report a bar carrying, and they are worth asking of anything about
#: to be announced. Resolved as defensively as the role above; where they cannot
#: be resolved the set is empty, which turns the check off rather than muting
#: everything.
try:
	_state = getattr(controlTypes, "State", None)
	_HIDDEN_STATES = frozenset(
		value for value in (
			getattr(_state, "INVISIBLE", None),
			getattr(_state, "OFFSCREEN", None),
		) if value is not None
	) if _state is not None else frozenset()
except Exception:
	_HIDDEN_STATES = frozenset()

#: The monitor thread's base tick, in seconds. The configurable tracking
#: interval is rounded up to a whole number of these, so it is also the finest
#: polling resolution and the fastest the add-on will react. A sweep that takes
#: longer than a tick simply stretches the effective interval: the thread sweeps
#: between waits, so slow targets can never pile polls up on top of each other.
POLL_INTERVAL = 1.0
#: Minimum seconds between relocation sweeps for remembered targets.
RELOCATE_INTERVAL = 3.0
#: Ceiling on the wait between attempts at one remembered target that keeps not
#: being found. Only a target whose application is actually running backs off at
#: all (see :meth:`Monitor._deferRelocate`), so this bounds the one search that
#: costs anything — a subtree walk for a control that may never come back —
#: without making a target whose application simply is not running any slower to
#: pick up than the pass itself.
RELOCATE_BACKOFF_MAX = 15.0
#: How many relocation passes the remembered targets restored at start-up are
#: gathered over before they are reported, as a single message. It closes early
#: the moment they are all back, so the wait is only ever paid where the answer
#: would otherwise be wrong: applications are still launching while NVDA starts,
#: and at one pass — a second in — most of them have not opened their windows
#: yet. Four passes is about ten seconds, which is late enough to have the real
#: answer and still be part of starting up.
STARTUP_PASSES = 4
#: A repeatedly-changing control is suppressed only while it keeps changing. Once
#: its template (see :func:`_templateOf`) has gone this many background polls
#: without changing, it is forgotten, so that if it starts moving again — a fresh
#: response, a new countdown — its next change is announced once more. At the
#: default one-second interval this is ~15 s: longer than the brief pauses inside
#: a single busy run, shorter than the gap between separate ones. It counts polls
#: rather than seconds, so it scales with the tracking interval.
FORGET_REPEATED_POLLS = 15
#: Caps on one sweep. MAX_NODES bounds the controls visited per target — a
#: window, a list, a document, all the same budget — and MAX_TEXT_CHARS bounds
#: one control's text. MAX_DEPTH is a guard against a pathological or cyclic
#: tree; MAX_NODES bounds the work on its own.
MAX_NODES = 1000
MAX_TEXT_CHARS = 10000
MAX_DEPTH = 50
#: How much raw text is worth normalising to keep MAX_TEXT_CHARS of it. An
#: object's own text can be a whole document; the slack covers what collapsing
#: the whitespace removes.
_RAW_TEXT_LIMIT = MAX_TEXT_CHARS * 4
#: Caps on one target's content cache. The cache holds every text the target is
#: known to have shown, not only what it shows now, so it has to be allowed to
#: outgrow any one sweep — that is what stops content which scrolled past the
#: node budget from being announced all over again when it comes back into view.
#: It is bounded by count and by weight together, because a single entry may be
#: MAX_TEXT_CHARS long and a count alone would leave the real cost unbounded.
#: Least recently seen is evicted first: the content that drifted out of the
#: target longest ago.
MAX_CACHE_ENTRIES = 100000
MAX_CACHE_CHARS = 20 * 1000 * 1000
#: The character an accessibility API substitutes for an embedded child object.
#: A container's "own text" is often nothing but a row of these.
_OBJECT_REPLACEMENT = u"￼"


def _hasOwnText(obj):
	"""Whether the object exposes real text of its own.

	``NVDAObjectTextInfo`` is NVDA's generic fallback: it only ever reports the
	object's name, value and description. An object still using it (a window, a
	pane, a list) has no text of its own and must be read through its children.
	Checking the class costs nothing, so it keeps the far more expensive
	:func:`_ownText` off every node that could not answer it anyway.
	"""
	try:
		return obj.TextInfo is not NVDAObjectTextInfo
	except Exception:
		return False


def _ownText(obj):
	try:
		return obj.makeTextInfo(textInfos.POSITION_ALL).text or ""
	except Exception:
		return ""


def _labelOf(obj):
	parts = []
	for attr in ("name", "value"):
		try:
			value = getattr(obj, attr)
		except Exception:
			value = None
		if isinstance(value, str) and value and not value.isspace():
			parts.append(value)
	return u" ".join(parts)


#: ``NVDAObject``'s own generic child accessors. A class that has not overridden
#: them answers ``getChild`` by building the whole child list, so fetching a tail
#: one child at a time would be quadratic there; only a class that provides its
#: own (``IAccessible`` and friends, which map straight onto the platform API) is
#: read that way. Resolved defensively so the module still imports offline.
try:
	from NVDAObjects import NVDAObject as _NVDAObject
except Exception:
	_NVDAObject = None
_BASE_GET_CHILD = getattr(_NVDAObject, "getChild", None)
_BASE_CHILD_COUNT = getattr(_NVDAObject, "_get_childCount", None)


def _hasFastChildAccess(obj):
	"""Whether ``obj`` can hand back one child without building all of them."""
	if _BASE_GET_CHILD is None:
		return False
	cls = type(obj)
	return (
		getattr(cls, "getChild", None) is not _BASE_GET_CHILD
		and getattr(cls, "_get_childCount", None) is not _BASE_CHILD_COUNT
	)


def _childrenOf(obj, limit):
	"""At most ``limit`` of ``obj``'s children, and the real child index of the first.

	The children are taken from the END, because that is where the sweep spends
	its budget and where new content appears. ``obj.children`` constructs an
	NVDAObject for every child, so a message list with five thousand rows costs
	five thousand constructions even though the budget can only ever reach the
	last few; where the object offers cheap indexed access the tail is fetched one
	child at a time instead. The returned index says where the tail starts, so
	keys still describe a node's real position in the tree.
	"""
	if limit <= 0:
		return [], 0
	if _hasFastChildAccess(obj):
		try:
			count = int(obj.childCount)
		except Exception:
			count = -1
		if count > limit:
			children = []
			for index in range(count - 1, count - limit - 1, -1):
				try:
					child = obj.getChild(index)
				except Exception:
					child = None
				if child is None:
					break  # the tail is shorter than advertised; keep what we have
				children.append(child)
			if children:
				children.reverse()
				return children, count - len(children)
	try:
		children = list(obj.children or [])
	except Exception:
		return [], 0
	if len(children) > limit:
		return children[-limit:], len(children) - limit
	return children, 0


def _cleanText(text):
	"""Reduce an object's raw text to the words a user could actually read.

	Embedded-object placeholders stand in for child objects rather than for
	anything readable, so they are stripped out; whitespace is normalised so that
	a reflow which changes nothing but line breaks is not mistaken for new
	content. A node left with nothing here contributes no text at all.
	"""
	if not text:
		return ""
	if _OBJECT_REPLACEMENT in text:
		text = text.replace(_OBJECT_REPLACEMENT, u"")
	return u" ".join(text.split())


def _readableText(raw):
	"""``raw`` normalised and capped to :data:`MAX_TEXT_CHARS`, keeping its end.

	The raw string is sliced before it is normalised: an object's own text can be
	a whole document, and rewriting all of it to keep the last thousand characters
	is wasted work. The slack absorbs whatever collapsing the whitespace removes.
	"""
	if not raw:
		return ""
	if len(raw) > _RAW_TEXT_LIMIT:
		raw = raw[-_RAW_TEXT_LIMIT:]
	text = _cleanText(raw)
	return text[-MAX_TEXT_CHARS:] if len(text) > MAX_TEXT_CHARS else text


def _isProgressBar(obj):
	"""Whether the object is a progress bar control.

	Tolerant of a missing role or an unavailable ``controlTypes``: a progress bar
	we cannot recognise is simply read like any other control.
	"""
	if _PROGRESSBAR_ROLE is None:
		return False
	try:
		return obj.role == _PROGRESSBAR_ROLE
	except Exception:
		return False


def _isPresented(obj):
	"""Whether the control is actually being shown, rather than merely present.

	NVDA asks exactly this of a progress bar before it says anything about it —
	``NVDAObjects.behaviors.ProgressBar`` returns at once for a bar that is
	invisible or off screen — and it is worth asking of anything this add-on is
	about to announce. A control that is hidden, collapsed, or scrolled out of
	view has shown the user nothing: its text appearing in a sweep says only that
	it exists, and reporting it turns a panel being uncovered into news.

	Asked only of the handful of nodes a poll actually surfaces, never of a whole
	sweep. It costs a cross-process read per node, and a thousand of those per
	target per poll would cost far more than the noise it saves.

	States that cannot be read answer True. A control the add-on is unable to
	ask must be announced rather than silently dropped: everywhere else being
	wrong costs a little noise, and here it would cost the change the user is
	waiting for.
	"""
	if obj is None or not _HIDDEN_STATES:
		return True
	try:
		states = obj.states
	except Exception:
		return True
	if not states:
		return True
	return not (states & _HIDDEN_STATES)


def _focusObject():
	"""NVDA's focus object, or ``None`` if it cannot be had.

	Safe to read from the monitor thread: this is a plain attribute of NVDA's
	``api`` module, rebound by the main thread and never mutated in place.
	"""
	try:
		return api.getFocusObject()
	except Exception:
		return None


def _sameObject(a, b):
	"""Whether two objects stand for the same control.

	NVDAObject equality is what knows how to answer this across the accessibility
	APIs, but it reaches into the application to do so, and is guarded here like
	every other cross-process call. An object we cannot compare is simply not the
	focus, and is read like any other.
	"""
	if a is None or b is None:
		return False
	try:
		return bool(a == b)
	except Exception:
		return False


def _sweepEntries(root, ignoreProgressBars=False, focusObj=None):
	"""The target's accessible subtree, as ``(entries, whole, focusKey, nodes)``.

	``entries`` is a list of ``(key, text)`` pairs — one per control that has
	anything to say, in document order, with no special case for windows: a
	window, a message list and a lone edit field are all swept the same way, so a
	list always yields its individual items and a document its individual
	paragraphs. ``whole`` says whether the sweep reached the entire subtree or
	stopped short of it at one of the caps below; only a whole sweep is allowed to
	conclude that content it did not find is gone. ``focusKey`` is the key of the
	node that is ``focusObj``, or ``None`` where the sweep never met it.

	``nodes`` maps each entry's key to the control it came from, for the one
	caller that has to ask a control something rather than read its text
	(:func:`_isPresented`). It is deliberately kept out of ``entries``, which is
	content and nothing else: the cache, the dark-sweep test and the change
	detection all work on text alone, and none of them should be handed an object
	they might be tempted to consult.

	**The text of a node.** The children are swept first. If anything below the
	node produced text, the node itself contributes only its *label* (name and
	value): a container is a heading over its children, never a second copy of
	them. Only when the whole subtree came back mute is the node's own text
	interface consulted, falling back to the label. That one rule is what stops a
	document, a rich edit or a UIA window from collapsing into a single flat blob
	spanning everything beneath it — the failure that made any change anywhere
	inside a window surface the entire window — while still rescuing a terminal
	or edit field whose children carry nothing. The *root's* label is skipped when
	it has children, because it is the target's own name, which the notifier
	already speaks; a root with no children is a control pointed straight at, so
	its label is exactly what should be read.

	**The key of a node.** Its path of child indices from the root. Change
	detection does not use it — that works on content alone
	(:meth:`Monitor._collectDelta`) — so it carries no weight there and is free to
	drift when a sibling is inserted above it. It is what tells
	:func:`_joinSurfaced` which surfaced nodes are nested inside which, so that a
	row named after the cells beneath it is not read out twice.

	Bounded by MAX_NODES/MAX_TEXT_CHARS/MAX_DEPTH. The sweep walks children in
	reverse and emits each node after its subtree, then reverses the result: the
	cost and the document order come out identical, but when the node budget runs
	out what survives is the *end* of the target rather than its beginning. Every
	case this add-on exists for — a chat log, a message list, streaming output —
	appends its new content at the end, so a snapshot truncated to the start would
	be a snapshot of the part that never changes.

	When ``ignoreProgressBars`` is set, a progress bar control (and its subtree)
	is skipped entirely, so its constant churn never registers as a change. The
	root itself is never skipped: a target the user pointed straight at is always
	read.

	``focusObj`` is the control the user is typing in, where the caller wants it
	kept quiet. It is swept like any other — naming it is all that happens here,
	and it is :meth:`Monitor._collectDelta` that keeps quiet about what was named,
	so the cache still learns what was typed and never has to announce it later.
	The root is again never named, for the same reason it is never skipped.
	"""
	entries = []
	nodes = {}
	budget = [MAX_NODES]
	#: Cleared as soon as any part of the subtree goes unread — the node budget
	#: ran out, a container was clipped to its tail, or the depth cap stopped the
	#: descent. Such a sweep still reports everything it found, but it cannot
	#: speak for what it never reached, which is why absence is only ever trusted
	#: from a whole one.
	whole = [True]
	#: The key of the focused node, once the sweep has met it. Held in a list for
	#: the same reason as the rest of this state: ``visit`` is a closure.
	focusKey = [None]

	def visit(obj, depth, key, isRoot):
		if budget[0] <= 0:
			whole[0] = False
			return False
		budget[0] -= 1
		if not isRoot and ignoreProgressBars and _isProgressBar(obj):
			return False  # a progress bar NVDA already handles; not our churn to report
		if focusObj is not None and focusKey[0] is None and not isRoot and _sameObject(obj, focusObj):
			focusKey[0] = key
		# Every child costs at least one node, so the remaining budget is exactly
		# how much of a huge container is worth fetching in the first place.
		looked = depth < MAX_DEPTH and budget[0] > 0
		if not looked:
			whole[0] = False
		children, firstIndex = _childrenOf(obj, budget[0]) if looked else ([], 0)
		if firstIndex:
			whole[0] = False  # only the tail of this container was fetched
		gotText = False
		for offset in range(len(children) - 1, -1, -1):
			if budget[0] <= 0:
				whole[0] = False
				break
			childKey = u"%s/%d" % (key, firstIndex + offset)
			if visit(children[offset], depth + 1, childKey, False):
				gotText = True
		text = u""
		# The own-text fallback is only honest when the subtree really came back
		# mute: a childless node always qualifies, and a node with children only if
		# nothing was clipped and the budget survived them. Otherwise "mute" just
		# means "not looked at", and its flat text would be the blob we swept to
		# avoid.
		trustOwnText = looked and (not children or (firstIndex == 0 and budget[0] > 0))
		if not gotText and trustOwnText and _hasOwnText(obj):
			text = _readableText(_ownText(obj))
		if not text and not (isRoot and children):
			text = _readableText(_labelOf(obj))
		if not text:
			return gotText
		entries.append((key, text))
		nodes[key] = obj
		return True

	visit(root, 0, u"", True)
	entries.reverse()
	return entries, whole[0], focusKey[0], nodes


def _isDarkSweep(entries, cache):
	"""Whether a sweep found nothing where the target is known to hold content.

	A collapsed accessible tree still answers: the sweep comes back with the
	target's own name and nothing beneath it, or with nothing at all. A target
	that genuinely holds a single line looks exactly the same, so the cache has
	to be holding more than such a sweep could ever produce before its emptiness
	is read as a failure to report rather than as content.
	"""
	return len(entries) <= 1 < len(cache)


#: A maximal run of digits, optionally with separators *between* digits — the
#: "." of a decimal, the "," or space/NBSP of grouped thousands (Czech writes
#: "1 234"), the ":" of a clock. This is the volatile part of a counter, timer,
#: clock, percentage or byte readout. Nothing here matches a letter, word, app
#: name or language: it recognises *numbers* only, so counters in any language
#: normalise identically.
_NUMBER_RUN = re.compile(u"\d(?:[\d.,:  ]*\d)?")
#: The sentinel a numeric run collapses to. A private-use character, so it can
#: never collide with anything in real content.
_NUMBER_SENTINEL = u""


def _templateOf(text):
	"""``text`` with every numeric run collapsed to a single sentinel.

	This is the stable identity of a repeatedly-changing control. "Thought for 4
	seconds", "Thought for 11 seconds" and "Thought for 2 minutes" all share the
	template "Thought for <n> seconds"/"<n> minutes"; "5.9s" and "6.1s" share
	"<n>s". A literal prefix/suffix could not do this: the moment a digit rolls
	over (9 -> 10, 19 -> 20) it leaks into the framing and mints a false new
	identity, which is exactly why an earlier scheme re-announced timers.

	It is deliberately used instead of the node key for suppression: a ticking
	control slides around the tree as content arrives above it, and its key slides
	with it, whereas its template does not move at all.
	"""
	return _NUMBER_RUN.sub(_NUMBER_SENTINEL, text)


def _joinSurfaced(surfaced):
	"""The announcement text for the ``(key, text)`` pairs judged new.

	Document order, one node per line, with one guard: a node whose text is
	already contained in that of a changed *ancestor* is dropped. Some
	applications name a row after the cells inside it, and hearing the row and
	then every cell would read the same message twice.

	Because the entries arrive in document order, an ancestor always precedes its
	descendants, so the ones a node could be nested in are exactly the ancestor
	chain — a stack, not everything kept so far. Comparing against everything
	would be quadratic, which on a poll where a whole window repainted means half
	a million string comparisons.
	"""
	kept = []
	chain = []
	for key, text in surfaced:
		while chain and not key.startswith(chain[-1][0] + u"/"):
			chain.pop()
		if any(text in ancestorText for _, ancestorText in chain):
			continue  # an ancestor already says this; do not read it twice
		chain.append((key, text))
		kept.append(text)
	return u"\n".join(kept).strip()


class Monitor(object):
	"""Owns the polling thread and the per-target content caches.

	The sweep runs on its own daemon thread, never on NVDA's main thread. Reading
	a window's accessible tree costs tens to hundreds of milliseconds, and doing
	that once a second on the main thread would stall speech, braille and keyboard
	handling. NVDA does exactly this for terminals and live regions
	(``NVDAObjects.behaviors.LiveText``): the text is fetched and diffed on a
	background thread, and only the announcement is handed back to the main one.

	Three rules keep that safe:

	* Nothing on this thread speaks, beeps, touches wx, or mutates the registry.
	  All of it is queued onto the main thread by :meth:`_callOnMainThread`.
	* NVDA's configuration is never read here. :func:`addonConfig.snapshot`
	  provides a plain dict instead.
	* :meth:`stop` never joins the thread. An application that has hung can block
	  a cross-process call for as long as the RPC layer allows, and NVDA must
	  still be able to exit. The thread is a daemon and checks the stop event
	  between targets.
	"""

	def __init__(self, registry, notifier):
		self.registry = registry
		self.notifier = notifier
		self._thread = None
		self._stop = threading.Event()
		self._lastRelocate = 0.0
		#: Whether the remembered targets restored at start-up have been reported.
		#: Until they have, an attaching target is folded into that one message
		#: instead of announcing itself; afterwards each announces as it appears.
		self._startupDone = False
		#: Relocation passes the restoration has had so far, how many targets it
		#: was looking for, and how many of them it has found. Monitor thread only.
		self._startupPasses = 0
		self._startupTotal = 0
		self._startupFound = 0

	# --- lifecycle -----------------------------------------------------------
	def start(self):
		if self._thread is not None:
			return
		self._stop.clear()
		self._thread = threading.Thread(
			name="BackgroundContentTracker._monitorThread",
			target=self._run,
			daemon=True,
		)
		self._thread.start()

	def stop(self):
		# Deliberately not joined; see the class docstring.
		self._stop.set()
		self._thread = None

	def _callOnMainThread(self, func, *args, **kwargs):
		"""Hand work back to NVDA's main thread.

		Everything that speaks, beeps or mutates the registry goes through here.
		``immediate=True`` places the call at the front of the event queue, as
		NVDA's own LiveText does when it reports newly appeared text. It is for
		the two things the user is waiting on — a change as it happens, and the
		outcome of a keypress — and for nothing else: a message that jumps the
		queue jumps it past NVDA's own pending events, which is precisely wrong
		for the housekeeping the monitor does on its own initiative while NVDA is
		still starting up.
		"""
		if self._stop.is_set():
			return
		immediate = kwargs.pop("immediate", False)
		queueHandler.queueFunction(
			queueHandler.eventQueue, func, *args, _immediate=immediate, **kwargs
		)

	def onAdded(self, target):
		obj = target.obj
		settings = addonConfig.snapshot()
		target.lastChangeTime = None
		target.announcedRun = 0
		target.announcedControls = {}
		target.pollTick = 0
		target.seenContent = OrderedDict()
		target.seenChars = 0
		target.prevTexts = frozenset()
		target.wasInForeground = isInForegroundApp(obj)
		# The title a whole-window target is held to, so that a window which later
		# renames itself can be told from the one that was actually added.
		target.captureTrackedTitle(settings)
		# Only take a baseline now if the target is already in the background.
		# Otherwise it is left to the first poll that actually reads the target:
		# when the user switches away from it, or on the very next poll if it is
		# tracked in the foreground as well. Either way, the sweep of the
		# application the user is working in stays off the main thread, which is
		# where this runs.
		if target.wasInForeground:
			target.staleCache = True
			return
		ignorePB = bool(target.setting("ignoreProgressBars", settings)) and target.kind == "window"
		# No focus to keep quiet about: this runs only for a target that is already
		# in the background, and the focus is always in the foreground application.
		entries, whole, _focusKey, _nodes = _sweepEntries(obj, ignorePB)
		self._absorb(target, entries, whole, False)
		target.prevTexts = frozenset(text for _, text in entries)
		target.staleCache = False

	# --- polling -------------------------------------------------------------
	def _run(self):
		"""The monitor thread's loop.

		The thread wakes on a fixed POLL_INTERVAL tick, but only actually sweeps
		once the configured *tracking interval* has elapsed. An interval of 0 is a
		special "detection only" mode: it still sweeps on every tick so the target
		menu stays current, but the sweep announces nothing.

		Elapsed time is measured, not counted in ticks. A sweep of a large window
		can take longer than a tick, and charging it a flat POLL_INTERVAL would
		make a five-second interval mean twenty seconds of wall clock. The interval
		is a floor, never a promise, but it should at least mean what it says.

		Waiting on the stop event rather than sleeping means :meth:`stop` takes
		effect at once instead of after the rest of a tick.
		"""
		sinceLast = 0.0
		lastTick = time.monotonic()
		while not self._stop.wait(POLL_INTERVAL):
			try:
				now = time.monotonic()
				elapsed = now - lastTick
				lastTick = now
				settings = addonConfig.snapshot()
				if not settings["enabled"]:
					continue
				interval = settings["trackingInterval"]
				announce = interval != 0
				effective = POLL_INTERVAL if interval <= 0 else max(interval, POLL_INTERVAL)
				sinceLast += elapsed
				if sinceLast + 1e-6 < effective:
					continue
				sinceLast = 0.0
				self._checkAllTargets(settings, announce)
			except Exception:
				log.error("Error in Background Content Tracker poll", exc_info=True)

	def _checkAllTargets(self, settings, announce=True):
		attached = ()
		remembered = [
			target for target in self.registry.detachedTargets()
			if target.setting("rememberTargets", settings)
		]
		if remembered:
			now = time.time()
			if now - self._lastRelocate >= RELOCATE_INTERVAL:
				self._lastRelocate = now
				attached = frozenset(self._relocatePass(remembered, settings, now))
				if not self._startupDone:
					self._noteStartupPass(len(remembered), len(attached))
		elif not self._startupDone:
			# Nothing is left to look for. Either the restoration has found
			# everything it was going to, and should say so now rather than wait
			# out passes with nothing to do, or nothing was remembered in the first
			# place and there is no restoration to report at all. Either way, the
			# targets that attach from here on speak for themselves again.
			if self._startupPasses:
				self._finishStartup()
			else:
				self._startupDone = True
		for target in self.registry.liveTargets():
			if self._stop.is_set():
				return
			if target in attached:
				# Attached moments ago, in this very poll: ``onAdded`` has just
				# swept it for its baseline, and sweeping it again here would only
				# diff it against a cache milliseconds old — at the price of a
				# second full sweep, and of announcing whatever happened to land in
				# between as though it were news.
				continue
			if not target.isAlive() or not self._keptItsTitle(target, target.obj, settings):
				self._handleDisappeared(target, target.setting("forgetOnDisappear", settings))
				continue
			self._checkTargetContent(target, settings, announce)

	# --- the one message the start-up restoration makes ---------------------
	def _noteStartupPass(self, pending, found):
		"""Fold one relocation pass into the report the restoration will make.

		Ten remembered targets used to mean ten "Tracking …" announcements in a
		quick loop, on top of NVDA's own start-up speech, and — decided on the
		strength of a single pass one second in — a "No targets to track" that the
		next few seconds routinely contradicted. So the passes that make up the
		restoration are counted here instead, and report themselves once.

		The window closes as soon as every remembered target is back, so the
		common case of everything already being open is still reported at once.
		"""
		if not self._startupPasses:
			self._startupTotal = pending
		self._startupPasses += 1
		self._startupFound += found
		if self._startupFound >= self._startupTotal or self._startupPasses >= STARTUP_PASSES:
			self._finishStartup()

	def _finishStartup(self):
		"""Report what the restoration found, and let later targets speak for themselves."""
		self._startupDone = True
		self._callOnMainThread(
			self.notifier.announceRestored, self._startupFound, self._startupTotal
		)

	def _checkTargetContent(self, target, settings=None, announce=True):
		if settings is None:
			settings = addonConfig.snapshot()
		obj = target.obj
		if obj is None:
			return
		isWindow = target.kind == "window"
		ignorePB = bool(target.setting("ignoreProgressBars", settings)) and isWindow
		inForeground = isInForegroundApp(obj)
		if inForeground != target.wasInForeground:
			# The user has just arrived at this target, or just left it; either
			# way they have been at it, so both suppression counters start afresh.
			# The "changes at once" cap and the repeatedly-changing-controls
			# memory are there to hold back a target nobody has looked at. This
			# turns on the foreground state alone, so it still happens for a
			# target that is read right through the visit instead of being
			# skipped, which is the only reset such a target ever gets.
			target.announcedRun = 0
			target.announcedControls = {}
		target.wasInForeground = inForeground
		if inForeground and not target.setting("trackForegroundTargets", settings):
			# The user is in this application. Nothing would be announced, so do
			# not even read it: the app being worked in is left entirely alone.
			# Whatever happens while we are not looking leaves the cache stale.
			target.staleCache = True
			return
		# The focused control is only worth naming while the user is actually in
		# this application; anywhere else the focus is in another one, and no node
		# of this target could be it.
		focusObj = (
			_focusObject()
			if inForeground and isWindow and target.setting("ignoreFocusedControl", settings)
			else None
		)
		entries, whole, focusKey, nodes = _sweepEntries(obj, ignorePB, focusObj)
		dark = _isDarkSweep(entries, target.seenContent)
		if target.staleCache:
			# The cache predates a spell that was never read: the user was in the
			# application, or the target was added while they were there. Fold the
			# sweep in silently, so that nothing which happened while nobody was
			# looking is announced at them now.
			target.staleCache = False
			self._absorb(target, entries, whole, dark)
			target.prevTexts = frozenset(text for _, text in entries)
			return
		# A poll that counts. Advance the target's poll clock even when
		# nothing changed, so the "how long has this control been quiet" measure
		# that ages out repeatedly-changing controls keeps ticking while the
		# window is idle, not only when something moves.
		target.pollTick += 1
		delta = self._collectDelta(target, entries, nodes, isWindow, settings, focusKey)
		self._absorb(target, entries, whole, dark)
		target.prevTexts = frozenset(text for _, text in entries)
		if not delta:
			return
		target.lastDelta = delta
		target.lastChangeTime = time.time()
		if not announce:
			return  # tracking interval 0: the menu is updated, nothing is spoken
		cap = settings["changesAtOnce"]
		if cap and target.announcedRun >= cap:
			return  # reached the consecutive-announcement cap; wait for a refocus
		target.announcedRun += 1
		self._callOnMainThread(self.notifier.announceChange, target, delta, immediate=True)

	def _collectDelta(self, target, entries, nodes, isWindow, settings, focusKey=None):
		"""The new content worth surfacing since the last poll.

		The cache is a multiset: every text the target is known to hold, mapped to
		how many copies of it are known. What this asks of a sweep is therefore
		arithmetic rather than structural — the target now shows this text four
		times and three were known, so one copy is new — and it needs no notion of
		where in the tree anything sits. A control that merely slid down as content
		arrived above it carries text the cache already holds, so it cannot be
		mistaken for new content; telling that apart used to take a two-pass
		comparison of structural keys, and is now not a case that can arise.

		New copies are surfaced from the END of the sweep, because appended content
		is what this add-on exists for: where a text really is repeated, the new
		copies are the latest arrivals, not the oldest survivors.

		When "Ignore repeatedly changing controls" is on for a window, a control
		that *replaced itself* — a different text sharing its template
		(:func:`_templateOf`) was in the previous sweep and is gone from this one —
		is announced once and its template remembered, so its later ticks are
		dropped. Replacement is exactly what a ticking timer does and an appending
		log does not: a log's earlier lines are all still there, so it can never
		mute itself. The template stays live while the control keeps changing and
		is forgotten once it has been quiet for :data:`FORGET_REPEATED_POLLS`
		polls, so a control that goes quiet and later resumes is announced afresh.

		Whatever survives all of that is finally held to being on screen at all
		(:func:`_isPresented`), which is asked here, of the few nodes about to be
		announced, rather than of every node of the sweep. Content that is hidden,
		collapsed or scrolled out of view is still absorbed into the cache like any
		other, so uncovering it later cannot turn it into news either.

		When "Ignore focused control" is on for a window, ``focusKey`` names the
		control the user is typing in, and it and everything inside it are dropped
		from what is surfaced. They are still absorbed into the cache, which is the
		whole point of dropping them here rather than skipping them in the sweep:
		what was typed is known to have been there, so moving the focus away later
		cannot turn it into new content and read it all back.

		What is surfaced is always the node's whole current text, never a
		character-level diff: a bare fragment of added characters is meaningless
		read aloud, so the listener always hears the complete line or message.
		"""
		cache = target.seenContent
		counts = Counter(text for _, text in entries)
		outstanding = {}
		for text, seen in counts.items():
			known = cache.get(text, 0)
			if seen > known:
				outstanding[text] = seen - known
		if not outstanding:
			return u""
		# The last copies of a repeated text are the new ones, so the pick runs
		# backwards and the result is turned back into document order.
		picked = []
		for key, text in reversed(entries):
			left = outstanding.get(text)
			if left:
				outstanding[text] = left - 1
				picked.append((key, text))
		picked.reverse()
		if focusKey is not None:
			prefix = focusKey + u"/"
			picked = [
				(key, text) for key, text in picked
				if key != focusKey and not key.startswith(prefix)
			]
			if not picked:
				return u""
		picked = [(key, text) for key, text in picked if _isPresented(nodes.get(key))]
		if not picked:
			return u""
		if not (isWindow and target.setting("ignoreRepeatedControls", settings)):
			return _joinSurfaced(picked)

		announced = target.announcedControls
		currentTick = target.pollTick
		if announced:
			# Forget controls that have gone quiet: a template not seen changing
			# for FORGET_REPEATED_POLLS polls is no longer treated as a timer, so
			# its next change is announced again.
			stale = [tpl for tpl, tick in announced.items()
			         if currentTick - tick > FORGET_REPEATED_POLLS]
			for tpl in stale:
				del announced[tpl]
		# The templates this sweep lost. A surfaced text whose template is in here
		# took something's place, which is a control changing rather than content
		# arriving. Nothing surfaced can itself have vanished, so a text is never
		# judged a replacement for itself.
		vanished = set()
		for text in target.prevTexts:
			if text not in counts:
				vanished.add(_templateOf(text))

		surfaced = []
		for key, text in picked:
			template = _templateOf(text)
			if template in announced:
				announced[template] = currentTick  # still churning; keep it live
				continue  # this control was already announced; do not repeat it
			if template in vanished:
				# A control replacing itself: announce it now, mute its ticks.
				announced[template] = currentTick
			surfaced.append((key, text))
		return _joinSurfaced(surfaced)

	def _absorb(self, target, entries, whole, dark):
		"""Fold a sweep into the target's content cache.

		Counts only ever rise, except where the sweep is in a position to testify
		that something has gone: a text missing from a sweep that read the target
		*whole* really is missing, and its count comes down — to zero, which drops
		it — so that content which returns later is announced again. Two kinds of
		sweep are not in that position, and neither is allowed to take anything
		away:

		* A **truncated** sweep (``whole`` false) stopped at the node budget or the
		  depth cap, so part of the target was never looked at. This is the
		  ordinary case for a long chat log, and it is what lets the cache outgrow
		  any one sweep: content that scrolled past the budget stays known, and is
		  not announced all over again if it later comes back into view.
		* A **dark** sweep found nothing where the cache holds real content. A
		  window whose accessibility provider has stopped publishing — minimizing a
		  Chromium window is the reliable way to see this — still answers, and
		  answers "empty". Believing it would adopt that emptiness as the truth and
		  then read the whole window back as new content the moment it returned.

		Neither case needs a state of its own, an announcement or a recovery path:
		a sweep that cannot testify simply changes nothing, and the next one that
		can carries on from where the last one left off.
		"""
		cache = target.seenContent
		counts = Counter(text for _, text in entries)
		trustAbsence = whole and not dark
		if trustAbsence:
			for gone in [text for text in cache if text not in counts]:
				target.seenChars -= len(gone)
				del cache[gone]
		for text, seen in counts.items():
			known = cache.get(text)
			if known is None:
				cache[text] = seen
				target.seenChars += len(text)
				continue
			if seen > known or trustAbsence:
				cache[text] = seen
			# The cache is ordered least-recently-seen first, so refreshing
			# everything the target still holds leaves the front of it as what
			# drifted out long ago — exactly what should go when the caps bite.
			cache.move_to_end(text)
		while cache and (len(cache) > MAX_CACHE_ENTRIES or target.seenChars > MAX_CACHE_CHARS):
			evicted, _count = cache.popitem(last=False)
			target.seenChars -= len(evicted)

	def _keptItsTitle(self, target, obj, settings):
		"""Whether ``obj`` still carries the title ``target`` was added with.

		The test behind "Consider changed title a disappeared target": a window
		that renames itself is a *different* window as far as the user is
		concerned — a browser window showing another page, an editor holding
		another document — even though the system still calls it the same one.
		A negative answer therefore takes the target down the disappearance path
		(so the list is managed exactly as for a window that closed) rather than
		announcing the new title's content as a change.

		Always true where the option cannot apply: for a target that is not held to
		a title at all (anything that is not a whole window, and any window while
		the option is off), and for a window added before the option was switched
		on globally, which has no remembered title to be held to.
		"""
		if not target.isHeldToItsTitle(settings):
			return True
		if target.trackedTitle is None:
			return True
		return targetsMod.titleOf(obj) == target.trackedTitle

	def _handleDisappeared(self, target, forget):
		target.obj = None
		# The user is always told a target is gone, however the list is managed.
		# With "Forget targets when they disappear" on, the entry is also dropped
		# from the list so old entries do not accumulate; with it off, the entry is
		# kept as a detached target that may re-attach when it reappears (see the
		# relocation pass above, which runs while "Remember targets" is on).
		if forget:
			self._callOnMainThread(self.registry.remove, target)
		self._callOnMainThread(self.notifier.announceStopped, target)

	# --- relocation of remembered / stale targets ---------------------------
	def relocate(self, target):
		"""Re-resolve ``target.obj`` from its identity against the live desktop.

		A cached control object goes stale when its application reshapes the
		accessibility tree — routine in Electron/Chromium apps, where a control
		keeps its name and role but its old node is discarded as content appears
		around it — and focusing a stale reference silently does nothing. Returns
		``True`` and refreshes ``target.obj`` (and its identity) when a live match
		is found, or ``False`` when nothing matches, so the caller can treat the
		target as gone rather than chase a stale location. Unlike the periodic
		relocation below it neither re-baselines nor announces: it is a lookup.
		"""
		obj = self._locate(target.identity, target.kind)
		if obj is None:
			return False
		target.obj = obj
		newIdentity = targetsMod.objectIdentity(obj)
		if newIdentity:
			target.identity = newIdentity
		return True

	def relocateAsync(self, target, callback):
		"""Run :meth:`relocate` off the main thread and hand the outcome back.

		The lookup scans every top-level window and then descends the matching
		application, which is hundreds of cross-process reads: run inline it would
		stall speech, braille and keyboard handling for exactly as long, and it is
		triggered by a keypress, which is the worst possible moment. The scan
		therefore runs on a short-lived daemon thread and only its result —
		``callback(target, found)`` — is queued onto NVDA's main thread.
		"""
		def run():
			try:
				found = self.relocate(target)
			except Exception:
				log.debugWarning("Could not relocate target", exc_info=True)
				found = False
			# The user pressed a key and is waiting on this one.
			self._callOnMainThread(callback, target, found, immediate=True)
		threading.Thread(
			name="BackgroundContentTracker._relocateThread",
			target=run,
			daemon=True,
		).start()

	def _relocatePass(self, targets, settings, now):
		"""Look for every detached target that is due, over one view of the desktop.

		The desktop is enumerated once for the whole pass rather than once per
		target: the list of top-level windows and their application names is the
		same for all of them, and re-reading it ten times over — every three
		seconds, for as long as NVDA runs — is ten times the cross-process traffic
		for one answer.

		Returns the targets it attached, which the caller skips when it sweeps the
		live targets: :meth:`_attach` has just baselined each of them.
		"""
		due = [target for target in targets if target.nextRelocate <= now]
		if not due:
			return []
		windows = self._desktopWindows()
		if not windows:
			return []
		attached = []
		for target in due:
			if self._stop.is_set():
				# NVDA is going down. Relocation is the one thing here that can run
				# long — a hung application can hold a cross-process read for as
				# long as the RPC layer allows — so it checks between targets just
				# as the content sweep does.
				break
			candidates = self._candidateWindows(windows, target.identity)
			obj = self._locateAmong(candidates, target.identity, target.kind)
			if obj is not None and not self._keptItsTitle(target, obj, settings):
				# A window this target was taken down from because it renamed
				# itself. The identity match can reach it through a stable
				# automation id alone, so without this it would be re-attached (and
				# its title re-cached) on the very next relocation pass, which is
				# the opposite of what the option asks for. It re-attaches when the
				# old title comes back.
				obj = None
			if obj is None:
				# Never back off during the start-up restoration: its passes are
				# the ones where an application is most likely to be halfway
				# through starting, and there are only a handful of them.
				self._deferRelocate(target, now, bool(candidates) and self._startupDone)
				continue
			# During the start-up restoration the targets are reported together,
			# so an attaching one does not speak for itself; afterwards it does.
			self._attach(target, obj, announce=self._startupDone)
			attached.append(target)
		return attached

	def _deferRelocate(self, target, now, searched):
		"""Put off the next attempt at ``target``, backing off if this one cost anything.

		A target whose application is not running is ruled out by the shared
		window list before a single cross-process read, so it is retried at the
		pass interval for as long as it takes and is picked up within one pass of
		its application appearing. Backing off is for the target that really was
		searched for — its application is running, but the control is not there —
		because that is the search that walks a subtree per pass, and repeating it
		every three seconds for a control that may never come back is the one case
		worth slowing down. Either way the wait is dropped the moment the target
		attaches (see :meth:`_attach`).
		"""
		if searched:
			target.relocateDelay = min(
				max(target.relocateDelay * 2, RELOCATE_INTERVAL), RELOCATE_BACKOFF_MAX
			)
		else:
			target.relocateDelay = 0.0
		target.nextRelocate = now + target.relocateDelay

	def _desktopWindows(self):
		"""Every top-level window as ``(application name, object)``, or ``[]``.

		The application name is read here, once per window per pass, because it is
		what rules a window out for every target that does not want that
		application: one read against the six a full identity descriptor costs,
		and shared by the whole pass instead of taken again for each target.
		"""
		try:
			topWindows = list(api.getDesktopObject().children)
		except Exception:
			return []
		return [(targetsMod.appNameOf(window), window) for window in topWindows]

	def _candidateWindows(self, windows, identity):
		"""The top-level windows from ``windows`` worth examining for ``identity``.

		Empty when the wanted application is not running at all, which is both the
		commonest case for a remembered target and the cheapest: it is settled by
		names already in hand, with nothing read from anywhere.
		"""
		if not identity:
			return []
		wantedApp = identity.get("appName")
		return [
			window for appName, window in windows
			if not wantedApp or appName == wantedApp
		]

	def _locateAmong(self, candidates, identity, kind=None):
		"""The object matching ``identity`` among ``candidates`` or below them.

		Every candidate is compared as a whole window first, and only then are
		they descended. A window target stops after the first phase: what it names
		is a top-level window, so walking a hundred and fifty nodes underneath each
		one — every pass, forever — could never find it. For a control target the
		phases also settle a tie the right way round: an exact match on a window
		beats a descendant match under an earlier one.
		"""
		for window in candidates:
			if targetsMod.identitiesMatch(identity, targetsMod.objectIdentity(window)):
				return window
		if kind == "window":
			return None
		for window in candidates:
			match = self._findMatchingDescendant(window, identity)
			if match is not None:
				return match
		return None

	def _locate(self, identity, kind=None):
		"""The live NVDAObject whose identity matches ``identity``, or ``None``.

		Enumerates the desktop for this one lookup; a relocation pass shares one
		enumeration across its targets instead (see :meth:`_relocatePass`).
		"""
		if not identity:
			return None
		windows = self._desktopWindows()
		return self._locateAmong(self._candidateWindows(windows, identity), identity, kind)

	def _findMatchingDescendant(self, root, identity, maxNodes=150):
		# Cheap pre-filter: with no automation id, identitiesMatch can only succeed
		# when the roles are equal, so a single role read rules a node out for one
		# cross-process access instead of the six a full identity descriptor costs.
		# With an automation id, role is ignored by the match, so we must not skip.
		roleFilter = None
		if not identity.get("automationID"):
			roleFilter = identity.get("role")
		queue = [root]
		examined = 0
		while queue and examined < maxNodes:
			node = queue.pop(0)
			examined += 1
			skip = False
			if roleFilter is not None:
				try:
					role = int(node.role)
				except Exception:
					role = None
				skip = role is not None and role != roleFilter
			if not skip:
				try:
					if targetsMod.identitiesMatch(identity, targetsMod.objectIdentity(node)):
						return node
				except Exception:
					pass
			try:
				children = node.children
			except Exception:
				children = None
			if children:
				queue.extend(children)
		return None

	def _attach(self, target, obj, announce=True):
		"""Take up a target that has been found again, and baseline it.

		``announce`` is false only for the targets restored at start-up, which are
		reported together rather than one by one (see :meth:`_noteStartupPass`).
		"""
		target.obj = obj
		newIdentity = targetsMod.objectIdentity(obj)
		if newIdentity:
			target.identity = newIdentity
		# It is here now, so any wait accumulated while it was not has done its
		# job: should it disappear again, it is looked for at the pass interval.
		target.relocateDelay = 0.0
		target.nextRelocate = 0.0
		self.onAdded(target)
		if announce:
			self._callOnMainThread(self.notifier.announceTracking, target)
