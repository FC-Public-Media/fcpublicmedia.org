#!/usr/bin/env python3
"""page: the origin's screen, painted from the machine it is kept beside (today digitization). The
origin's leash (../leash.py) runs this at the far end of its `ssh -T`, a forced command:

    page.py [ROOT]     read the leash's lines on stdin, paint its console on stdout. ROOT: the
                       origin kept here, /srv/origin. Test here: `leash.py --facts facts.py -- page.py`

One pane per owner, one line per repository, newest commit first: main's hash on the box, how many
commits main holds, its branches and tags, its size there, the age of main's last commit. Those are
read from the box (facts.py) and checked here ref by ref against the origin kept here. A repository
whose branches or tags differ says how far, with this side's hash ("9 behind 674c381": the box's
main lacks 9 of the commits in ours), on a muted wedge, red once it stays apart five minutes. A
difference from GitHub's main (intake's github/main) shows in the same place.
The last pane is the box itself, red with the trouble when there is one.
"""
import calendar, json, os, socket, subprocess, sys, threading, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from facts import refs, repos  # noqa: E402  the same reading on both sides

PALETTE = "\x1b]P0121417\x1b]P22f9e5b\x1b]P3ffc61a\x1b]P6a8841a\x1b]P7ece8e1"   # 0 ink, 2 go, 3 yellow, 6 muted, 7 paper
OFF, BOLD = "\x1b[0m", "\x1b[1m"
ON_YELLOW, ON_MUTED, ON_BAD = "\x1b[43;30m", "\x1b[46;30m", "\x1b[41;37m"
ROOT = sys.argv[1] if len(sys.argv) > 1 else "/srv/origin"
STATE = os.path.expanduser("~/.local/state/fcpm/crew")
INTAKE = os.path.join(ROOT, ".intake", "state.json")
QUIET = 90          # seconds without facts before the box counts as not heard from
STALE = 300         # seconds apart before a line turns to trouble
FRESH = 3600        # a commit this new is bold
HOST = socket.gethostname().split(".")[0]


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
    """Commits in b that a lacks, and in a that b lacks; None when this side lacks one of them."""
    out = known(repo, "rev-list", "--left-right", "--count", f"{a}...{b}")
    return tuple(int(n) for n in out.split()) if out else None


class Seen:
    def __init__(self):
        self.lock = threading.Lock()
        self.grid, self.host = (80, 25), "origin"
        self.facts, self.heard = None, 0.0
        self.rows, self.since = [], {}
        self.dirty = True

    def take(self, msg):
        with self.lock:
            self.dirty = True
            if "hello" in msg:
                h = msg["hello"]
                self.grid, self.host = (h["cols"], h["rows"]), h.get("host", "origin")
            elif "facts" in msg:
                self.facts, self.heard = msg["facts"], time.time()
                self.compare()

    def compare(self):
        here, there = repos(ROOT), self.facts.get("repos", {})
        now, rows, since = time.time(), [], {}
        for name in sorted(set(here) | set(there)):
            owner, repo = name.split("/", 1)
            r = here.get(name)
            mine = refs(r) if r else {}
            t = there.get(name) or {}
            theirs = t.get("refs", {}) if isinstance(t, dict) else {}
            main = theirs.get("heads/main") or mine.get("heads/main")
            row = {"owner": owner, "name": repo, "sha": main, "bytes": t.get("bytes") if isinstance(t, dict) else None,
                   "branches": sum(1 for k in (theirs or mine) if k.startswith("heads/") and not k.startswith("heads/github/")),
                   "tags": sum(1 for k in (theirs or mine) if k.startswith("tags/")),
                   "count": None, "when": 0, "apart": None, "github": None, "even": False}
            if r and main:
                c = known(r, "rev-list", "--count", main)
                row["count"] = int(c) if c else None
                w = known(r, "log", "-1", "--format=%ct", main)
                row["when"] = int(w) if w else 0
            if name not in there:
                row["apart"] = "not on the box"
            elif not r:
                row["apart"] = "only on the box"
            elif mine != theirs:
                a, b = mine.get("heads/main"), theirs.get("heads/main")
                if a != b:
                    s = steps(r, b, a) if a and b else None
                    row["apart"] = (f"{s[1]} behind" if s[1] and not s[0] else f"{s[0]} ahead of" if s[0] and not s[1]
                                    else f"{s[1]} behind, {s[0]} off") if s else "main unknown here,"
                    row["mine"] = a
                else:
                    n = len({k for k in set(mine) | set(theirs) if mine.get(k) != theirs.get(k)})
                    row["apart"] = f"{n} ref{'s' if n != 1 else ''} apart"
            if row["apart"]:
                since[name] = self.since.get(name, now)
                row["since"] = since[name]
            elif r and mine.get("heads/main"):
                gh = mine.get("heads/github/main")         # GitHub's main, as intake last fetched it
                row["even"] = gh == mine["heads/main"]
                if gh and gh != mine["heads/main"]:
                    s = steps(r, mine["heads/main"], gh)
                    row["github"] = (f"github {s[1]} ahead" if s[1] and not s[0] else f"{s[0]} not on github" if s[0] and not s[1]
                                     else f"github {s[1]} ahead, {s[0]} not on it") if s else "github differs"
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
    when = " ".join(lines[starts[-1]].split()[1:3])
    said = [l for l in lines[starts[-1] + 1:] if l.strip()]
    return when, (f"{job}: {said[0]}" if said else None)


def intake():
    try:
        s = json.load(open(INTAKE))
        t = calendar.timegm(time.strptime(s["checked"][:19], "%Y-%m-%dT%H:%M:%S"))
        return time.strftime("%H:%M", time.localtime(t)), s.get("github")
    except (OSError, ValueError, KeyError):
        return None, None


def pad(text, width):
    text = text if len(text) <= width else text[:width - 1] + "…"
    return text + " " * (width - len(text))


def bar(C, left, right="", surface=ON_YELLOW, bold=False):
    right = right + " " if right else ""
    return surface + (BOLD if bold else "") + pad(" " + left, C - len(right)) + right + OFF


def ago(t):
    s = max(0, int(t))
    return (f"{s}s" if s < 60 else f"{s // 60}m" if s < 3600 else f"{s // 3600}h" if s < 86400
            else f"{s // 86400}d" if s < 86400 * 365 else f"{s // (86400 * 365)}y")


def size(n):
    if n is None:
        return ""
    for unit in ("B", "K", "M", "G", "T"):
        if n < 1024 or unit == "T":
            return f"{n:.0f}{unit}" if unit in ("B", "K") or n >= 10 else f"{n:.1f}{unit}"
        n /= 1024


def plural(n, word):
    return f"{n} {word}" if n == 1 else f"{n} {word}{'es' if word.endswith('h') else 's'}"


def line(C, row, now, w):
    sha = (row["sha"] or "")[:7]
    count = "" if row["count"] is None else plural(row["count"], "commit")
    head = (f" {pad(row['name'], w)} {sha:<7}  {count:>11}  {plural(row['branches'], 'branch'):>11}"
            f"  {plural(row['tags'], 'tag') if row['tags'] else '':>7}")
    if row["apart"]:
        tail = row["apart"] + (f" {row['mine'][:7]}" if row.get("mine") else "")
        tail += f"  {ago(now - row['since'])}"
        surface = ON_BAD if now - row["since"] > STALE else ON_MUTED
        return surface + pad(head + "  " + tail, C) + OFF
    tail = row["github"] or f"{size(row['bytes']):>5}  {ago(now - row['when']) if row['when'] else '':>3}"
    text = pad(head + "  " + tail, C)
    return (BOLD + text + OFF) if row["when"] and now - row["when"] < FRESH else text


def paint():
    with S.lock:
        C, R = S.grid
        f, now = S.facts, time.time()
        top = [bar(C, f"{S.host}.local", f"FC Public Media  {time.strftime('%H:%M')}", bold=True)]

        standby, complaint = last_run("standby")
        checked, github = intake()
        trouble = complaint
        if f and f.get("synced") is False:
            trouble = trouble or "clock not synced"
        if f and f.get("size") and f["free"] / f["size"] < 0.1:
            trouble = trouble or f"{size(f['free'])} free"
        if github and github != "ok":
            trouble = trouble or f"github: {github}"
        if not f:
            box = [bar(C, "the box", "waiting", ON_MUTED)]
        else:
            name = f.get("body") or "the box"
            state = f"up {ago(f['up'])} · {size(f['free'])} free of {size(f['size'])}"
            if now - S.heard > QUIET:
                box = [bar(C, name, f"not heard from · {ago(now - S.heard)}", ON_BAD)]
            else:
                box = [bar(C, name, trouble or state, ON_BAD if trouble else ON_YELLOW)]
            cpu = f"{f['cpu'].split(' @ ')[0].replace('(R)', '').replace('(TM)', '')} ×{f['cores']}" if f.get("cpu") else None
            mem = f"{size(f['memory'])} memory, {size(f['available'])} free" if f.get("memory") else None
            box.append(" " + pad(" · ".join(x for x in (f.get("os"), f"Linux {f['kernel']}" if f.get("kernel") else None,
                                                        cpu, mem) if x), C - 1))
            clock = {True: "clock synced", False: "clock not synced"}.get(f.get("synced"))
            box.append(" " + pad(" · ".join(x for x in (f.get("address"), f.get("screen"),
                                                        f"load {f['load']:.2f}" if "load" in f else None, clock,
                                                        f"standby {standby[-8:-3]}" if standby else None,
                                                        f"github {checked}" if checked else None) if x), C - 1))

        owners = {}
        for row in S.rows:
            owners.setdefault(row["owner"], []).append(row)
        room = R - len(top) - len(box) - len(owners)
        w = max((len(r["name"]) for r in S.rows), default=10)
        body = []
        for owner, rows in sorted(owners.items(), key=lambda kv: -len(kv[1])):
            rows.sort(key=lambda r: (not r["apart"], -r["when"]))
            apart = sum(1 for r in rows if r["apart"])
            even = sum(1 for r in rows if r["even"])
            right = f"{len(rows) - apart} in step with {HOST} · {even} with github" + (f" · {apart} apart" if apart else "")
            body.append(bar(C, owner, right if f else ""))
            show = rows if len(rows) <= room else rows[:max(0, room - 1)]
            body += [line(C, r, now, w) for r in show]
            if len(show) < len(rows):
                body.append(" " + pad(f"{len(rows) - len(show)} more", C - 1))
            room -= len(show) + (len(show) < len(rows))
        lines = top + body
        lines = lines[:R - len(box)]
        lines += [""] * (R - len(box) - len(lines)) + box
        S.dirty = False
    return "\x1b[H" + "\n".join(l + "\x1b[K" for l in lines[:R])


def main():
    threading.Thread(target=listen, daemon=True).start()
    out = sys.stdout
    out.write(PALETTE + "\x1b[?25l\x1b[2J")
    last = ""
    while True:
        tick = time.strftime("%H:%M") + str(int(time.time()) // 10)
        if S.dirty or tick != last:
            out.write(paint())
            out.flush()
            last = tick
        time.sleep(0.2)


if __name__ == "__main__":
    main()
