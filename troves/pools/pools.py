# pools.py — scan this machine's storage pools and show them as a page on
# 127.0.0.1, for as long as the window that ran it stays open: squares at /,
# the timeline at /timeline, where stretches of it are grouped into shows.
#   pools.py [view|scan|key|sample|sample clear|groups]
# Doc: troves/pools/README.md. Config: machines/<profile>/pools.yml.

import functools, json, os, re, shutil, struct, subprocess, sys, threading, time, urllib.parse
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
            "state": state, "short": dur is not None and dur < SHORT_S,
            "level": _levels.get(level_key(f, st))}


# --- loudness: one number per recording, its average level (RMS, dBFS) ------
# Enough to tell a room's background from people talking. Worked out once per
# file by a background pass and kept on disk beside the groups, so a restart
# does not read the pile again. A settled file only: one still being written
# is measured once it settles.

_levels = {}   # level_key -> dBFS
_levels_lock = threading.Lock()


def level_key(f, st):
    return f"{f}|{st.st_size}|{int(st.st_mtime)}"


def levels_file():
    return groups_file().with_name("levels.json")


def measure(path):
    """Average level of a recording in dBFS (-96 for digital silence)."""
    body = as_wav(path)
    if struct.unpack("<H", body[34:36])[0] != 16:
        return None
    pcm = body[44:44 + (len(body) - 44) // 2 * 2]
    if not pcm:
        return -96.0
    try:
        import audioop   # Python 3.12, which fcpm pins; gone in 3.13
        rms = audioop.rms(pcm, 2)
    except ImportError:
        import array
        a = array.array("h"); a.frombytes(pcm[::max(2, len(pcm) // 400000 * 2)])   # a sample of it
        rms = (sum(x * x for x in a) / max(1, len(a))) ** .5
    import math
    return round(20 * math.log10(rms / 32768), 1) if rms else -96.0


def levels_pass(cfg):
    """Measure every settled recording on a folder pool that has no level yet.
    Depot copies are skipped: the page counts a copy once, by name and size."""
    f = levels_file()
    if f.exists():
        try:
            _levels.update(json.loads(f.read_text(encoding="utf-8")))
        except ValueError:
            pass
    while True:
        done = 0
        data = current(cfg)
        for p in data["pools"]:
            if p["kind"] != "folder":
                continue
            for r in p["rows"]:
                for x in r.get("files") or []:
                    if x["state"] == "live":
                        continue
                    try:
                        st = os.stat(x["path"])
                    except OSError:
                        continue
                    k = level_key(x["path"], st)
                    if k in _levels:
                        continue
                    try:
                        lv = measure(x["path"])
                    except (OSError, ValueError, struct.error):
                        lv = None
                    with _levels_lock:
                        _levels[k] = lv
                    done += 1
                    if done % 200 == 0:
                        save_levels()
        if done:
            save_levels()
            with _lock:
                _last["at"] = 0   # the next look carries the new levels
        time.sleep(60)


def save_levels():
    with _levels_lock:
        body = json.dumps(_levels)
    tmp = levels_file().with_suffix(".tmp")
    tmp.write_text(body, encoding="utf-8")
    os.replace(tmp, levels_file())


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
    out = {"at": now, "stages": cfg.get("stages") or {}, "view": cfg.get("view") or {}, "pools": []}
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
            p["base"] = str(base)
        out["pools"].append(p)
    out["removed"] = remember_seen(out)
    return out


# --- what was here and is not now --------------------------------------------
# Every recording a folder pool has shown is remembered (seen.json, beside the
# groups). One that has gone from a folder that is still there is a ghost:
# moved aside into .removed (by this page or by hand), or gone. A pool that is
# not reachable makes no ghosts: its recordings are not gone, only out of sight.

_seen = None


def seen_file():
    return groups_file().with_name("seen.json")


def remember_seen(out):
    global _seen
    if _seen is None:
        try:
            _seen = json.loads(seen_file().read_text(encoding="utf-8"))
        except (OSError, ValueError):
            _seen = {}
    here, changed, removed = set(), False, []
    for p in out["pools"]:
        if p["kind"] != "folder" or not p.get("base"):
            continue
        for r in p["rows"]:
            for f in r.get("files") or []:
                here.add(f["path"])
                if f["path"] not in _seen:
                    _seen[f["path"]] = {k: f[k] for k in ("name", "start", "end", "duration", "bytes")}
                    _seen[f["path"]]["base"] = p["base"]
                    changed = True
                elif f.get("level") is not None and _seen[f["path"]].get("level") is None:
                    _seen[f["path"]]["level"] = f["level"]; changed = True
    for path, f in _seen.items():
        if path in here or not os.path.isdir(f.get("base", "")) or not os.path.isdir(os.path.dirname(path)):
            continue
        aside = Path(f["base"]) / ".removed"
        held = next((str(c) for c in aside.rglob(f["name"])), None) if aside.is_dir() else None
        removed.append(dict(f, path=path, held=held))
    listed = {r["path"] for r in removed}
    bases = {p["base"] for p in out["pools"] if p["kind"] == "folder" and p.get("base")}
    for b in bases:
        for f in recycled(b):
            if f["path"] not in listed and f["path"] not in here:
                removed.append(f)
    if changed:
        tmp = seen_file().with_suffix(".tmp")
        tmp.write_text(json.dumps(_seen), encoding="utf-8")
        os.replace(tmp, seen_file())
    return removed


_bin = {}   # $I file -> what it says, read once


def recycled(base):
    """Recordings from under base that sit in its drive's Recycle Bin. Windows
    keeps, per deleted file, an $I record (original path, size, when) beside
    the file itself ($R, with its original times), so the ghost goes exactly
    where the recording was."""
    out, root = [], Path(Path(base).anchor) / "$RECYCLE.BIN"
    try:
        sids = [d for d in root.iterdir() if d.is_dir()]
    except OSError:
        return out
    for sid in sids:
        try:
            infos = list(sid.glob("$I*"))
        except OSError:
            continue
        for i in infos:
            if str(i) not in _bin:
                rec = None
                try:
                    b = i.read_bytes()
                    ver, size, ft = struct.unpack("<qqq", b[:24])
                    path = (b[28:28 + 2 * struct.unpack("<i", b[24:28])[0]] if ver == 2 else b[24:24 + 520]).decode("utf-16-le").split("\0")[0]
                    r = i.with_name("$R" + i.name[2:])
                    if Path(path).suffix.lower() in AUDIO and r.is_file():
                        st = r.stat()
                        d = length_of(r, st) if r.suffix.lower() in (".aif", ".aiff", ".wav") else None
                        rec = {"name": Path(path).name, "path": path, "bytes": size, "end": st.st_mtime,
                               "start": st.st_mtime - (d or 0), "duration": d, "held": "Recycle Bin",
                               "deleted": ft / 1e7 - 11644473600}
                except (OSError, struct.error, UnicodeDecodeError):
                    rec = None
                _bin[str(i)] = rec
            rec = _bin[str(i)]
            if rec and os.path.normcase(rec["path"]).startswith(os.path.normcase(str(base))):
                out.append(rec)
    return out


def remove_marked(cfg):
    """Move every recording inside a group marked for removal into its pool's
    .removed/<date>/ folder, keeping its place below the pool. Nothing is
    deleted: moving it back undoes it. Returns what moved."""
    data = scan(cfg)
    marked = [g for g in groups() if g.get("remove")]
    moved, size = 0, 0
    day = datetime.now().strftime("%Y-%m-%d")
    for p in data["pools"]:
        if p["kind"] != "folder" or not p.get("base"):
            continue
        base = Path(p["base"])
        for r in p["rows"]:
            for f in r.get("files") or []:
                end = f["start"] + (f["duration"] or 0)
                if f["state"] == "live" or not any(end > g["start"] and f["start"] < g["end"] for g in marked):
                    continue
                src = Path(f["path"])
                dst = base / ".removed" / day / src.relative_to(base)
                dst.parent.mkdir(parents=True, exist_ok=True)
                os.replace(src, dst)
                moved += 1
                size += f["bytes"]
    gs = groups()
    for g in gs:
        if g.get("remove"):
            g["remove"], g["removed"] = False, datetime.now().astimezone().isoformat(timespec="seconds")
    save_groups(gs)
    with _lock:
        _last["at"] = 0
    return {"moved": moved, "bytes": size}


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
    gs = json.loads(f.read_text(encoding="utf-8")) if f.exists() else []
    for g in gs:   # a removal mark is not a name: early marks were saved as one
        if not g.get("show") and g.get("name") == "to remove" and (g.get("remove") or g.get("removed")):
            g["name"] = None
    return gs


def save_groups(gs):
    f = groups_file()
    tmp = f.with_suffix(".tmp")
    tmp.write_text(json.dumps(sorted(gs, key=lambda g: g["start"]), indent=1), encoding="utf-8")
    os.replace(tmp, f)


def group(body):
    """Assign [start, end] to a show, or to a provisional name for what nobody
    has identified yet ("unknown 1"), replacing any group it overlaps; or
    ungroup it, when neither is given."""
    start, end = float(body["start"]), float(body["end"])
    if "remove" in body:
        # Mark (or unmark) the groups this stretch covers. A stretch with none
        # gets a bare mark: no show and no name, only "remove". Unmarking a bare
        # mark takes it away; a named group only loses the flag.
        gs, hit, keep = groups(), False, []
        for g in gs:
            if g["end"] > start and g["start"] < end:
                hit = True
                if not body["remove"] and not g.get("show") and not g.get("name"):
                    continue
                g["remove"] = bool(body["remove"])
            keep.append(g)
        gs = keep
        if not hit and body["remove"]:
            gs.append({"show": None, "name": None, "start": start, "end": end, "remove": True,
                       "files": int(body.get("files") or 0), "sound": float(body.get("sound") or 0),
                       "at": datetime.now().astimezone().isoformat(timespec="seconds")})
        save_groups(gs)
        return gs
    show, name = str(body.get("show") or ""), " ".join(str(body.get("name") or "").split())[:60]
    if not end > start:
        raise ValueError("empty stretch")
    if show and show not in [s["slug"] for s in shows()]:
        raise ValueError("no such show")
    gs = [g for g in groups() if g["end"] <= start or g["start"] >= end]
    if show or name:
        gs.append({"show": show or None, "name": None if show else name, "start": start, "end": end,
                   "files": int(body.get("files") or 0), "sound": float(body.get("sound") or 0),
                   "at": datetime.now().astimezone().isoformat(timespec="seconds")})
    save_groups(gs)
    return gs


def as_wav(path):
    """A recording as WAV bytes, for the page's player: browsers cannot play
    AIFF, which is big-endian PCM, so its samples are swapped into a WAV."""
    raw = Path(path).read_bytes()
    if raw[:4] == b"RIFF":
        return raw
    if raw[:4] != b"FORM" or raw[8:12] not in (b"AIFF", b"AIFC"):
        raise ValueError("not WAV or AIFF")
    i, ch, bits, rate, pcm, swap = 12, 0, 0, 0, b"", True
    while i + 8 <= len(raw):
        cid, n = raw[i:i + 4], struct.unpack(">I", raw[i + 4:i + 8])[0]
        body = raw[i + 8:i + 8 + n]
        if cid == b"COMM":
            ch, _, bits = struct.unpack(">hIh", body[:8])
            e = body[8:18]
            rate = round(int.from_bytes(e[2:10], "big") * 2.0 ** (((e[0] & 0x7f) << 8 | e[1]) - 16383 - 63))
            swap = raw[8:12] == b"AIFF" or body[18:22] not in (b"sowt",)
        elif cid == b"SSND":
            off = struct.unpack(">I", body[:4])[0]
            pcm = body[8 + off:]
        i += 8 + n + (n & 1)
    w = (bits + 7) // 8
    if swap and w > 1:
        b = bytearray(len(pcm) - len(pcm) % w)
        for k in range(w):
            b[k::w] = pcm[w - 1 - k:len(b):w]
        pcm = bytes(b)
    if w == 1:
        pcm = bytes((x + 128) & 0xff for x in pcm)   # AIFF 8-bit is signed, WAV's is not
    head = struct.pack("<4sI4s4sIHHIIHH4sI", b"RIFF", 36 + len(pcm), b"WAVE", b"fmt ", 16, 1, ch, rate,
                       rate * ch * w, ch * w, bits, b"data", len(pcm))
    return head + pcm


_peaks = {}   # (path, size, mtime) -> 512 loudness buckets, 0..1: an envelope is worked out once


def peaks(path, n=512):
    """A recording's envelope: the loudest sample in each of n slices, per
    channel, 0..1: {"ch": [[...], [...]]}. 16-bit PCM only; else flat."""
    st = os.stat(path)
    key = (path, st.st_size, st.st_mtime)
    if key not in _peaks:
        import array
        body = _wavs.get(path) or as_wav(path)   # not wav_of: leave the player's cache alone
        bits, chans = struct.unpack("<H", body[34:36])[0], struct.unpack("<H", body[22:24])[0] or 1
        out = []
        if bits == 16:
            a = array.array("h")
            a.frombytes(body[44:44 + (len(body) - 44) // 2 * 2])
            for c in range(min(chans, 2)):
                ch, env = a[c::chans], [0.0] * n
                size = max(1, -(-len(ch) // n))
                for i in range(n):
                    s = ch[i * size:(i + 1) * size]
                    if s:
                        env[i] = round(max(max(s), -min(s)) / 32768, 3)
                out.append(env)
        _peaks[key] = {"ch": out or [[0.0] * n]}
    return _peaks[key]


_wavs = {}   # path -> bytes, the last few played


def wav_of(path):
    if path not in _wavs:
        if len(_wavs) > 6:
            _wavs.pop(next(iter(_wavs)))
        _wavs[path] = as_wav(path)
    return _wavs[path]


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
            elif self.path.startswith("/peaks?"):
                path = urllib.parse.parse_qs(self.path.split("?", 1)[1]).get("p", [""])[0]
                if not path or not os.path.isfile(path) or not known_path(current(cfg), path):
                    return self.send(403, b"not a pool recording", "text/plain")
                try:
                    self.send(200, json.dumps(peaks(path)).encode(), "application/json")
                except (OSError, ValueError, struct.error) as e:
                    self.send(415, str(e).encode(), "text/plain")
            elif self.path.startswith("/audio?"):
                self.audio(urllib.parse.parse_qs(self.path.split("?", 1)[1]).get("p", [""])[0])
            else:
                self.send(404, b"", "text/plain")

        def audio(self, path):
            """One recording, as WAV, with byte ranges so the player can seek.
            Only a file inside a pool, as with /open."""
            if not path or not os.path.isfile(path) or not known_path(current(cfg), path):
                return self.send(403, b"not a pool recording", "text/plain")
            try:
                body = wav_of(path)
            except (OSError, ValueError, struct.error) as e:
                return self.send(415, str(e).encode(), "text/plain")
            a, b = 0, len(body) - 1
            m = re.match(r"bytes=(\d*)-(\d*)", self.headers.get("Range", ""))
            if m and (m.group(1) or m.group(2)):
                if m.group(1):
                    a, b = int(m.group(1)), int(m.group(2) or b)
                else:
                    a = max(0, len(body) - int(m.group(2)))
                b = min(b, len(body) - 1)
            part = a > 0 or b < len(body) - 1
            self.send_response(206 if part else 200)
            self.send_header("Content-Type", "audio/wav")
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Length", str(b - a + 1))
            if part:
                self.send_header("Content-Range", f"bytes {a}-{b}/{len(body)}")
            self.end_headers()
            try:
                self.wfile.write(body[a:b + 1])
            except (ConnectionError, OSError):
                pass   # the player moved on

        def do_POST(self):
            if self.path == "/remove-marked":
                n = int(self.headers.get("Content-Length", 0)); self.rfile.read(n)
                try:
                    return self.send(200, json.dumps(remove_marked(cfg)).encode(), "application/json")
                except OSError as e:
                    return self.send(500, str(e).encode(), "text/plain")
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
    threading.Thread(target=levels_pass, args=(cfg,), daemon=True).start()
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
            print(f"{(titles.get(g['show']) if g.get('show') else '~' + (g.get('name') or '?')):24} {a:%a %Y-%m-%d %H:%M} -> {b:%a %H:%M}"
                  f"  {g['files']:5} files  {g['sound'] / 3600:4.1f} h sound")
        print(f"({groups_file()})")
    else:
        sys.exit("pools.py [view|scan|key|sample|sample clear|groups]")
