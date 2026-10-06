# pools.py — scan this machine's storage pools and show them as a page on
# 127.0.0.1, for as long as the window that ran it stays open.
#   pools.py [view|scan|key|sample|sample clear]
# Doc: troves/pools/README.md. Config: machines/<profile>/pools.yml.

import json, os, re, shutil, struct, subprocess, sys, threading, time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
PORT = 8091
AUDIO = {".wav", ".aif", ".aiff", ".mp3", ".m4a", ".flac", ".caf", ".ogg"}
LIVE_S, FRESH_S, SHORT_S = 90, 24 * 3600, 3.0
STAMP = re.compile(r"(20\d\d)-?(\d\d)-?(\d\d)\D{0,4}?(\d\d)[.:\-h]?(\d\d)[.:\-m]?(\d\d)")


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


def describe(f, st, now):
    """One recording: when it ran, how long, and what state it is in."""
    end = st.st_mtime
    rate = wav_rate(f) if f.suffix.lower() == ".wav" else None
    dur = max(0.0, (st.st_size - 44) / rate) if rate else None
    m = STAMP.search(f.stem)
    if m:
        start = datetime(*map(int, m.groups())).timestamp()
    else:
        start = end - dur if dur is not None else end
    age = now - end
    state = "live" if age < LIVE_S else "fresh" if age < FRESH_S else "settled"
    return {"name": f.name, "start": start, "end": end, "duration": dur, "bytes": st.st_size,
            "state": state, "short": dur is not None and dur < SHORT_S}


def walk(root, now):
    files, other = [], 0
    for dirpath, dirs, names in os.walk(root):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
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
            base.mkdir(parents=True, exist_ok=True)
            cap = size_of(pool["capacity"]) if pool.get("capacity") else shutil.disk_usage(base).total
            order = list(out["stages"])
            subs = sorted([d for d in base.iterdir() if d.is_dir() and not d.name.startswith(".")],
                          key=lambda d: (order.index(d.name) if d.name in order else len(order), d.name)) or [base]
            used = 0
            for d in subs:
                stage = d.name if d.name in out["stages"] else pool.get("stage")
                files, other = walk(d, now)
                b = sum(f["bytes"] for f in files)
                used += b
                p["rows"].append({"id": d.name, "label": out["stages"].get(stage, {}).get("label", d.name),
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
            elif self.path == "/now":
                self.send(200, json.dumps(current(cfg)).encode(), "application/json")
            else:
                self.send(404, b"", "text/plain")

        def do_POST(self):
            if self.path != "/open":
                return self.send(404, b"", "text/plain")
            try:
                path = str(json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}").get("path", ""))
            except (ValueError, AttributeError):
                return self.send(400, b"bad request", "text/plain")
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
    pool = next((p for p in cfg["pools"] if p["kind"] == "folder"), None)
    if not pool:
        sys.exit("pools: no folder pool to put samples in")
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
    else:
        sys.exit("pools.py [view|scan|key|sample|sample clear]")
