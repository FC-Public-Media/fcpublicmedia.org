"""camera.py -- a studio camera on this host's USB, as a console and operator pages.

see docs/inline/troves/camera/camera.py.md#1"""
import json
import os
import queue
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

MATCH = "Pocket Cinema Camera"
PORT = 8790

# see docs/inline/troves/camera/camera.py.md#2
PROPS = {
    0x5001: {"key": "battery", "name": "Battery", "unit": "%"},
    0x5003: {"key": "resolution", "name": "Resolution", "unit": ""},
    0x5007: {"key": "iris", "name": "Iris", "unit": "f/x100"},
    0x5008: {"key": "focal", "name": "Focal length", "unit": "mm x100"},
    0x5009: {"key": "focus_distance", "name": "Focus distance", "unit": "raw"},
    0x500F: {"key": "iso", "name": "ISO", "unit": ""},
    0xD001: {"key": "shutter", "name": "Shutter speed", "unit": "1/x"},
    0xD002: {"key": "shutter_angle", "name": "Shutter angle", "unit": "deg x100"},
    0xD003: {"key": "focus", "name": "Focus position", "unit": "raw", "note": "0 near, 65536 infinity (community notes)"},
    0xD004: {"key": "wb", "name": "White balance", "unit": "K"},
    0xD005: {"key": "tint", "name": "Tint", "unit": ""},
    0xD006: {"key": "fps", "name": "Project frame rate", "unit": "fps x100"},
    0xD007: {"key": "d007", "name": "Unnamed D007", "unit": "raw", "note": "5 to 60; perhaps the off-speed frame rate"},
    0xD008: {"key": "d008", "name": "Unnamed D008", "unit": "raw"},
    0xD009: {"key": "d009", "name": "Unnamed D009", "unit": "raw"},
    0xD00A: {"key": "d00a", "name": "Unnamed D00A", "unit": "raw"},
    0xD00B: {"key": "nd", "name": "ND filter", "unit": "fixed16", "note": "stops"},
}
BY_KEY = {v["key"]: k for k, v in PROPS.items()}


def to_raw(code, value):
    """see docs/inline/troves/camera/camera.py.md#3"""
    u = PROPS.get(code, {}).get("unit", "raw")
    if u in ("fps x100", "f/x100", "deg x100", "mm x100"):
        return int(round(float(value) * 100))
    if u == "fixed16":
        return int(round(float(value) * 2048))
    if code == 0x5003:
        return str(value)
    return int(value)


def shown(code, raw):
    """What the camera stores, as a person reads it."""
    if raw is None:
        return None
    u = PROPS.get(code, {}).get("unit", "raw")
    if isinstance(raw, str):
        return raw.replace(" x ", " × ") if code == 0x5003 else raw
    if u == "fps x100":
        return ("%.2f" % (raw / 100)).rstrip("0").rstrip(".") + " fps"
    if u == "f/x100":
        return "f/%.1f" % (raw / 100) if raw else "not reported"
    if u == "deg x100":
        return ("%.1f" % (raw / 100)).rstrip("0").rstrip(".") + "°"
    if u == "mm x100":
        return "%d mm" % round(raw / 100)
    if u == "fixed16":
        return ("%.2f" % (raw / 2048)).rstrip("0").rstrip(".") + " stops"
    if u == "1/x":
        return "1/%d" % raw
    if u == "K":
        return "%d K" % raw
    if u == "%":
        return "%d%%" % raw
    return str(raw)


def load_presets():
    import yaml
    with open(os.path.join(HERE, "presets.yml"), encoding="utf-8") as fh:
        return (yaml.safe_load(fh) or {}).get("presets") or []


# ---------------------------------------------------------------- the camera

class Keeper(threading.Thread):
    """The one thread that talks to the camera."""

    def __init__(self):
        super().__init__(daemon=True)
        self.lock = threading.Lock()
        self.jobs = queue.Queue()
        self.cam = None
        self.link = {"state": "looking", "since": time.time(), "note": ""}
        self.info = {}
        self.desc = {}
        self.values = {}
        self.read_at = 0.0
        self.events = []
        self.seq = 0

    def event(self, kind, text):
        with self.lock:
            self.seq += 1
            self.events.append({"seq": self.seq, "t": time.time(), "kind": kind, "text": text})
            del self.events[:-80]

    def set_link(self, state, note=""):
        with self.lock:
            if self.link["state"] != state:
                self.link = {"state": state, "since": time.time(), "note": note}
                changed = True
            else:
                self.link["note"] = note
                changed = False
        if changed:
            self.event("link", {"connected": "Camera connected", "looking": "Camera not connected"}.get(state, state)
                       + (": " + note if note else ""))

    def run(self):
        import comtypes
        comtypes.CoInitialize()
        from ptp import Camera
        while True:
            if self.cam is None:
                try:
                    self.cam = Camera.find(MATCH)
                except Exception as exc:
                    self.cam = None
                    self.set_link("looking", str(exc))
                if self.cam is None:
                    self.set_link("looking", "")
                    self.drain(error="The camera is not connected.")
                    time.sleep(2)
                    continue
                try:
                    info = self.cam.info()
                    desc = {}
                    for code in info["properties"]:
                        try:
                            desc[code] = self.cam.describe(code)
                        except Exception:
                            pass
                    with self.lock:
                        self.info, self.desc = info, desc
                    self.set_link("connected", "%s, firmware %s" % (info["model"], info["firmware"]))
                except Exception as exc:
                    self.drop(exc)
                    continue
            try:
                self.drain(block=0.9)
                self.read_all()
            except Exception as exc:
                self.drop(exc)

    def drop(self, exc):
        if self.cam is not None:
            self.cam.close()
        self.cam = None
        self.set_link("looking", "lost it (%s)" % exc)

    def drain(self, block=0.0, error=None):
        end = time.time() + block
        while True:
            try:
                job = self.jobs.get(timeout=max(0.0, end - time.time()) if block else 0)
            except queue.Empty:
                return
            fn, box, done = job
            if error:
                box["error"] = error
            else:
                try:
                    box["result"] = fn(self.cam)
                except Exception as exc:
                    box["error"] = str(exc)
            done.set()

    def read_all(self):
        vals = {}
        for code in self.desc:
            try:
                vals[code] = self.cam.get(code)
            except Exception as exc:
                if "not supported" in str(exc):
                    continue
                raise
        with self.lock:
            old = self.values
            self.values, self.read_at = vals, time.time()
        for code, v in vals.items():
            if code in old and old[code] != v:
                self.event("change", "%s: %s → %s" % (PROPS.get(code, {}).get("name", "0x%04X" % code),
                                                         shown(code, old[code]), shown(code, v)))

    def ask(self, fn, timeout=15):
        box, done = {}, threading.Event()
        self.jobs.put((fn, box, done))
        if not done.wait(timeout):
            return {"error": "The camera did not answer in %d s." % timeout}
        return box

    # what the pages read -------------------------------------------------------

    def snapshot(self):
        with self.lock:
            props = []
            for code, d in sorted(self.desc.items()):
                p = PROPS.get(code, {"key": "0x%04X" % code, "name": "Unnamed 0x%04X" % code, "unit": "raw"})
                cur = self.values.get(code, d.get("current"))
                row = {"code": "0x%04X" % code, "key": p["key"], "name": p["name"], "unit": p["unit"],
                       "note": p.get("note", ""), "writable": d["writable"], "raw": cur, "shown": shown(code, cur)}
                if "choices" in d:
                    row["choices"] = [{"raw": c, "shown": shown(code, c)} for c in d["choices"]]
                if "min" in d:
                    row.update({"min": d["min"], "max": d["max"], "step": d.get("step") or 1})
                props.append(row)
            return {"link": dict(self.link), "info": {k: v for k, v in self.info.items() if not isinstance(v, list)},
                    "read_at": self.read_at, "props": props, "events": list(self.events[-40:])}


def apply(keeper, preset):
    """Set each value a preset names, then read them all back."""
    wanted = []
    for key, value in (preset.get("settings") or {}).items():
        code = BY_KEY.get(key)
        if code is None:
            return {"error": "Preset %r names %r, which this console doesn't know." % (preset.get("name"), key)}
        wanted.append((code, key, value))

    def run(cam):
        out = []
        for code, key, value in wanted:
            raw = to_raw(code, value)
            try:
                cam.set(code, raw)
                err = None
            except Exception as exc:
                err = str(exc)
            out.append([code, key, raw, err])
        time.sleep(0.4)
        checked = []
        for code, key, raw, err in out:
            try:
                got = cam.get(code)
            except Exception as exc:
                got, err = None, err or str(exc)
            checked.append({"key": key, "name": PROPS[code]["name"], "wanted": shown(code, raw),
                            "got": shown(code, got), "ok": err is None and got == raw, "error": err})
        return checked

    box = keeper.ask(run, timeout=30)
    if "result" in box:
        bad = [c for c in box["result"] if not c["ok"]]
        keeper.event("preset", "Preset %s: %s" % (preset.get("label", preset.get("name")),
                     "all %d set and checked" % len(box["result"]) if not bad else
                     "%d of %d did not take" % (len(bad), len(box["result"]))))
    return box


# ------------------------------------------------------------------ the server

class Handler(BaseHTTPRequestHandler):
    keeper = None

    def log_message(self, *a):
        pass

    def send(self, code, body, ctype="application/json; charset=utf-8"):
        data = body if isinstance(body, bytes) else (json.dumps(body) if not isinstance(body, str) else body).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def page(self, name):
        with open(os.path.join(HERE, name), "rb") as fh:
            self.send(200, fh.read(), "text/html; charset=utf-8")

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/", "/console"):
            return self.page("console.html")
        if path == "/presets":
            return self.page("presets.html")
        if path == "/state":
            return self.send(200, self.keeper.snapshot())
        if path == "/presets.json":
            try:
                return self.send(200, {"presets": load_presets()})
            except Exception as exc:
                return self.send(500, {"error": "presets.yml could not be read: %s" % exc})
        self.send(404, {"error": "no such page"})

    def do_POST(self):
        # Same-origin only: the pages here, not another site in the browser.
        origin = self.headers.get("Origin")
        if origin and origin not in ("http://127.0.0.1:%d" % self.server.server_port,
                                     "http://localhost:%d" % self.server.server_port):
            return self.send(403, {"error": "not from this console"})
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
        except ValueError:
            return self.send(400, {"error": "not JSON"})
        k = self.keeper
        if self.path == "/set":
            code = int(str(body.get("code")), 16) if str(body.get("code", "")).startswith("0x") else BY_KEY.get(body.get("key"))
            if code is None:
                return self.send(400, {"error": "which setting?"})
            try:
                raw = to_raw(code, body["value"]) if body.get("as") == "shown" else body["value"]
            except (KeyError, ValueError):
                return self.send(400, {"error": "that isn't a value"})

            def run(cam):
                cam.set(code, raw)
                return cam.get(code)
            box = k.ask(run)
            if "result" in box:
                k.event("set", "%s set to %s" % (PROPS.get(code, {}).get("name", hex(code)), shown(code, box["result"])))
            return self.send(200 if "result" in box else 409, box)
        if self.path == "/preset":
            try:
                preset = next(p for p in load_presets() if p.get("name") == body.get("name"))
            except StopIteration:
                return self.send(404, {"error": "no preset called %r" % body.get("name")})
            box = apply(k, preset)
            return self.send(200 if "result" in box else 409, box)
        if self.path == "/record":
            on = bool(body.get("on"))
            box = k.ask(lambda cam: cam.record(on) or on)
            if "result" in box:
                k.event("record", "Recording %s" % ("started" if on else "stopped"))
            return self.send(200 if "result" in box else 409, box)
        self.send(404, {"error": "no such action"})


def main(argv):
    cmd = argv[0] if argv and not argv[0].startswith("--") else "console"
    rest = argv[1:] if argv and not argv[0].startswith("--") else argv
    if cmd == "presets":
        for p in load_presets():
            print("%-18s %s" % (p["name"], p.get("label", "")))
        return 0
    k = Keeper()
    k.start()
    if cmd in ("state", "apply"):
        for _ in range(40):
            if k.link["state"] == "connected" and k.read_at:
                break
            time.sleep(0.25)
        if k.link["state"] != "connected":
            print("camera: not connected", file=sys.stderr)
            return 1
        if cmd == "state":
            print(json.dumps(k.snapshot(), indent=1, default=str))
            return 0
        name = rest[0] if rest else ""
        preset = next((p for p in load_presets() if p.get("name") == name), None)
        if not preset:
            print("camera: no preset %r (camera.py presets)" % name, file=sys.stderr)
            return 2
        box = apply(k, preset)
        if "error" in box:
            print("camera: " + box["error"], file=sys.stderr)
            return 1
        for c in box["result"]:
            print("%-4s %-18s wanted %-12s got %s%s" % ("ok" if c["ok"] else "NO", c["name"], c["wanted"], c["got"],
                                                        "  (%s)" % c["error"] if c["error"] else ""))
        return 0 if all(c["ok"] for c in box["result"]) else 1
    if cmd != "console":
        print(__doc__)
        return 2
    port = int(rest[rest.index("--port") + 1]) if "--port" in rest else PORT
    Handler.keeper = k
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    url = "http://127.0.0.1:%d/" % port
    print("camera: console at %s  (presets at %spresets; ctrl-c to stop)" % (url, url), flush=True)
    if "--no-open" not in rest:
        webbrowser.open(url)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
