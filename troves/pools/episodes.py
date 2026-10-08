"""episodes.py -- the supervisor of released episodes: it admits them to post.

    episodes.py tick      one pass: admit each released episode not yet admitted
    episodes.py status    each released episode, and its take in post

Release hands an episode on, and this is what it is handed to (the production
crew runs `tick` every few minutes: crews/production/services). A held episode
is left alone. A released one is admitted to post (troves/post/README.md,
*Admission*): what releasing rendered (its show, out name, pipeline and
recordings) becomes a take, a folder on E:\\POST that carries its whole route.
From there the pools page is no longer the one talking about it; post's
workers take its steps, and the disk is the record of how far it got.

What is admitted is the ejected config if releasing wrote one (what was
released is what runs), else what the pools server renders now: the show's
pipeline, read fresh, and the episode's recordings less what is marked for
removal. Admitting the same release twice finds the same take, so a pass that
is interrupted is simply run again.

The pools server stays the one writer of the groups: the episode is read from
it, and its admission comes back to it as an event on the episode (/supervised,
step `admit`). Nothing is remembered here.
"""
import json
import os
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

POOLS = os.environ.get("POOLS_URL", "http://127.0.0.1:8091")
HERE = Path(__file__).resolve().parent
POST = HERE.parent / "post" / "post.py"
STAGE = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "editing-bay-1" / "crew" / "admit"


def get(path):
    with urllib.request.urlopen(POOLS + path, timeout=60) as r:
        return json.load(r)


def post(path, body):
    req = urllib.request.Request(POOLS + path, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


def admitted(g):
    """The take this release was admitted as, if it was."""
    evs = [e for e in g.get("events") or [] if e.get("phase") == "supervised" and e.get("step") == "admit"
           and e.get("release") == g.get("released") and e.get("state") == "done"]
    return evs[-1].get("job") if evs else None


def ejected(g):
    rel = [e for e in g.get("events") or [] if e.get("phase") == "release" and e.get("at") == g.get("released")]
    cfg = rel[-1].get("config") if rel else None
    return Path(cfg) if cfg and Path(cfg).exists() else None


def clips_of(g, groups):
    """What plays in the episode: its recordings, less what is marked for removal."""
    out = []
    for pool in get("/now").get("pools") or []:
        for row in pool.get("rows") or []:
            for f in row.get("files") or []:
                if not g["start"] <= (f["start"] + f["end"]) / 2 <= g["end"]:
                    continue
                if any(r.get("remove") and r["start"] < f["end"] and r["end"] > f["start"] for r in groups):
                    continue
                out.append({"path": f["path"], "start": f["start"], "end": f["end"]})
    return sorted(out, key=lambda c: c["start"])


def admit(config):
    """post.py admit CONFIG, with this Python (pyyaml is in it). The take's folder, or why not."""
    r = subprocess.run([sys.executable, str(POST), "admit", str(config)], capture_output=True, text=True, encoding="utf-8")
    m = re.search(r"admitted: (.+)$", r.stdout.strip())
    if r.returncode or not m:
        raise RuntimeError((r.stderr or r.stdout).strip().splitlines()[-1] if (r.stderr or r.stdout).strip() else f"exit {r.returncode}")
    return Path(m.group(1).strip()).name


def tick():
    d = get("/groups")
    groups = d["groups"]
    for g in groups:
        if not (g.get("show") and g.get("released")) or admitted(g):
            continue   # held, or already in post
        name = f"{g['show']} released {g['released'][:16]}"
        config = ejected(g)
        if not config:
            clips = clips_of(g, groups)
            doc = post("/render", {"start": g["start"], "end": g["end"], "clips": clips,
                                   "settings": {"by": "episodes"}})["config"]
            STAGE.mkdir(parents=True, exist_ok=True)
            config = STAGE / f"{doc['out']}.{re.sub(r'[^0-9]', '', g['released'])[:14]}.json"
            config.write_text(json.dumps(doc, indent=1), encoding="utf-8")
        try:
            take = admit(config)
        except RuntimeError as e:
            post("/supervised", {"start": g["start"], "end": g["end"], "step": "admit", "release": g["released"],
                                 "state": "failed", "why": str(e)})
            print(f"{name}: not admitted: {e}", flush=True)
            continue
        post("/supervised", {"start": g["start"], "end": g["end"], "step": "admit", "release": g["released"],
                             "state": "done", "job": take})
        print(f"{name}: admitted to post as {take}", flush=True)


def status():
    d = get("/groups")
    out = [g for g in d["groups"] if g.get("show") and g.get("released")]
    held = sum(1 for g in d["groups"] if g.get("show") and not g.get("released"))
    if not out:
        print(f"no episode is released ({held} held): release one from its episode panel, in transcript time")
    for g in out:
        take = admitted(g)
        print(f"{g['show']}  released {g['released'][:16]}  " + (f"in post as {take} (fcpm post)" if take else "not admitted yet"))


if __name__ == "__main__":
    verb = sys.argv[1] if len(sys.argv) > 1 else "status"
    run = {"tick": tick, "status": status}.get(verb)
    if not run:
        sys.exit(__doc__.split("\n\n")[1])
    try:
        run()
    except OSError as e:   # the pools server is not up: nothing to do this pass
        sys.exit(f"episodes: the pools server did not answer ({e})")
