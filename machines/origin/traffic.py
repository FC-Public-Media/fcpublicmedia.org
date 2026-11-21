"""traffic -- the origin's listing and its traffic orders: everything the origin holds, read in one look, and
which branches land in main on the next beat, in the order they were given.

    look([owner/repo])           every repository (or one): main, its .issues tape, and each branch: its last
                                 commit, how far it is ahead of main and behind, whether it lands clean or
                                 collides (and on which files), and the issue lines it brings; then the orders
                                 waiting, in turn, and the last ones done. The door's `look`
    order(full, branch, tip, who)  land BRANCH, at the commit TIP it was seen at, on the next beat (`land`)
    hold(full, branch, who)      take a waiting order back (`hold`)
    land(names, who)             intake, each beat, under its lock: each waiting order in turn, merged into main
                                 as the one before left it, by main's own .gitattributes

Orders are a tape, .intake/orders.ndjson, appended to and never rewritten: a line gives an order, takes one back, or says how
one went (landed, collides, moved, already, gone). An order lands only the commit it names: a branch that moved
after it was ordered is not landed, and is said so, to be looked at and ordered again. A landed branch is a
merge commit on main saying who ordered it; intake's landed pass lets the branch go on the same beat, and the
relay carries main out. Stdlib and git. See PROFILE.md, traffic.
"""
import datetime
import json
import os
import re
import subprocess
import time



def root():
    """The origin: /srv/origin, or FCPM_ORIGIN, as asked at the time."""
    return os.environ.get("FCPM_ORIGIN", "/srv/origin")
TAPE = ".issues"
BEAT = 600
LAN_ONLY = ("retain", "library", "librarians")             # the library's branches: never landed
BRANCH = re.compile(r"(?!.*\.\.)(?!.*//)[A-Za-z0-9][A-Za-z0-9._/-]*(?<![./])")
TIP = re.compile(r"[0-9a-f]{40}|[0-9a-f]{64}")
DONE_KEPT = 20


def orders_file():
    return os.path.join(root(), ".intake", "orders.ndjson")


def seen_file():
    return os.path.join(root(), ".intake", "look.json")       # what a merge would do, by repo, main and tip


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def next_beat(at=None):
    at = time.time() if at is None else at
    return datetime.datetime.fromtimestamp(at - at % BEAT + BEAT, datetime.timezone.utc).isoformat(timespec="seconds")


def git(repo, *args, check=False, input=None):
    r = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, encoding="utf-8",
                       errors="replace", input=input, timeout=120)
    if check and r.returncode:
        raise RuntimeError("git %s: %s" % (args[0], r.stderr.strip()[-300:]))
    return r


def ref(repo, name):
    return git(repo, "rev-parse", "--verify", "-q", name).stdout.strip() or None


def holds(repo, a, b):
    """Whether b already holds commit a."""
    return git(repo, "merge-base", "--is-ancestor", a, b).returncode == 0


def library(name):
    return any(name == b or name.startswith(b + "/") for b in LAN_ONLY)


def landable(name):
    return bool(BRANCH.fullmatch(name)) and name != "main" and not name.startswith("github/") and not library(name)


def repos():
    out = []
    for owner in sorted(os.listdir(root())) if os.path.isdir(root()) else []:
        d = os.path.join(root(), owner)
        if owner.startswith(".") or owner == "lost+found" or not os.path.isdir(d):
            continue
        out += [owner + "/" + n for n in sorted(os.listdir(d)) if os.path.isfile(os.path.join(d, n, "HEAD"))]
    return out


# ------------------------------------------------------------------ orders --
def tape():
    try:
        with open(orders_file(), encoding="utf-8") as f:
            return [json.loads(l) for l in f if l.strip()]
    except OSError:
        return []


def write(row):
    os.makedirs(os.path.dirname(orders_file()), exist_ok=True)
    with open(orders_file(), "a", encoding="utf-8") as f:              # one short line, appended whole
        f.write(json.dumps({"at": now(), **row}) + "\n")


def waiting():
    """The orders still to land, in turn: an order given again goes to the back."""
    out = {}
    for row in tape():
        key = (row.get("repo"), row.get("branch"))
        if row.get("order") == "land":
            out.pop(key, None)
            out[key] = row
        elif row.get("order") == "hold" or "done" in row:
            out.pop(key, None)
    return list(out.values())


def done(n=DONE_KEPT):
    return [row for row in tape() if "done" in row or row.get("order") == "hold"][-n:]


def order(full, branch, tip, who):
    """Order BRANCH, as seen at TIP, to land in main on the next beat. Returns a sentence; raises ValueError."""
    p = os.path.join(root(), full)
    if not landable(branch):
        raise ValueError("%s is not a branch that lands (main, github/* and the library's branches never do)" % branch)
    if not TIP.fullmatch(tip):
        raise ValueError("%r is not a commit" % tip)
    at = ref(p, "refs/heads/" + branch)
    if at is None:
        raise ValueError("there is no branch %s in %s" % (branch, full))
    if at != tip:
        raise ValueError("%s has moved since it was looked at (it is at %s now): look again" % (branch, at[:7]))
    main = ref(p, "refs/heads/main")
    if main and holds(p, tip, main):
        raise ValueError("main already holds %s" % branch)
    ahead = [o for o in waiting() if (o["repo"], o["branch"]) != (full, branch)]
    write({"order": "land", "repo": full, "branch": branch, "tip": tip, **who})
    return "%s lands in %s's main on the beat of %s UTC%s" % (
        branch, full, next_beat()[11:16], ", after %d waiting" % len(ahead) if ahead else "")


def hold(full, branch, who):
    if not any((o["repo"], o["branch"]) == (full, branch) for o in waiting()):
        raise ValueError("no order is waiting for %s in %s" % (branch, full))
    write({"order": "hold", "repo": full, "branch": branch, **who})
    return "%s will not land; the order is taken back" % branch


def land(names, who_git):
    """Each waiting order in turn, against main as the one before left it. Returns rows for intake's log."""
    rows = []
    for o in waiting():
        full, branch, tip = o["repo"], o["branch"], o["tip"]
        p = os.path.join(root(), full)
        out = {"repo": full, "branch": branch, "tip": tip}
        main = ref(p, "refs/heads/main") if full in names else None
        at = ref(p, "refs/heads/" + branch) if main else None
        if not main:
            out.update(done="gone", said="the repository is not here")
        elif at != tip and holds(p, tip, main):
            out.update(done="already", said="main already held it")
        elif at is None:
            out.update(done="gone", said="the branch is not here any more")
        elif at != tip:
            out.update(done="moved", said="the branch moved after it was ordered (to %s): look again" % at[:7])
        elif holds(p, tip, main):
            out.update(done="already", said="main already held it")
        else:
            m = git(p, "--attr-source=" + main, "merge-tree", "--write-tree", "--name-only", main, tip)
            if m.returncode == 0:
                tree = m.stdout.split("\n", 1)[0].strip()
                msg = "Land %s\n\nOrdered by %s (%s) at %s; landed on the beat by the origin." % (
                    branch, o.get("holder", "?"), o.get("office", "?"), o.get("at", "?"))
                commit = git(p, *who_git, "commit-tree", tree, "-p", main, "-p", tip, "-m", msg, check=True).stdout.strip()
                git(p, "update-ref", "refs/heads/main", commit, main, check=True)
                out.update(done="landed", main=commit, said="landed in main")
            elif m.returncode != 1:
                out.update(done="refused", main=main, said="git would not merge it: " + m.stderr.strip()[-200:])
            else:
                files = m.stdout.split("\n\n", 1)[0].splitlines()[1:]
                out.update(done="collides", main=main, conflicts=files[:50],
                           said="collides with main on %s; main left alone" % ", ".join(files[:5]))
        write(out)
        row = {"repo": full, "branch": branch, "sha": tip, "state": out["done"], "said": out["said"]}
        if out["done"] == "landed":
            row.update(main=out["main"], did="landed %s by order of %s" % (branch, o.get("holder", "?")))
        rows.append(row)
    return rows


# -------------------------------------------------------------------- look --
def _seen():
    try:
        with open(seen_file(), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _measure(p, main, tip):
    """What landing tip in main would do: how far apart they are, clean or not, and the issue lines it brings."""
    behind, ahead = (int(x) for x in git(p, "rev-list", "--left-right", "--count",
                                         "%s...%s" % (main, tip)).stdout.split() or (0, 0))
    out = {"ahead": ahead, "behind": behind}
    if not ahead:
        out["lands"] = "held"                                   # main holds all of it
        return out
    m = git(p, "--attr-source=" + main, "merge-tree", "--write-tree", "--name-only", main, tip)
    if m.returncode == 0:
        out["lands"] = "clean"
    elif m.returncode == 1:
        out.update(lands="collides", conflicts=m.stdout.split("\n\n", 1)[0].splitlines()[1:][:20])
    else:
        out["lands"] = "unrelated"                              # no history in common: nothing to merge into
        return out
    lines = git(p, "diff", "--no-color", "-U0", "%s...%s" % (main, tip), "--", TAPE).stdout.splitlines()
    out["issues"] = [l[1:] for l in lines if l.startswith("+") and not l.startswith("+++")][:20]
    return out


def look(only=None):
    seen, kept = _seen(), {}
    out = []
    for full in [only] if only else repos():
        p = os.path.join(root(), full)
        main = ref(p, "refs/heads/main")
        here = {"repo": full, "main": main, "began_here": not git(p, "config", "remote.github.url").stdout.strip()}
        if main:
            text = git(p, "show", "%s:%s" % (main, TAPE))
            here["tape"] = [l.partition(" ")[::2] for l in text.stdout.splitlines() if l.strip()] if text.returncode == 0 else None
            gh = ref(p, "refs/heads/github/main")
            if gh and not here["began_here"]:
                behind, ahead = git(p, "rev-list", "--left-right", "--count", "%s...%s" % (gh, main)).stdout.split() or ("0", "0")
                here["github"] = {"ours_ahead": int(ahead), "theirs_ahead": int(behind)}
        branches = []
        fmt = "%(refname:strip=2)%00%(objectname)%00%(committerdate:unix)%00%(authorname)%00%(subject)"
        for line in git(p, "for-each-ref", "--sort=-committerdate", "--format=" + fmt, "refs/heads").stdout.splitlines():
            name, tip, when, author, subject = (line.split("\0") + [""] * 5)[:5]
            if name == "main" or name.startswith("github/"):
                continue
            b = {"name": name, "tip": tip, "when": int(when or 0), "author": author, "said": subject}
            if library(name):
                b["library"] = True
            elif main:
                key = "%s %s %s" % (full, main, tip)
                kept[key] = seen.get(key) or _measure(p, main, tip)
                b.update(kept[key])
            branches.append(b)
        here["branches"] = branches
        out.append(here)
    if not only and kept != seen:
        try:
            tmp = seen_file() + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(kept, f)
            os.replace(tmp, seen_file())
        except OSError:
            pass                                                # a reading not kept is read again next time
    return {"at": now(), "next_beat": next_beat(), "repos": out, "waiting": waiting(), "done": done()}
