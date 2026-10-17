#!/usr/bin/env python3
"""page: the origin's screen, painted from the machine it is kept beside (today digitization). The
origin's leash (../leash.py) runs this at the far end of its `ssh -T`, a forced command:

    page.py [ROOT]     read the leash's lines on stdin, paint its console on stdout. ROOT: the
                       origin kept here, /srv/origin. Test here: `leash.py --facts facts.py -- page.py`

A pane per owner, a line per repository, in name order so a place on the screen keeps meaning:

    name   history ┊ week  size  ◉score ⑂⑂⑂  last  github  tag  hash

history is main's commits a day as one centred square that grows: a period under 1 a day, a
small square from 1, a square from 3, a full square from 8; empty where there were none. Ten blocks reach back about seven months, each
step longer, then the seven days ending today. ◉ counts main's commits. A ⑂ per other branch, newest first: bright with work this week, grey
when quiet, dark once merged into main (a leftover). Size is in megabytes: .2M, 5.3M, 37M. last is the time today, the weekday within a week, the date
before that, dimmer with age. github is dim when GitHub's main is ours, lit with how far when
not; another remote would get its own word. A tag shows by name; the hash, dim, is the box's main. Everything is read from the box
(facts.py) and checked here, ref by ref, against the origin kept here: a repository apart sits on
a muted wedge, red after five minutes, with how far where its tag would be (−9: the box's main
lacks 9 of ours; ~1: a branch or tag differs; ∅: not on the box). The bar at the bottom is the
room's: free space on the box, its memory, its load, the time; red with the trouble.
"""
import calendar, json, os, re, subprocess, sys, threading, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from facts import refs, repos  # noqa: E402  the same reading on both sides

# The console's 16 colours, all ours: 0-7 as backgrounds too, 8-15 as text only.
PALETTE = "".join(f"\x1b]P{i:X}{c}" for i, c in enumerate((
    "121417", "c8372d", "3fb36f", "ffc61a", "5b8fe0", "a58be6", "a8841a", "ece8e1",   # ink red tag yellow (spare) github muted paper
    "2b2f36", "454a53", "646a74", "8b919b", "b8bdc4", "f4f5f7", "ff6b5b", "ffffff")))  # the greys, dark to light; alarm; white


def fg(i):
    return f"\x1b[1;3{i - 8}m" if i >= 8 else f"\x1b[22;3{i}m"


OFF = "\x1b[0m"
INK, TAGGED, PAPER, LIT = fg(0), fg(2), fg(7), fg(15)
GREY = [fg(8), fg(9), fg(10), fg(11), fg(12), fg(13)]       # 0: nothing; 1-5: more
ON_YELLOW, ON_MUTED, ON_BAD = "\x1b[22;43;30m", "\x1b[22;46;30m", "\x1b[22;41;37m"
COMMIT, BRANCH, TAG = "\ue000", "\ue001", "\ue002"     # drawn by ../console-font.py
ROOT = sys.argv[1] if len(sys.argv) > 1 else "/srv/origin"
STATE = os.path.expanduser("~/.local/state/fcpm/crew")
INTAKE = os.path.join(ROOT, ".intake", "state.json")
QUIET = 90          # seconds without facts before the box counts as not heard from
STALE = 300         # seconds apart before a line turns to trouble
EDGES = [7 * 2 ** (k / 2) for k in range(11)]          # days: 7, 9.9, 14, … 224; ten blocks
RATES = (1, 3, 8)                                       # commits a day where the mark steps up
FILL = "\ue010\ue011\ue012\ue013"                         # one centred square growing: 3, 6, 9, 12 pixels (../console-font.py)


def shade(rate):
    return " " if not rate else GREY[4] + FILL[sum(1 for r in RATES if rate >= r)]


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


def signed(s, mark=""):
    """(ours lacking, theirs lacking) as one terse mark: −9, +3, ±2/5."""
    if s is None:
        return mark + "?"
    a, b = s
    return mark + (f"−{b}" if b and not a else f"+{a}" if a and not b else f"±{a}/{b}")


def history(times, now):
    """Ten log blocks, a divider, seven days: commits a day, in grey."""
    if not times:
        return " " * 10 + GREY[1] + "┊" + " " * 7 + OFF
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
        cells.append(shade(n / (min(hi, born + 1) - lo)))
    cells.append(GREY[1] + "┊")
    for d in range(6, -1, -1):
        cells.append(" " if born < d else shade(days.count(d)))
    return "".join(cells) + OFF


def forks(repo, main, branches, now):
    """A ⑂ per branch, newest first: bright with work this week, grey when quiet, dark once merged."""
    out = []
    for sha in branches.values():
        t = known(repo, "log", "-1", "--format=%ct", sha, "--")
        merged = known(repo, "merge-base", "--is-ancestor", sha, main) is not None
        t = int(t) if t else 0
        out.append((t, GREY[2] if merged else GREY[5] if now - t < 7 * 86400 else GREY[3]))
    return [c for _, c in sorted(out, reverse=True)]


def mb(n):
    """Megabytes without a leading zero: .2M, 5.3M, 37M."""
    if n is None:
        return ""
    m = n / (1 << 20)
    return (f"{m:.1f}".lstrip("0") if m < 9.95 else f"{m:.0f}") + "M"


def last(t, now):
    if not t:
        return ""
    lt, ln = time.localtime(t), time.localtime(now)
    if lt[:3] == ln[:3]:
        return GREY[5] + time.strftime("%H:%M", lt)
    if now - t < 6.5 * 86400:
        return GREY[4] + time.strftime("%a", lt)
    date = time.strftime("%b", lt) + f"{lt.tm_mday:>3}" if lt.tm_year == ln.tm_year else time.strftime("%Y", lt)
    return (GREY[3] if now - t < 30 * 86400 else GREY[2]) + date


class Seen:
    def __init__(self):
        self.lock = threading.Lock()
        self.grid = (80, 25)
        self.facts, self.heard = None, 0.0
        self.rows, self.since = [], {}
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
            row = {"owner": owner, "name": repo, "sha": theirs.get("heads/main"), "bytes": t.get("bytes"),
                   "branches": {k: v for k, v in seen.items() if k.startswith("heads/") and k != "heads/main"
                                and not k.startswith("heads/github/")},
                   "tags": sorted(k[len("tags/"):] for k in seen if k.startswith("tags/")),
                   "times": [], "forks": [], "apart": None, "github": None}
            if r and main:
                out = known(r, "log", "--format=%ct", main)
                row["times"] = [int(x) for x in out.split()] if out else []
                row["forks"] = forks(r, main, row["branches"], now)
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
                    row["github"] = "" if gh == mine["heads/main"] else signed(steps(r, mine["heads/main"], gh))
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


def size(n):
    if n is None:
        return ""
    for unit in ("B", "K", "M", "G", "T"):
        if n < 1024 or unit == "T":
            return f"{n:.0f}{unit}" if unit in ("B", "K") or n >= 10 else f"{n:.1f}{unit}"
        n /= 1024


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
    return surface + fit(" " + left, C - len(right)) + right + OFF


def line(C, row, now, w):
    count, gh = len(row["times"]), row["github"]
    text = (f" {PAPER}{row['name']:<{w}} " + history(row["times"], now)
            + f" {GREY[2] if (row['bytes'] or 0) < 1 << 20 else GREY[3]}{mb(row['bytes']):>5}"
            + f" {GREY[3]}{COMMIT}{PAPER}{count if count else '':<4}"
            + " " + fit("".join(c + BRANCH for c in row["forks"]), 8) + " "
            + fit(last(row["times"][0] if row["times"] else 0, now), 6) + " "
            + fit((GREY[2] + "github") if gh == "" else (LIT + "github" + gh) if gh else "", 9))
    tail = (PAPER + row["apart"]) if row["apart"] else (TAGGED + TAG + PAPER + row["tags"][-1]) if row["tags"] else ""
    sha = GREY[2] + (row["sha"] or "")[:7]
    room = C - visible(text) - 1
    if room < 7 or tail and visible(tail) + 2 + 7 > room:     # a tag's name before the hash
        text += " " + fit(tail, room)
    else:
        text += " " + fit(tail, room - 7) + sha
    text = fit(text, C)
    if row["apart"]:            # on the wedge, everything in ink
        wedge = ON_BAD if now - row["since"] > STALE else ON_MUTED
        text = wedge + re.sub(r"\x1b\[[0-9;]*m", "", text)
    return text + OFF


def paint():
    with S.lock:
        C, R = S.grid
        f, now = S.facts, time.time()
        when, complaint = last_run("standby")
        checked, reach = github()
        trouble = complaint
        if when and now - when > STALE:
            trouble = trouble or f"standby {ago(now - when)}"
        if reach and reach != "ok":
            trouble = trouble or f"github: {reach}"
        if f and f.get("synced") is False:
            trouble = trouble or "clock"
        if f and f.get("size") and f["free"] / f["size"] < 0.1:
            trouble = trouble or f"{size(f['free'])} free"
        clock = time.strftime("%H:%M")
        if not f:
            foot = bar(C, "FC Public Media", clock, ON_MUTED)
        elif now - S.heard > QUIET:
            foot = bar(C, f"— {ago(now - S.heard)}", clock, ON_BAD)
        else:
            stats = "  ".join(x for x in (size(f.get("free")), size(f.get("available")),
                                          f"{f['load']:.2f}" if "load" in f else None, clock) if x)
            foot = bar(C, trouble or "FC Public Media", stats, ON_BAD if trouble else ON_YELLOW)

        owners = {}
        for row in S.rows:
            owners.setdefault(row["owner"], []).append(row)
        room = R - 1 - len(owners)
        w = max((len(r["name"]) for r in S.rows), default=10)
        body = []
        for owner in sorted(owners, key=str.lower):
            rows = owners[owner]
            body.append(bar(C, owner))
            show = rows if len(rows) <= room else rows[:max(0, room - 1)]
            body += [line(C, r, now, w) for r in show]
            if len(show) < len(rows):
                body.append(f" {GREY[3]}+{len(rows) - len(show)}{OFF}")
            room -= len(show) + (len(show) < len(rows))
        lines = body[:R - 1]
        lines += [""] * (R - 1 - len(lines)) + [foot]
        S.dirty = False
    # Each line placed: erasing to the end of a full line would take its last cell with it.
    return "".join(f"\x1b[{i + 1};1H" + l + ("\x1b[K" if visible(l) < C else "") for i, l in enumerate(lines[:R]))


def main():
    threading.Thread(target=listen, daemon=True).start()
    out = sys.stdout
    out.write(PALETTE + "\x1b[?25l\x1b[2J")
    last_tick = ""
    while True:
        tick = time.strftime("%H:%M") + str(int(time.time()) // 10)
        if S.dirty or tick != last_tick:
            out.write(paint())
            out.flush()
            last_tick = tick
        time.sleep(0.2)


if __name__ == "__main__":
    main()
