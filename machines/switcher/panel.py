#!/usr/bin/env python3
"""panel [--atem HOST] [--port N] -- the switcher's control page: stays joined to the ATEM, every press lands at once."""
import argparse
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from atem import Switcher  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--atem", default=os.environ.get("FCPM_ATEM", "10.1.10.150"))
    ap.add_argument("--port", type=int, default=int(os.environ.get("FCPM_SWITCHER_PORT", "8970")))
    args = ap.parse_args()
    sw = Switcher(args.atem)

    verbs = {
        "pgm": lambda a: sw.program(int(a["src"])),
        "pvw": lambda a: sw.preview(int(a["src"])),
        "cut": lambda a: sw.cut(),
        "auto": lambda a: sw.auto(),
        "ftb": lambda a: sw.fade_to_black(),
        "aux": lambda a: sw.aux(int(a["out"]), int(a["src"])),
        "mv": lambda a: sw.multiview(int(a["window"]), int(a["src"])),
        "mode": lambda a: sw.everything(a["mode"]),
        "switcher-mode": lambda a: sw.mode(a["mode"]),
        "camera-mode": lambda a: sw.camera_format(a["mode"], int(a.get("dest", 255))),
    }

    class Door(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def reply(self, code, body, kind="application/json"):
            data = body if isinstance(body, bytes) else json.dumps(body).encode()
            self.send_response(code)
            self.send_header("Content-Type", kind)
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if self.path == "/now":
                return self.reply(200, sw.snapshot())
            if self.path in ("/", "/index.html"):
                with open(os.path.join(HERE, "panel.html"), "rb") as f:
                    return self.reply(200, f.read(), "text/html; charset=utf-8")
            self.reply(404, {"error": "no such page"})

        def do_POST(self):
            if self.path != "/do":
                return self.reply(404, {"error": "no such verb"})
            try:
                a = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
                verbs[a["verb"]](a)
            except Exception as e:  # noqa: BLE001 -- every refusal goes back to the page as words
                return self.reply(400, {"error": str(e)})
            self.reply(200, {"ok": True})

    ThreadingHTTPServer(("", args.port), Door).serve_forever()


if __name__ == "__main__":
    main()
