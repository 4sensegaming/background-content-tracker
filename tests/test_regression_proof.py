# Proves the regression tests in test_logic.py actually catch the two shipped bugs.
# Reconstructs the ORIGINAL (buggy) _capture/_disarm and asserts each is detected.
import sys, types, importlib, os

PKGDIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "addon", "globalPlugins", "backgroundContentTracker",
)
T = types


class ThreadViolation(BaseException):
    pass


HOOK = {"on": False}
MONITOR = {"on": False}
MESSAGES = []
QUEUED = []


def stub(name, **attrs):
    m = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(m, k, v)
    sys.modules[name] = m
    return m


def _ui_message(text, speechPriority=None):
    if HOOK["on"]:
        raise ThreadViolation("ui.message() on hook thread")
    if MONITOR["on"]:
        raise ThreadViolation("ui.message() on monitor thread")
    MESSAGES.append(text)


class FakeTimer:
    def Stop(self):
        if HOOK["on"]:
            raise ThreadViolation("wx timer .Stop() on hook thread")


def _callLater(ms, fn, *a, **k):
    if HOOK["on"]:
        raise ThreadViolation("core.callLater() on hook thread")
    return FakeTimer()


cfg = stub("config")
class Conf(dict):
    pass
cfg.conf = Conf(); cfg.conf.spec = Conf()
stub("winUser", isWindow=lambda h: bool(h))
stub("logHandler", log=T.SimpleNamespace(error=lambda *a, **k: None, debugWarning=lambda *a, **k: None))
def initTranslation():
    g = sys._getframe(1).f_globals
    g["_"] = lambda s: s
    g["ngettext"] = lambda s, p, n: s if n == 1 else p
stub("addonHandler", initTranslation=initTranslation)
stub("tones", beep=lambda *a, **k: None)
stub("ui", message=_ui_message)
stub("speech")
stub("speech.priorities", Spri=T.SimpleNamespace(NORMAL=0, NEXT=1, NOW=2))
stub("inputCore", manager=T.SimpleNamespace(_captureFunc=None))
stub("core", callLater=_callLater)
stub("queueHandler", eventQueue=object(),
     queueFunction=lambda q, f, *a, _immediate=False, **k: QUEUED.append((f, a)))
class KeyboardInputGesture:
    pass
stub("keyboardHandler", KeyboardInputGesture=KeyboardInputGesture)
stub("api", getDesktopObject=lambda: T.SimpleNamespace(children=[]))
stub("textInfos", POSITION_ALL="all")
class NVDAObjectTextInfo:
    pass
class RealTextInfo(NVDAObjectTextInfo):
    pass
class NVDAObject:
    """Stand-in for NVDA's base object; its generic child accessors build the
    whole child list, which is what the sweep's fast-path check must detect."""
    def getChild(self, index):
        return self.children[index]
    def _get_childCount(self):
        return len(self.children)
stub("NVDAObjects", NVDAObject=NVDAObject, NVDAObjectTextInfo=NVDAObjectTextInfo)

pkg = types.ModuleType("backgroundContentTracker"); pkg.__path__ = [PKGDIR]
sys.modules["backgroundContentTracker"] = pkg
addonConfig = importlib.import_module("backgroundContentTracker.addonConfig")
overlay = importlib.import_module("backgroundContentTracker.overlay")
monitor = importlib.import_module("backgroundContentTracker.monitor")
targets = importlib.import_module("backgroundContentTracker.targets")
notifier = importlib.import_module("backgroundContentTracker.notifier")
import inputCore as inputCoreStub
addonConfig.initialize()


class FakeGesture(KeyboardInputGesture):
    def __init__(self, key, mods=(), isModifier=False):
        self.mainKeyName = key; self.modifierNames = tuple(mods); self.isModifier = isModifier


class FakeController:
    def __init__(self): self.calls = []
    def __getattr__(self, name):
        def rec(*a): self.calls.append((name,) + a)
        return rec


class BuggyOverlay(overlay.Overlay):
    """The ORIGINAL, shipped implementation of the two broken methods."""

    def _disarm(self):
        self._cancelTimer()
        if self._armed:
            try:
                # BUG 2: `self._capture` makes a NEW bound method -> never matches.
                if inputCoreStub.manager._captureFunc is self._capture:
                    inputCoreStub.manager._captureFunc = self._prevCapture
            except Exception:
                pass
            self._armed = False
        self._prevCapture = None

    def _capture(self, gesture):
        # BUG 1: does wx/speech/controller work directly on the hook thread.
        try:
            if not isinstance(gesture, KeyboardInputGesture):
                return True
            if gesture.isModifier:
                return True
            self._cancelTimer()          # wx timer .Stop() on the hook thread
            self._disarm()
            if not self._dispatchOld(gesture):
                _ui_message("Overlay closed")   # speech on the hook thread
        except Exception:
            self._disarm()
        return False

    def _dispatchOld(self, gesture):
        return self._dispatch((gesture.mainKeyName or "").lower(),
                              tuple(m.lower() for m in gesture.modifierNames))


def read(obj, ignoreProgressBars=False):
    """The text of a sweep, rendered as the cached snapshot renders it."""
    return "\n".join(text for _, text in monitor._sweepEntries(obj, ignoreProgressBars))


results = []
def check(cond, msg):
    results.append(bool(cond)); print(("PASS" if cond else "FAIL") + ": " + msg)


# --- Proof for BUG 1: the hook-thread tripwire fires on the old _capture ---
inputCoreStub.manager._captureFunc = None
fc = FakeController()
buggy = BuggyOverlay(fc)
buggy._prevCapture = None
buggy._armed = True
buggy._timer = FakeTimer()
inputCoreStub.manager._captureFunc = buggy._capture

caught = None
HOOK["on"] = True
try:
    buggy._capture(FakeGesture("h"))
except ThreadViolation as e:
    caught = str(e)
finally:
    HOOK["on"] = False
check(caught is not None, "OLD _capture is caught doing forbidden hook-thread work: %s" % caught)

# --- Proof for BUG 2: old _disarm never releases the captor ---
inputCoreStub.manager._captureFunc = None
buggy2 = BuggyOverlay(FakeController())
buggy2._prevCapture = None
buggy2._armed = True
buggy2._timer = None
stored = buggy2._capture                      # exactly what open() used to store
inputCoreStub.manager._captureFunc = stored
buggy2._disarm()                              # HOOK off, so no tripwire interference
check(inputCoreStub.manager._captureFunc is stored,
      "OLD _disarm FAILS to release the captor (input stays swallowed forever)")

# --- The fixed implementation releases it correctly ---
inputCoreStub.manager._captureFunc = None
fixed = overlay.Overlay(FakeController())
fixed.open()
check(inputCoreStub.manager._captureFunc is fixed._captureRef, "FIXED open() installs stable captor")
HOOK["on"] = True
try:
    r = fixed._capture(FakeGesture("h"))
    violation = None
except ThreadViolation as e:
    violation = str(e); r = None
finally:
    HOOK["on"] = False
check(violation is None, "FIXED _capture does no forbidden hook-thread work")
check(inputCoreStub.manager._captureFunc is None, "FIXED _capture releases the captor")
check(len(QUEUED) == 1, "FIXED _capture queued the work to the main thread")

# --- Proof for BUG 3: the alt+tab dump -------------------------------------
# v1.0.2's readContent() consulted obj.treeInterceptor FIRST. For any node inside
# a browse-mode document that returns the WHOLE page, no matter which node was
# asked about -- and the descendant-event path then announced it verbatim.
class FakeTreeInterceptor:
    isReady = True
    passThrough = False
    def makeTextInfo(self, pos):
        return T.SimpleNamespace(text="ENTIRE DOCUMENT: msg 1 msg 2 msg 3 ...thousands of words...")

class NodeInsideDocument:
    """One small node (a chat message) inside a browse-mode document."""
    TextInfo = NVDAObjectTextInfo
    def __init__(self, name):
        self.name = name; self.value = None; self.children = []
        self.treeInterceptor = FakeTreeInterceptor()
        self.windowHandle = 100
    def makeTextInfo(self, pos):
        raise NotImplementedError

def oldReadContent(obj):
    """Verbatim shape of the v1.0.2 implementation."""
    text = ""
    ti = getattr(obj, "treeInterceptor", None)
    if ti is not None:
        try:
            if getattr(ti, "isReady", False) and not getattr(ti, "passThrough", True):
                text = ti.makeTextInfo("all").text
        except Exception:
            text = ""
    if not text:
        try:
            text = obj.makeTextInfo("all").text
        except Exception:
            text = ""
    if not text:
        text = " ".join(x for x in (getattr(obj, "name", None), getattr(obj, "value", None)) if x)
    return text

node = NodeInsideDocument("msg 3")
check(oldReadContent(node).startswith("ENTIRE DOCUMENT"),
      "OLD readContent returns the WHOLE document for one small node -> the alt+tab dump")
check(read(node) == "msg 3",
      "NEW readContent returns only that node's own text")
import os as _os
_monsrc = open(_os.path.join(PKGDIR, "monitor.py"), encoding="utf-8").read()
check("treeInterceptor" not in _monsrc, "NEW monitor never consults the tree interceptor at all")
check(_monsrc.count("notifier.announceChange") == 1, "NEW monitor has exactly one announce site")
# BUG 6: a character-level diff decided whether a change was worth reporting, so a
# change it could not express came back empty and was silently dropped. The keyed
# snapshot answers "is this new" on its own; nothing can swallow a detected change.
check("diffHandler" not in _monsrc, "NEW monitor runs no character-level diff at all")

# --- Proof for BUG 4: chars=0 on a real Chromium window --------------------
# v1.0.3 rule: "if the object has its own text, take it and do not look inside".
# A Chromium document advertises a text interface but hands back nothing, so the
# sweep stopped at it. Reproduces Lukas's console output exactly: chars=0.
class Leaf:
    TextInfo = NVDAObjectTextInfo
    def __init__(self, name):
        self.name = name; self.value = None; self.children = []

class DocumentWithNoOwnText:
    """Claims a text interface; its own text is empty (or just placeholders)."""
    TextInfo = RealTextInfo
    def __init__(self, kids):
        self.name = ""; self.value = None; self._kids = list(kids)
    @property
    def children(self):
        return list(self._kids)
    def makeTextInfo(self, pos):
        return T.SimpleNamespace(text="")

class TopWindow:
    TextInfo = NVDAObjectTextInfo
    def __init__(self, child):
        self.name = "Claude"; self.value = None; self._kids = [child]
    @property
    def children(self):
        return list(self._kids)

def oldGather(root):
    """The v1.0.3 sweep."""
    lines, stack, nodes = [], [(root, 0)], 0
    while stack and nodes < 2500:
        obj, depth = stack.pop()
        nodes += 1
        if obj.TextInfo is not NVDAObjectTextInfo:      # "has its own text"
            text = obj.makeTextInfo("all").text.strip()
            if text:
                lines.append(text)
            continue                                     # <-- never looks inside
        kids = getattr(obj, "children", None)
        if kids:
            for k in reversed(kids):
                stack.append((k, depth + 1))
            continue
        if obj.name:
            lines.append(obj.name)
    return chr(10).join(lines)

window = TopWindow(DocumentWithNoOwnText([Leaf("msg 1"), Leaf("msg 2")]))
check(len(oldGather(window)) == 0,
      "OLD sweep reads 0 characters from the real window shape (matches the console output)")
check(read(window) == "msg 1" + chr(10) + "msg 2",
      "NEW sweep descends past the document and reads the messages")
_src = open(__import__("os").path.join(PKGDIR, "monitor.py"), encoding="utf-8").read()
check("_cleanText" in _src and "_OBJECT_REPLACEMENT" in _src,
      "NEW monitor strips embedded-object placeholders")

# --- Proof for BUG 5: the sweep ran on NVDA's main thread ------------------
# v1.0.4 scheduled the sweep with core.callLater and spoke straight out of it,
# so ~50 ms of cross-process reads landed on the thread that drives speech,
# braille and keyboard handling, once every 700 ms.
class Win:
    TextInfo = NVDAObjectTextInfo
    def __init__(self, kids, hwnd=100):
        self.name = "Claude"; self.value = None; self.role = None
        self._kids = list(kids); self.windowHandle = hwnd
    @property
    def children(self):
        return list(self._kids)


class OldMonitor(monitor.Monitor):
    """v1.0.4: announced inline, straight from the polling call. The delta is
    reconstructed here rather than called on the monitor, whose own diff has since
    been rewritten; all this fixture has to reproduce is the ANNOUNCEMENT SITE."""
    def _checkTargetContent(self, target):
        newText = read(target.obj)
        old = target.cachedContent
        delta = (newText[len(old):] if newText.startswith(old) else newText).strip()
        target.cachedContent = newText
        if delta:
            self.notifier.announceChange(target, delta)


def sweepOnMonitorThread(mon, target):
    """Run one sweep with the monitor-thread tripwires armed."""
    MONITOR["on"] = True
    try:
        mon._checkTargetContent(target)
        return None
    except ThreadViolation as violation:
        return violation
    finally:
        MONITOR["on"] = False


reg = targets.TargetRegistry()
realNotifier = notifier.Notifier()
win = Win([Leaf("one")])

tgOld = reg.add(win, "window"); tgOld.cachedContent = "one"; tgOld.wasInForeground = False
win._kids.append(Leaf("two"))
check(sweepOnMonitorThread(OldMonitor(reg, realNotifier), tgOld) is not None,
      "OLD monitor speaks straight out of the sweep -> caught on the monitor thread")

tgNew = reg.add(win, "window"); tgNew.cachedContent = "one"; tgNew.wasInForeground = False
MESSAGES.clear(); QUEUED.clear()
check(sweepOnMonitorThread(monitor.Monitor(reg, realNotifier), tgNew) is None,
      "NEW monitor never speaks on its own thread")
check(MESSAGES == [] and len(QUEUED) == 1,
      "NEW monitor hands the announcement to NVDA's main thread instead")

check("core.callLater" not in _monsrc, "NEW monitor no longer schedules a timer on the main thread")
check("threading.Thread" in _monsrc and "daemon=True" in _monsrc,
      "NEW monitor polls on its own daemon thread")
_stopBody = _monsrc.split("def stop", 1)[1].split(chr(9) + "def ", 1)[0]
check(".join(" not in _stopBody,
      "stop() never joins the thread: a hung target cannot block NVDA's exit")
check("config.conf" not in _monsrc and "addonConfig.get(" not in _monsrc,
      "NEW monitor never reads NVDA's live configuration off the main thread")
check("addonConfig.snapshot()" in _monsrc, "NEW monitor reads the thread-safe settings snapshot")

# --- Proof for BUG 7: the poll clock counted ticks, not elapsed time --------
# Charging every sweep a flat POLL_INTERVAL made a five-second tracking interval
# mean twenty seconds of wall clock once a window took three seconds to read.
check("time.monotonic()" in _monsrc and "sinceLast += elapsed" in _monsrc,
      "NEW monitor measures elapsed time, so the tracking interval means what it says")

# --- Proof for BUG 8: two full copies of every snapshot --------------------
# The joined text was rebuilt every poll, for every target, purely to shortcut a
# diff that already answers the same question -- up to a megabyte per target per
# second of pure allocation.
check("cachedContent" not in _monsrc, "NEW monitor keeps one snapshot per target, not two")

# --- Proof for BUG 9: the focus lookup ran on NVDA's main thread -----------
# Re-resolving a stale control scans the desktop: hundreds of cross-process reads
# fired from a keypress, blocking speech and keyboard handling for all of them.
_initsrc = open(_os.path.join(PKGDIR, "__init__.py"), encoding="utf-8").read()
check("relocateAsync" in _monsrc and "relocateAsync" in _initsrc,
      "NEW focus command resolves the target off the main thread")
check("self.monitor.relocate(" not in _initsrc,
      "NEW focus command never runs the desktop scan inline")

print("\n%d/%d passed" % (sum(results), len(results)))
sys.exit(0 if all(results) else 1)
