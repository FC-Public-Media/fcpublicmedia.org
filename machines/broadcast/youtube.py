#!/usr/bin/env python3
"""youtube -- which episodes don't go to YouTube, and whether one is on our push now.

    python3 -I machines/broadcast/youtube.py                   every episode marked, and what is on now
    python3 -I machines/broadcast/youtube.py mark SHOW no|yes   mark an episode (Cablecast's show id) and push

The marks are youtube.scopes at the top of the broadcast repository, one reader's lines (machines/scopes.py):
show.<id>.youtube.no, with show.<id>.title.<title> beside it for people. Marking commits it in the crew's checkout
(as ../lay keeps it) and pushes to our origin. Cable is never touched: a marked episode airs on 97 as scheduled, and
the relay (./relay) holds YouTube's primary off while it is on our push, so YouTube shows the backup. See PROFILE.md,
"Not to YouTube".
"""
import datetime
import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import cablecast  # noqa: E402
import scopes  # noqa: E402

REPO = pathlib.Path(os.environ.get("FCPM_BROADCAST") or pathlib.Path.home() / ".local/share/fcpm/broadcast")
FILE = "youtube.scopes"
HEAD = "# Episodes that don't go to YouTube (Cablecast show ids). Written by machines/broadcast/youtube.py.\n"
LAG = 30      # seconds our push runs behind the room (./fetch reads three segments behind)
EARLY = 15    # seconds before an airing reaches our push that the primary is let go
LATE = 15     # seconds after it has passed that the primary comes back


def marks(text=None):
    """{show id: title} for every episode marked no."""
    if text is None:
        try:
            text = (REPO / FILE).read_text(encoding="utf-8")
        except OSError:
            return {}
    no, titles = set(), {}
    for ln in scopes.lines_of(text):
        p = scopes.parts(ln)
        if len(p) >= 4 and p[0] == "show" and p[1].isdigit():
            if p[2:4] == ["youtube", "no"]:
                no.add(int(p[1]))
            elif p[2] == "title":
                titles[int(p[1])] = ".".join(p[3:])
    return {i: titles.get(i, "") for i in sorted(no)}


def write(have):
    out = HEAD + "".join("%s\n%s\n" % (scopes.line("show", i, "youtube", "no"), scopes.line("show", i, "title", t))
                         if t else "%s\n" % scopes.line("show", i, "youtube", "no") for i, t in sorted(have.items()))
    (REPO / FILE).write_text(out, encoding="utf-8")


def git(*args):
    return subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True, timeout=60)


def mark(show, youtube, title=""):
    """Mark one episode for YouTube or not, commit, push. ({marks}, None) or ({marks}, why it isn't pushed)."""
    git("fetch", "-q", "origin", "main")
    if git("merge", "-q", "--ff-only", "FETCH_HEAD").returncode:
        return marks(), "the crew's checkout of the broadcast repository has gone its own way; nothing marked"
    have = marks()
    if youtube:
        have.pop(show, None)
    else:
        have[show] = " ".join(title.split()) or have.get(show, "")
    write(have)
    if not git("status", "--porcelain", FILE).stdout.strip():
        return have, None
    git("add", FILE)
    made = git("-c", "user.name=broadcast, on %s" % os.uname().nodename, "-c", "user.email=technology@fcpublicmedia.org",
               "-c", "commit.gpgsign=false", "commit", "-q",   # the machine's commit, as ../lay's are
               "-m", "%s %d %s YouTube" % ("Mark" if not youtube else "Unmark", show, "not for" if not youtube else "back on"),
               "-m", have.get(show) or title or "")
    if made.returncode:
        return have, "kept here, not committed: %s" % made.stderr.strip()[:200]
    pushed = git("push", "-q", "origin", "main")
    return have, (None if pushed.returncode == 0 else "kept here, not pushed: %s" % pushed.stderr.strip()[:200])


def held(now=None, have=None):
    """The marked airing on our push at `now` (with EARLY/LATE around it): {show, title, until} or None."""
    have = marks() if have is None else have
    if not have:
        return None
    now = now or datetime.datetime.now(datetime.timezone.utc)
    room = now - datetime.timedelta(seconds=LAG)
    q = "/scheduleitems?channel=%d&start=%s&end=%s&page_size=200" % (
        cablecast.CHANNEL, (room - datetime.timedelta(hours=6)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        (room + datetime.timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ"))
    items = [i for i in cablecast.call("GET", q)["scheduleItems"] if not i.get("deleted")]
    if not items:
        return None
    ids = sorted({i["show"] for i in items})
    runs = {s["id"]: s.get("totalRunTime") or 0
            for s in cablecast.call("GET", "/shows?%s&page_size=200" % "&".join("ids=%d" % i for i in ids))["shows"]}
    for i in items:
        if i["show"] not in have:
            continue
        start = datetime.datetime.fromisoformat(i["runDateTimeUtc"].replace("Z", "+00:00"))
        end = start + datetime.timedelta(seconds=runs.get(i["show"], 0))
        if start - datetime.timedelta(seconds=EARLY) <= room <= end + datetime.timedelta(seconds=LATE):
            return {"show": i["show"], "title": have[i["show"]] or "show %d" % i["show"],
                    "until": end + datetime.timedelta(seconds=LAG + LATE)}
    return None


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["mark"] and len(args) == 3 and args[1].isdigit() and args[2] in ("no", "yes"):
        have, why = mark(int(args[1]), args[2] == "yes")
        print(why or "marked and pushed")
    elif not args:
        for i, t in marks().items():
            print("%6d  %s" % (i, t))
        h = held()
        print("on our push now: %s" % ("%s, held until %s" % (h["title"], h["until"].astimezone().strftime("%H:%M:%S"))
                                       if h else "nothing marked"))
    else:
        sys.exit(__doc__)
