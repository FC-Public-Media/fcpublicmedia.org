"""episodes.py -- the supervisor of released episodes.

    episodes.py tick      one pass: what each released episode's pipeline can do next
    episodes.py status    each released episode, and where its steps stand

Release hands an episode on, and this is what it is handed to (the production
crew runs `tick` every few minutes: machines/crews/production/services). A held
episode is left alone. A released one goes through its show's pipeline, step
by step, in order: the pipeline in its ejected config if releasing wrote one
(what was released is what runs), else the show's, read fresh.

A step that cannot run here yet waits, and the steps after it wait behind it:
the order is the show's, and transcribing unenhanced sound because enhancing
is not ready would be a different pipeline. So far only `transcribe` (whisper)
runs. Audition's steps wait for its panel (enhance gear/audition). A show that
wants its transcripts first can say so, by putting the step first.

Everything goes through the pools server (POOLS, the one writer of the groups):
the episode is read from it, the transcription is sent to it as a job, and each
step's progress comes back to it as an event on the episode (/supervised).
One job at a time, as the engine wants. Nothing is remembered here.
"""
import json
import os
import sys
import urllib.request
from pathlib import Path

POOLS = os.environ.get("POOLS_URL", "http://127.0.0.1:8091")
RUNS = {"transcribe"}   # the steps this machine can do; the rest wait


def get(path):
    with urllib.request.urlopen(POOLS + path, timeout=60) as r:
        return json.load(r)


def post(path, body):
    req = urllib.request.Request(POOLS + path, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


def say(msg):
    print(msg, flush=True)


def pipeline(g, shows):
    """The steps a released episode goes through, and the clips, if the
    release fixed them: its ejected config's, else the show's own, fresh."""
    rel = [e for e in g.get("events") or [] if e.get("phase") == "release" and e.get("at") == g.get("released")]
    cfg = rel[-1].get("config") if rel else None
    if cfg and Path(cfg).exists():
        import yaml
        doc = yaml.safe_load(Path(cfg).read_text(encoding="utf-8")) or {}
        return (doc.get("pipeline") or {}).get("steps") or [], doc.get("clips"), "ejected"
    s = next((s for s in shows if s["slug"] == g["show"]), None)
    return ((s or {}).get("pipeline") or {}).get("steps") or [], None, "managed"


def where(g, step):
    """The step's last event for this release: (state, event), or (None, None)."""
    evs = [e for e in g.get("events") or [] if e.get("phase") == "supervised"
           and e.get("step") == step and e.get("release") == g.get("released")]
    return (evs[-1]["state"], evs[-1]) if evs else (None, None)


def clips_of(g, groups):
    """What plays in the episode: its recordings, less what is marked for removal."""
    now = get("/now")
    out = []
    for pool in now.get("pools") or []:
        for row in pool.get("rows") or []:
            for f in row.get("files") or []:
                mid = (f["start"] + f["end"]) / 2
                if not g["start"] <= mid <= g["end"]:
                    continue
                if any(r.get("remove") and r["start"] < f["end"] and r["end"] > f["start"] for r in groups):
                    continue
                out.append({"path": f["path"], "start": f["start"], "end": f["end"], "name": f.get("name")})
    return sorted(out, key=lambda c: c["start"])


def tick():
    d = get("/groups")
    groups, shows = d["groups"], d["shows"]
    jobs = {j["id"]: j for j in get("/transcripts")}
    busy = any(j.get("state") == "running" for j in jobs.values())
    for g in groups:
        if not (g.get("show") and g.get("released")):
            continue   # held: left alone
        steps, fixed, how = pipeline(g, shows)
        name = f"{g['show']} {g.get('released', '')[:16]}"
        for st in steps:
            step = next(iter(st)) if isinstance(st, dict) else str(st)
            state, ev = where(g, step)
            if state == "done":
                continue
            if step not in RUNS:
                say(f"{name}: {step} waits ({(st.get(step) or {}).get('by', 'nothing here') if isinstance(st, dict) else 'nothing here'} cannot run it yet); the steps after it wait too")
                break
            if state == "sent":
                j = jobs.get(ev.get("job"))
                if j and j.get("state") == "running":
                    say(f"{name}: {step} being heard ({j.get('done')}/{j.get('total')})")
                    break
                bad = len((j or {}).get("errors") or [])
                post("/supervised", {"start": g["start"], "end": g["end"], "step": step, "release": g["released"],
                                     "state": "done", "job": ev.get("job"), "why": f"{bad} recordings could not be heard" if bad else ""})
                say(f"{name}: {step} done ({ev.get('job')})")
                continue
            if busy:
                say(f"{name}: {step} waits for the engine (another job is running)")
                break
            clips = fixed or clips_of(g, groups)
            if not clips:
                post("/supervised", {"start": g["start"], "end": g["end"], "step": step, "release": g["released"],
                                     "state": "failed", "why": "nothing plays in it"})
                say(f"{name}: {step} failed: nothing plays in it")
                break
            r = post("/transcribe", {"a": g["start"], "b": g["end"], "marks": [{"start": g["start"], "end": g["end"]}],
                                     "clips": clips, "settings": {"by": "episodes", "pipeline": how}})
            post("/supervised", {"start": g["start"], "end": g["end"], "step": step, "release": g["released"],
                                 "state": "sent", "job": r["id"]})
            say(f"{name}: {step} sent ({r['id']}, {len(clips)} recordings, {how})")
            busy = True
            break


def status():
    d = get("/groups")
    for g in d["groups"]:
        if not g.get("show"):
            continue
        if not g.get("released"):
            continue
        steps, _, how = pipeline(g, d["shows"])
        print(f"{g['show']}  released {g['released'][:16]}  ({how})")
        for st in steps:
            step = next(iter(st)) if isinstance(st, dict) else str(st)
            state, ev = where(g, step)
            print(f"  {step:12} {state or ('waiting' if step not in RUNS else 'not yet')}")


if __name__ == "__main__":
    verb = sys.argv[1] if len(sys.argv) > 1 else "status"
    run = {"tick": tick, "status": status}.get(verb)
    if not run:
        sys.exit(__doc__.split("\n\n")[1])
    try:
        run()
    except OSError as e:   # the pools server is not up: nothing to do this pass
        sys.exit(f"episodes: the pools server did not answer ({e})")
