# pools.py — scan this machine's storage pools and show them as a page on
# 127.0.0.1, for as long as the window that ran it stays open: squares at /,
# the timeline at /timeline, where stretches of it are grouped into shows.
#   pools.py [view|scan|key|sample|sample clear|groups]
# Doc: troves/pools/README.md. Config: machines/<profile>/pools.yml.

import functools, json, os, re, shutil, struct, subprocess, sys, threading, time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
PORT = 8091
AUDIO = {".wav", ".aif", ".aiff", ".mp3", ".m4a", ".flac", ".caf", ".ogg"}
SYSTEM = {"System Volume Information"}   # and anything starting "$" or ".": Windows' and macOS's own
LIVE_S, FRESH_S, SHORT_S = 90, 24 * 3600, 3.0
STAMP = re.compile(r"(20\d\d)-?(\d\d)-?(\d\d)\D{0,4}?(\d\d)[.:\-h]?(\d\d)[.:\-m]?(\d\d)")


@functools.lru_cache(None)
def profile():
    out = subprocess.run(["sh", str(REPO / "machines" / "sync")], capture_output=True, text=True).stdout
    return next((l.split()[1] for l in out.splitlines() if l.startswith("profile ")), None)


def config():
    p = profile()
    f = REPO / "machines" / (p or "-") / "pools.yml"
    if not f.exists():
        sys.exit(f"pools: {p or 'this machine'} declares no pools (machines/<profile>/pools.yml)")
    return yaml.safe_load(f.read_text(encoding="utf-8"))


def size_of(text):
    n, unit = str(text).split()
    if unit in ("KB", "MB", "GB", "TB"):
        return int(float(n) * 1000 ** ("B KB MB GB TB".split().index(unit)))
    return int(float(n) * 1024 ** "B KiB MiB GiB TiB".split().index(unit))


def wav_rate(f):
    """Bytes per second from a WAV's fmt chunk, or None."""
    try:
        with open(f, "rb") as h:
            head = h.read(64)
        if head[:4] != b"RIFF" or head[8:12] != b"WAVE":
            return None
        i = head.find(b"fmt ")
        return struct.unpack("<I", head[i + 16:i + 20])[0] if i >= 0 else None
    except OSError:
        return None


def aiff_seconds(f):
    """Length from an AIFF's COMM chunk (frames over an 80-bit float rate), or None."""
    try:
        with open(f, "rb") as h:
            if h.read(12)[:4] != b"FORM":
                return None
            while True:
                c = h.read(8)
                if len(c) < 8:
                    return None
                n = struct.unpack(">I", c[4:])[0]
                if c[:4] == b"COMM":
                    b = h.read(18)
                    frames = struct.unpack(">I", b[2:6])[0]
                    e = b[8:18]
                    rate = int.from_bytes(e[2:10], "big") * 2.0 ** (((e[0] & 0x7f) << 8 | e[1]) - 16383 - 63)
                    return frames / rate if rate else None
                h.seek(n + (n & 1), 1)
    except OSError:
        return None


_lengths = {}   # (path, size, mtime) -> seconds: a header is read once, not every pass


def length_of(f, st):
    key = (str(f), st.st_size, st.st_mtime)
    if key not in _lengths:
        ext = f.suffix.lower()
        if ext == ".wav":
            rate = wav_rate(f)
            _lengths[key] = max(0.0, (st.st_size - 44) / rate) if rate else None
        elif ext in (".aif", ".aiff"):
            _lengths[key] = aiff_seconds(f)
        else:
            _lengths[key] = None
    return _lengths[key]


def describe(f, st, now):
    """One recording: when it ran, how long, and what state it is in.

    It ran until its last write, for as long as it is: Audio Hijack names a
    file for the minute it was armed, which can be long before its first byte
    (enhance/docs/CAPTURE.md). The name's stamp is only for a file whose
    length cannot be read."""
    end = st.st_mtime
    dur = length_of(f, st)
    m = STAMP.search(f.stem)
    if dur is not None:
        start = end - dur
    elif m:
        start = datetime(*map(int, m.groups())).timestamp()
    else:
        start = end
    age = now - end
    state = "live" if age < LIVE_S else "fresh" if age < FRESH_S else "settled"
    return {"name": f.name, "start": start, "end": end, "duration": dur, "bytes": st.st_size,
            "state": state, "short": dur is not None and dur < SHORT_S}


def hidden(name):
    return name.startswith((".", "$")) or name in SYSTEM


def walk(root, now):
    files, other = [], 0
    for dirpath, dirs, names in os.walk(root):
        dirs[:] = [d for d in dirs if not hidden(d)]
        for n in names:
            f = Path(dirpath) / n
            if n.startswith("."):
                continue
            if f.suffix.lower() not in AUDIO:
                other += 1
                continue
            try:
                d = describe(f, f.stat(), now)
            except OSError:
                continue
            d["path"] = str(f)
            files.append(d)
    files.sort(key=lambda d: d["start"])
    return files, other


def depot_shares(pool):
    """The share names kiosk keeps, plus any the server offers beyond them."""
    names = []
    src = pool.get("shares_from")
    if src:
        node = yaml.safe_load((REPO / src).read_text(encoding="utf-8"))
        for g in (node.get("depot") or {}).get("groups") or []:
            for row in g.get("rows") or []:
                names += [(s["share"], s.get("label", s["share"])) for s in row.get("shares") or []]
    try:
        out = subprocess.run(["net", "view", "\\\\" + pool["server"]], capture_output=True, text=True, timeout=15).stdout
        for l in out.splitlines():
            m = re.match(r"^(.+?)\s{2,}Disk\b", l)
            if m and m.group(1).strip() not in [n for n, _ in names]:
                names.append((m.group(1).strip(), m.group(1).strip()))
    except (OSError, subprocess.TimeoutExpired):
        pass
    return names


def scan(cfg):
    now = time.time()
    out = {"at": now, "stages": cfg.get("stages") or {}, "pools": []}
    for pool in cfg.get("pools") or []:
        p = {"name": pool["name"], "title": pool.get("title", pool["name"]), "kind": pool["kind"], "rows": []}
        if pool["kind"] == "smb":
            for share, label in depot_shares(pool):
                root = Path(f"\\\\{pool['server']}\\{share}")
                row = {"id": share, "label": label, "path": str(root),
                       "stage": (pool.get("stage_by_share") or {}).get(share, pool.get("stage"))}
                try:
                    u = shutil.disk_usage(root)
                    row.update(capacity=u.total, used=u.used, free=u.free)
                    row["files"], row["other"] = walk(root, now)
                except OSError as e:
                    row["error"] = "locked" if getattr(e, "winerror", 0) in (5, 1326, 86) else "unreachable"
                p["rows"].append(row)
        else:
            base = Path(os.path.expanduser(pool["path"]))
            if not base.exists():
                if pool.get("create"):
                    base.mkdir(parents=True, exist_ok=True)
                else:
                    p["rows"].append({"id": "-", "label": p["title"], "path": str(base), "error": "unreachable", "files": []})
                    out["pools"].append(p)
                    continue
            cap = size_of(pool["capacity"]) if pool.get("capacity") else shutil.disk_usage(base).total
            order = list(out["stages"])
            subs = sorted([d for d in base.iterdir() if d.is_dir() and not hidden(d.name)],
                          key=lambda d: (order.index(d.name) if d.name in order else len(order), d.name)) or [base]
            used = 0
            for d in subs:
                stage = d.name if d.name in out["stages"] else pool.get("stage")
                files, other = walk(d, now)
                b = sum(f["bytes"] for f in files)
                used += b
                label = out["stages"][d.name]["label"] if d.name in out["stages"] else d.name
                p["rows"].append({"id": d.name, "label": label,
                                  "path": str(d), "stage": stage, "files": files, "other": other, "used": b})
            p.update(capacity=cap, used=used, free=max(0, cap - used))
        out["pools"].append(p)
    return out


# --- the page, and the one thing it may ask of this machine: open Explorer --

_last = {"data": None, "at": 0}
_lock = threading.Lock()


def current(cfg):
    with _lock:
        if time.time() - _last["at"] > 20:
            _last.update(data=scan(cfg), at=time.time())
        return _last["data"]


def shows():
    """The shows FCPM keeps a record of (site/_shows/*.md): slug and title."""
    out = []
    for f in sorted((REPO / "site" / "_shows").glob("*.md")):
        head = f.read_text(encoding="utf-8").split("---")
        meta = yaml.safe_load(head[1]) if len(head) > 2 else {}
        out.append({"slug": meta.get("slug", f.stem), "title": meta.get("title", f.stem)})
    return out


# A group is a stretch of the timeline someone has said belongs to one show.
# Kept on this machine until it is written to the show's own repository.
def groups_file():
    d = Path(os.environ.get("LOCALAPPDATA", Path.home())) / (profile() or "pools") / "pools"
    d.mkdir(parents=True, exist_ok=True)
    return d / "groups.json"


def groups():
    f = groups_file()
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else []


def save_groups(gs):
    f = groups_file()
    tmp = f.with_suffix(".tmp")
    tmp.write_text(json.dumps(sorted(gs, key=lambda g: g["start"]), indent=1), encoding="utf-8")
    os.replace(tmp, f)


def group(body):
    """Assign [start, end] to a show, replacing any group it overlaps; or
    ungroup it, when show is empty."""
    start, end, show = float(body["start"]), float(body["end"]), str(body.get("show") or "")
    if not end > start:
        raise ValueError("empty stretch")
    if show and show not in [s["slug"] for s in shows()]:
        raise ValueError("no such show")
    gs = [g for g in groups() if g["end"] <= start or g["start"] >= end]
    if show:
        gs.append({"show": show, "start": start, "end": end,
                   "files": int(body.get("files") or 0), "sound": float(body.get("sound") or 0),
                   "at": datetime.now().astimezone().isoformat(timespec="seconds")})
    save_groups(gs)
    return gs


def known_path(data, path):
    roots = [r["path"] for p in data["pools"] for r in p["rows"]]
    rp = os.path.normcase(os.path.abspath(path))
    return any(rp == os.path.normcase(r) or rp.startswith(os.path.normcase(r) + os.sep) for r in roots)


def serve(cfg):


    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def send(self, code, body, kind):
            self.send_response(code)
            self.send_header("Content-Type", kind)
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path == "/":
                self.send(200, (HERE / "view.html").read_bytes(), "text/html; charset=utf-8")
            elif self.path == "/timeline":
                self.send(200, (HERE / "timeline.html").read_bytes(), "text/html; charset=utf-8")
            elif self.path == "/now":
                self.send(200, json.dumps(current(cfg)).encode(), "application/json")
            elif self.path == "/groups":
                self.send(200, json.dumps({"shows": shows(), "groups": groups()}).encode(), "application/json")
            else:
                self.send(404, b"", "text/plain")

        def do_POST(self):
            if self.path not in ("/open", "/group"):
                return self.send(404, b"", "text/plain")
            try:
                body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
                if self.path == "/group":
                    return self.send(200, json.dumps({"shows": shows(), "groups": group(body)}).encode(), "application/json")
                path = str(body.get("path", ""))
            except (ValueError, AttributeError, KeyError, TypeError) as e:
                return self.send(400, str(e).encode(), "text/plain")
            if not known_path(current(cfg), path):
                return self.send(403, b"not a pool path", "text/plain")
            arg = ["explorer", "/select,", path] if os.path.isfile(path) else ["explorer", path]
            subprocess.Popen(arg)
            self.send(204, b"", "text/plain")

    class Server(ThreadingHTTPServer):
        allow_reuse_address = False   # on Windows, True lets a second copy share the port silently

    url = f"http://127.0.0.1:{PORT}/"
    edge = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    show = os.path.exists(edge) and not os.environ.get("POOLS_NO_OPEN")
    try:
        srv = Server(("127.0.0.1", PORT), H)
    except OSError:
        if show:
            subprocess.Popen([edge, f"--app={url}"])
        sys.exit(f"pools: another window is already showing {url}; opened it")
    if show:
        subprocess.Popen([edge, f"--app={url}"])
    print(f"pools: showing {url} until this window closes (Ctrl+C)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


# --- sample recordings for the emulated pool, so the page has something real to show

def sample(cfg, clear=False):
    # Only a pool this page made (`create:`), never a real disk that happens to be a folder.
    pool = next((p for p in cfg["pools"] if p["kind"] == "folder" and p.get("create")), None)
    if not pool:
        sys.exit("pools: no emulated pool (kind: folder, create: true) to put samples in")
    base = Path(os.path.expanduser(pool["path"]))
    for f in base.rglob("sample *.wav"):
        f.unlink()
    if clear:
        print(f"cleared the samples in {base}")
        return
    import random
    rnd, now, rate = random.Random(7), time.time(), 1000   # 1 kHz, 8-bit mono: 1 KB a second
    by_age = ["landed", "to-enhance", "to-enhance", "enhanced", "enhanced", "transcribed"]   # older is further along
    n = 0
    for day in range(5, -1, -1):
        t = now - day * 86400 - 9 * 3600
        for _ in range(rnd.randint(4, 9)):
            t += rnd.randint(120, 3600)
            secs = rnd.choice([1, 2, rnd.randint(30, 300), rnd.randint(300, 2400)])
            stage = "declined" if secs < 3 and rnd.random() < .6 else by_age[day]
            if day == 0 and t > now:
                break
            d = base / stage
            d.mkdir(parents=True, exist_ok=True)
            f = d / f"sample {datetime.fromtimestamp(t):%Y-%m-%d at %H.%M.%S}.wav"
            data = bytes(rnd.randint(118, 138) for _ in range(secs * rate))
            f.write_bytes(b"RIFF" + struct.pack("<I", 36 + len(data)) + b"WAVEfmt "
                          + struct.pack("<IHHIIHH", 16, 1, 1, rate, rate, 1, 8) + b"data"
                          + struct.pack("<I", len(data)) + data)
            os.utime(f, (t + secs, t + secs))
            n += 1
    print(f"wrote {n} sample recordings into {base}, by stage")


if __name__ == "__main__":
    verb = sys.argv[1] if len(sys.argv) > 1 else "view"
    cfg = config()
    if verb == "view":
        serve(cfg)
    elif verb == "scan":
        print(json.dumps(scan(cfg), indent=1)[:4000])
    elif verb == "key":
        smb = next((p for p in cfg["pools"] if p["kind"] == "smb"), None)
        if not smb:
            sys.exit("pools: no depot to hold a key for")
        print(f"The depot's password for {smb.get('user', 'FCPM')}, kept in Windows Credential Manager (it does not show as you type):")
        sys.exit(subprocess.run(["cmdkey", f"/add:{smb['server']}", f"/user:{smb.get('user', 'FCPM')}", "/pass"]).returncode)
    elif verb == "sample":
        sample(cfg, clear=sys.argv[2:3] == ["clear"])
    elif verb == "groups":
        titles = {s["slug"]: s["title"] for s in shows()}
        for g in groups():
            a, b = datetime.fromtimestamp(g["start"]), datetime.fromtimestamp(g["end"])
            print(f"{titles.get(g['show'], g['show']):24} {a:%a %Y-%m-%d %H:%M} -> {b:%a %H:%M}"
                  f"  {g['files']:5} files  {g['sound'] / 3600:4.1f} h sound")
        print(f"({groups_file()})")
    else:
        sys.exit("pools.py [view|scan|key|sample|sample clear|groups]")
