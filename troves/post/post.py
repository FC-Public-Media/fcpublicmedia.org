# post.py — a released take as a folder on the post partition; its progress is nothing but files.
#   post.py [view|status|run [STEP]|admit CONFIG|retry TAKE N|sample|sample clear]
# Doc: troves/post/README.md. Config: machines/<profile>/post.yml.

import functools, hashlib, json, os, re, shutil, socket, subprocess, sys, threading, time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
PORT = int(os.environ.get("POST_PORT", 8093))
HOST = socket.gethostname()
UNITS = {"s": 1, "m": 60, "h": 3600, "d": 86400}
STEP = re.compile(r"^(\d+)-([a-z0-9][a-z0-9-]*)$")


@functools.lru_cache(None)
def profile():
    out = subprocess.run(["sh", str(REPO / "machines" / "sync")], capture_output=True, text=True).stdout
    return next((l.split()[1] for l in out.splitlines() if l.startswith("profile ")), None)


def config():
    f = Path(os.environ["POST_CONFIG"]) if os.environ.get("POST_CONFIG") else \
        REPO / "machines" / (profile() or "-") / "post.yml"
    if not f.exists():
        sys.exit(f"post: {profile() or 'this machine'} declares no post partition (machines/<profile>/post.yml)")
    cfg = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
    cfg["root"] = Path(os.path.expandvars(os.path.expanduser(cfg["root"])))
    cfg["doors"] = Path(os.path.expandvars(os.path.expanduser(cfg.get("doors") or cfg["root"].parent / "DOORS")))
    # Steps: each worn crew's post.yml, this config's own over them; the first crew owns an unmarked release.
    crews = cfg.get("crews") or ([cfg["crew"]] if cfg.get("crew") else [])
    cfg["crews"], cfg["crew"] = list(crews), (crews[0] if crews else None)
    steps = {}
    for c in reversed(cfg["crews"]):
        f = REPO / "crews" / str(c) / "post.yml"
        if f.is_file():
            steps.update((yaml.safe_load(f.read_text(encoding="utf-8")) or {}).get("steps") or {})
    cfg["steps"] = {**steps, **(cfg.get("steps") or {})}
    return cfg


def seconds(text):
    m = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*([smhd])\s*", str(text))
    return float(m.group(1)) * UNITS[m.group(2)] if m else float(text)


def now_iso(t=None):
    return datetime.fromtimestamp(t or time.time()).astimezone().isoformat(timespec="seconds")


# --- the bytes: a folder declares itself by a SHA256SUMS and a rename --------

def sha256(f):
    h = hashlib.sha256()
    with open(f, "rb") as r:
        for b in iter(lambda: r.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def seal(d):
    """Write SHA256SUMS over everything in d (the form sha256sum -c reads)."""
    lines = [f"{sha256(f)}  {f.relative_to(d).as_posix()}"
             for f in sorted(d.rglob("*")) if f.is_file() and f.name != "SHA256SUMS"]
    (d / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def files_of(d):
    return sorted(f for f in d.iterdir() if f.is_file() and f.name != "SHA256SUMS") if d.is_dir() else []


# --- a take: route.json, written once; everything else is read off the folder --

def takes(cfg):
    root = cfg["root"]
    if not root.is_dir():
        return []
    return sorted((d for d in root.iterdir() if d.is_dir() and not d.name.startswith(".") and (d / "route.json").is_file()),
                  key=lambda d: d.name)


def route_of(take):
    return json.loads((take / "route.json").read_text(encoding="utf-8"))


def step_name(n, s):
    return f"{n}-{s['step']}"


def claim_file(take, n, s):
    return take / f".{step_name(n, s)}.claim"


def read_claim(f):
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None   # mid-write, or just taken back: read as held, not as free


def cells(cfg, take, route=None, t=None):
    """Each step of the take as the disk says; the first without an output folder is next."""
    route = route or route_of(take)
    t = t or time.time()
    out, blocked = [], False
    src = take / "0-source"
    out.append({"n": 0, "step": "source", "state": "done" if src.is_dir() else "missing"})
    blocked = not src.is_dir()
    for n, s in enumerate(route["steps"], 1):
        name = step_name(n, s)
        c = {"n": n, "step": s["step"], "here": s["step"] in cfg["steps"]}
        failed, claim = take / f"{name}.failed.json", claim_file(take, n, s)
        if (take / name).is_dir():
            c["state"] = "done"
            c["files"] = len(files_of(take / name))
        elif failed.exists():
            c["state"], blocked = "failed", True
            try:
                c["failed"] = json.loads(failed.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                c["failed"] = {"error": "unreadable failed.json"}
        elif claim.exists():
            k = read_claim(claim) or {}
            c.update(by=k.get("worker"), host=k.get("host"), until=k.get("until"))
            c["state"] = "stale" if k.get("until") and k["until"] < t else "door" if k.get("door") else "held"
            blocked = True
        elif blocked:
            c["state"] = "waiting"
        else:
            c["state"], blocked = "ready", True
        out.append(c)
    return out


def state(cfg):
    t = time.time()
    rows = []
    for take in takes(cfg):
        try:
            r = route_of(take)
            rows.append({"id": take.name, "show": r.get("show"), "out": r.get("out"), "for": r.get("for") or {},
                         "admitted": r.get("admitted"), "cells": cells(cfg, take, r, t)})
        except (OSError, ValueError, KeyError) as e:
            rows.append({"id": take.name, "error": str(e), "cells": []})
    return {"root": str(cfg["root"]), "host": HOST, "here": sorted(cfg["steps"]), "at": now_iso(t), "takes": rows}


# --- admission: a released episode becomes a take -----------------------------

def steps_of(pipeline):
    """`- enhance` or `- transcribe: {engine: whisper}` as the route keeps them: [{step, ...params}]."""
    out = []
    for item in pipeline or []:
        if isinstance(item, str):
            out.append({"step": item})
        elif isinstance(item, dict) and len(item) == 1:
            (k, v), = item.items()
            out.append({"step": str(k), **(v if isinstance(v, dict) else {})})
        else:
            raise ValueError(f"a pipeline step is a name, or a name with settings: {item!r}")
    for s in out:
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", s["step"]):
            raise ValueError(f"a step's name is lowercase letters, digits and dashes: {s['step']!r}")
    return out


def admit(cfg, doc):
    """Make the take, hidden until whole; its id is the out name and route hash, so a re-admit finds it."""
    steps = steps_of((doc.get("pipeline") or {}).get("steps"))
    clips = [c for c in doc.get("clips") or [] if c.get("path")]
    if not clips:
        raise ValueError("nothing to admit: the release names no recordings")
    source = []
    for c in clips:
        p = Path(c["path"])
        if not p.is_file():
            raise ValueError(f"not there: {p}")
        source.append({"name": p.name, "from": str(p), "bytes": p.stat().st_size, "sha256": sha256(p),
                       **{k: c[k] for k in ("start", "end") if c.get(k) is not None}})
    out = re.sub(r"[^A-Za-z0-9._-]+", "-", str(doc.get("out") or "take")).strip("-.") or "take"
    # Whose take: the crew and recipe it was released for; the same recordings for two crews are two takes.
    who = doc.get("for") or {"crew": cfg.get("crew")}
    who = {"crew": who} if isinstance(who, str) else {k: str(v) for k, v in who.items() if v}
    route = {"out": out, "show": doc.get("show"), "for": who, "steps": steps, "source": source,
             "settings": doc.get("settings") or {}}
    digest = hashlib.sha256(json.dumps(route, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    tid = f"{out}.{digest[:8]}"
    take = cfg["root"] / tid
    if take.is_dir():
        return take, False
    cfg["root"].mkdir(parents=True, exist_ok=True)
    tmp = cfg["root"] / f".{tid}.partial"
    shutil.rmtree(tmp, ignore_errors=True)
    (tmp / "0-source").mkdir(parents=True)
    names = set()
    for s in source:
        name = s["name"]
        while name.lower() in names:   # two recordings of one name, from two folders
            name = f"_{name}"
        names.add(name.lower())
        s["as"] = name
        dst = tmp / "0-source" / name
        try:
            os.link(s["from"], dst)   # same volume: no second copy
        except OSError:
            shutil.copy2(s["from"], dst)
    seal(tmp / "0-source")
    route.update(id=tid, sha256=digest, admitted=now_iso(), by=HOST)
    (tmp / "route.json").write_text(json.dumps(route, indent=1, ensure_ascii=False), encoding="utf-8", newline="\n")
    os.replace(tmp, take)
    return take, True


# --- claims: the file is the lock, and a lease says until when ---------------

def try_claim(take, n, s, lease, door=False):
    f = claim_file(take, n, s)
    body = {"worker": f"{HOST}:{os.getpid()}", "host": HOST, "pid": os.getpid(),
            "at": time.time(), "until": time.time() + lease, "door": door, "since": now_iso()}
    try:
        fd = os.open(f, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        k = read_claim(f)
        if not k or k.get("until", 0) >= time.time():
            return None
        try:   # the worker went quiet: only one taker's rename succeeds
            os.rename(f, take / f".{step_name(n, s)}.claim.stale-{int(time.time())}")
        except OSError:
            return None
        return try_claim(take, n, s, lease, door)
    with os.fdopen(fd, "w", encoding="utf-8") as w:
        json.dump(body, w)
    return body


def renew(take, n, s, lease, stop):
    """Push the lease on while the step runs; a worker that dies stops pushing."""
    f = claim_file(take, n, s)
    while not stop.wait(max(5, lease / 3)):
        k = read_claim(f)
        if not k or k.get("pid") != os.getpid() or k.get("host") != HOST:
            return
        k["until"] = time.time() + lease
        tmp = f.with_name(f.name + ".renew")
        tmp.write_text(json.dumps(k), encoding="utf-8")
        os.replace(tmp, f)


def fail(take, n, s, **why):
    f = take / f"{step_name(n, s)}.failed.json"
    f.write_text(json.dumps({"host": HOST, "at": now_iso(), **why}, indent=1, ensure_ascii=False), encoding="utf-8")


def release_claim(take, n, s):
    try:
        claim_file(take, n, s).unlink()
    except OSError:
        pass


def input_of(take, n, route):
    return take / ("0-source" if n == 1 else step_name(n - 1, route["steps"][n - 2]))


def declare(take, n, s, partial):
    seal(partial)
    os.replace(partial, take / step_name(n, s))
    release_claim(take, n, s)


def retry(cfg, tid, n):
    take = cfg["root"] / tid
    route = route_of(take)
    s = route["steps"][int(n) - 1]
    f = take / f"{step_name(int(n), s)}.failed.json"
    if not f.exists():
        raise ValueError("nothing failed there")
    os.replace(f, take / f".{step_name(int(n), s)}.failed-{int(time.time())}.json")   # kept, out of the way


# --- running a step: a command, or a door -------------------------------------

def run_command(cfg, take, n, s, spec, route):
    """A command step: {in} the step before's folder, {out} the partial; its output to a hidden log."""
    lease = seconds(spec.get("lease", "30m"))
    partial = take / f".{step_name(n, s)}.partial"
    shutil.rmtree(partial, ignore_errors=True)
    partial.mkdir()
    subs = {"in": str(input_of(take, n, route)), "out": str(partial), "take": str(take),
            "here": str(HERE), "repo": str(REPO), "python": sys.executable, **{f"step.{k}": str(v) for k, v in s.items()}}
    cmd = spec["run"]
    argv = [os.path.expandvars(str(a)).format_map(subs) for a in (cmd if isinstance(cmd, list) else [cmd])]
    log = take / f".{step_name(n, s)}.log"
    stop = threading.Event()
    threading.Thread(target=renew, args=(take, n, s, lease, stop), daemon=True).start()
    try:
        with open(log, "w", encoding="utf-8") as w:
            w.write(f"{now_iso()} {HOST} {argv}\n")
            w.flush()
            code = subprocess.run(argv if isinstance(cmd, list) else argv[0], shell=not isinstance(cmd, list),
                                  stdout=w, stderr=subprocess.STDOUT, cwd=str(take)).returncode
    except OSError as e:
        code, msg = -1, str(e)
    else:
        msg = None
    finally:
        stop.set()
    if code == 0 and files_of(partial):
        declare(take, n, s, partial)
        return "done"
    tail = log.read_text(encoding="utf-8", errors="replace").splitlines()[-20:] if log.exists() else []
    fail(take, n, s, run=argv, exit=code, error=msg or ("made nothing" if code == 0 else None), log=tail)
    shutil.rmtree(partial, ignore_errors=True)
    release_claim(take, n, s)
    return "failed"


def door_dirs(cfg, s):
    d = cfg["doors"] / s["step"]
    return d / "out", d / "back"


def open_door(cfg, take, n, s, route):
    """A door step: the input goes out under names what comes back can't be mistaken for; the claim waits."""
    out, back = door_dirs(cfg, s)
    out.mkdir(parents=True, exist_ok=True)
    back.mkdir(parents=True, exist_ok=True)
    for k, f in enumerate(files_of(input_of(take, n, route)), 1):
        dst = out / f"{take.name}.{step_name(n, s)}.{k}{f.suffix.lower()}"
        try:
            os.link(f, dst)
        except OSError:
            shutil.copy2(f, dst)
    return "door"


def collect(cfg):
    """A door whose every piece is back: that is the step's output, and the door's copies go."""
    done = []
    for take in takes(cfg):
        route = route_of(take)
        for n, s in enumerate(route["steps"], 1):
            k = read_claim(claim_file(take, n, s)) if claim_file(take, n, s).exists() else None
            if not k or not k.get("door"):
                continue
            out, back = door_dirs(cfg, s)
            stem = f"{take.name}.{step_name(n, s)}."
            sent = sorted(f for f in out.glob(stem + "*") if f.is_file()) if out.is_dir() else []
            got = sorted(f for f in back.iterdir() if f.is_file() and f.name.startswith(stem)) if back.is_dir() else []
            want = {f.name[len(stem):].split(".")[0] for f in sent}
            have = {f.name[len(stem):].split(".")[0].split(" ")[0] for f in got}
            if not want or not want <= have:
                continue
            partial = take / f".{step_name(n, s)}.partial"
            shutil.rmtree(partial, ignore_errors=True)
            partial.mkdir()
            ins = files_of(input_of(take, n, route))
            for f in got:   # back under the name it went out as: piece k is the input's k-th file
                k = f.name[len(stem):].split(".")[0].split(" ")[0]
                name = ins[int(k) - 1].stem if k.isdigit() and 0 < int(k) <= len(ins) else f.name[len(stem):]
                while (partial / f"{name}{f.suffix.lower()}").exists():
                    name = f"_{name}"
                shutil.move(str(f), str(partial / f"{name}{f.suffix.lower()}"))
            declare(take, n, s, partial)
            for f in sent:
                f.unlink(missing_ok=True)
            done.append(f"{take.name} {step_name(n, s)}")
    return done


def run(cfg, only=None, say=print):
    """Every ready step this machine can do, until none is left; doors are opened, not waited on."""
    for line in collect(cfg):
        say(f"back through the door: {line}")
    tried = set()
    while True:
        did = False
        for take in takes(cfg):
            route = route_of(take)
            for c in cells(cfg, take, route):
                if c["state"] not in ("ready", "stale") or c["n"] == 0:
                    continue
                n, s = c["n"], route["steps"][c["n"] - 1]
                spec = cfg["steps"].get(s["step"])
                if not spec or (only and s["step"] != only) or (take.name, n) in tried:
                    continue
                tried.add((take.name, n))
                door = bool(spec.get("door"))
                if not try_claim(take, n, s, seconds(spec.get("lease", "7d" if door else "30m")), door):
                    continue
                say(f"{take.name} {step_name(n, s)} ...")
                r = open_door(cfg, take, n, s, route) if door else run_command(cfg, take, n, s, spec, route)
                say(f"{take.name} {step_name(n, s)} {r}")
                did = True
        if not did:
            return


# --- status in a terminal ------------------------------------------------------

MARK = {"done": "■", "ready": "□", "held": "◐", "door": "◑", "stale": "◌", "failed": "!", "waiting": "·", "missing": "?"}


def status(cfg):
    st = state(cfg)
    print(f"{st['root']}  ({len(st['takes'])} takes; this machine does: {', '.join(st['here']) or 'nothing'})")
    for r in st["takes"]:
        row = "  ".join(f"{MARK[c['state']]} {c['step']}" for c in r["cells"])
        print(f"  {r['id']:36} {row}" + (f"  {r['error']}" if r.get("error") else ""))


# --- the page: served while its window is open --------------------------------

def known_take(cfg, tid):
    take = cfg["root"] / str(tid)
    return take if re.fullmatch(r"[A-Za-z0-9._-]+", str(tid)) and (take / "route.json").is_file() else None


def serve(cfg):
    runs = {"proc": None}

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def send(self, code, body, kind):
            self.send_response(code)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path in ("/", "/index.html"):
                return self.send(200, (HERE / "view.html").read_bytes(), "text/html; charset=utf-8")
            if self.path == "/state":
                st = state(cfg)
                p = runs["proc"]
                st["running"] = bool(p and p.poll() is None)
                return self.send(200, json.dumps(st, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")
            self.send(404, b"", "text/plain")

        def do_POST(self):
            try:
                body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
                if self.path == "/run":
                    p = runs["proc"]
                    if not (p and p.poll() is None):   # one run at a time from this page; claims keep it from colliding with others
                        log = cfg["root"] / f".run-{HOST}.log"
                        cfg["root"].mkdir(parents=True, exist_ok=True)
                        runs["proc"] = subprocess.Popen([sys.executable, str(Path(__file__)), "run"],
                                                        stdout=open(log, "a", encoding="utf-8"), stderr=subprocess.STDOUT,
                                                        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                    return self.send(204, b"", "text/plain")
                take = known_take(cfg, body.get("take"))
                if not take:
                    return self.send(403, b"not a take", "text/plain")
                if self.path == "/retry":
                    retry(cfg, take.name, int(body["n"]))
                    return self.send(204, b"", "text/plain")
                if self.path == "/open":
                    n = body.get("n")
                    d = take
                    if n is not None:
                        route = route_of(take)
                        d = take / ("0-source" if int(n) == 0 else step_name(int(n), route["steps"][int(n) - 1]))
                    subprocess.Popen(["explorer", str(d if d.is_dir() else take)])
                    return self.send(204, b"", "text/plain")
            except (ValueError, KeyError, TypeError, IndexError, OSError) as e:
                return self.send(400, str(e).encode(), "text/plain")
            self.send(404, b"", "text/plain")

    class Server(ThreadingHTTPServer):
        allow_reuse_address = False   # on Windows, True lets a second copy share the port silently

    url = f"http://127.0.0.1:{PORT}/"
    edge = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    show = os.path.exists(edge) and not os.environ.get("POST_NO_OPEN")
    try:
        srv = Server(("127.0.0.1", PORT), H)
    except OSError:
        if show:
            subprocess.Popen([edge, f"--app={url}"])
        sys.exit(f"post: another window is already showing {url}; opened it")
    if show:
        subprocess.Popen([edge, f"--app={url}"])
    print(f"post: showing {url} until this window closes (Ctrl+C)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


# --- sample takes, for a post root that is not the real one -------------------

def sample(cfg, clear=False):
    if not cfg.get("sample"):
        sys.exit("post: this post root is not marked `sample: true`; samples go only where nothing real is")
    if clear:
        for d in list(cfg["root"].iterdir()) if cfg["root"].is_dir() else []:
            shutil.rmtree(d, ignore_errors=True) if d.is_dir() else d.unlink()
        shutil.rmtree(cfg["doors"], ignore_errors=True)
        print(f"cleared {cfg['root']} and {cfg['doors']}")
        return
    src = cfg["root"].parent / "sample-recordings"
    src.mkdir(parents=True, exist_ok=True)
    pipes = [["enhance", "transcribe"], ["copy", "copy-twice"], ["copy", "fail"], ["copy"]]
    for i, steps in enumerate(pipes):
        f = src / f"sample {i + 1}.wav"
        if not f.exists():
            f.write_bytes(b"RIFF" + os.urandom(64))
        take, made = admit(cfg, {"out": f"sample-{i + 1}", "show": "sample", "pipeline": {"steps": steps},
                                 "clips": [{"path": str(f)}]})
        print(f"{'admitted' if made else 'already'} {take.name}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")   # the marks, in cmd's codepage or redirected to a log
    verb = sys.argv[1] if len(sys.argv) > 1 else "view"
    cfg = config()
    try:
        if verb == "view":
            serve(cfg)
        elif verb == "status":
            status(cfg)
        elif verb == "run":
            run(cfg, only=sys.argv[2] if len(sys.argv) > 2 else None,
                say=lambda m: print(f"{now_iso()} {m}", flush=True))
        elif verb == "admit" and len(sys.argv) > 2:
            text = Path(sys.argv[2]).read_text(encoding="utf-8")
            take, made = admit(cfg, yaml.safe_load(text))
            print(f"{'admitted' if made else 'already admitted'}: {take}")
        elif verb == "retry" and len(sys.argv) > 3:
            retry(cfg, sys.argv[2], sys.argv[3])
        elif verb == "sample":
            sample(cfg, clear=sys.argv[2:3] == ["clear"])
        else:
            sys.exit("post.py [view|status|run [STEP]|admit CONFIG|retry TAKE N|sample|sample clear]")
    except ValueError as e:
        sys.exit(f"post: {e}")
