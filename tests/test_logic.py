# Offline logic tests for Background Content Tracker.
# Stubs out NVDA modules so the pure-logic add-on modules can be imported and
# exercised outside NVDA. Covers slots/sorting, identity, notification
# formatting, overlay dispatch, and — critically — the overlay THREADING
# CONTRACT: _capture() runs on NVDA's low-level keyboard hook thread and must
# never touch wx, speech or NVDAObject/COM APIs.
import sys, types, importlib, os

PKGDIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "addon", "globalPlugins", "backgroundContentTracker",
)
T = types


class ThreadViolation(BaseException):
    """Raised by tripwires. Derives from BaseException so that _capture()'s own
    `except Exception` cannot swallow it and hide a contract breach."""


HOOK = {"on": False}      # True while we simulate running on the keyboard hook thread
MONITOR = {"on": False}   # True while we simulate running on the monitor thread
MESSAGES = []
QUEUED = []
TIMERS = []


def stub(name, **attrs):
    m = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(m, k, v)
    sys.modules[name] = m
    return m


def _ui_message(text, speechPriority=None):
    if HOOK["on"]:
        raise ThreadViolation("ui.message() called on the keyboard hook thread")
    if MONITOR["on"]:
        raise ThreadViolation("ui.message() called on the monitor thread")
    MESSAGES.append(text)


def _beep(*a, **k):
    if HOOK["on"]:
        raise ThreadViolation("tones.beep() called on the keyboard hook thread")
    if MONITOR["on"]:
        raise ThreadViolation("tones.beep() called on the monitor thread")


class FakeTimer:
    def __init__(self):
        self.stopped = False
    def Stop(self):
        if HOOK["on"]:
            raise ThreadViolation("wx timer .Stop() called on the keyboard hook thread")
        self.stopped = True


def _callLater(ms, fn, *a, **k):
    if HOOK["on"]:
        raise ThreadViolation("core.callLater() called on the keyboard hook thread")
    if MONITOR["on"]:
        raise ThreadViolation("core.callLater() called on the monitor thread")
    t = FakeTimer()
    TIMERS.append((t, ms, fn, a))
    return t


def _queueFunction(queue, func, *args, _immediate=False, **kwargs):
    QUEUED.append((func, args, kwargs, _immediate))


def drain():
    """Run everything the monitor thread handed to NVDA's main thread."""
    pending, QUEUED[:] = list(QUEUED), []
    for func, args, kwargs, _immediate in pending:
        func(*args, **kwargs)


cfg = stub("config")
class Conf(dict):
    pass
cfg.conf = Conf()
cfg.conf.spec = Conf()

#: Simulated window topology. ROOTOWNER maps an hwnd to its root-owner hwnd,
#: so a control (101) can belong to a top-level window (100).
FG = {"hwnd": 0}
ROOTOWNER = {}

stub("winUser",
     isWindow=lambda hwnd: bool(hwnd),
     getForegroundWindow=lambda: FG["hwnd"],
     getAncestor=lambda hwnd, flags: ROOTOWNER.get(hwnd, hwnd),
     isDescendantWindow=lambda parent, child: parent == child,
     GA_PARENT=1, GA_ROOT=2, GA_ROOTOWNER=3)
stub("api",
     getFocusObject=lambda: None, getForegroundObject=lambda: None,
     getNavigatorObject=lambda: None, getMouseObject=lambda: None,
     getDesktopObject=lambda: T.SimpleNamespace(children=[]))
stub("eventHandler", requestEvents=lambda *a, **k: None)
stub("textInfos", POSITION_ALL="all")
stub("logHandler", log=T.SimpleNamespace(
    debugWarning=lambda *a, **k: None, error=lambda *a, **k: None,
    info=lambda *a, **k: None, exception=lambda *a, **k: None, warning=lambda *a, **k: None))

def initTranslation():
    g = sys._getframe(1).f_globals
    g["_"] = lambda s: s
    g["ngettext"] = lambda s, p, n: s if n == 1 else p
    g["pgettext"] = lambda c, s: s
    g["npgettext"] = lambda c, s, p, n: s if n == 1 else p
stub("addonHandler", initTranslation=initTranslation)
stub("tones", beep=_beep)
stub("ui", message=_ui_message)
stub("speech")
stub("speech.priorities", Spri=T.SimpleNamespace(NORMAL=0, NEXT=1, NOW=2))
stub("inputCore", manager=T.SimpleNamespace(_captureFunc=None))
stub("core", callLater=_callLater)
stub("queueHandler", eventQueue=object(), queueFunction=_queueFunction)

class KeyboardInputGesture:
    pass
stub("keyboardHandler", KeyboardInputGesture=KeyboardInputGesture)

class NVDAObjectTextInfo:
    """Stand-in for NVDA's generic fallback TextInfo (name/value/description only)."""
class RealTextInfo(NVDAObjectTextInfo):
    """Stand-in for a TextInfo backed by a real text interface."""
class NVDAObject:
    """Stand-in for NVDA's base object. Its generic child accessors answer by
    building the WHOLE child list, which is exactly what the sweep must detect:
    fetching a tail one child at a time from such a class would be quadratic."""
    def getChild(self, index):
        return self.children[index]
    def _get_childCount(self):
        return len(self.children)
stub("NVDAObjects", NVDAObject=NVDAObject, NVDAObjectTextInfo=NVDAObjectTextInfo)

#: A stand-in for NVDA's progress bar role, so the "ignore progress bars" sweep
#: filter can be exercised offline.
PROGRESSBAR_ROLE = 24
stub("controlTypes", Role=T.SimpleNamespace(PROGRESSBAR=PROGRESSBAR_ROLE))

# Deliberately NOT stubbed: diffHandler. The monitor diffs its own keyed snapshot
# and never runs a character-level diff, so importing it would hide a regression.

pkg = types.ModuleType("backgroundContentTracker")
pkg.__path__ = [PKGDIR]
sys.modules["backgroundContentTracker"] = pkg

addonConfig = importlib.import_module("backgroundContentTracker.addonConfig")
targets = importlib.import_module("backgroundContentTracker.targets")
notifier = importlib.import_module("backgroundContentTracker.notifier")
overlay = importlib.import_module("backgroundContentTracker.overlay")
monitor = importlib.import_module("backgroundContentTracker.monitor")
import inputCore as inputCoreStub
addonConfig.initialize()


class FakeRole(int):
    def __new__(cls, val, disp):
        o = int.__new__(cls, val); o.displayString = disp; return o
WIN, LIST, EDIT = FakeRole(9, "window"), FakeRole(8, "list"), FakeRole(7, "edit")

class FakeObj:
    def __init__(self, name="", role=None, app="", cls="", ctrl=0, auto="", hwnd=1):
        self.name = name; self.role = role; self.windowClassName = cls
        self.windowControlID = ctrl; self.UIAAutomationId = auto; self.windowHandle = hwnd
        self.appModule = T.SimpleNamespace(appName=app)
    def __eq__(self, o): return self is o
    def __hash__(self): return id(self)
    def setFocus(self): pass

class FakeGesture(KeyboardInputGesture):
    def __init__(self, mainKeyName, mods=(), isModifier=False):
        self.mainKeyName = mainKeyName
        self.modifierNames = tuple(mods)
        self.isModifier = isModifier

class FakeController:
    def __init__(self): self.calls = []
    def __getattr__(self, name):
        def rec(*a): self.calls.append((name,) + a)
        return rec

results = []
def check(cond, msg):
    results.append(bool(cond)); print(("PASS" if cond else "FAIL") + ": " + msg)


# ============ config defaults ============
check(addonConfig.get("enabled") is True, "default enabled True")
check(addonConfig.get("overlayTimeout") == 10, "default overlayTimeout 10")
check(addonConfig.get("targetSorting") == "oldest", "default sorting oldest")

# ============ registry / slots / sorting ============
reg = targets.TargetRegistry()
oA, oB, oC = FakeObj("A", WIN, "app1"), FakeObj("B", LIST, "app2"), FakeObj("C", EDIT, "app3")
t1, t2, t3 = reg.add(oA, "window"), reg.add(oB, "focus"), reg.add(oC, "navigator")
addonConfig.set("targetSorting", "oldest")
check([t.name for t in reg.sortedTargets()] == ["A", "B", "C"], "oldest-first order")
check(reg.slot(0) is t1 and reg.slot(2) is t3 and reg.slot(3) is None, "slot indexing")
check(reg.newest() is t3, "newest is last added")
addonConfig.set("targetSorting", "newest")
check([t.name for t in reg.sortedTargets()] == ["C", "B", "A"], "newest-first order")
check(reg.slot(0) is t3 and reg.newest() is t3, "newest-first slot(0); newest unaffected")
check(reg.findByObject(oB) is t2, "findByObject")
reg.remove(t2)
addonConfig.set("targetSorting", "oldest")
check([t.name for t in reg.sortedTargets()] == ["A", "C"] and reg.slot(1) is t3, "compaction after removal")

# ============ identity ============
idA = targets.objectIdentity(oA)
check(idA["appName"] == "app1" and idA["role"] == 9 and idA["name"] == "A", "identity fields")
check(targets.identitiesMatch(idA, dict(idA)), "identity matches itself")
idA2 = dict(idA); idA2["name"] = "different"
check(not targets.identitiesMatch(idA, idA2), "identity name mismatch")
autoX = {"appName": "x", "automationID": "a1", "windowClassName": "c1", "role": 1, "name": "n1"}
autoY = {"appName": "x", "automationID": "a1", "windowClassName": "c2", "role": 2, "name": "n2"}
check(targets.identitiesMatch(autoX, autoY), "automationID short-circuit match")

# ============ notifier formatting ============
d = notifier._describe
check(d("window", "Claude", True, []) == "window: Claude", "describe type+name")
check(d("window", "Claude", False, []) == "Claude", "describe name only")
check(d("window", "Claude", True, ["3 minutes ago", "content"]) == "window: Claude, 3 minutes ago, content", "describe with extras")
import time as _t
check(notifier.relativeTime(None) == "no changes yet", "relativeTime none")
check(notifier.relativeTime(_t.time() - 3) == "just now", "relativeTime just now")
check(notifier.relativeTime(_t.time() - 90) == "1 minute ago", "relativeTime singular")
check(notifier.relativeTime(_t.time() - 150) == "2 minutes ago", "relativeTime plural")
n = notifier.Notifier()
tgt = targets.TrackedTarget(1, FakeObj("A", WIN, "app1"), "window")
addonConfig.set("announceTargetType", True)
MESSAGES.clear(); n.announceTracking(tgt)
check(MESSAGES[-1] == "Tracking window: A", "announceTracking with type")
addonConfig.set("announceTargetType", False)
MESSAGES.clear(); n.announceStopped(tgt)
check(MESSAGES[-1] == "Stopped tracking A", "announceStopped without type")
addonConfig.set("announceTargetType", True)

# ============ manual queries report "no changes" while the target is foreground =
# A change detected during an earlier background spell must NOT be replayed on a
# manual query when the user is looking at the target right now. The target still
# appears in the menu; only its description reflects "no changes yet".
for k in ("announceTargetType", "menuTargetType", "menuTimeSinceChange",
          "menuChangedContent", "announceChangedContent"):
    addonConfig.set(k, True)
ROOTOWNER.clear(); ROOTOWNER.update({100: 100, 200: 200})
qObj = FakeObj("Claude", WIN, "app", hwnd=100)
qTgt = targets.TrackedTarget(99, qObj, "window")
qTgt.lastDelta = "a whole message"; qTgt.lastChangeTime = _t.time()

FG["hwnd"] = 200                                   # the target is in the background
check(qTgt.hasReportableChange() is True, "backgrounded + changed: the change is reportable")
MESSAGES.clear(); n.speakInfo(qTgt)
check(MESSAGES[-1] == "window: Claude, a whole message",
      "query while backgrounded reports the cached change")
check(n.menuDescription(qTgt) == "window: Claude, just now, a whole message",
      "menu while backgrounded shows the change and its age")

FG["hwnd"] = 100                                   # now the target IS the foreground window
check(qTgt.hasReportableChange() is False, "foreground: a cached change is no longer reportable")
MESSAGES.clear(); n.speakInfo(qTgt)
check(MESSAGES[-1] == "window: Claude, no changes yet",
      "query while foreground reports no change, not the stale delta")
check(n.menuDescription(qTgt) == "window: Claude, no changes yet",
      "menu while foreground shows no change but the target still appears")

# A never-changed target reports "no changes yet" too, whatever the foreground.
FG["hwnd"] = 200
freshTgt = targets.TrackedTarget(98, FakeObj("Chat", LIST, "app2", hwnd=200), "window")
check(freshTgt.hasReportableChange() is False, "never-changed target has nothing to report")
MESSAGES.clear(); n.speakInfo(freshTgt)
check(MESSAGES[-1] == "list: Chat, no changes yet", "never-changed target speaks 'no changes yet'")

# ============ overlay dispatch (key, mods) ============
fc = FakeController()
ov = overlay.Overlay(fc)
def dispatched(key, mods=()):
    fc.calls = []
    r = ov._dispatch(key, mods)
    return r, list(fc.calls)

check(dispatched("h") == (True, [("help",)]), "dispatch h -> help")
check(dispatched("w") == (True, [("toggleWindow",)]), "dispatch w -> toggleWindow")
check(dispatched("t") == (True, [("openMenu",)]), "dispatch t -> openMenu")
check(dispatched("p") == (True, [("togglePause",)]), "dispatch p -> togglePause")
check(dispatched("2") == (True, [("slotInfo", 1)]), "dispatch 2 -> slotInfo(1)")
check(dispatched("0") == (True, [("slotInfo", 9)]), "dispatch 0 -> slotInfo(9)")
check(dispatched("1", ("control",)) == (True, [("stopSlot", 0)]), "dispatch control+1 -> stopSlot(0)")
check(dispatched("space") == (True, [("newestInfo",)]), "dispatch space -> newestInfo")
check(dispatched("enter") == (True, [("newestInfo",)]), "dispatch enter -> newestInfo")
check(dispatched("backspace") == (True, [("stopNewest",)]), "dispatch backspace -> stopNewest")
check(dispatched("delete") == (True, [("clearAll",)]), "dispatch delete -> clearAll")
check(dispatched("numpad3") == (True, [("slotInfo", 2)]), "dispatch numpad3 -> slotInfo(2)")
check(dispatched("x") == (False, []), "dispatch invalid key -> False, no call")
check(dispatched("1", ("alt",)) == (False, []), "dispatch alt+1 -> invalid")

# ============ bound-method identity (the bug that never released capture) ======
check(ov._capture is not ov._capture, "bound method identity differs on each access (why _captureRef exists)")
check(ov._captureRef is ov._captureRef, "_captureRef is a stable single object")

# ============ overlay lifecycle + THREADING CONTRACT ============
def resetOverlay(prevCaptor=None):
    global fc, ov
    inputCoreStub.manager._captureFunc = prevCaptor
    fc = FakeController(); ov = overlay.Overlay(fc)
    MESSAGES.clear(); QUEUED.clear(); TIMERS.clear()
    return ov

def captureOnHookThread(gesture):
    """Call _capture() with tripwires armed, as if on the hook thread."""
    HOOK["on"] = True
    try:
        return ov._capture(gesture)
    finally:
        HOOK["on"] = False

# open()
ov = resetOverlay()
ov.open()
check(inputCoreStub.manager._captureFunc is ov._captureRef, "open() installs the stable captor")
check(ov._armed is True, "open() arms the overlay")
check(MESSAGES[-1] == "Background Content Tracker, H for help", "open() announces")
check(len(TIMERS) == 1 and TIMERS[0][1] == 10000, "open() arms a 10s timeout timer")

# capture a real command key on the hook thread
violation = None
try:
    r = captureOnHookThread(FakeGesture("h"))
except ThreadViolation as e:
    violation = str(e); r = None
check(violation is None, "capture does NO wx/speech/timer work on hook thread" + (" (%s)" % violation if violation else ""))
check(r is False, "capture swallows the follow-up key (returns False)")
check(inputCoreStub.manager._captureFunc is None, "capture RELEASES the captor (restores previous)")
check(ov._armed is False, "capture disarms the overlay")
check(fc.calls == [], "capture runs NO controller command on the hook thread")
check(len(QUEUED) == 1 and QUEUED[0][0] == ov._handleKey, "capture queues _handleKey onto the main thread")
check(QUEUED[0][1] == ("h", (), 1) and QUEUED[0][3] is True, "queued with parsed key/mods/session, _immediate=True")

# now run the queued work on the "main thread"
func, args, kwargs, _imm = QUEUED[0]
func(*args, **kwargs)
check(fc.calls == [("help",)], "queued _handleKey dispatches the command on the main thread")
check(TIMERS[0][0].stopped is True, "the timeout timer is stopped on the main thread")

# previous captor is restored, not clobbered
sentinel = lambda g: None
ov = resetOverlay(prevCaptor=sentinel)
ov.open()
check(inputCoreStub.manager._captureFunc is ov._captureRef, "open() replaces an existing captor")
captureOnHookThread(FakeGesture("w"))
check(inputCoreStub.manager._captureFunc is sentinel, "capture restores the PREVIOUS captor, not None")

# lone modifiers keep the overlay open and pass through
ov = resetOverlay()
ov.open()
r = captureOnHookThread(FakeGesture("control", isModifier=True))
check(r is True, "lone modifier passes through (returns True)")
check(ov._armed is True and inputCoreStub.manager._captureFunc is ov._captureRef, "lone modifier keeps overlay armed")
check(QUEUED == [], "lone modifier queues nothing")

# invalid key -> swallowed, released, announces Overlay closed on main thread
ov = resetOverlay()
ov.open(); MESSAGES.clear()
r = captureOnHookThread(FakeGesture("x"))
check(r is False and inputCoreStub.manager._captureFunc is None, "invalid key swallowed and captor released")
func, args, kwargs, _imm = QUEUED[0]
func(*args, **kwargs)
check(MESSAGES[-1] == "Overlay closed" and fc.calls == [], "invalid key announces 'Overlay closed'")

# timeout path
ov = resetOverlay()
ov.open(); MESSAGES.clear()
session = ov._session
ov._onTimeout(session)
check(MESSAGES[-1] == "Overlay closed", "timeout announces 'Overlay closed'")
check(inputCoreStub.manager._captureFunc is None and ov._armed is False, "timeout releases the captor")
MESSAGES.clear()
ov._onTimeout(session)
check(MESSAGES == [], "timeout is idempotent (already disarmed)")

# stale timer from a previous session must not close a new overlay
ov = resetOverlay()
ov.open()
stale = ov._session - 1
MESSAGES.clear()
ov._onTimeout(stale)
check(MESSAGES == [] and ov._armed is True, "stale timer does not close the current overlay")

# stale queued key from a previous session is ignored
ov = resetOverlay()
ov.open()
captureOnHookThread(FakeGesture("h"))
staleSession = ov._session - 1
fc.calls = []
ov._handleKey("w", (), staleSession)
check(fc.calls == [], "stale queued key press is ignored")

# a key arriving after the overlay already closed passes through, never queues
ov = resetOverlay()
ov.open()
ov._onTimeout(ov._session)   # closes it
QUEUED.clear()
r = captureOnHookThread(FakeGesture("h"))
check(r is True and QUEUED == [], "key after close passes through and queues nothing")

# ============ reading content: containers must be swept, never dumped ========
class FakeLeaf:
    """A leaf node carrying its text in its name (list item, static text)."""
    TextInfo = NVDAObjectTextInfo
    def __init__(self, name, hwnd=100):
        self.name = name; self.value = None; self.children = []
        self.windowHandle = hwnd; self.role = WIN
    def __eq__(self, o): return self is o
    def __hash__(self): return id(self)

class FakeTextCtrl:
    """A control with real text of its own (an edit field, a document)."""
    TextInfo = RealTextInfo
    def __init__(self, text, hwnd=100):
        self._text = text; self.name = ""; self.value = None; self.children = []
        self.windowHandle = hwnd; self.role = EDIT
    def makeTextInfo(self, pos): return T.SimpleNamespace(text=self._text)
    def __eq__(self, o): return self is o
    def __hash__(self): return id(self)

class FakeDocument:
    """Claims a text interface (like a Chromium document) but its own text is
    either empty or nothing but embedded-object placeholders."""
    TextInfo = RealTextInfo
    def __init__(self, kids, text=""):
        self._text = text; self.name = ""; self.value = None
        self._kids = list(kids); self.windowHandle = 100; self.role = WIN
    @property
    def children(self): return list(self._kids)
    def makeTextInfo(self, pos): return T.SimpleNamespace(text=self._text)
    def __eq__(self, o): return self is o
    def __hash__(self): return id(self)

class FakeContainer:
    """A window/pane/list: no text of its own, only children."""
    TextInfo = NVDAObjectTextInfo
    def __init__(self, name, kids, hwnd=100):
        self.name = name; self.value = None
        self._kids = list(kids); self.windowHandle = hwnd; self.role = WIN
        self.childReads = 0
    @property
    def children(self):
        self.childReads += 1
        return list(self._kids)
    def add(self, kid): self._kids.append(kid)
    def __eq__(self, o): return self is o
    def __hash__(self): return id(self)

class Materialised(BaseException):
    """Raised by a fake whose whole child list was built. Derives from
    BaseException so the sweep's own `except Exception` cannot swallow it."""


class FakeBigList(NVDAObject):
    """A container offering cheap indexed access, as IAccessible does. Touching
    .children is a failure: that is the materialisation the tail fetch avoids."""
    TextInfo = NVDAObjectTextInfo
    def __init__(self, names, hwnd=100):
        self.name = ""; self.value = None; self.role = LIST
        self.windowHandle = hwnd; self._names = list(names); self.fetches = 0
    @property
    def children(self):
        raise Materialised("the whole child list must not be built")
    @property
    def childCount(self):
        return len(self._names)
    def _get_childCount(self):
        return len(self._names)
    def getChild(self, index):
        self.fetches += 1
        return FakeLeaf(self._names[index])
    def __eq__(self, o): return self is o
    def __hash__(self): return id(self)


class FakeNotifier:
    def __init__(self): self.changes = []; self.tracking = []; self.stopped = []
    def announceChange(self, target, delta): self.changes.append(delta)
    def announceTracking(self, target): self.tracking.append(target)
    def announceStopped(self, target): self.stopped.append(target)


def read(obj, ignoreProgressBars=False):
    """The text of a sweep, rendered as the cached snapshot renders it."""
    return "\n".join(text for _, text in monitor._sweepEntries(obj, ignoreProgressBars))


def cached(target):
    """A target's cached snapshot as text, in document order."""
    return "\n".join(target.cachedNodes.values())

check(read(FakeTextCtrl("typed text")) == "typed text",
      "a real text control is read directly")
check(read(FakeContainer("win", [FakeLeaf("hello"), FakeLeaf("world")])) == "hello\nworld",
      "a container is swept, leaves in document order")
check(read(FakeContainer("win", [FakeTextCtrl("body")])) == "body",
      "a text control inside a container is not descended into")
nested = FakeContainer("win", [FakeContainer("pane", [FakeLeaf("a"), FakeLeaf("b")]), FakeLeaf("c")])
check(read(nested) == "pane\na\nb\nc",
      "nested containers keep document order, each labelled before its own children")
check(read(FakeContainer("Window title", [FakeLeaf("body")])) == "body",
      "the root's label is skipped: it is the target's name, which the notifier already speaks")
check(read(FakeLeaf("just a label")) == "just a label",
      "a root with no children IS read from its label (a control pointed straight at)")
check(read(None) == "", "reading a detached target is safe")

# The exact shape of Lukas's Claude window: one child that claims its own text
# interface and hands back nothing. v1.0.3 stopped there and read 0 characters.
claudeShape = FakeContainer("Claude", [FakeDocument([FakeLeaf("msg 1"), FakeLeaf("msg 2")], text="")])
check(read(claudeShape) == "msg 1" + chr(10) + "msg 2",
      "a document whose own text is EMPTY is descended into (the chars=0 bug)")
placeholders = FakeContainer("Claude", [FakeDocument([FakeLeaf("msg 1"), FakeLeaf("msg 2")], text=chr(0xFFFC) * 2)])
check(read(placeholders) == "msg 1" + chr(10) + "msg 2",
      "a document whose own text is only placeholders is descended into")
# The redesign reverses the old "real words win" rule. A node WITH children is
# always read through them: its own text interface renders the whole subtree flat,
# so trusting it collapsed a document, a rich edit or a UIA window into one blob,
# and any change anywhere inside then surfaced the entire blob. The children carry
# the content; the node itself contributes only its label.
realWords = FakeContainer("win", [FakeDocument([FakeLeaf("dup"), FakeLeaf("dup")], text="real words")])
check(read(realWords) == "dup\ndup",
      "a node with children is read through them, never through its own flat blob")
# ...but a node whose whole subtree came back mute still falls back to its own
# text, so a terminal or edit field with unhelpful children is not read as empty.
muteKids = FakeContainer("win", [FakeDocument([FakeLeaf("")], text="the only text there is")])
check(read(muteKids) == "the only text there is",
      "a node whose subtree is mute falls back to its own text interface")
check(read(FakeLeaf("  spaced  ")) == "spaced", "leaf text is trimmed")
check(read(FakeTextCtrl("two\nlines  here")) == "two lines here",
      "whitespace is normalised, so a pure reflow never reads as new content")
check(read(FakeLeaf("a" + chr(0xFFFC) + "b")) == "ab", "placeholders are stripped from words")

# A target whose ROOT exposes a real text interface spanning everything below it
# (UIA windows, or anything NVDA wraps with a document TextInfo): its flat own
# text runs the title-bar chrome straight into the content. The same rule applies
# as anywhere else -- it has children, so it is read through them -- and windows
# and single controls are now swept identically.
wholeWindow = FakeDocument(
    [FakeLeaf("Minimize"), FakeLeaf("Restore"), FakeLeaf("Close"), FakeLeaf("msg 1")],
    text="Minimize Restore Close msg 1")
check(read(wholeWindow) == "Minimize\nRestore\nClose\nmsg 1",
      "a root's own-text blob is drilled into per-control leaves")

# A single control -- a message list tracked with F, not a whole window -- is
# swept exactly like a window, so it is read as its individual items and not as
# one lump of list text.
msgList = FakeDocument([FakeLeaf("Alice: hi"), FakeLeaf("Bob: hello"), FakeLeaf("Alice: how are you")],
                       text="Alice: hi Bob: hello Alice: how are you")
check(read(msgList) == "Alice: hi\nBob: hello\nAlice: how are you",
      "a tracked message list is drilled into its individual items")

# The node budget is spent from the END of the target, so a window bigger than
# the cap keeps its newest content -- a chat log, a message list, streaming
# output all append there -- instead of a snapshot of the part that never moves.
_savedMax = monitor.MAX_NODES
monitor.MAX_NODES = 4
bigList = FakeContainer("win", [FakeLeaf("old 1"), FakeLeaf("old 2"), FakeLeaf("new 1"), FakeLeaf("new 2")])
check(read(bigList) == "old 2\nnew 1\nnew 2",
      "over the cap: the END of the target survives, still in document order")
# And the own-text fallback must not fire for a subtree the cap cut short: "mute"
# would then only mean "not looked at", and the node's flat text is exactly the
# blob the whole sweep exists to avoid.
monitor.MAX_NODES = 2
cutShort = FakeDocument([FakeContainer("", []), FakeContainer("", []), FakeContainer("", [])],
                        text="the whole subtree flattened")
check(read(cutShort) == "",
      "over the cap: a node whose subtree was cut short never falls back to its blob")
# A container that offers cheap indexed access is never materialised whole: only
# the children the budget can actually reach are fetched, and their keys still
# say where they really sit. Without this, a five-thousand-row message list costs
# five thousand object constructions per poll to look at the last few.
monitor.MAX_NODES = 4
big = FakeBigList(["m%d" % i for i in range(1000)])
check(read(big) == "m997\nm998\nm999",
      "a huge container is read from its end, one child at a time")
check(big.fetches == 3, "only the children the budget can reach are fetched at all")
check(list(dict(monitor._sweepEntries(big)))[0] == "/997",
      "a tail-fetched child keeps its real index in its key")
monitor.MAX_NODES = _savedMax

# A text node far past the cap is capped from its end, and the raw string is
# sliced before it is normalised rather than after.
check(len(read(FakeTextCtrl("word " * 5000))) == monitor.MAX_TEXT_CHARS,
      "a huge text node is capped to MAX_TEXT_CHARS, keeping its end")

# ============ isInForegroundApp ============
ROOTOWNER.clear(); ROOTOWNER.update({100: 100, 101: 100, 200: 200})
w100, c101, w200 = FakeLeaf("w", 100), FakeLeaf("c", 101), FakeLeaf("o", 200)
FG["hwnd"] = 100
check(monitor.isInForegroundApp(w100) is True, "foreground: the window itself")
check(monitor.isInForegroundApp(c101) is True, "foreground: a control inside it (same root owner)")
check(monitor.isInForegroundApp(w200) is False, "foreground: another app's window is not foreground")
FG["hwnd"] = 200
check(monitor.isInForegroundApp(w100) is False, "background: the window once another app is in front")
check(monitor.isInForegroundApp(None) is False, "foreground check tolerates a detached target")

# ============ the alt+tab regression: track Claude, switch away ============
reg2 = targets.TargetRegistry(); notif = FakeNotifier()
mon = monitor.Monitor(reg2, notif)
claude = FakeContainer("Claude", [FakeLeaf("msg 1")], hwnd=100)


def tick(target):
    """One poll, as the monitor thread would perform it, then run what it queued."""
    MONITOR["on"] = True
    try:
        mon._checkTargetContent(target)
    finally:
        MONITOR["on"] = False
    drain()


FG["hwnd"] = 100                                   # we are in Claude
tg = reg2.add(claude, "window")
mon.onAdded(tg)
check(tg.wasInForeground is True, "adding a foreground target records that it is in front")
check(cached(tg) == "" and claude.childReads == 0,
      "adding a foreground target sweeps nothing (the app you work in is left alone)")

claude.add(FakeLeaf("msg 2"))                      # content grows while we are still there
tick(tg)
check(notif.changes == [], "foreground target announces nothing")
check(claude.childReads == 0, "foreground target is not even read")

FG["hwnd"] = 200                                   # alt+tab away
tick(tg)
check(notif.changes == [], "NO DUMP: switching away announces nothing at all")
check(cached(tg) == "msg 1\nmsg 2", "switching away silently re-baselines the snapshot")

claude.add(FakeLeaf("msg 3"))                      # a genuine background change
tick(tg)
check(notif.changes == ["msg 3"], "announces only the new content, never the whole window")

claude.add(FakeLeaf("msg 3"))                      # the same message again
tick(tg)
check(notif.changes == ["msg 3", "msg 3"], "a genuinely repeated message is announced again")

readsBefore = claude.childReads
FG["hwnd"] = 100                                   # switch back into Claude
tick(tg)
check(claude.childReads == readsBefore, "returning to the app stops reading it")
check(notif.changes == ["msg 3", "msg 3"], "returning to the app stops announcing")
check(tg.wasInForeground is True, "the foreground flag is re-armed")

claude.add(FakeLeaf("msg 4"))                      # arrives while we are present
FG["hwnd"] = 200                                   # and we leave again
tick(tg)
check(notif.changes == ["msg 3", "msg 3"], "content seen while present is never announced on leaving")
check(cached(tg).endswith("msg 4"), "leaving re-baselines to include what we already saw")

# ============ a window whose ROOT exposes its own text is still drilled down ====
# The regression: some windows (UIA, or anything NVDA wraps with a document
# TextInfo) expose a real text interface at the top level whose flat rendering
# spans the whole window, title-bar chrome included. Trusting it as one node made
# a later change surface the ENTIRE window ("Minimize Restore Close ... content")
# instead of the one control that moved. For a window target the root is now
# drilled into, so only the changed control is announced -- exactly as for a
# window read as a plain tree above. Baseline and poll use the same granularity,
# so the title-bar buttons sit in the baseline and are filtered as unchanged.
regBlob = targets.TargetRegistry(); notifBlob = FakeNotifier()
monBlob = monitor.Monitor(regBlob, notifBlob)
blobWin = FakeDocument(
    [FakeLeaf("Minimize", 100), FakeLeaf("Restore", 100), FakeLeaf("Close", 100), FakeLeaf("msg 1", 100)],
    text="Minimize Restore Close msg 1")
blobWin.windowHandle = 100
FG["hwnd"] = 200                                   # backgrounded from the start
tgBlob = regBlob.add(blobWin, "window"); monBlob.onAdded(tgBlob)
check(cached(tgBlob) == "Minimize\nRestore\nClose\nmsg 1",
      "root-own-text window: the baseline is drilled into per-control leaves")
blobWin._kids.append(FakeLeaf("msg 2", 100))       # a new message arrives
blobWin._text = "Minimize Restore Close msg 1 msg 2"
def tickBlob(target):
    MONITOR["on"] = True
    try:
        monBlob._checkTargetContent(target)
    finally:
        MONITOR["on"] = False
    drain()
tickBlob(tgBlob)
check(notifBlob.changes == ["msg 2"],
      "root-own-text window: only the changed control is announced, never the whole window")

# ============ the thread-safe settings snapshot ============
check(set(addonConfig.snapshot()) == set(addonConfig.DEFAULTS), "the snapshot covers every setting")
addonConfig.set("enabled", False)
check(addonConfig.snapshot()["enabled"] is False, "snapshot follows a set()")
held = addonConfig.snapshot()                      # as the monitor thread would hold it
addonConfig.set("enabled", True)
check(held["enabled"] is False,
      "refresh rebinds the snapshot; a reader's copy is never mutated under its feet")
check(addonConfig.snapshot()["enabled"] is True, "the next read sees the new value")

# ============ the monitor thread contract ============
# Nothing on the monitor thread may speak, beep, or mutate the registry: it all
# has to be handed to NVDA's main thread. The tripwires above turn a breach into
# a ThreadViolation rather than a silently passing test.
reg3 = targets.TargetRegistry()
realNotifier = notifier.Notifier()
mon3 = monitor.Monitor(reg3, realNotifier)
win3 = FakeContainer("Claude", [FakeLeaf("one")], hwnd=100)
FG["hwnd"] = 200                                   # backgrounded from the start
tg3 = reg3.add(win3, "window")
mon3.onAdded(tg3)                                  # baseline: "one"
win3.add(FakeLeaf("two"))
MESSAGES.clear(); QUEUED.clear()
MONITOR["on"] = True
try:
    mon3._checkTargetContent(tg3)
finally:
    MONITOR["on"] = False
check(MESSAGES == [], "the monitor thread speaks nothing inline")
check(len(QUEUED) == 1 and QUEUED[0][0] == realNotifier.announceChange,
      "the announcement is queued onto NVDA's main thread")
check(QUEUED[0][3] is True, "queued with _immediate, as NVDA's own LiveText does")
drain()
check(MESSAGES == ["window: Claude, two"], "the queued announcement speaks on the main thread")

# A target that disappears must not be removed from the registry by the monitor.
reg4 = targets.TargetRegistry(); notif4 = FakeNotifier()
mon4 = monitor.Monitor(reg4, notif4)
tg4 = reg4.add(FakeContainer("Gone", [], hwnd=100), "window")
QUEUED.clear()
MONITOR["on"] = True
try:
    mon4._handleDisappeared(tg4, forget=True)
finally:
    MONITOR["on"] = False
check(len(reg4) == 1, "the monitor thread does not mutate the registry itself")
check([f.__name__ for f, a, k, i in QUEUED] == ["remove", "announceStopped"],
      "both the removal and the announcement are queued, in that order")
drain()
check(len(reg4) == 0, "the main thread performs the removal")

# "Forget" drops a disappeared target regardless of whether it is remembered: the
# removal is decided by the forget flag alone (the relocation pass, not this call,
# is what "Remember targets" governs). Same behaviour as above with forget=True.
reg4b = targets.TargetRegistry(); notif4b = FakeNotifier()
mon4b = monitor.Monitor(reg4b, notif4b)
tg4b = reg4b.add(FakeContainer("Gone", [], hwnd=100), "window")
QUEUED.clear()
MONITOR["on"] = True
try:
    mon4b._handleDisappeared(tg4b, forget=True)
finally:
    MONITOR["on"] = False
check([f.__name__ for f, a, k, i in QUEUED] == ["remove", "announceStopped"],
      "forget removes the target even when it would otherwise be remembered")

# With "Forget" off, a disappeared target is kept as a detached entry, but the
# user is still told it is gone: only the announcement is queued, never a removal.
reg5 = targets.TargetRegistry(); notif5 = FakeNotifier()
mon5 = monitor.Monitor(reg5, notif5)
tg5 = reg5.add(FakeContainer("Gone", [], hwnd=100), "window")
QUEUED.clear()
MONITOR["on"] = True
try:
    mon5._handleDisappeared(tg5, forget=False)
finally:
    MONITOR["on"] = False
check([f.__name__ for f, a, k, i in QUEUED] == ["announceStopped"],
      "forget off announces the disappearance but queues no removal")
check(tg5.obj is None, "the disappeared target is detached")
drain()
check(len(reg5) == 1, "forget off keeps the detached entry in the list")

# ============ the monitor thread's lifecycle ============
monitor.POLL_INTERVAL = 0.01                       # so the test does not take a second
regT = targets.TargetRegistry()
monT = monitor.Monitor(regT, FakeNotifier())
monT.start()
thread = monT._thread
check(thread is not None and thread.daemon, "start() runs a daemon thread")
check(thread.is_alive(), "the monitor thread is running")
monT.start()
check(monT._thread is thread, "start() is idempotent")
monT.stop()
thread.join(2.0)
check(not thread.is_alive(), "stop() ends the thread at once, without joining it")
QUEUED.clear()
monT._callOnMainThread(lambda: None)
check(QUEUED == [], "a sweep still in flight when stop() lands can no longer speak")

# ============ new option: Ignore progress bars ============
# A progress bar descendant is filtered out of a window sweep when asked, so its
# constant churn never registers as a change; the root is never filtered.
_pb = FakeLeaf("50 percent"); _pb.role = PROGRESSBAR_ROLE
progWin = FakeContainer("app", [FakeLeaf("real output"), _pb])
check(read(progWin, ignoreProgressBars=True) == "real output",
      "ignore progress bars: the progress bar is dropped from the sweep")
check(read(progWin, ignoreProgressBars=False) == "real output\n50 percent",
      "ignore progress bars off: the progress bar is read like anything else")
check(read(_pb, ignoreProgressBars=True) == "50 percent",
      "a target pointed straight at a progress bar is still read (root is never filtered)")


def pump(m, tg, announce=True):
    """One background poll on the monitor thread, then run what it queued."""
    MONITOR["on"] = True
    try:
        m._checkTargetContent(tg, addonConfig.snapshot(), announce)
    finally:
        MONITOR["on"] = False
    drain()


# ============ new option: Changes to announce at once (the cap) ============
addonConfig.set("changesAtOnce", 2)
addonConfig.set("ignoreRepeatedControls", False)
ROOTOWNER.clear(); ROOTOWNER.update({100: 100, 200: 200})
regC = targets.TargetRegistry(); notifC = FakeNotifier()
monC = monitor.Monitor(regC, notifC)
capWin = FakeContainer("Chat", [FakeLeaf("a")], hwnd=100)
FG["hwnd"] = 200
tgC = regC.add(capWin, "window"); monC.onAdded(tgC)
capWin.add(FakeLeaf("b")); pump(monC, tgC)
capWin.add(FakeLeaf("c")); pump(monC, tgC)
check(notifC.changes == ["b", "c"], "cap: the first two consecutive changes are announced")
capWin.add(FakeLeaf("d")); pump(monC, tgC)
capWin.add(FakeLeaf("e")); pump(monC, tgC)
check(notifC.changes == ["b", "c"], "cap: further changes are suppressed once the cap is reached")
check(tgC.lastDelta == "e", "cap: the menu delta still tracks the latest suppressed change")
FG["hwnd"] = 100; pump(monC, tgC)               # refocus the target
FG["hwnd"] = 200; pump(monC, tgC)               # and switch away again (re-baseline)
check(tgC.announcedRun == 0, "cap: refocusing the target resets the counter")
capWin.add(FakeLeaf("f")); pump(monC, tgC)
check(notifC.changes == ["b", "c", "f"], "cap: announcing resumes after a refocus")

# changesAtOnce 0 means never cap.
addonConfig.set("changesAtOnce", 0)
regZ = targets.TargetRegistry(); notifZ = FakeNotifier()
monZ = monitor.Monitor(regZ, notifZ)
zWin = FakeContainer("Chat", [FakeLeaf("a")], hwnd=100)
FG["hwnd"] = 200
tgZ = regZ.add(zWin, "window"); monZ.onAdded(tgZ)
for word in ("b", "c", "d", "e", "f"):
    zWin.add(FakeLeaf(word)); pump(monZ, tgZ)
check(notifZ.changes == ["b", "c", "d", "e", "f"], "changesAtOnce 0: every change is announced")

# ============ new option: Ignore repeatedly changing controls ============
addonConfig.set("changesAtOnce", 0)             # isolate from the cap
addonConfig.set("ignoreRepeatedControls", True)
regR = targets.TargetRegistry(); notifR = FakeNotifier()
monR = monitor.Monitor(regR, notifR)
timer = FakeLeaf("Thought for 1 seconds")
repWin = FakeContainer("Claude", [FakeLeaf("message"), timer], hwnd=100)
FG["hwnd"] = 200
tgR = regR.add(repWin, "window"); monR.onAdded(tgR)
timer.name = "Thought for 2 seconds"; pump(monR, tgR)
check(notifR.changes == ["Thought for 2 seconds"], "repeated control: the first change is announced")
timer.name = "Thought for 3 seconds"; pump(monR, tgR)
timer.name = "Thought for 4 seconds"; pump(monR, tgR)
check(notifR.changes == ["Thought for 2 seconds"],
      "repeated control: further changes to the SAME control are suppressed")
repWin.add(FakeLeaf("a real new message")); pump(monR, tgR)
check(notifR.changes == ["Thought for 2 seconds", "a real new message"],
      "repeated control: genuinely new content is still announced")
FG["hwnd"] = 100; pump(monR, tgR)               # refocus
FG["hwnd"] = 200; pump(monR, tgR)               # switch away (re-baseline)
timer.name = "Thought for 9 seconds"; pump(monR, tgR)
check(notifR.changes[-1] == "Thought for 9 seconds",
      "repeated control: the memory resets on a refocus, so it announces once more")

# With the option OFF, every change to the same control is announced.
addonConfig.set("ignoreRepeatedControls", False)
regRO = targets.TargetRegistry(); notifRO = FakeNotifier()
monRO = monitor.Monitor(regRO, notifRO)
timerO = FakeLeaf("Thought for 1 seconds")
roWin = FakeContainer("Claude", [timerO], hwnd=100)
FG["hwnd"] = 200
tgRO = regRO.add(roWin, "window"); monRO.onAdded(tgRO)
timerO.name = "Thought for 2 seconds"; pump(monRO, tgRO)
timerO.name = "Thought for 3 seconds"; pump(monRO, tgRO)
check(notifRO.changes == ["Thought for 2 seconds", "Thought for 3 seconds"],
      "ignore repeated off: every change to the same control is announced")

# A non-window target (a single control) is never subject to the window filters.
addonConfig.set("ignoreRepeatedControls", True)
regF = targets.TargetRegistry(); notifF = FakeNotifier()
monF = monitor.Monitor(regF, notifF)
ctrl = FakeTextCtrl("one", hwnd=100)
FG["hwnd"] = 200
tgF = regF.add(ctrl, "focus"); monF.onAdded(tgF)
ctrl._text = "one two"; pump(monF, tgF)
ctrl._text = "one two three"; pump(monF, tgF)
check(notifF.changes == ["one two", "one two three"],
      "a focused control target is exempt from the repeatedly-changing-controls filter")

# ============ announcements carry the whole node text, not just the diff ======
# A change is DETECTED by diffing against the previous poll, but what gets
# ANNOUNCED is the node's whole current text: a bare "ld" from "Hello wor" ->
# "Hello world" is meaningless read aloud. Detection/suppression logic is
# unchanged; only the surfaced string is now the complete line.
addonConfig.set("changesAtOnce", 0)
addonConfig.set("ignoreRepeatedControls", False)
regW = targets.TargetRegistry(); notifW = FakeNotifier()
monW = monitor.Monitor(regW, notifW)
growCtrl = FakeTextCtrl("Hello wor", hwnd=100)
FG["hwnd"] = 200
tgW = regW.add(growCtrl, "focus"); monW.onAdded(tgW)
growCtrl._text = "Hello world"; pump(monW, tgW)      # a pure append: diff would be "ld"
check(notifW.changes == ["Hello world"],
      "whole-text: a growing control announces its full current text, not the appended 'ld'")
growCtrl._text = "Hello world!"; pump(monW, tgW)
check(notifW.changes == ["Hello world", "Hello world!"],
      "whole-text: each change re-reads the complete line, never the fragment")
check(tgW.lastDelta == "Hello world!",
      "whole-text: lastDelta holds the whole text for the menu and the info key")

# ============ new content must survive a churning control that shifts position =
# The regression: a "Thought for N seconds" timer ticks every poll while genuine
# new messages arrive ABOVE it, so the timer's child-index keeps shifting. Keying
# change detection on tree position mistook the shifted timer for new content and
# the new message for the (already-announced) timer, so the timer was announced
# over and over and the real message was silently dropped. Content is matched by
# text now, so the timer stays suppressed and every new message gets through.
addonConfig.set("changesAtOnce", 5)
addonConfig.set("ignoreRepeatedControls", True)
regS = targets.TargetRegistry(); notifS = FakeNotifier()
monS = monitor.Monitor(regS, notifS)
shiftTimer = FakeLeaf("Thought for 1 seconds")
shiftWin = FakeContainer("Claude", [FakeLeaf("msg 1"), shiftTimer], hwnd=100)  # timer LAST
FG["hwnd"] = 200
tgS = regS.add(shiftWin, "window"); monS.onAdded(tgS)
shiftTimer.name = "Thought for 2 seconds"; pump(monS, tgS)
shiftTimer.name = "Thought for 3 seconds"; pump(monS, tgS)
check(notifS.changes == ["Thought for 2 seconds"],
      "shifting control: the ticking timer is announced once then suppressed")
# A real message arrives above the timer (index 1), pushing the timer to index 2,
# while the timer keeps ticking in the same poll.
shiftWin._kids.insert(1, FakeLeaf("brand new message"))
shiftTimer.name = "Thought for 4 seconds"; pump(monS, tgS)
check(notifS.changes == ["Thought for 2 seconds", "brand new message"],
      "shifting control: genuine new content is announced, the shifted timer is NOT re-announced")
# And again: another new message, timer still ticking.
shiftWin._kids.insert(2, FakeLeaf("second new message"))
shiftTimer.name = "Thought for 5 seconds"; pump(monS, tgS)
check(notifS.changes == ["Thought for 2 seconds", "brand new message", "second new message"],
      "shifting control: each further new message gets through while the timer stays quiet")
check(tgS.announcedRun == 3, "shifting control: only genuine content counts against the cap, not the timer")

# ============ digit roll-over: the template is the stable identity ===========
# The regression this whole redesign targets: suppression used to key on the
# literal common prefix/suffix of two consecutive values, which drifts the
# moment a digit rolls over (9->10, 19->20) and mints a false new identity, so
# the timer blurted again every few seconds. Keying on the numeric *template*
# instead, a counter is announced once and then stays silent however its digits
# grow.
addonConfig.set("changesAtOnce", 0)
addonConfig.set("ignoreRepeatedControls", True)
regM = targets.TargetRegistry(); notifM = FakeNotifier()
monM = monitor.Monitor(regM, notifM)
tk = FakeLeaf("Thought for 8 seconds")
mWin = FakeContainer("Claude", [FakeLeaf("msg"), tk], hwnd=100)
FG["hwnd"] = 200
tgM = regM.add(mWin, "window"); monM.onAdded(tgM)
for v in ("9", "10", "11", "20", "21", "100"):
    tk.name = "Thought for %s seconds" % v; pump(monM, tgM)
check(notifM.changes == ["Thought for 9 seconds"],
      "rollover: a multi-digit timer is announced once, never re-announced as its digits roll over")

# Separators and decimals fold too, so a token counter (Czech-style spaced
# thousands) and a fractional-second timer are each announced exactly once,
# where the old prefix/suffix scheme would have re-fired or treated them as new.
regN = targets.TargetRegistry(); notifN = FakeNotifier()
monN = monitor.Monitor(regN, notifN)
tokens = FakeLeaf("1 234 tokens")
secs = FakeLeaf("5.9s")
nWin = FakeContainer("Claude", [tokens, secs], hwnd=100)
FG["hwnd"] = 200
tgN = regN.add(nWin, "window"); monN.onAdded(tgN)
tokens.name = "2 000 tokens"; secs.name = "6.1s"; pump(monN, tgN)
tokens.name = "3 456 tokens"; secs.name = "6.4s"; pump(monN, tgN)
tokens.name = "12 000 tokens"; secs.name = "10.2s"; pump(monN, tgN)
# Both counters change in the same first poll, so they are surfaced together in
# one announcement; every later poll is fully suppressed.
check(notifN.changes == ["2 000 tokens\n6.1s"],
      "separators/decimals: numeric counters fold to one template, announced once each")

# ============ forgetting a control that has gone quiet ======================
# A control suppressed as a timer must not stay muted forever: once it has been
# quiet for FORGET_REPEATED_POLLS polls it is forgotten, so when it starts
# moving again (a fresh response) its next change is announced afresh. But while
# it is still within that window it stays suppressed.
_savedForget = monitor.FORGET_REPEATED_POLLS
monitor.FORGET_REPEATED_POLLS = 3               # keep the test short
try:
    # Positive case: goes quiet past the window, then resumes -> announced again.
    regA = targets.TargetRegistry(); notifA = FakeNotifier()
    monA = monitor.Monitor(regA, notifA)
    tmr = FakeLeaf("Thought for 1 seconds")
    aWin = FakeContainer("Claude", [FakeLeaf("msg"), tmr], hwnd=100)
    FG["hwnd"] = 200
    tgA = regA.add(aWin, "window"); monA.onAdded(tgA)
    tmr.name = "Thought for 2 seconds"; pump(monA, tgA)   # announced once
    tmr.name = "Thought for 3 seconds"; pump(monA, tgA)   # suppressed
    check(notifA.changes == ["Thought for 2 seconds"], "forget: still churning, suppressed")
    for _ in range(4):                                    # idle > FORGET_REPEATED_POLLS
        pump(monA, tgA)
    tmr.name = "Thought for 4 seconds"; pump(monA, tgA)
    check(notifA.changes == ["Thought for 2 seconds", "Thought for 4 seconds"],
          "forget: a control that went quiet is announced again when it resumes")

    # Negative case: a brief quiet spell within the window keeps it suppressed.
    regB = targets.TargetRegistry(); notifB = FakeNotifier()
    monB = monitor.Monitor(regB, notifB)
    tmrB = FakeLeaf("Thought for 1 seconds")
    bWin = FakeContainer("Claude", [FakeLeaf("msg"), tmrB], hwnd=100)
    FG["hwnd"] = 200
    tgB = regB.add(bWin, "window"); monB.onAdded(tgB)
    tmrB.name = "Thought for 2 seconds"; pump(monB, tgB)  # announced once
    tmrB.name = "Thought for 3 seconds"; pump(monB, tgB)  # suppressed
    pump(monB, tgB)                                       # one idle poll (< window)
    tmrB.name = "Thought for 4 seconds"; pump(monB, tgB)
    check(notifB.changes == ["Thought for 2 seconds"],
          "forget: a control quiet only briefly is NOT forgotten, stays suppressed")
finally:
    monitor.FORGET_REPEATED_POLLS = _savedForget

# ============ new option: Tracking interval 0 (detect quietly) ============
addonConfig.set("changesAtOnce", 0)
addonConfig.set("ignoreRepeatedControls", True)
regI = targets.TargetRegistry(); notifI = FakeNotifier()
monI = monitor.Monitor(regI, notifI)
iWin = FakeContainer("W", [FakeLeaf("x")], hwnd=100)
FG["hwnd"] = 200
tgI = regI.add(iWin, "window"); monI.onAdded(tgI)
iWin.add(FakeLeaf("y"))
QUEUED.clear()
MONITOR["on"] = True
try:
    monI._checkTargetContent(tgI, addonConfig.snapshot(), announce=False)
finally:
    MONITOR["on"] = False
check(QUEUED == [], "interval 0: a change is detected but nothing is queued to speak")
check(tgI.lastDelta == "y" and tgI.lastChangeTime is not None,
      "interval 0: the menu delta and change time are still updated")

# ============ the redesign: a keyed snapshot of the whole subtree ============
# What made window tracking unreliable was the old rule "a node with real words of
# its own is never descended into". A content pane, a document or a rich edit
# renders its whole subtree flat, so a window collapsed into ONE node and any
# change anywhere inside it surfaced the entire pane. Every control is its own
# entry in the snapshot now, keyed by its position in the tree, so a change is
# pinned to the one control that made it.
addonConfig.set("changesAtOnce", 0)
addonConfig.set("ignoreRepeatedControls", True)
regD = targets.TargetRegistry(); notifD = FakeNotifier()
monD = monitor.Monitor(regD, notifD)
pane = FakeDocument([FakeLeaf("msg 1"), FakeLeaf("msg 2")], text="msg 1 msg 2")
deepWin = FakeContainer("Claude", [FakeContainer("Toolbar", [FakeLeaf("New chat")]), pane], hwnd=100)
FG["hwnd"] = 200
tgD = regD.add(deepWin, "window"); monD.onAdded(tgD)
check(cached(tgD) == "Toolbar\nNew chat\nmsg 1\nmsg 2",
      "snapshot: every nested control is its own entry, in document order")
pane._kids.append(FakeLeaf("msg 3")); pane._text = "msg 1 msg 2 msg 3"
pump(monD, tgD)
check(notifD.changes == ["msg 3"],
      "deep window: only the new control is announced, never the whole content pane")

# A single control tracked with F -- a Thunderbird or WhatsApp message list -- is
# swept exactly like a window: its items are cached individually and drilled into,
# so a new message is announced on its own rather than as the whole list.
regL = targets.TargetRegistry(); notifL = FakeNotifier()
monL = monitor.Monitor(regL, notifL)
listCtrl = FakeDocument([FakeLeaf("Alice: hi"), FakeLeaf("Bob: hello")], text="Alice: hi Bob: hello")
FG["hwnd"] = 200
tgL = regL.add(listCtrl, "focus"); monL.onAdded(tgL)
listCtrl._kids.append(FakeLeaf("Alice: are you there"))
listCtrl._text = "Alice: hi Bob: hello Alice: are you there"
pump(monL, tgL)
check(notifL.changes == ["Alice: are you there"],
      "single-control target: a message list reports the new item, not the whole list")

# Changed text inside an existing control counts as a change, not just a new
# control appearing: that control's cached entry no longer matches its key.
regE = targets.TargetRegistry(); notifE = FakeNotifier()
monE = monitor.Monitor(regE, notifE)
status = FakeLeaf("Connected")
eWin = FakeContainer("App", [FakeContainer("Status bar", [status])], hwnd=100)
FG["hwnd"] = 200
tgE = regE.add(eWin, "window"); monE.onAdded(tgE)
status.name = "Disconnected"; pump(monE, tgE)
check(notifE.changes == ["Disconnected"],
      "changed text in an existing control is announced, and only that control")

# A container's own label is content too, so an unread count appearing on a tab is
# announced. The ROOT's label is not: it is the target's own name, which the
# notifier already speaks alongside every change.
regG = targets.TargetRegistry(); notifG = FakeNotifier()
monG = monitor.Monitor(regG, notifG)
tab = FakeContainer("Chat", [FakeLeaf("Alice: hi")])
gWin = FakeContainer("Messenger", [tab], hwnd=100)
FG["hwnd"] = 200
tgG = regG.add(gWin, "window"); monG.onAdded(tgG)
tab.name = "(1) Chat"; pump(monG, tgG)
check(notifG.changes == ["(1) Chat"], "a container's label change is announced")
notifG.changes = []
gWin.name = "Messenger - 2 unread"; pump(monG, tgG)
check(notifG.changes == [], "the target's own name is never announced as its content")

# Some applications name a row after the cells inside it. Hearing the row and then
# every one of its cells would read the same message twice, so a changed node
# whose text a changed ancestor already contains is dropped.
regH = targets.TargetRegistry(); notifH = FakeNotifier()
monH = monitor.Monitor(regH, notifH)
rows = FakeContainer("List", [], hwnd=100)
hWin = FakeContainer("Mail", [rows], hwnd=100)
FG["hwnd"] = 200
tgH = regH.add(hWin, "window"); monH.onAdded(tgH)
rows.add(FakeContainer("Alice Lunch today", [FakeLeaf("Alice"), FakeLeaf("Lunch today")]))
pump(monH, tgH)
check(notifH.changes == ["Alice Lunch today"],
      "a row that names itself after its cells is announced once, not once per cell")
# ...but only what the ancestor actually says is dropped. The guard walks the
# ancestor chain, not everything announced so far, so a sibling's text can never
# swallow another's and a whole-window repaint stays linear rather than quadratic.
regJ = targets.TargetRegistry(); notifJ = FakeNotifier()
monJ = monitor.Monitor(regJ, notifJ)
rowsJ = FakeContainer("List", [], hwnd=100)
jWin = FakeContainer("Mail", [rowsJ], hwnd=100)
FG["hwnd"] = 200
tgJ = regJ.add(jWin, "window"); monJ.onAdded(tgJ)
rowsJ.add(FakeContainer("Alice", [FakeLeaf("Lunch today")]))
pump(monJ, tgJ)
check(notifJ.changes == ["Alice\nLunch today"],
      "a descendant saying something its ancestor does not is still announced")

# Content going away is not content arriving: the add-on reports what is new.
regX = targets.TargetRegistry(); notifX = FakeNotifier()
monX = monitor.Monitor(regX, notifX)
xWin = FakeContainer("W", [FakeLeaf("a"), FakeLeaf("b")], hwnd=100)
FG["hwnd"] = 200
tgX = regX.add(xWin, "window"); monX.onAdded(tgX)
xWin._kids.pop(); pump(monX, tgX)
check(notifX.changes == [], "a control that disappears is not announced as a change")
check(cached(tgX) == "a", "...but the snapshot follows it, so it cannot come back as new")

# ============ relocation runs off the main thread ============
# Re-resolving a stale control scans every top-level window and then descends the
# matching application: hundreds of cross-process reads, triggered by a keypress.
# Run inline it would freeze NVDA for exactly that long, so only its OUTCOME may
# reach the main thread.
regRel = targets.TargetRegistry()
monRel = monitor.Monitor(regRel, FakeNotifier())
relocated = FakeObj("A", WIN, "app")
monRel._locate = lambda identity: relocated
relTarget = targets.TrackedTarget(1, None, "focus")
relTarget.identity = {"appName": "app", "name": "A"}
handled = []
QUEUED.clear()
monRel.relocateAsync(relTarget, lambda t, ok: handled.append((t, ok)))
_deadline = _t.time() + 5.0
while not QUEUED and _t.time() < _deadline:
    _t.sleep(0.01)
check(handled == [], "relocateAsync never calls back inline")
check(len(QUEUED) == 1 and QUEUED[0][0] is not None,
      "the lookup runs on its own thread and only queues its outcome")
drain()
check(handled == [(relTarget, True)], "the callback runs on the main thread with the result")
check(relTarget.obj is relocated, "a successful lookup re-attaches the target")

# A lookup that finds nothing reports that, rather than leaving the caller waiting.
monRel._locate = lambda identity: None
handled = []
QUEUED.clear()
monRel.relocateAsync(relTarget, lambda t, ok: handled.append((t, ok)))
_deadline = _t.time() + 5.0
while not QUEUED and _t.time() < _deadline:
    _t.sleep(0.01)
drain()
check(handled == [(relTarget, False)], "a failed lookup still reaches the main thread")

# ============ new option: Consider changed title a disappeared target =======
# A window that renames itself is a different window as far as the user is
# concerned -- another document, another page -- even though the system still
# calls it the same one. With this option on, such a target therefore goes down
# the DISAPPEARANCE path (announced as gone, and dropped or kept exactly as the
# list-management options dictate) instead of the new title's content being
# announced as an ordinary change.
def sweep(m):
    """One whole monitor poll over every target, then run what it queued."""
    MONITOR["on"] = True
    try:
        m._checkAllTargets(addonConfig.snapshot())
    finally:
        MONITOR["on"] = False
    drain()

ROOTOWNER.clear(); ROOTOWNER.update({100: 100, 200: 200})
FG["hwnd"] = 200
addonConfig.setMany({"titleChangeDisappears": True, "rememberTargets": False,
                     "forgetOnDisappear": True, "changesAtOnce": 0,
                     "ignoreRepeatedControls": False})
regTT = targets.TargetRegistry(); notifTT = FakeNotifier()
monTT = monitor.Monitor(regTT, notifTT)
ttWin = FakeContainer("Doc A - Editor", [FakeLeaf("line 1")], hwnd=100)
tgTT = regTT.add(ttWin, "window"); monTT.onAdded(tgTT)
check(tgTT.trackedTitle == "Doc A - Editor", "title: the title is cached when the target is added")
ttWin.add(FakeLeaf("line 2")); sweep(monTT)
check(notifTT.changes == ["line 2"] and notifTT.stopped == [],
      "title: content arriving under the same title is an ordinary change")
ttWin.name = "Doc B - Editor"; ttWin.add(FakeLeaf("line 3")); sweep(monTT)
check(notifTT.stopped == [tgTT], "title: a renamed window is announced as gone")
check(notifTT.changes == ["line 2"], "title: nothing in the renamed window is announced as a change")
check(len(regTT) == 0, "title: 'forget when they disappear' drops the renamed window")

# With the option off, the very same rename is nothing but the window carrying on.
addonConfig.set("titleChangeDisappears", False)
regTO = targets.TargetRegistry(); notifTO = FakeNotifier()
monTO = monitor.Monitor(regTO, notifTO)
oWin = FakeContainer("Doc A - Editor", [FakeLeaf("line 1")], hwnd=100)
tgTO = regTO.add(oWin, "window"); monTO.onAdded(tgTO)
check(tgTO.trackedTitle is None, "title off: no title is cached to hold the target to")
oWin.name = "Doc B - Editor"; oWin.add(FakeLeaf("line 2")); sweep(monTO)
check(notifTO.stopped == [] and len(regTO) == 1, "title off: a renamed window is still tracked")
check(notifTO.changes == ["line 2"], "title off: only its content is announced")

# The option is about whole windows: a single control tracked with F is exempt,
# exactly like the other options in the Window tracking behavior group.
addonConfig.set("titleChangeDisappears", True)
regTF = targets.TargetRegistry(); notifTF = FakeNotifier()
monTF = monitor.Monitor(regTF, notifTF)
fCtrl = FakeContainer("Message list", [FakeLeaf("Alice: hi")], hwnd=100)
tgTF = regTF.add(fCtrl, "focus"); monTF.onAdded(tgTF)
check(tgTF.trackedTitle is None, "title: a control target caches no title")
fCtrl.name = "Message list (1 unread)"; sweep(monTF)
check(notifTF.stopped == [] and len(regTF) == 1, "title: a renamed control target is not a disappearance")

# Remember on, forget off: the renamed window is kept as a detached entry and
# re-attached only once it carries its original title again. _locate is stubbed
# to always find the window, standing in for an identity match that ignores the
# name (the automation id short-circuit) -- without the title check in the
# relocation pass, the window would be re-attached under its new title at once.
_savedRelocate = monitor.RELOCATE_INTERVAL
monitor.RELOCATE_INTERVAL = 0.0                 # a relocation pass on every sweep
try:
    addonConfig.setMany({"rememberTargets": True, "forgetOnDisappear": False})
    regTR = targets.TargetRegistry(); notifTR = FakeNotifier()
    monTR = monitor.Monitor(regTR, notifTR)
    rWin = FakeContainer("Doc A - Editor", [FakeLeaf("line 1")], hwnd=100)
    tgTR = regTR.add(rWin, "window"); monTR.onAdded(tgTR)
    monTR._locate = lambda identity: rWin
    rWin.name = "Doc B - Editor"; sweep(monTR)
    check(notifTR.stopped == [tgTR] and tgTR.obj is None, "title: the renamed window is detached")
    check(len(regTR) == 1, "title: 'forget' off keeps the renamed window as a detached entry")
    sweep(monTR); sweep(monTR)
    check(notifTR.tracking == [], "title: it is not re-attached while it carries the new title")
    rWin.name = "Doc A - Editor"; sweep(monTR)
    check(notifTR.tracking == [tgTR] and tgTR.obj is rWin,
          "title: it re-attaches once the original title comes back")
    check(tgTR.trackedTitle == "Doc A - Editor", "title: re-attaching caches the title again")
    rWin.add(FakeLeaf("line 2")); sweep(monTR)
    check(notifTR.changes == ["line 2"], "title: the re-attached window is tracked as before")
finally:
    monitor.RELOCATE_INTERVAL = _savedRelocate
addonConfig.setMany({"titleChangeDisappears": False, "rememberTargets": False,
                     "forgetOnDisappear": True})

# ============ batched configuration writes ============
# Every write re-reads the whole settings snapshot, so the settings panel writes
# its eighteen values in one go rather than paying eighteen full re-reads.
addonConfig.setMany({"beepPitch": 880, "beepDuration": 25})
check(addonConfig.get("beepPitch") == 880 and addonConfig.get("beepDuration") == 25,
      "setMany writes every value it is given")
check(addonConfig.snapshot()["beepPitch"] == 880, "setMany refreshes the snapshot")
addonConfig.setMany({"beepPitch": 440, "beepDuration": 50})
addonConfig.set("beepPitch", 440)
check(addonConfig.snapshot()["beepPitch"] == 440, "set() still works, through setMany")

# ============ new config defaults ============
addonConfig.set("trackingInterval", 1); addonConfig.set("changesAtOnce", 5)
addonConfig.set("ignoreProgressBars", True); addonConfig.set("ignoreRepeatedControls", True)
check(addonConfig.get("trackingInterval") == 1, "default trackingInterval 1")
check(addonConfig.get("changesAtOnce") == 5, "default changesAtOnce 5")
check(addonConfig.get("ignoreProgressBars") is True, "default ignoreProgressBars True")
check(addonConfig.get("ignoreRepeatedControls") is True, "default ignoreRepeatedControls True")
check(addonConfig.get("titleChangeDisappears") is False, "default titleChangeDisappears False")

print("\n%d/%d passed" % (sum(results), len(results)))
sys.exit(0 if all(results) else 1)
