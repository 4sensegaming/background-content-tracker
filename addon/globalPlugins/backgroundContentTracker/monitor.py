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

A target read in the foreground says nothing about what the user is typing,
unless "Ignore focused control" is off for it: every keystroke moves that text,
and hearing your own typing back is not news. Whatever is part of the value of
NVDA's focus object, or of any control nested in it — alone, or with the
control's name in front, and whatever punctuation stands between the words — is
kept quiet wherever in the window it turns up.

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
from collections import Counter, OrderedDict, deque
from collections.abc import Callable, Mapping, Sequence
from typing import Any

import api
import queueHandler
import textInfos
from controlTypes import Role, State
from editableText import EditableText
from logHandler import log
from NVDAObjects import NVDAObject, NVDAObjectTextInfo

from . import addonConfig
from . import targets as targetsMod
from .addonConfig import Settings
from .notifier import Notifier
from .targets import Identity, TargetRegistry, TrackedTarget, isInForegroundApp, onThisThread, safeCall

#: One control's contribution to a sweep: the key naming where in the tree it
#: sits, and the text it holds. The key is for nesting alone; every question
#: asked of a sweep's content is asked of the text.
Entry = tuple[str, str]

#: The states that mean a control is not actually being shown to anyone: hidden,
#: or scrolled out of view. They are what NVDA's own ProgressBar behaviour
#: refuses to report a bar carrying, and they are worth asking of anything about
#: to be announced.
_HIDDEN_STATES = frozenset((State.INVISIBLE, State.OFFSCREEN))

#: The monitor thread's base tick, in seconds. Every tick looks for the
#: remembered targets that are not attached, and the configurable tracking
#: interval is rounded up to a whole number of ticks, so this is also the finest
#: polling resolution and the fastest the add-on will react. A sweep that takes
#: longer than a tick simply stretches the effective interval: the thread sweeps
#: between waits, so slow targets can never pile polls up on top of each other.
POLL_INTERVAL = 1.0
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
_OBJECT_REPLACEMENT = "￼"


def _hasOwnText(obj: NVDAObject) -> bool:
	"""Whether the object exposes real text of its own.

	``NVDAObjectTextInfo`` is NVDA's generic fallback: it only ever reports the
	object's name, value and description. An object still using it (a window, a
	pane, a list) has no text of its own and must be read through its children.
	Checking the class costs nothing, so it keeps the far more expensive
	:func:`_ownText` off every node that could not answer it anyway.
	"""
	return safeCall(lambda: obj.TextInfo is not NVDAObjectTextInfo, False) is True


def _ownText(obj: NVDAObject) -> str:
	return safeCall(lambda: obj.makeTextInfo(textInfos.POSITION_ALL).text, "") or ""


def _labelOf(obj: NVDAObject, withValue: bool = True) -> str:
	return _joinLabel(safeCall(lambda: obj.name), safeCall(lambda: obj.value) if withValue else None)


def _joinLabel(name: object, value: object) -> str:
	parts = (name, value)
	return " ".join(part for part in parts if isinstance(part, str) and part and not part.isspace())


#: ``NVDAObject``'s own generic child accessors. A class that has not overridden
#: them answers ``getChild`` by building the whole child list, so fetching a tail
#: one child at a time would be quadratic there; only a class that provides its
#: own (``IAccessible`` and friends, which map straight onto the platform API) is
#: read that way.
_BASE_GET_CHILD = NVDAObject.getChild
_BASE_CHILD_COUNT = NVDAObject._get_childCount


def _hasFastChildAccess(obj: NVDAObject) -> bool:
	"""Whether ``obj`` can hand back one child without building all of them."""
	cls = type(obj)
	return (
		getattr(cls, "getChild", None) is not _BASE_GET_CHILD
		and getattr(cls, "_get_childCount", None) is not _BASE_CHILD_COUNT
	)


def _childrenOf(obj: NVDAObject, limit: int) -> tuple[list[NVDAObject], int]:
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
		count = safeCall(lambda: int(obj.childCount), -1)
		if count > limit:
			tail: list[NVDAObject] = []
			for index in range(count - 1, count - limit - 1, -1):
				child = safeCall(lambda i=index: obj.getChild(i))
				if child is None:
					break  # the tail is shorter than advertised; keep what we have
				tail.append(child)
			if tail:
				tail.reverse()
				return tail, count - len(tail)
	children: list[NVDAObject] | None = safeCall(lambda: list(obj.children or []))
	if children is None:
		return [], 0
	if len(children) > limit:
		return children[-limit:], len(children) - limit
	return children, 0


def _cleanText(text: str) -> str:
	"""Reduce an object's raw text to the words a user could actually read.

	Embedded-object placeholders stand in for child objects rather than for
	anything readable, so they are stripped out; whitespace is normalised so that
	a reflow which changes nothing but line breaks is not mistaken for new
	content. A node left with nothing here contributes no text at all.
	"""
	if not text:
		return ""
	if _OBJECT_REPLACEMENT in text:
		text = text.replace(_OBJECT_REPLACEMENT, "")
	return " ".join(text.split())


def _readableText(raw: str) -> str:
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


def _isProgressBar(obj: NVDAObject) -> bool:
	"""Whether the object is a progress bar control.

	Tolerant of a missing role: a progress bar that cannot be recognised is simply
	read like any other control.
	"""
	return safeCall(lambda: obj.role == Role.PROGRESSBAR, False) is True


def _isPresented(obj: NVDAObject | None) -> bool:
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
	if obj is None:
		return True
	states = safeCall(lambda: obj.states)
	if not states:
		return True
	return not (states & _HIDDEN_STATES)


def _focusObject() -> NVDAObject | None:
	"""NVDA's focus object, as one this thread may ask things of, or ``None``.

	NVDA made the object on its main thread, and asked anything from this one it
	fails every question, which the guard around every question here turns into a
	control that holds nothing. That is how the Claude app's prompt, whose value
	NVDA itself reads without trouble, went on having everything typed into it
	read back. It is therefore fetched again for this thread
	(:func:`.onThisThread`); where that fails, NVDA's own object is returned,
	and asking it costs nothing worse than no answer.
	"""
	focus = safeCall(api.getFocusObject)
	if focus is None:
		return None
	return onThisThread(focus) or focus


def _focusedValues(focusObj: NVDAObject) -> frozenset[str]:
	"""The values of the focused control and of every control nested in it.

	A field's value is its text, so this is what the user has typed, read through
	the simplest property a control has; a slider's, spin button's or combo box's
	is what the user has set it to. Each value is taken twice: on its own, and
	with the control's name in front, exactly as a sweep reads a control that has
	no text of its own (:func:`_labelOf`). Held only against the value, that
	control's own piece of the sweep — "Volume 55", or "Prompt" and everything
	typed into it — holds the value rather than being part of it, and was read
	back at the user on every change they made. The name is never taken without
	a value beside it: on its own it is not anything the user did, and an empty
	field would silence every control that mentions the field's name. Nor is a
	control's own text, which a field's value already gives, and which a control
	with no value was never typed into.

	Read as a poll begins and again once something is about to be announced
	(:meth:`Monitor._collectDelta`), because the sweep in between takes its own
	copy of the field at some moment of its own. Typed into or deleted from
	meanwhile, the field no longer holds what the sweep saw, but the sweep's copy
	is always part of what it held at one reading or the other.

	A focused control that is a whole document — browse mode leaves the focus
	there while the user reads — gives nothing: everything in it would count as
	typed, and the window would fall silent for as long as the user read it.
	Bounded by :data:`MAX_NODES`, like any sweep.
	"""
	if safeCall(lambda: focusObj.role) == Role.DOCUMENT:
		return frozenset()
	values: set[str] = set()
	budget = MAX_NODES
	pending = [focusObj]
	while pending and budget > 0:
		obj = pending.pop()
		budget -= 1
		value = safeCall(lambda o=obj: o.value)
		text = _readableText(value) if isinstance(value, str) else ""
		if text:
			values.add(text)
			values.add(_readableText(_joinLabel(safeCall(lambda o=obj: o.name), value)))
		children, _firstIndex = _childrenOf(obj, budget)
		pending.extend(children)
	return frozenset(values)


#: A run of letters or digits, in any script.
_WORD = re.compile(r"\w+")


def _wordsOf(text: str) -> str:
	"""``text`` as its words alone, one space apart, with every punctuation mark gone."""
	return " ".join(_WORD.findall(text))


def _isTyped(text: str, typed: frozenset[str], typedWords: frozenset[str]) -> bool:
	"""Whether ``text`` is part of what the focused control holds (:func:`_focusedValues`).

	Part of it as written, or word for word: with the punctuation gone from both
	sides, a button that shows a slider's setting as "Effort: High" repeats the
	slider's own "Effort High", which is what the Claude app's effort button
	does. ``typedWords`` is ``typed`` put through :func:`_wordsOf` once for the
	whole poll, rather than once for every text asked about. A text that is
	nothing but punctuation is only ever held against ``typed`` as written:
	as words it is empty, and empty is part of everything.
	"""
	if any(text in value for value in typed):
		return True
	words = _wordsOf(text)
	return bool(words) and any(words in value for value in typedWords)


def _sweepEntries(
	root: NVDAObject,
	ignoreProgressBars: bool = False,
) -> tuple[list[Entry], bool, dict[str, NVDAObject]]:
	"""The target's accessible subtree, as ``(entries, whole, nodes)``.

	``entries`` is a list of ``(key, text)`` pairs — one per control that has
	anything to say, in document order, with no special case for windows: a
	window, a message list and a lone edit field are all swept the same way, so a
	list always yields its individual items and a document its individual
	paragraphs. ``whole`` says whether the sweep reached the entire subtree or
	stopped short of it at one of the caps below; only a whole sweep is allowed to
	conclude that content it did not find is gone.

	``nodes`` maps each entry's key to the control it came from, for the one
	caller that has to ask a control something rather than read its text
	(:func:`_isPresented`). It is deliberately kept out of ``entries``, which is
	content and nothing else: the cache, the dark-sweep test and the change
	detection all work on text alone, and none of them should be handed an object
	they might be tempted to consult.

	**The text of a node.** The children are swept first. If anything below the
	node produced text, the node itself contributes only its *label* (name and
	value): a container is a heading over its children, never a second copy of
	them. An editable field is the exception to the value: its value *is* its
	text, which its children have just given, so it contributes its name alone;
	taking both read a field that changed as its name followed by all of its
	text, where the paragraph that changed is what there was to hear. Only when the whole subtree came back mute is the node's own text
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
	"""
	entries: list[Entry] = []
	nodes: dict[str, NVDAObject] = {}
	budget = [MAX_NODES]
	#: Cleared as soon as any part of the subtree goes unread — the node budget
	#: ran out, a container was clipped to its tail, or the depth cap stopped the
	#: descent. Such a sweep still reports everything it found, but it cannot
	#: speak for what it never reached, which is why absence is only ever trusted
	#: from a whole one.
	whole = [True]

	def visit(obj: NVDAObject, depth: int, key: str, isRoot: bool) -> bool:
		if budget[0] <= 0:
			whole[0] = False
			return False
		budget[0] -= 1
		if not isRoot and ignoreProgressBars and _isProgressBar(obj):
			return False  # a progress bar NVDA already handles; not our churn to report
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
			childKey = f"{key}/{firstIndex + offset}"
			if visit(children[offset], depth + 1, childKey, False):
				gotText = True
		text = ""
		# The own-text fallback is only honest when the subtree really came back
		# mute: a childless node always qualifies, and a node with children only if
		# nothing was clipped and the budget survived them. Otherwise "mute" just
		# means "not looked at", and its flat text would be the blob we swept to
		# avoid.
		trustOwnText = looked and (not children or (firstIndex == 0 and budget[0] > 0))
		if not gotText and trustOwnText and _hasOwnText(obj):
			text = _readableText(_ownText(obj))
		if not text and not (isRoot and children):
			# A field's value is its text, which its children have just given.
			isFieldOverText = gotText and isinstance(obj, EditableText)
			text = _readableText(_labelOf(obj, withValue=not isFieldOverText))
		if not text:
			return gotText
		entries.append((key, text))
		nodes[key] = obj
		return True

	visit(root, 0, "", True)
	entries.reverse()
	return entries, whole[0], nodes


def _isDarkSweep(entries: Sequence[Entry], cache: Mapping[str, int]) -> bool:
	"""Whether a sweep found nothing where the target is known to hold content.

	A collapsed accessible tree still answers: the sweep comes back with the
	target's own name and nothing beneath it, or with nothing at all. A target
	that genuinely holds a single line looks exactly the same, so the cache has
	to be holding more than such a sweep could ever produce before its emptiness
	is read as a failure to report rather than as content.
	"""
	return len(entries) <= 1 < len(cache)


#: A maximal run of digits, optionally with separators *between* digits — the
#: "." of a decimal, the "," or space of grouped thousands, the no-break space
#: Czech writes them with ("1\u00a0234"), the ":" of a clock. This is the
#: volatile part of a counter, timer, clock, percentage or byte readout.
#: Nothing here matches a letter, word, app name or language: it recognises
#: *numbers* only, so counters in any language normalise identically. The
#: separators are spelt as escapes rather than written out, so that a space
#: and a no-break space are told apart by reading the source, not measuring it.
_NUMBER_RUN = re.compile(r"\d(?:[\d.,:\u00a0\u0020]*\d)?")
#: The sentinel a numeric run collapses to. A private-use character, so it can
#: never collide with anything in real content. Spelt as an escape for the same
#: reason as the separators above.
_NUMBER_SENTINEL = "\uf8ff"


def _templateOf(text: str) -> str:
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


def _stripAnnounced(delta: str, announced: str) -> str:
	"""``delta`` with everything the previous announcement said taken out of it.

	Every line of ``announced`` is cut out of every line of ``delta`` wherever it
	occurs, so a reply that has grown since it was last read is heard only from
	where it left off, and a line heard already is not heard again. Longer lines
	are cut first, so that a short one cannot break up a longer one before that
	has been cut out whole. A cut leaves a space rather than nothing, so the words
	on either side of it are not run together, and a line left with nothing in it
	is dropped.
	"""
	if not announced:
		return delta
	heard = sorted({line for line in announced.split("\n") if line}, key=len, reverse=True)
	kept: list[str] = []
	for line in delta.split("\n"):
		rest = line
		for old in heard:
			if old in rest:
				rest = rest.replace(old, " ")
		rest = " ".join(rest.split())
		if rest:
			kept.append(rest)
	return "\n".join(kept)


def _joinSurfaced(surfaced: Sequence[Entry]) -> str:
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
	kept: list[str] = []
	chain: list[Entry] = []
	for key, text in surfaced:
		while chain and not key.startswith(chain[-1][0] + "/"):
			chain.pop()
		if any(text in ancestorText for _, ancestorText in chain):
			continue  # an ancestor already says this; do not read it twice
		chain.append((key, text))
		kept.append(text)
	return "\n".join(kept).strip()


class Monitor:
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

	def __init__(
		self,
		registry: TargetRegistry,
		notifier: Notifier,
		onListChanged: Callable[[], None] | None = None,
	):
		self.registry = registry
		self.notifier = notifier
		#: Called, on the main thread, after this monitor changes anything the
		#: owner persists. See :meth:`_notifyListChanged`.
		self._onListChanged = onListChanged
		self._thread: threading.Thread | None = None
		self._stop = threading.Event()
		#: Whether the first search for the remembered targets has run. The
		#: targets it finds are reported as one message rather than announcing
		#: themselves one by one; every target that attaches after it announces
		#: itself as it appears. Monitor thread only.
		self._startupDone = False

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

	def _callOnMainThread(self, func: Callable[..., object], *args: Any, **kwargs: Any):
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
		queueHandler.queueFunction(queueHandler.eventQueue, func, *args, _immediate=immediate, **kwargs)

	def _notifyListChanged(self):
		"""Tell the owner that what it persists about the targets has moved.

		The monitor manages the target list on its own account: a target that
		disappears is dropped from it, and one that reappears is taken up again
		under a freshly read identity. Both are things the saved list records, and
		without this it would not follow them — a target dropped here would still
		be in the stored list and would come back at the next NVDA start, and a
		target that moved would go on being looked for where it used to be.

		Queued onto the main thread like everything else this thread hands over,
		and therefore behind whatever was queued before it, so the list is already
		in the state that is about to be written out.
		"""
		if self._onListChanged is not None:
			self._callOnMainThread(self._onListChanged)

	def _refreshIdentity(self, target: TrackedTarget, obj: NVDAObject) -> bool:
		"""Re-take ``target``'s identity from the object it has been found at.

		Returns whether the identity actually moved, so that the caller can have
		the saved list written out again only when there is something new in it
		to write.
		"""
		newIdentity = targetsMod.objectIdentity(obj)
		if not newIdentity or newIdentity == target.identity:
			return False
		target.identity = newIdentity
		return True

	def onAdded(self, target: TrackedTarget):
		"""Take a target up, or take it up again, with nothing known about it yet.

		The baseline is deliberately not taken here. A sweep costs tens to hundreds
		of milliseconds, and this runs on NVDA's main thread as well as on the
		monitor's — the overlay's tracking commands and the target menu both reach
		it — where a sweep would stall speech, braille and keyboard handling for
		exactly that long. Nor is the target's own application any guide: the mouse
		and the navigator object can both be pointed at a window in the background,
		and it is a background window that costs a full sweep rather than nothing.

		The cache is marked stale instead, which is this add-on's existing way of
		saying that it predates a spell nobody read: the next poll folds its sweep
		in silently, on the monitor's own thread, so the baseline is taken there and
		nothing that arrived before the target was watched is announced afterwards.
		"""
		settings = addonConfig.snapshot()
		target.lastChangeTime = None
		target.announcedDelta = ""
		target.announcedRun = 0
		target.ignoredTemplates = frozenset()
		target.seenContent = OrderedDict()
		target.seenChars = 0
		target.prevTexts = frozenset()
		target.wasInForeground = isInForegroundApp(target.obj)
		# The title a whole-window target is held to, so that a window which later
		# renames itself can be told from the one that was actually added.
		target.captureTrackedTitle(settings)
		target.staleCache = True

	# --- polling -------------------------------------------------------------
	def _run(self):
		"""The monitor thread's loop, which runs two jobs at two different rates.

		Presence — which targets exist right now — is settled on every
		POLL_INTERVAL tick, and the first time before the thread has waited at
		all, so a remembered target is taken up, or reported missing, as soon as
		the answer can be had. Content is swept only once the configured
		*tracking interval* has elapsed. They are separate questions: how often
		the user wants a window re-read says nothing about how soon they want to
		hear that it has opened.

		An interval of 0 is a special "detection only" mode: it still sweeps on
		every tick so the target menu stays current, but the sweep announces
		nothing.

		Elapsed time is measured, not counted in ticks. A sweep of a large window
		can take longer than a tick, and charging it a flat POLL_INTERVAL would
		make a five-second interval mean twenty seconds of wall clock. The interval
		is a floor, never a promise, but it should at least mean what it says.

		Waiting on the stop event rather than sleeping means :meth:`stop` takes
		effect at once instead of after the rest of a tick.
		"""
		sinceLast = 0.0
		lastTick = time.monotonic()
		while True:
			try:
				now = time.monotonic()
				elapsed = now - lastTick
				lastTick = now
				settings = addonConfig.snapshot()
				if settings["enabled"]:
					self._checkPresence(settings)
					interval = int(settings["trackingInterval"])
					effective = POLL_INTERVAL if interval <= 0 else max(interval, POLL_INTERVAL)
					sinceLast += elapsed
					if sinceLast + 1e-6 >= effective:
						sinceLast = 0.0
						self._checkContent(settings, announce=interval != 0)
			# The last line of defence for the whole add-on: whatever one poll ran
			# into, the thread has to survive it and try again on the next tick.
			except Exception:
				log.exception("Error in Background Content Tracker poll")
			if self._stop.wait(POLL_INTERVAL):
				return

	def _checkPresence(self, settings: Settings):
		"""Take up the remembered targets that are there, and let go of those that are not.

		The first run of this is also the start-up restoration, and it is the whole
		of it: whatever is open when the add-on loads is found and reported there
		and then. Nothing is waited for, because there is nothing to wait for — the
		applications the user had open were open before NVDA started, and one that
		is launching announces itself as it attaches, like any other target that
		appears later in the session.
		"""
		remembered = [
			target
			for target in self.registry.detachedTargets()
			if target.setting("rememberTargets", settings)
		]
		attached = self._relocatePass(remembered, settings)
		if not self._startupDone:
			self._startupDone = True
			# Silent where nothing was remembered in the first place: there is no
			# restoration to report, and the user has not asked for one.
			if remembered:
				self._callOnMainThread(self.notifier.announceRestored, attached, len(remembered))
		for target in self.registry.liveTargets():
			if self._stop.is_set():
				return
			if not target.isAlive() or not self._keptItsTitle(target, target.obj, settings):
				self._handleDisappeared(target, target.isForgottenWhenGone(settings))

	def _checkContent(self, settings: Settings, announce: bool):
		"""Read every target that is there, and announce what has arrived in it."""
		for target in self.registry.liveTargets():
			if self._stop.is_set():
				return
			self._checkTargetContent(target, settings, announce)

	def _checkTargetContent(self, target: TrackedTarget, settings: Settings, announce: bool):
		obj = target.obj
		if obj is None:
			return
		isWindow = target.kind == "window"
		ignorePB = bool(target.setting("ignoreProgressBars", settings)) and isWindow
		inForeground = isInForegroundApp(obj)
		if inForeground != target.wasInForeground:
			# The user has just arrived at this target, or just left it; either
			# way they have been at it, so the run of announcements they have not
			# heard starts afresh. This turns on the foreground state alone, so it
			# still happens for a target that is read right through the visit
			# instead of being skipped, which is the only reset such a target ever
			# gets.
			#
			# What the target has learned about its counters is deliberately not
			# reset here: a clock is still a clock after the user has looked at
			# the window, and having to recognise it again on every visit is what
			# would let it be heard again.
			target.announcedRun = 0
		target.wasInForeground = inForeground
		if inForeground and not target.setting("trackForegroundTargets", settings):
			# The user is in this application. Nothing would be announced, so do
			# not even read it: the app being worked in is left entirely alone.
			# Whatever happens while we are not looking leaves the cache stale.
			target.staleCache = True
			return
		# The focused control is only worth keeping quiet while the user is actually
		# in this application; anywhere else the focus is in another one, and
		# nothing typed there is in this target. It is deliberately not held to
		# being inside this very window as well: such a test could only ever let
		# the user's typing through, and what the focused control holds is text
		# they put there, wherever in the window it turns up. Its value is read
		# before the sweep as well as after it; see :func:`_focusedValues`.
		focusObj = None
		typedBefore: frozenset[str] = frozenset()
		if inForeground and isWindow and target.setting("ignoreFocusedControl", settings):
			focusObj = _focusObject()
			if focusObj is not None:
				typedBefore = _focusedValues(focusObj)
		entries, whole, nodes = _sweepEntries(obj, ignorePB)
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
		delta = self._collectDelta(target, entries, nodes, isWindow, settings, focusObj, typedBefore)
		self._absorb(target, entries, whole, dark)
		target.prevTexts = frozenset(text for _, text in entries)
		if not delta:
			return
		target.lastDelta = delta
		target.lastChangeTime = time.time()
		if not announce:
			return  # tracking interval 0: the menu is updated, nothing is spoken
		cap = int(settings["changesAtOnce"])
		if cap and target.announcedRun >= cap:
			return  # reached the consecutive-announcement cap; wait for a refocus
		# A poll catches everything that arrived since the previous one, so however
		# many changes a long interval gathered, this is already all of them as one.
		spoken = _stripAnnounced(delta, target.announcedDelta)
		if not spoken:
			return  # nothing the previous announcement did not already say
		target.announcedDelta = delta
		target.announcedRun += 1
		self._callOnMainThread(self.notifier.announceChange, target, spoken, immediate=True)

	def _collectDelta(
		self,
		target: TrackedTarget,
		entries: Sequence[Entry],
		nodes: Mapping[str, NVDAObject],
		isWindow: bool,
		settings: Settings,
		focusObj: NVDAObject | None,
		typedBefore: frozenset[str],
	) -> str:
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

		When "Ignore counters, steppers and timers" is on for a window, a control
		that does nothing but count is recognised and silenced. Three things have
		to be true of a surfaced text at once, and each rules out something the
		option is not about:

		* It **contains a number** — its template (:func:`_templateOf`) differs
		  from the text itself. A control with no number in it cannot be a counter,
		  whatever else it does, so nothing further is asked of it.
		* A different text **sharing its template** was in the previous sweep and
		  is gone from this one. Sharing a template is precisely "these differ in
		  nothing but their numbers", and the disappearance is what makes it a
		  *replacement*: the control took its own previous value's place. A log
		  that appended a line still holds every earlier line, so it can never
		  mute itself, and two separate messages that happen to differ by a number
		  are both still there, so neither mutes the other.
		* Its template is not silenced **already**, in which case there is nothing
		  left to decide and the text is simply dropped.

		Recognition and silence begin together: the change that identifies a
		counter is the first one dropped, not the last one announced. Its arrival
		was announced when the control first appeared, which is the part worth
		hearing; from then on it is only counting.

		The silence lasts as long as the target does. A clock does not stop being
		a clock because it paused, because the user looked at the window, or
		because a minute has gone by, so nothing here expires — only re-baselining
		the target or moving the option itself clears what was learned (see
		:meth:`.TrackedTarget.forgetIgnoredControls`).

		Whatever survives all of that is finally held to being on screen at all
		(:func:`_isPresented`), which is asked here, of the few nodes about to be
		announced, rather than of every node of the sweep. Content that is hidden,
		collapsed or scrolled out of view is still absorbed into the cache like any
		other, so uncovering it later cannot turn it into news either.

		When "Ignore focused control" is on for a window, ``focusObj`` is NVDA's
		focus object, and ``typedBefore`` the values it and the controls nested in
		it held as the poll began, each alone and with its control's name in front
		(:func:`_focusedValues`). They are read once more here, and a surfaced text
		that is part of what either reading holds, as written or word for word
		(:func:`_isTyped`), is dropped: the field's own paragraph, a line of a
		longer prompt set out as a control of its own, a slider or combo box as it
		reads itself or as another control repeats it, and any of those as the
		sweep caught it between the two readings. What this cannot tell apart is a genuinely new message that
		happens to be part of what the field holds, which stays silent for as long
		as the field holds it. Only those texts are dropped, never the rest of the change, and
		they are still absorbed into the cache, which is the whole point of
		dropping them here rather than skipping them in the sweep: what was typed is
		known to have been there, so moving the focus away later cannot turn it
		into new content and read it all back.

		What is surfaced is always the node's whole current text, never a
		character-level diff. It is what the target menu shows, and what the next
		announcement is measured against; what is spoken has the previous
		announcement taken out of it first (:func:`_stripAnnounced`).
		"""
		cache = target.seenContent
		counts = Counter(text for _, text in entries)
		outstanding: dict[str, int] = {}
		for text, seen in counts.items():
			known = cache.get(text, 0)
			if seen > known:
				outstanding[text] = seen - known
		if not outstanding:
			return ""
		# The last copies of a repeated text are the new ones, so the pick runs
		# backwards and the result is turned back into document order.
		picked: list[Entry] = []
		for key, text in reversed(entries):
			left = outstanding.get(text)
			if left:
				outstanding[text] = left - 1
				picked.append((key, text))
		picked.reverse()
		if focusObj is not None:
			# Read again, now that the sweep has taken its own copy of the field.
			typed = typedBefore | _focusedValues(focusObj)
			if typed:
				typedWords = frozenset(_wordsOf(value) for value in typed)
				picked = [(key, text) for key, text in picked if not _isTyped(text, typed, typedWords)]
				if not picked:
					return ""
		picked = [(key, text) for key, text in picked if _isPresented(nodes.get(key))]
		if not picked:
			return ""
		if not (isWindow and target.setting("ignoreCounters", settings)):
			return _joinSurfaced(picked)

		ignored = target.ignoredTemplates
		# The templates this sweep lost. A surfaced text whose template is in here
		# took something's place, which is a control changing rather than content
		# arriving. Nothing surfaced can itself have vanished, so a text is never
		# judged a replacement for itself.
		vanished: set[str] = set()
		for text in target.prevTexts:
			if text not in counts:
				vanished.add(_templateOf(text))

		surfaced: list[Entry] = []
		learned: set[str] = set()
		for key, text in picked:
			template = _templateOf(text)
			if template == text:
				# Not a single digit anywhere in it. Whatever this control is
				# doing, it is not counting.
				surfaced.append((key, text))
				continue
			if template in ignored:
				continue  # a control already known to be counting
			if template in vanished:
				learned.add(template)  # caught counting: silent from here on
				continue
			surfaced.append((key, text))
		if learned:
			# Rebound rather than added to, because the main thread may empty it
			# from under this one when the option moves; the worst a collision
			# can cost is recognising a counter again on the next poll.
			target.ignoredTemplates = ignored | learned
		return _joinSurfaced(surfaced)

	def _absorb(self, target: TrackedTarget, entries: Sequence[Entry], whole: bool, dark: bool):
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

	def _keptItsTitle(self, target: TrackedTarget, obj: NVDAObject, settings: Settings) -> bool:
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

	def _handleDisappeared(self, target: TrackedTarget, forget: bool):
		target.obj = None
		# The user is always told a target is gone, however the list is managed.
		# ``forget`` is :meth:`.TrackedTarget.isForgottenWhenGone`, which is where
		# the rule is stated: the entry is dropped unless the target is remembered
		# and asked to be kept, in which case it stays as a detached target for the
		# relocation pass above to take up again when it reappears.
		if forget:
			self._callOnMainThread(self.registry.remove, target)
		self._callOnMainThread(self.notifier.announceStopped, target, unprompted=True)
		if forget:
			# Queued after the removal, so what is written out is the list without
			# this target rather than the one it is still in.
			self._notifyListChanged()

	# --- relocation of remembered / stale targets ---------------------------
	def relocate(self, target: TrackedTarget) -> bool:
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
		if self._refreshIdentity(target, obj):
			self._notifyListChanged()
		return True

	def relocateAsync(self, target: TrackedTarget, callback: Callable[[TrackedTarget, bool], None]):
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
			# A lookup that failed is a target that was not found; the user is waiting
			# on an answer either way.
			except Exception:  # noqa: BLE001
				log.debugWarning("Could not relocate target", exc_info=True)
				found = False
			# The user pressed a key and is waiting on this one.
			self._callOnMainThread(callback, target, found, immediate=True)

		threading.Thread(
			name="BackgroundContentTracker._relocateThread",
			target=run,
			daemon=True,
		).start()

	def _relocatePass(self, targets: Sequence[TrackedTarget], settings: Settings) -> int:
		"""Look for every detached target, over one view of the desktop.

		The desktop is enumerated once for the whole pass rather than once per
		target: the list of top-level windows and their application names is the
		same for all of them, and re-reading it ten times over — every tick, for
		as long as NVDA runs — is ten times the cross-process traffic for one
		answer.

		Every target is tried on every pass, however long it has been missing. A
		target whose application is not running is ruled out by the shared window
		list before a single cross-process read; one whose application is running
		walks a subtree, and pays that walk every tick for as long as its control
		is absent. That is the price of a target being taken up the moment it
		comes back rather than up to a back-off later.

		Returns how many targets it attached. Each of them is baselined by the
		next content sweep: :meth:`_attach` leaves its cache stale, so whatever
		arrived before anybody was looking is folded in silently.
		"""
		if not targets:
			return 0
		windows = self._desktopWindows()
		if not windows:
			return 0
		attached = 0
		for target in targets:
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
				continue
			# The targets the first pass finds are reported together, so one
			# attaching there does not speak for itself; afterwards each does.
			self._attach(target, obj, announce=self._startupDone)
			attached += 1
		return attached

	def _desktopWindows(self) -> list[tuple[str, NVDAObject]]:
		"""Every reachable top-level window as ``(application name, object)``, or ``[]``.

		The application name is read here, once per window per pass, because it is
		what rules a window out for every target that does not want that
		application: one read against the six a full identity descriptor costs,
		and shared by the whole pass instead of taken again for each target.

		A window the user cannot get to is left out, by the same test that decides
		a target has gone (:func:`.isReachableWindow`), and this pass must not be
		allowed to disagree with that one: a target detached because its window was
		hidden would otherwise be found again here while it is still hidden, called
		gone by the very next sweep, and announced back and forth for as long as
		the application sat in the tray. Leaving those windows out is also what
		makes restoring one from the tray read as the target reappearing.
		"""
		topWindows = safeCall(lambda: list(api.getDesktopObject().children))
		if not topWindows:
			return []
		return [
			(targetsMod.appNameOf(window), window)
			for window in topWindows
			if targetsMod.isReachableWindow(window)
		]

	def _candidateWindows(
		self,
		windows: Sequence[tuple[str, NVDAObject]],
		identity: Identity,
	) -> list[NVDAObject]:
		"""The top-level windows from ``windows`` worth examining for ``identity``.

		Empty when the wanted application is not running at all, which is both the
		commonest case for a remembered target and the cheapest: it is settled by
		names already in hand, with nothing read from anywhere.
		"""
		if not identity:
			return []
		wantedApp = identity.get("appName")
		return [window for appName, window in windows if not wantedApp or appName == wantedApp]

	def _locateAmong(
		self,
		candidates: Sequence[NVDAObject],
		identity: Identity,
		kind: str | None = None,
	) -> NVDAObject | None:
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

	def _locate(self, identity: Identity, kind: str | None = None) -> NVDAObject | None:
		"""The live NVDAObject whose identity matches ``identity``, or ``None``.

		Enumerates the desktop for this one lookup; a relocation pass shares one
		enumeration across its targets instead (see :meth:`_relocatePass`).
		"""
		if not identity:
			return None
		windows = self._desktopWindows()
		return self._locateAmong(self._candidateWindows(windows, identity), identity, kind)

	def _findMatchingDescendant(
		self,
		root: NVDAObject,
		identity: Identity,
		maxNodes: int = 150,
	) -> NVDAObject | None:
		# Cheap pre-filter: with no automation id, identitiesMatch can only succeed
		# when the roles are equal, so a single role read rules a node out for one
		# cross-process access instead of the six a full identity descriptor costs.
		# With an automation id, role is ignored by the match, so we must not skip.
		roleFilter = None
		if not identity.get("automationID"):
			roleFilter = identity.get("role")
		# A deque, because this is a breadth-first walk and a list would pay for
		# every remaining node each time the front of it is taken off.
		queue = deque((root,))
		examined = 0
		while queue and examined < maxNodes:
			node = queue.popleft()
			examined += 1
			skip = False
			if roleFilter is not None:
				role = safeCall(lambda n=node: int(n.role))
				skip = role is not None and role != roleFilter
			if not skip and safeCall(
				lambda n=node: targetsMod.identitiesMatch(identity, targetsMod.objectIdentity(n)),
				False,
			):
				return node
			children = safeCall(lambda n=node: n.children)
			if children:
				queue.extend(children)
		return None

	def _attach(self, target: TrackedTarget, obj: NVDAObject, announce: bool = True):
		"""Take up a target that has been found again, and baseline it.

		``announce`` is false only for the targets found by the first pass, which
		are reported together rather than one by one (see :meth:`_checkPresence`).
		"""
		target.obj = obj
		moved = self._refreshIdentity(target, obj)
		self.onAdded(target)
		if announce:
			self._callOnMainThread(self.notifier.announceTracking, target, unprompted=True)
		if moved:
			self._notifyListChanged()
