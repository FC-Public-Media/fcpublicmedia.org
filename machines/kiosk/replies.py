#!/usr/bin/env python3
"""replies: the door's intake for what a wizard made. A wizard is a page that helps a person form
one reply (site/lights.md was the first; /host/ the second; /check-in/ the first public one). The reply travels in a bottle: a
signed transfer, as AC1 frames for a camera, or the same bytes set down over the LAN (POST /drop).
A bottle is KEPT FIRST, as the file it arrived as; on the next pass it is read, checked and applied,
or held with the reason. Nothing is refused at the door, and nothing is applied on arrival.

    replies.py take                 one pass over the inbox: apply what is good, hold what is not
    replies.py status               each room's state, then what is held and why
    replies.py friends              who signs for us: name and fingerprint
    replies.py trust <fp> <name>    add one (a phone's key, from a held reply or the wizard's page)

Under the door's state (~/.local/state/media-node/replies on Linux, %LOCALAPPDATA%\\media-node\\replies):
    inbox/      set down, not yet read         applied/     read, good, acted on
    held/       read, not acted on             state/<room>.json   what a room's page reads
    visits.ndjson   one line per check-in shown to us, timed when it was read
    log.ndjson  one line per arrival and per verdict        nonces.json   replies already applied
The signature is read by the composer (verify-bottle.mjs, Node, troves/scanner/composer); without it
the payload's hash is still checked here and the reply is applied as `unverified`. docs/kiosk.md, Replies.
"""
import base64
import datetime
import hashlib
import json
import os
import pathlib
import secrets
import shutil
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
STATE = (pathlib.Path(os.environ["LOCALAPPDATA"]) if "LOCALAPPDATA" in os.environ
         else pathlib.Path.home() / ".local" / "state") / "media-node" / "replies"
COMPOSER = ROOT / "troves" / "scanner" / "composer"
SCHEMA = "fcpm.reply/v0"
TRANSFER = "anecdote.transfer/v1"
MAX_BYTES = 64 * 1024          # a reply is words; a file in a form is a longer bottle, for later
SKEW = datetime.timedelta(days=1)   # `issued` may be this far from our clock: phones drift, bottles wait
NONCES_KEPT = 5000


def now():
    return datetime.datetime.now().astimezone()


def load_yaml(path):
    import yaml
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


# ---- rooms --------------------------------------------------------------------------------------

def rooms():
    """{id: its rooms/<id>.yml}, every room the kiosk knows."""
    out = {}
    for f in sorted((HERE / "rooms").glob("*.yml")):
        cfg = load_yaml(f)
        if cfg.get("room"):
            out[str(cfg["room"])] = cfg
    return out


def room_state(room):
    try:
        return json.loads((STATE / "state" / ("%s.json" % room)).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def room_now(room, cfg=None, at=None):
    """What a room's page shows: hosting only while a reply says so and its `until` has not passed;
    gear lit as the last reply left it, or as `usually:` says while no reply has spoken."""
    cfg = cfg or rooms().get(room) or {}
    at = at or now()
    s = room_state(room)
    hosting = bool(s.get("hosting"))
    if hosting and s.get("until"):
        try:
            hosting = datetime.datetime.fromisoformat(s["until"]) > at
        except ValueError:
            hosting = False
    present = s.get("present") if isinstance(s.get("present"), list) else None
    gear = []
    for g in cfg.get("gear") or []:
        lit = (g["id"] in present) if present is not None else bool(g.get("usually"))
        gear.append({"id": g["id"], "name": g.get("name", g["id"]), "say": g.get("say", ""),
                     "count": g.get("count"), "lit": lit})
    return {"room": room, "hosting": hosting, "host": s.get("host") if hosting else None,
            "since": s.get("since") if hosting else None, "until": s.get("until") if hosting else None,
            "gear": gear, "spoken": present is not None, "trust": s.get("trust")}


# ---- arrivals -------------------------------------------------------------------------------------

def log(entry):
    STATE.mkdir(parents=True, exist_ok=True)
    entry = dict({"at": now().isoformat(timespec="seconds")}, **entry)
    with open(STATE / "log.ndjson", "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def name_for():
    """Sorts by arrival (take() reads in name order), to the microsecond: a line of phones at once."""
    return "%s-%s" % (datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ"), secrets.token_hex(3))


def drop(data, origin="", kind="json"):
    """Keep a bottle exactly as it was set down. Returns its name; `take()` reads it later."""
    if not isinstance(data, (bytes, bytearray)):
        data = str(data).encode("utf-8")
    if len(data) > MAX_BYTES:
        raise ValueError("too big: %d bytes, %d allowed" % (len(data), MAX_BYTES))
    (STATE / "inbox").mkdir(parents=True, exist_ok=True)
    name = name_for()
    (STATE / "inbox" / ("%s.%s" % (name, kind))).write_bytes(bytes(data))
    log({"name": name, "kept": kind, "bytes": len(data), "from": origin})
    return name


def drop_frames(frames, origin=""):
    """AC1 frames as a camera read them, one per line: the eyes' path (troves/scanner page.py)."""
    return drop("\n".join(f for f in frames if isinstance(f, str)), origin, "frames")


def where(name):
    """inbox, applied or held, with the last word said about it; None if never seen."""
    for folder in ("inbox", "applied", "held"):
        if list((STATE / folder).glob(name + ".*")) if (STATE / folder).is_dir() else []:
            why = ""
            try:
                for line in (STATE / "log.ndjson").read_text(encoding="utf-8").splitlines():
                    row = json.loads(line)
                    if row.get("name") == name and row.get("verdict"):
                        why = row.get("why", "")
            except (OSError, ValueError):
                pass
            return {"name": name, "state": folder, "why": why}
    return None


# ---- reading ---------------------------------------------------------------------------------------

def friends():
    try:
        return json.loads((STATE / "friends.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []


def node_exe():
    for c in (shutil.which("node"), pathlib.Path.home() / ".local" / "share" / "pnpm" / "bin" / "node",
              "/usr/local/bin/node", "/usr/bin/node"):
        if c and pathlib.Path(c).is_file():
            return str(c)
    return None


def composer_reads(payload):
    """Ask the composer (verify-bottle.mjs) to read a transfer or frames. None when it cannot be asked."""
    node = node_exe()
    if not node or not (COMPOSER / "transfer.mjs").is_file():
        return None
    try:
        out = subprocess.run([node, str(HERE / "verify-bottle.mjs"), str(COMPOSER)],
                             input=json.dumps(dict(payload, friends=[f["fingerprint"] for f in friends()])),
                             capture_output=True, text=True, timeout=60, cwd=str(ROOT))
        return json.loads(out.stdout) if out.returncode == 0 and out.stdout.strip() else \
            {"ok": False, "errors": ["verifier: " + (out.stderr.strip() or "exit %d" % out.returncode)[:200]]}
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        return {"ok": False, "errors": ["verifier: %r" % exc]}


def hash_ok(transfer):
    """The payload's own check, in Python: its bytes hash to its `hash`."""
    try:
        data = base64.b64decode(transfer["bytes"])
        return "sha256:" + hashlib.sha256(data).hexdigest() == transfer.get("hash"), data
    except (KeyError, TypeError, ValueError):
        return False, None


def read(path):
    """A kept bottle -> (reply dict, meta) or (None, why). meta: by, trust, kind."""
    raw = path.read_bytes()
    if path.suffix == ".frames":
        frames = raw.decode("utf-8", "replace").splitlines()
        v = composer_reads({"frames": frames})
        if v is None:
            return None, "frames need the composer (node and troves/scanner)"
        if not v.get("ok"):
            return None, "; ".join(v.get("errors") or ["unreadable frames"])
        return parse_reply(v.get("text")), {"by": v.get("by"), "kind": v.get("kind"),
                                             "trust": "friend" if v.get("trusted") else "signed"}
    try:
        obj = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return None, "not JSON"
    if not isinstance(obj, dict):
        return None, "not an object"
    if obj.get("schema") == TRANSFER:
        ok, data = hash_ok(obj)
        if not ok:
            return None, "payload hash mismatch"
        v = composer_reads({"transfer": obj})
        if v is None:
            return parse_reply(data.decode("utf-8", "replace")), {
                "by": (obj.get("sig") or {}).get("by"), "kind": obj.get("kind"), "trust": "unverified"}
        if not v.get("ok"):
            return None, "; ".join(v.get("errors") or ["signature"])
        return parse_reply(v.get("text")), {"by": v.get("by"), "kind": v.get("kind"),
                                             "trust": "friend" if v.get("trusted") else "signed"}
    return obj, {"by": None, "kind": None, "trust": "unsigned"}


def parse_reply(text):
    try:
        r = json.loads(text or "")
        return r if isinstance(r, dict) else None
    except ValueError:
        return None


# ---- the wizards known here ------------------------------------------------------------------------

def host_reply(reply, meta):
    """wizard:kiosk+host: somebody is hosting a room (or has left it), and what is in it."""
    cfg = rooms().get(str(reply.get("room") or ""))
    if not cfg:
        return "no such room: %r" % reply.get("room")
    hosting = reply.get("hosting")
    if hosting not in (True, False):
        return "hosting must be true or false"
    host = str(reply.get("host") or "").strip()
    if hosting and not (0 < len(host) <= 40):
        return "host: a name, up to 40 characters"
    until = None
    if hosting and reply.get("until"):
        try:
            until = datetime.datetime.fromisoformat(str(reply["until"]))
            if until.tzinfo is None:
                until = until.astimezone()
        except ValueError:
            return "until: not a time"
        if until <= now():
            return "until has already passed"
    ids = {g["id"] for g in cfg.get("gear") or []}
    present = reply.get("present")
    if present is not None and not (isinstance(present, list) and all(isinstance(p, str) for p in present)):
        return "present: a list of gear ids"
    unknown = [p for p in present or [] if p not in ids]
    state = room_state(cfg["room"])
    new = {"room": cfg["room"], "hosting": hosting, "host": host or state.get("host"),
           "since": state.get("since") if hosting and state.get("hosting") else (now().isoformat(timespec="seconds") if hosting else None),
           "until": until.isoformat(timespec="seconds") if until else None,
           "present": [p for p in present if p in ids] if present is not None else state.get("present"),
           "by": meta.get("by"), "trust": meta.get("trust"),
           "applied": now().isoformat(timespec="seconds"), "wizard_at": reply.get("at")}
    if not hosting:
        new["left"] = now().isoformat(timespec="seconds")
    (STATE / "state").mkdir(parents=True, exist_ok=True)
    tmp = STATE / "state" / ("%s.json.new" % cfg["room"])
    tmp.write_text(json.dumps(new, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, STATE / "state" / ("%s.json" % cfg["room"]))
    note = "%s %s %s" % (host or "somebody", "hosting" if hosting else "left", cfg["room"])
    return None, note + ("; unknown gear ignored: %s" % ", ".join(unknown) if unknown else "")


def checkin_reply(reply, meta):
    """wizard:kiosk+checkin: somebody showed us their check-in. One visit, timed when we read it; when they
    made it (`issued`) is theirs to say. Everything in it may be empty."""
    for key, most in (("name", 80), ("email", 254), ("reason", 80)):
        v = reply.get(key)
        if v is not None and not (isinstance(v, str) and len(v) <= most):
            return "%s: text, up to %d characters" % (key, most)
    visit = {"seen": now().isoformat(timespec="seconds"), "issued": reply.get("issued"),
             "name": reply.get("name"), "email": reply.get("email"), "reason": reply.get("reason"),
             "by": meta.get("by"), "trust": meta.get("trust"), "wizard_at": reply.get("at")}
    STATE.mkdir(parents=True, exist_ok=True)
    with open(STATE / "visits.ndjson", "a", encoding="utf-8") as fh:
        fh.write(json.dumps(visit, ensure_ascii=False) + "\n")
    return None, "%s checked in%s" % (visit["name"] or "somebody", " (%s)" % visit["reason"] if visit["reason"] else "")


def visits(day=None):
    """The check-ins read on `day` (a date; today by default), oldest first."""
    day = day or now().date()
    out = []
    try:
        for line in (STATE / "visits.ndjson").read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            if datetime.datetime.fromisoformat(row["seen"]).date() == day:
                out.append(row)
    except (OSError, ValueError, KeyError):
        pass
    return out


WIZARDS = {"wizard:kiosk+host": host_reply, "wizard:kiosk+checkin": checkin_reply}


def nonces():
    try:
        return json.loads((STATE / "nonces.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []


def examine(reply, meta):
    """The checks every reply passes before its wizard's own: shape, age, and never twice."""
    if reply.get("schema") != SCHEMA:
        return "not a %s" % SCHEMA
    handler = WIZARDS.get(str(reply.get("wizard") or ""))
    if not handler:
        return "unknown wizard: %r" % reply.get("wizard")
    try:
        issued = datetime.datetime.fromisoformat(str(reply.get("issued")))
        if issued.tzinfo is None:
            issued = issued.astimezone()
    except ValueError:
        return "issued: not a time"
    if abs(now() - issued) > SKEW:
        return "issued %s: too far from now" % reply.get("issued")
    nonce = str(reply.get("nonce") or "")
    if not nonce:
        return "no nonce"
    seen = nonces()
    if nonce in seen:
        return "already applied (nonce seen)"
    out = handler(reply, meta)
    verdict, note = out if isinstance(out, tuple) else (out, "")
    if verdict:
        return verdict
    seen.append(nonce)
    (STATE / "nonces.json").write_text(json.dumps(seen[-NONCES_KEPT:]), encoding="utf-8")
    return None, note


def take():
    """One pass: every bottle in the inbox is read, then moved to applied/ or held/. Returns the verdicts."""
    inbox = STATE / "inbox"
    if not inbox.is_dir():
        return []
    out = []
    for path in sorted(inbox.iterdir()):
        if not path.is_file():
            continue
        name = path.stem                      # the name has a dot of its own (the microseconds)
        reply, meta = read(path)
        if reply is None:
            verdict, why = "held", meta
        else:
            res = examine(reply, meta)
            if isinstance(res, tuple):
                verdict, why = "applied", res[1]
            else:
                verdict, why = "held", res
        folder = STATE / verdict
        folder.mkdir(parents=True, exist_ok=True)
        shutil.move(str(path), str(folder / path.name))
        log({"name": name, "verdict": verdict, "why": why, "wizard": (reply or {}).get("wizard"),
             "by": (meta or {}).get("by") if isinstance(meta, dict) else None})
        out.append((name, verdict, why))
    return out


# ---- the command -----------------------------------------------------------------------------------

def status():
    for room, cfg in rooms().items():
        r = room_now(room, cfg)
        lit = [g["id"] for g in r["gear"] if g["lit"]]
        print("%-12s %s%s  gear: %s" % (room, ("hosting: %s until %s" % (r["host"], r["until"])) if r["hosting"] else "nobody hosting",
                                        " (%s)" % r["trust"] if r["spoken"] and r["trust"] else "", ", ".join(lit) or "none"))
    today = visits()
    print("visits today: %d%s" % (len(today), "  last: %s at %s" % (today[-1].get("name") or "somebody", today[-1]["seen"][11:16])
                                   if today else ""))
    held = sorted((STATE / "held").iterdir()) if (STATE / "held").is_dir() else []
    waiting = sorted((STATE / "inbox").iterdir()) if (STATE / "inbox").is_dir() else []
    print("inbox: %d waiting · held: %d" % (len(waiting), len(held)))
    whys = {}
    try:
        for line in (STATE / "log.ndjson").read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            if row.get("verdict") == "held":
                whys[row["name"]] = row.get("why", "")
    except (OSError, ValueError):
        pass
    for p in held[-10:]:
        print("  held  %s  %s" % (p.name, whys.get(p.name.split(".", 1)[0], "")))


def main(argv):
    cmd = argv[1] if len(argv) > 1 else "status"
    if cmd == "take":
        for name, verdict, why in take():
            print("%-8s %s  %s" % (verdict, name, why))
    elif cmd == "status":
        status()
    elif cmd == "friends":
        for f in friends():
            print("%-20s %s" % (f.get("name", ""), f.get("fingerprint", "")))
    elif cmd == "trust" and len(argv) == 4:
        fp, name = argv[2], argv[3]
        if not fp.startswith("key:sha256:"):
            sys.exit("a fingerprint looks like key:sha256:<hex>")
        rows = [f for f in friends() if f.get("fingerprint") != fp] + [{"name": name, "fingerprint": fp}]
        STATE.mkdir(parents=True, exist_ok=True)
        (STATE / "friends.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
        print("trusted %s as %s" % (fp, name))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv)
