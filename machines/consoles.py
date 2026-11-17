"""consoles -- what this machine holds up to be read: a screen each, written whole on its own beat.

    fcpm consoles              the list, and how fresh each one is
    fcpm consoles NAME         one console as it was last written
    fcpm consoles beat         keep every console written, each on its beat, until stopped (the helm does this)

A console is one fixed shape: ROWS lines of at most COLS characters. Its first line says what it is, where, when
it was written and until when it is fresh, and the same thing is always on the same line, so a change shows
as a different shape. It is never a log that grows: what does not fit is counted on its last line.

Each is written to a file beside it and renamed over the old one, so a reader gets a whole page, old or new,
and never waits on the script that composes it. Reading never runs a composer, unless the page is missing or
three beats stale (no helm keeping it), and then only once. ~/code/consoles/ holds one file per console and
CONSOLES, the list Fighter's console tabs read (`name<TAB>path<TAB>supplier`). The helm serves the same at
/consoles. Doc: docs/consoles.md.
"""
import datetime
import os
import pathlib
import socket
import subprocess
import sys
import threading
import time
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
CODE = pathlib.Path(os.environ.get("FCPM_CODE") or pathlib.Path.home() / "code")
DIR = CODE / "consoles"
ROWS, COLS = 24, 80
SUPPLIER = "helm"


def utc(t, fmt):
    return datetime.datetime.fromtimestamp(t, datetime.timezone.utc).strftime(fmt)


def _import(name, where):
    """A sibling module, imported without leaving __pycache__ beside the profiles (test_binding)."""
    if str(where) not in sys.path:
        sys.path.append(str(where))
    was, sys.dont_write_bytecode = sys.dont_write_bytecode, True
    try:
        return __import__(name)
    finally:
        sys.dont_write_bytecode = was


def jobs():
    """The jobs this machine wears (machines/binding, through replies.wears)."""
    try:
        return sorted(_import("replies", HERE / "kiosk").wears())
    except Exception:
        return []


# ------------------------------------------------------------------- composers --
# Each returns the console's lines below its first. Kept short, and the same thing on the same line.

def helm():
    replies = _import("replies", HERE / "kiosk")
    worn = jobs()
    every = replies.helms()
    port = int(os.environ.get("FCPM_DOOR_PORT") or 8080)
    lines = ["wears     %s" % (", ".join(worn) or "no job: machines/binding finds none for this computer"),
             "door      %s" % ("answering on %d" % port if answers("http://127.0.0.1:%d/revision" % port)
                              else "not answering on %d" % port),
             "revision  %s" % (git("log", "-1", "--format=%h %cs %s") or "?")[:COLS - 10]]
    holds = sorted({w for j in worn for w in ((every.get(j) or {}).get("holds") or [])})
    lines.append("holds     %s" % (", ".join(holds) or "nothing only it applies"))
    lines.append("peers")
    for job, h in every.items():
        if job in worn:
            continue
        at = (h or {}).get("at") or ""
        state = "no address yet" if not at else ("answering" if answers(at.rstrip("/") + "/revision") else "not answering")
        lines.append("  %-14s %-15s %s" % (job, state, at))
    return lines


def workshed():
    w = _import("workshed", HERE)
    d = w.everything()
    lines = ["builds    %s" % ("node and jekyll-enough here" if d["node"] and d["engine"] else
                                 "cannot: fcpm workshed check says what is missing")]
    up = [x for x in d["worktrees"] if x["running"]]
    lines.append("up        %d of %d" % (len(up), len(d["worktrees"])))
    if not d["worktrees"]:
        lines.append("  empty: fcpm workshed new BRANCH")
    for x in d["worktrees"]:
        said = []
        if x["changed_pages"]:
            said.append(" ".join(x["changed_pages"]))
        if x["dirty"]:
            said.append("uncommitted")
        if x["ahead"]:
            said.append("%d ahead" % x["ahead"])
        if x["behind"]:
            said.append("%d behind" % x["behind"])
        state = (":%d" % x["port"]) if x["running"] else "stopped"
        if x["running"] and x["ok"] is False:
            state += " FAILED"
        lines.append("  %-38s %-11s %s" % (x["name"], state, ", ".join(said) or "as main"))
    return lines


def library():
    """The library's own console (machines/library.py), kept at most a minute old; its first line is dropped
    for ours."""
    lib = _import("library", HERE)
    if not (lib.location() / ".git").exists():
        return ["none here: no library on this machine (fcpm library)"]
    profile = os.environ.get("FCPM_PROFILE") or (jobs() or [""])[0]
    lib.refresh(profile)
    text = lib.buffer().read_text(encoding="utf-8") if lib.buffer().exists() else ""
    return text.splitlines()[1:] or ["not written yet"]


def constitution():
    """The constitution each job this machine wears declares (machines/<job>/CONSTITUTION.md), with the history
    that is its body language. A missing one is said, never left off: a blank constitution is not metadata."""
    lines = []
    for job in jobs() or ["(no job)"]:
        path = ROOT / "machines" / job / "CONSTITUTION.md"
        if not path.is_file():
            lines += ["%-9s none yet: machines/%s/CONSTITUTION.md, written by merged PR" % (job, job)]
            continue
        rel = path.relative_to(ROOT).as_posix()
        n = git("rev-list", "--count", "HEAD", "--", rel) or "0"
        last = git("log", "-1", "--format=%h %cs", "--", rel) or "not committed"
        lines += ["%-9s %s: %s commits, last %s" % (job, rel, n, last), ""]
        lines += [l for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    return lines


# name: (beat in seconds, composer). The order is the list's.
CONSOLES = {"helm": (10, helm), "workshed": (5, workshed), "library": (60, library), "constitution": (300, constitution)}


def git(*args):
    r = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.stdout.strip() if r.returncode == 0 else ""


def answers(url, timeout=2):
    try:
        with urllib.request.urlopen(url, timeout=timeout):
            return True
    except Exception:
        return False


# ----------------------------------------------------------------- the page --
def page(name, body, now=None):
    """The fixed shape: a first line, then exactly ROWS - 1 more, each at most COLS characters."""
    now = time.time() if now is None else now
    beat = CONSOLES[name][0]
    head = "%-12s %s  written %s, fresh until %s" % (name, socket.gethostname().lower(), utc(now, "%Y-%m-%d %H:%M:%SZ"),
                                                     utc(now + beat, "%H:%M:%SZ"))
    room = ROWS - 1
    body = [str(l).replace("\t", "  ").rstrip() for l in body]
    if len(body) > room:
        more = len(body) - (room - 1)
        body = body[:room - 1] + ["... %d more line%s" % (more, "" if more == 1 else "s")]
    lines = [head] + body + [""] * (room - len(body))
    return "\n".join(l if len(l) <= COLS else l[:COLS - 3] + "..." for l in lines) + "\n"


def path(name):
    return DIR / name


def write(name):
    """Compose one console and put it in place whole. A composer that fails writes a page saying so."""
    try:
        body = CONSOLES[name][1]()
    except Exception as exc:
        body = ["could not be written: %s" % (" ".join(str(exc).split()) or type(exc).__name__)]
    text = page(name, body)
    DIR.mkdir(parents=True, exist_ok=True)
    tmp = DIR / (".%s.%d.part" % (name, os.getpid()))
    tmp.write_text(text, encoding="utf-8", newline="\n")
    for _ in range(20):                     # Windows refuses a rename over a file a reader has open this instant
        try:
            os.replace(tmp, path(name))
            break
        except PermissionError:
            time.sleep(0.05)
    else:
        tmp.unlink(missing_ok=True)         # the old page stands until the next beat
    write_list()
    return text


def write_list():
    text = "# supplier: %s\n" % SUPPLIER + "".join("%s\t%s\t%s\n" % (n, path(n), SUPPLIER) for n in CONSOLES)
    p = DIR / "CONSOLES"
    if not p.exists() or p.read_text(encoding="utf-8") != text:
        DIR.mkdir(parents=True, exist_ok=True)
        tmp = DIR / (".CONSOLES.%d.part" % os.getpid())
        tmp.write_text(text, encoding="utf-8", newline="\n")
        try:
            os.replace(tmp, p)
        except PermissionError:
            tmp.unlink(missing_ok=True)


def age(name):
    try:
        return time.time() - path(name).stat().st_mtime
    except OSError:
        return None


def read(name):
    """The page as it stands. Written now only when there is none, or it is three beats stale."""
    if name not in CONSOLES:
        raise KeyError(name)
    a = age(name)
    if a is None or a > 3 * CONSOLES[name][0]:
        return write(name)
    try:
        return path(name).read_text(encoding="utf-8")
    except OSError:
        return write(name)


def listing(base=None):
    """CONSOLES as Fighter reads it; `base` (a URL) puts the helm's addresses where the paths are."""
    return "# supplier: %s\n" % SUPPLIER + "".join(
        "%s\t%s\t%s\n" % (n, (base.rstrip("/") + "/consoles/" + n) if base else path(n), SUPPLIER) for n in CONSOLES)


def keep(stop=None):
    """Every console on its own beat, each in its own thread, so a slow one never holds another up."""
    def one(name):
        beat = CONSOLES[name][0]
        while not (stop and stop.is_set()):
            write(name)
            if stop:
                stop.wait(beat)
            else:
                time.sleep(beat)
    threads = [threading.Thread(target=one, args=(n,), daemon=True, name="console:" + n) for n in CONSOLES]
    for t in threads:
        t.start()
    return threads


def main(argv):
    sys.stdout.reconfigure(errors="backslashreplace", newline="\n")      # a page is LF, as its file is
    if not argv:
        for n, (beat, _) in CONSOLES.items():
            a = age(n)
            print("%-13s every %3ds  %s" % (n, beat, "not written yet" if a is None else
                                            "written %ds ago%s" % (a, "" if a < 3 * beat else ", STALE: is a helm keeping it?")))
        print("in %s" % DIR)
        return 0
    if argv == ["beat"]:
        keep()
        while True:
            time.sleep(3600)
    if len(argv) == 1 and argv[0] in CONSOLES:
        print(read(argv[0]), end="")
        return 0
    print(__doc__.split("\n\n")[1])
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
