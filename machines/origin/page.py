#!/usr/bin/env python3
"""page: the origin's screen, painted from the machine it is kept beside (today digitization). The
origin's leash (../leash.py) runs this at the far end of its `ssh -T`, a forced command:

    page.py [ROOT]     read the leash's lines on stdin, paint its console on stdout. ROOT: the
                       origin kept here, /srv/origin. Test here: `leash.py --facts facts.py -- page.py`

What is out of step is the inbox: one line per repository whose branches and tags differ there, and
inbox zero when the standby has caught up. Its bar says how many are in step; `latest`, at the
bottom, the last few events, its bar the box's own state, red with the trouble when there is one.
"""
import collections, json, os, sys, threading, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from facts import digest, repos  # noqa: E402  the same digest on both sides

PALETTE = "\x1b]P0121417\x1b]P22f9e5b\x1b]P3ffc61a\x1b]P6a8841a\x1b]P7ece8e1"   # 0 ink, 2 go, 3 yellow, 6 muted, 7 paper
OFF, BOLD, BAD = "\x1b[0m", "\x1b[1m", "\x1b[31m"
ON_YELLOW, ON_MUTED, ON_BAD = "\x1b[43;30m", "\x1b[46;30m", "\x1b[41;37m"
ROOT = sys.argv[1] if len(sys.argv) > 1 else "/srv/origin"
STANDBY_LOG = os.path.expanduser("~/.local/state/fcpm/crew/standby.log")
QUIET = 90          # seconds without facts before the box counts as not heard from
STALE = 300         # seconds out of step before a line turns to trouble


class Seen:
    def __init__(self):
        self.lock = threading.Lock()
        self.grid, self.host = (80, 25), "origin"
        self.facts, self.heard = None, 0.0
        self.apart = {}                 # name -> (what, since)
        self.log = collections.deque(maxlen=6)
        self.dirty = True

    def event(self, text, bad=False):
        self.log.append((time.strftime("%H:%M"), text, bad))

    def take(self, msg):
        with self.lock:
            self.dirty = True
            if "hello" in msg:
                h = msg["hello"]
                self.grid, self.host = (h["cols"], h["rows"]), h.get("host", "origin")
                self.event("screen up")
            elif "facts" in msg:
                self.facts, self.heard = msg["facts"], time.time()
                self.compare()

    def compare(self):
        here = {name: digest(r) for name, r in repos(ROOT).items()}
        there = self.facts.get("repos", {})
        now, apart = time.time(), {}
        for name in sorted(set(here) | set(there)):
            if name not in there:
                what = "missing"
            elif name not in here:
                what = "only there"
            elif here[name] != there[name]:
                what = "behind"
            else:
                if name in self.apart:
                    self.event(f"{name} · in step")
                continue
            was = self.apart.get(name)
            apart[name] = (what, was[1] if was and was[0] == what else now)
            if not was:
                self.event(f"{name} · {what}")
        self.apart = apart
        self.in_step = len(set(here) & set(there)) - sum(1 for w, _ in apart.values() if w == "behind")


S = Seen()


def listen():
    for line in sys.stdin:
        try:
            S.take(json.loads(line))
        except (ValueError, KeyError, TypeError, OSError):
            continue
    sys.exit(0)


def standby_trouble():
    """The last standby run's first complaint, if it had one."""
    try:
        lines = open(STANDBY_LOG, encoding="utf-8", errors="replace").read().splitlines()[-200:]
    except OSError:
        return None
    last = [l for l in lines[max((i for i, l in enumerate(lines) if l.startswith("--- ")), default=-1) + 1:] if l.strip()]
    return f"standby: {last[0]}" if last else None


def pad(text, width):
    text = text if len(text) <= width else text[:width - 1] + "…"
    return text + " " * (width - len(text))


def title(C, left, right="", surface=ON_YELLOW, bold=False):
    right = right + " " if right else ""
    return surface + (BOLD if bold else "") + pad(" " + left, C - len(right)) + right + OFF


def ago(t):
    s = max(0, int(time.time() - t))
    return f"{s // 60}m" if s < 3600 else f"{s // 3600}h" if s < 86400 else f"{s // 86400}d"


def size(n):
    for unit in ("B", "K", "M", "G", "T"):
        if n < 1024 or unit == "T":
            return f"{n:.0f}{unit}"
        n /= 1024


def paint():
    with S.lock:
        C, R = S.grid
        f, now = S.facts, time.time()
        lines = [title(C, f"{S.host}.local", f"FC Public Media  {time.strftime('%H:%M')}", bold=True)]
        if not f:
            lines.append(title(C, "origin", "waiting", ON_MUTED))
        elif now - S.heard > QUIET:
            lines.append(title(C, "origin", f"not heard from · {ago(S.heard)}", ON_BAD))
        elif S.apart:
            lines.append(title(C, "origin", f"catching up · {len(S.apart)}"))
        else:
            lines.append(title(C, "origin", f"standby · {S.in_step} in step", ON_MUTED))
        for name, (what, since) in sorted(S.apart.items(), key=lambda kv: kv[1][1]):
            late = now - since > STALE
            right = f"{what}  {ago(since)} "
            lines.append((ON_BAD if late else ON_MUTED) + pad(" " + name, C - len(right)) + right + OFF)
        latest = [f" {when}  " + (BAD if bad else "") + pad(text, C - 9) + OFF for when, text, bad in S.log][-4:]
        trouble = standby_trouble()
        if f and f.get("synced") is False:
            trouble = trouble or "clock not synced"
        if f and f.get("size") and f["free"] / f["size"] < 0.1:
            trouble = trouble or f"{size(f['free'])} free"
        state = f"up {ago(now - f['up'])} · {size(f['free'])} free" if f else ""
        latest.append(title(C, "latest", trouble or state, ON_BAD if trouble else ON_YELLOW))
        lines = lines[:R - len(latest)]
        lines += [""] * (R - len(latest) - len(lines)) + latest
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
