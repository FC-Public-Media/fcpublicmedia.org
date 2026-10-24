#!/usr/bin/env python3
"""page: the origin's screen, painted on the box itself. tty1 runs the leash (../leash.py) with this
as its command, on the box, not at the end of an ssh (outfit):

    page.py [ROOT]     read the leash's lines on stdin, paint its console on stdout. ROOT: the
                       origin, /srv/origin. FCPM_LOGS, FCPM_ORIGIN_JOB: where the job feeding it logs,
                       and its name (on the box: /var/log/fcpm, intake). `leash.py --facts facts.py -- page.py`

A pane per owner, a line per repository, in name order so a place on the screen keeps meaning:

    name   history ┊ week  size  ◉score ⑂⑂⑂  last  github  tag  hash

A name past 20 cells keeps its start and end around an ellipsis, so one long name never widens the column.

history is main's commits a day as one centred square that grows: a period under 1 a day, a small
square from 1, a square from 3, a full square from 8; empty where there were none. Full squares
fill the cell, so full days meet; inside a run every second one loses its left column, so the run
still counts. The seven days ending today are the strongest thing on the line, in the colour the
repository's kind gives it (the file it carries: show.yml a show, instrument.yml an instrument,
gear.yml gear, residency.yml an engine; paper for the rest). Ten blocks behind them reach back
about seven months, each step longer, and cool as they recede: the kind's colour, then a blue, then
a deeper one. ◉ counts main's commits. A ⑂ per other branch, newest first: bright with work this
week, grey when quiet, dark once merged into main. last is the time today, the weekday within a
week, the date before that, dimmer with age. github is dim when GitHub's main is ours, lit with
↓n when GitHub holds n commits that have not come in, ↑n for ours not on GitHub. A tag shows by
name; the hash, dim, is the box's main.

Everything is read from the box (facts.py) and checked here, ref by ref, against the origin kept
here: a repository apart sits on a muted wedge, red after five minutes, with how far where its tag
would be (−9: the box's main lacks 9 of ours; ~1: a branch or tag differs; ∅: not on the box).

The crew's git runs here too, so the page watches it: the repository being worked on flickers
softly in blue, and its owner's bar says the step on the right (pools → origin.local, pools ←
github), holding the last one, dimmer, once it is done. The bar at the bottom is the room's: the
box's disk and memory as gauges (yellow is used, black is free, then how much is free in G), its
load, the time; red with the trouble. On its left, the origin's own settings: its name, and while
the LAN's dev is on the pace intake asks GitHub at, called out in ink (weekly, the usual, says nothing).
"""
import calendar, importlib.machinery, importlib.util, json, os, re, subprocess, sys, threading, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from facts import refs, repos  # noqa: E402  the same reading on both sides

# The console's 16 colours, all ours: 0-7 as backgrounds too, 8-15 as text only. Ink, yellow and paper
# are the brand's (site/_data/brand.json; on the box, the copy beside this file); the rest are this screen's own.
BRAND = json.load(open(next(p for p in (os.path.join(HERE, "brand.json"),
                                        os.path.join(HERE, "..", "..", "site", "_data", "brand.json"))
                            if os.path.exists(p)), encoding="utf-8"))
PALETTE = "".join(f"\x1b]P{i:X}{c.lstrip('#')}" for i, c in enumerate((
    BRAND["colours"]["ink"], "c8372d", "1b2b45", BRAND["colours"]["signal"], "24395c", "7fb2ff", "a8841a", BRAND["dark"]["ink"],   # ink red work work' yellow github muted paper
    "3d5f94", "6b717b", "a3a9b1", "6f8fc4", "f0a35e", "6cc58a", "e889b5", "b59cf0")))  # deep cool, grey, light grey, cool; the kinds


def fg(i):
    return f"\x1b[1;3{i - 8}m" if i >= 8 else f"\x1b[22;3{i}m"


OFF = "\x1b[0m"
INK, GH, MUTED_T, PAPER = fg(0), fg(5), fg(6), fg(7)
DEEP, DIM, LIGHT, COOL = fg(8), fg(9), fg(10), fg(11)
KINDS = {"show.yml": fg(14), "instrument.yml": fg(12), "gear.yml": fg(13), "residency.yml": fg(15)}
ON_YELLOW, ON_MUTED, ON_BAD = "\x1b[22;43;30m", "\x1b[22;46;30m", "\x1b[22;41;37m"
ON_DEV = "\x1b[22;40;33m"                               # yellow on ink: dev mode, on the bottom bar
WORK = ("\x1b[42m", "\x1b[44m")                         # the flicker under a repository being worked on
COMMIT, BRANCH, TAG = "", "", ""     # drawn by ../console-font.py
FILL, SEAM = "", ""      # one centred square growing: 3, 6, 9, 14 pixels
GAUGE_L, GAUGE_R, GAUGE_USED, GAUGE_FREE = "", "", "", ""
GAUGE_PART = [chr(0xE024 + k) for k in range(7)]
ROOT = sys.argv[1] if len(sys.argv) > 1 else "/srv/origin"
# Where the job that feeds this origin logs, and its name: on the box itself, intake by cron (run-intake).
STATE = os.environ.get("FCPM_LOGS") or os.path.expanduser("~/.local/state/fcpm/crew")
JOB = os.environ.get("FCPM_ORIGIN_JOB") or "standby"
INTAKE = os.path.join(ROOT, ".intake", "state.json")
QUIET = 90          # seconds without facts before the box counts as not heard from
STALE = 300         # seconds apart before a line turns to trouble
LINGER = 1.5        # seconds a repository stays lit after its git is done
EDGES = [7 * 2 ** (k / 2) for k in range(11)]          # days: 7, 9.9, 14, … 224; ten blocks
RATES = (1, 3, 8)                                       # commits a day where the mark steps up


def intake_pace():
    """intake's own dev flag and dev pace (./intake, beside this file here and on the box), so the bar
    says what intake does."""
    path = os.path.join(HERE, "intake")
    loader = importlib.machinery.SourceFileLoader("origin_intake", path)
    intake = importlib.util.module_from_spec(importlib.util.spec_from_loader("origin_intake", loader))
    loader.exec_module(intake)
    return intake.DEV, int(intake.DEV_EVERY.total_seconds() // 60)


NAME = next((w[2] for w in (line.split() for line in open(os.path.join(HERE, "names")))
             if w[:2] == ["linux", "Hostname"]), "origin") + ".local"
DEV_FLAG, DEV_MINUTES = intake_pace()


def settings(surface):
    """The left of the bottom bar: this origin's name, and intake's pace while `fcpm dev on`."""
    if os.path.exists(DEV_FLAG):
        return f"{NAME}  {ON_DEV} dev {DEV_MINUTES}m {surface}"
    return NAME


def step(rate):
    """None for no commits, else 0-3: under 1 a day, from 1, from 3, from 8."""
    return None if not rate else sum(1 for r in RATES if rate >= r)


def marks(cells):
    """(colour, step) cells as marks. Full squares meet; in a run every second one is seamed."""
    out, run = [], 0
    for c in cells:
        if isinstance(c, str):
            out.append(c)
            run = 0
            continue
        colour, s = c
        run = run + 1 if s == 3 else 0
        out.append(" " if s is None else colour + (SEAM if run and run % 2 == 0 else FILL[s]))
    return "".join(out)


def git(repo, *args):
    r = subprocess.run(["git", "-c", "safe.directory=*", "-C", repo, *args], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


MEMO = {}


def known(repo, *args):
    """git answers that never change for the same commits."""
    key = (repo, args)
    if key not in MEMO:
        MEMO[key] = git(repo, *args)
    return MEMO[key]


def steps(repo, a, b):
    """Commits in a that b lacks, and in b that a lacks; None when this side lacks one of them."""
    out = known(repo, "rev-list", "--left-right", "--count", f"{a}...{b}")
    return tuple(int(n) for n in out.split()) if out else None


def signed(s):
    """(ours lacking, theirs lacking) as one terse mark: −9, +3, ±2/5."""
    if s is None:
        return "?"
    a, b = s
    return f"−{b}" if b and not a else f"+{a}" if a and not b else f"±{a}/{b}"


def history(times, now, kind):
    """Ten log blocks cooling with distance, a divider, seven days in the kind's colour."""
    if not times:
        return " " * 10 + DIM + "┊" + " " * 7 + OFF
    midnight = time.mktime(time.localtime(now)[:3] + (0, 0, 0, 0, 0, -1))
    def day(t):
        return 0 if t >= midnight else 1 + int((midnight - t) // 86400)
    days = [day(t) for t in times]
    born, cells = max(days), []
    for k in range(9, -1, -1):
        lo, hi = EDGES[k], EDGES[k + 1] if k < 9 else 10 ** 9
        if born < lo:
            cells.append(" ")
            continue
        n = sum(1 for d in days if lo <= d < hi)
        cells.append((kind if k < 3 else COOL if k < 6 else DEEP, step(n / (min(hi, born + 1) - lo))))
    cells.append(DIM + "┊")
    for d in range(6, -1, -1):
        cells.append(" " if born < d else (kind, step(days.count(d))))
    return marks(cells) + OFF


def forks(repo, main, branches, now):
    """A ⑂ per branch, newest first: bright with work this week, grey when quiet, dark once merged."""
    out = []
    for sha in branches.values():
        t = known(repo, "log", "-1", "--format=%ct", sha, "--")
        merged = known(repo, "merge-base", "--is-ancestor", sha, main) is not None
        t = int(t) if t else 0
        out.append((t, DIM if merged else PAPER if now - t < 7 * 86400 else LIGHT))
    return [c for _, c in sorted(out, reverse=True)]


def mb(n):
    """Megabytes without a leading zero: .2M, 5.3M, 37M."""
    if n is None:
        return ""
    m = n / (1 << 20)
    return (f"{m:.1f}".lstrip("0") if m < 9.95 else f"{m:.0f}") + "M"


def gb(n):
    """Gigabytes, no unit: .48, 1.6, 12."""
    g = n / (1 << 30)
    return f"{g:.2f}".lstrip("0") if g < 1 else f"{g:.1f}" if g < 10 else f"{g:.0f}"


def gauge(free, width=8):
    """Outlined; the used part lets the bar's colour through, the free part is solid, at the right."""
    eighths = round(max(0.0, min(1.0, free)) * width * 8)
    whole, part = divmod(eighths, 8)
    used = width - whole - (1 if part else 0)
    return (GAUGE_L + GAUGE_USED * used + (GAUGE_PART[part - 1] if part else "") + GAUGE_FREE * whole + GAUGE_R)


def last(t, now):
    if not t:
        return ""
    lt, ln = time.localtime(t), time.localtime(now)
    if lt[:3] == ln[:3]:
        return PAPER + time.strftime("%H:%M", lt)
    if now - t < 6.5 * 86400:
        return LIGHT + time.strftime("%a", lt)
    date = time.strftime("%b", lt) + f"{lt.tm_mday:>3}" if lt.tm_year == ln.tm_year else time.strftime("%Y", lt)
    return (LIGHT if now - t < 30 * 86400 else DIM) + date


class Seen:
    def __init__(self):
        self.lock = threading.Lock()
        self.grid = (80, 25)
        self.facts, self.heard = None, 0.0
        self.rows, self.since = [], {}
        self.busy = {}              # owner/repo -> when its git was last seen
        self.said = {}              # owner -> (when, the step)
        self.dirty = True

    def take(self, msg):
        with self.lock:
            self.dirty = True
            if "hello" in msg:
                h = msg["hello"]
                self.grid = (h["cols"], h["rows"])
            elif "facts" in msg:
                self.facts, self.heard = msg["facts"], time.time()
                self.compare()

    def compare(self):
        here, there = repos(ROOT), self.facts.get("repos", {})
        now, rows, since = time.time(), [], {}
        for name in sorted(set(here) | set(there), key=str.lower):
            owner, repo = name.split("/", 1)
            r = here.get(name)
            mine = refs(r) if r else {}
            t = there.get(name) if isinstance(there.get(name), dict) else {}
            theirs = t.get("refs", {})
            seen = theirs or mine
            main = theirs.get("heads/main") or mine.get("heads/main")
            row = {"owner": owner, "name": repo, "full": name, "sha": theirs.get("heads/main"), "bytes": t.get("bytes"),
                   "branches": {k: v for k, v in seen.items() if k.startswith("heads/") and k != "heads/main"
                                and not k.startswith("heads/github/")},
                   "tags": sorted(k[len("tags/"):] for k in seen if k.startswith("tags/")),
                   "times": [], "forks": [], "kind": PAPER, "apart": None, "github": None}
            if r and main:
                out = known(r, "log", "--format=%ct", main)
                row["times"] = [int(x) for x in out.split()] if out else []
                row["forks"] = forks(r, main, row["branches"], now)
                files = (known(r, "ls-tree", "--name-only", main) or "").split("\n")
                row["kind"] = next((c for f, c in KINDS.items() if f in files), PAPER)
            if name not in there:
                row["apart"] = "∅"
            elif not r:
                row["apart"] = "new"
            elif mine != theirs:
                a, b = mine.get("heads/main"), theirs.get("heads/main")
                if a != b:
                    row["apart"] = signed(steps(r, b, a) if a and b else None)
                else:
                    n = len({k for k in set(mine) | set(theirs) if mine.get(k) != theirs.get(k)})
                    row["apart"] = f"~{n}"
            if row["apart"]:
                since[name] = self.since.get(name, now)
                row["since"] = since[name]
            if r and mine.get("heads/main"):
                gh = mine.get("heads/github/main")          # GitHub's main, as intake last fetched it
                if gh:
                    row["github"] = steps(r, mine["heads/main"], gh) if gh != mine["heads/main"] else (0, 0)
            rows.append(row)
        self.rows, self.since = rows, since


S = Seen()


def listen():
    for line in sys.stdin:
        try:
            S.take(json.loads(line))
        except (ValueError, KeyError, TypeError, OSError):
            continue
    sys.exit(0)


ORIGIN_PATH = re.compile(r"/srv/origin/([^/\s']+/[^/\s']+?)(?:\.git)?/?(?=['\s]|$)")


def what(argv):
    """The step a crew process is taking: (owner/repo or None, words), or None."""
    line = " ".join(argv)
    m = ORIGIN_PATH.search(line)
    if "git-receive-pack" in line or ("push" in argv and ("fcpm-origin:" in line or "origin-standby:" in line)):
        return (m.group(1) if m else None), "→ origin.local"
    if "ls-remote" in argv and ("fcpm-origin:" in line or "origin-standby:" in line):
        return (m.group(1) if m else None), "… origin.local"
    if "fetch" in argv and "github" in argv:
        i = argv.index("-C") + 1 if "-C" in argv else None
        p = argv[i] if i else ""
        m = ORIGIN_PATH.search(p + "'") if p else m
        return (m.group(1) if m else None), "← github"
    if argv[:1] and argv[0].endswith("gh") and "graphql" in argv:
        return None, "github …"
    return None


def watch():
    """Every quarter second, the crew's git processes on this machine."""
    while True:
        now = time.time()
        found = []
        for pid in os.listdir("/proc"):
            if not pid.isdigit():
                continue
            try:
                argv = open(f"/proc/{pid}/cmdline", "rb").read().decode(errors="replace").split("\0")
            except OSError:
                continue
            argv = [a for a in argv if a]
            if argv and (argv[0].endswith(("git", "ssh", "gh")) or "git" in argv[:2]):
                w = what(argv)
                if w:
                    found.append(w)
        with S.lock:
            for repo, words in found:
                if repo:
                    S.busy[repo] = now
                    owner, name = repo.split("/", 1)
                    S.said[owner] = (now, f"{name} {words}")
                else:
                    for owner in {r["owner"] for r in S.rows}:
                        S.said[owner] = (now, words)
                S.dirty = True
        time.sleep(0.25)


def last_run(job):
    """When the crew last started JOB, and its last run's first complaint if it had one."""
    try:
        lines = open(os.path.join(STATE, f"{job}.log"), encoding="utf-8", errors="replace").read().splitlines()[-200:]
    except OSError:
        return None, None
    starts = [i for i, l in enumerate(lines) if l.startswith("--- ")]
    if not starts:
        return None, None
    try:
        when = time.mktime(time.strptime(" ".join(lines[starts[-1]].split()[1:3]), "%Y-%m-%d %H:%M:%S"))
    except ValueError:
        when = None
    said = [l for l in lines[starts[-1] + 1:] if l.strip()]
    return when, (f"{job}: {said[0]}" if said else None)


def github():
    try:
        s = json.load(open(INTAKE))
        return calendar.timegm(time.strptime(s["checked"][:19], "%Y-%m-%dT%H:%M:%S")), s.get("github")
    except (OSError, ValueError, KeyError):
        return None, None


def ago(s):
    s = max(0, int(s))
    return f"{s}s" if s < 60 else f"{s // 60}m" if s < 3600 else f"{s // 3600}h" if s < 86400 else f"{s // 86400}d"


def visible(s):
    out, i = 0, 0
    while i < len(s):
        if s[i] == "\x1b":
            i = s.index("m", i) + 1
            continue
        out += 1
        i += 1
    return out


NAME_MAX = 20                  # the name column's widest; a longer name loses its middle


def short(name, width=NAME_MAX):
    """NAME, or its start and end around an ellipsis, so one long name never widens the column."""
    if len(name) <= width:
        return name
    head = width // 2
    return name[:head] + "…" + name[len(name) - (width - 1 - head):]


def fit(s, width):
    """Pad or cut a styled string to WIDTH visible cells."""
    n = visible(s)
    if n <= width:
        return s + " " * (width - n)
    out, i, kept = [], 0, 0
    while i < len(s) and kept < width - 1:
        if s[i] == "\x1b":
            j = s.index("m", i) + 1
            out.append(s[i:j])
            i = j
            continue
        out.append(s[i])
        kept += 1
        i += 1
    return "".join(out) + "…"


def bar(C, left, right="", surface=ON_YELLOW):
    right = "  " + right + " " if right else ""
    return surface + fit(" " + left, C - visible(right)) + surface + right + OFF


def remote(gh):
    """github, dim when even, lit ↓n with commits to come in, ↑n for ours not there."""
    if gh is None:
        return ""
    if gh == (0, 0):
        return DIM + "github"
    ours, theirs = gh
    return (GH if theirs else LIGHT) + "github" + (f"↓{theirs}" if theirs else "") + (f"↑{ours}" if ours else "")


def line(C, row, now, w, lit):
    count = len(row["times"])
    text = (f" {PAPER}{short(row['name']):<{w}} " + history(row["times"], now, row["kind"])
            + f" {DIM if (row['bytes'] or 0) < 1 << 20 else LIGHT}{mb(row['bytes']):>5}"
            + f" {LIGHT}{COMMIT}{PAPER}{count if count else '':<4}"
            + " " + fit("".join(c + BRANCH for c in row["forks"]), 8) + " "
            + fit(last(row["times"][0] if row["times"] else 0, now), 6) + " "
            + fit(remote(row["github"]), 9))
    tail = (PAPER + row["apart"]) if row["apart"] else (LIGHT + TAG + PAPER + row["tags"][-1]) if row["tags"] else ""
    sha = DIM + (row["sha"] or "")[:7]
    room = C - visible(text) - 1
    if room < 7 or tail and visible(tail) + 2 + 7 > room:     # a tag's name before the hash
        text += " " + fit(tail, room)
    else:
        text += " " + fit(tail, room - 7) + sha
    text = fit(text, C)
    if row["apart"]:            # on the wedge, everything in ink
        wedge = ON_BAD if now - row["since"] > STALE else ON_MUTED
        return wedge + re.sub(r"\x1b\[[0-9;]*m", "", text) + OFF
    if lit:                     # being worked on: a soft flicker underneath
        under = WORK[int(now * 3) % 2]
        return under + text.replace(OFF, OFF + under) + OFF
    return text + OFF


def paint():
    with S.lock:
        C, R = S.grid
        f, now = S.facts, time.time()
        when, complaint = last_run(JOB)
        checked, reach = github()
        trouble = complaint
        if when and now - when > STALE:
            trouble = trouble or f"{JOB} {ago(now - when)}"
        if reach and reach != "ok":
            trouble = trouble or f"github: {reach}"
        if f and f.get("synced") is False:
            trouble = trouble or "clock"
        if f and f.get("size") and f["free"] / f["size"] < 0.1:
            trouble = trouble or f"{gb(f['free'])} free"
        clock = time.strftime("%H:%M")
        if not f:
            foot = bar(C, settings(ON_MUTED), clock, ON_MUTED)
        elif now - S.heard > QUIET:
            foot = bar(C, f"— {ago(now - S.heard)}", clock, ON_BAD)
        else:
            parts = []
            if f.get("size"):
                parts.append(f"disk {gauge(f['free'] / f['size'])} {gb(f['free'])}")
            if f.get("memory") and f.get("available") is not None:
                parts.append(f"mem {gauge(f['available'] / f['memory'])} {gb(f['available'])}")
            if "load" in f:
                parts.append(f"load {f['load']:.2f}")
            parts.append(clock)
            foot = bar(C, trouble or settings(ON_YELLOW), "   ".join(parts), ON_BAD if trouble else ON_YELLOW)

        owners = {}
        for row in S.rows:
            owners.setdefault(row["owner"], []).append(row)
        room = R - 1 - len(owners)
        w = max((len(short(r["name"])) for r in S.rows), default=10)
        body, busy = [], False
        for owner in sorted(owners, key=str.lower):
            rows = owners[owner]
            said = S.said.get(owner)
            if said:
                live = now - said[0] < LINGER
                busy = busy or live
                right = (INK + said[1]) if live else (MUTED_T + time.strftime("%H:%M ", time.localtime(said[0])) + said[1])
            else:
                right = ""
            body.append(bar(C, owner, right))
            show = rows if len(rows) <= room else rows[:max(0, room - 1)]
            for r in show:
                lit = now - S.busy.get(r["full"], 0) < LINGER
                busy = busy or lit
                body.append(line(C, r, now, w, lit))
            if len(show) < len(rows):
                body.append(f" {LIGHT}+{len(rows) - len(show)}{OFF}")
            room -= len(show) + (len(show) < len(rows))
        lines = body[:R - 1]
        lines += [""] * (R - 1 - len(lines)) + [foot]
        S.dirty = busy           # keep painting while something flickers
    # Each line placed: erasing to the end of a full line would take its last cell with it.
    return "".join(f"\x1b[{i + 1};1H" + l + ("\x1b[K" if visible(l) < C else "") for i, l in enumerate(lines[:R]))


def main():
    threading.Thread(target=listen, daemon=True).start()
    threading.Thread(target=watch, daemon=True).start()
    out = sys.stdout
    out.write(PALETTE + "\x1b[?25l\x1b[2J")
    last_tick = ""
    while True:
        tick = time.strftime("%H:%M") + str(int(time.time()) // 10)
        if S.dirty or tick != last_tick:
            out.write(paint())
            out.flush()
            last_tick = tick
        time.sleep(0.15)


if __name__ == "__main__":
    main()
