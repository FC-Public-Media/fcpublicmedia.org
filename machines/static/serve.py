#!/usr/bin/env python3
"""serve — the static job's server: each site in sites.yml, by the LAN name it is asked for.

    python3 machines/static/serve.py           serve on sites.yml's port (or FCPM_STATIC_PORT)
    python3 machines/static/serve.py list      each name, its site and the folder behind it

The name is the request's Host; this machine's lan.yml (machines/lan.py) says which site a name
serves. GET and HEAD only: a route is the file, then <route>.html, then <route>/index.html; a folder
asked without its slash is sent to it; anything else is the site's own 404.html. Nothing here builds,
writes or remembers. System python and PyYAML. See CREW.md.
"""
import importlib.util
import mimetypes
import os
import pathlib
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
STATE = pathlib.Path(os.environ.get("XDG_STATE_HOME") or pathlib.Path.home() / ".local" / "state") / "fcpm"
TYPES = {".woff2": "font/woff2", ".woff": "font/woff", ".ttf": "font/ttf", ".webp": "image/webp",
         ".mjs": "text/javascript", ".webmanifest": "application/manifest+json"}


def load():
    """(port, {site: folder}) from sites.yml."""
    import yaml
    cfg = yaml.safe_load((HERE / "sites.yml").read_text(encoding="utf-8")) or {}
    sites = {}
    for name, site in (cfg.get("sites") or {}).items():
        root = str(site.get("root") or "").replace("{state}", str(STATE))
        sites[name] = pathlib.Path(root) if os.path.isabs(root) else ROOT / root
    return int(os.environ.get("FCPM_STATIC_PORT") or cfg.get("port") or 8480), sites


def names():
    """{LAN name: what it serves}, this machine's, by machines/lan.py (loaded without a __pycache__)."""
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("lan", ROOT / "machines" / "lan.py")
    lan = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(lan)
    return {name: serves for name, (serves, _gear) in lan.load().items()}


PORT, SITES = load()
NAMES = names()


def find(base, route):
    """(path, code) or (redirect, 301) or (None, 404) for a route under a site's folder."""
    base = base.resolve()
    rel = urllib.parse.unquote(route).lstrip("/")
    tries = [rel + "index.html"] if route.endswith("/") else [rel, rel + ".html", rel + "/index.html"]
    for t in tries:
        p = (base / t).resolve()
        if (p == base or base in p.parents) and p.is_file():
            if t.endswith("/index.html") and not route.endswith("/"):
                return route + "/", 301
            return p, 200
    p = base / "404.html"
    return (p, 404) if p.is_file() else (None, 404)


class Static(BaseHTTPRequestHandler):
    server_version = "fcpm-static"

    def log_message(self, fmt, *args):
        pass

    def answer(self, body_too):
        host = (self.headers.get("Host") or "").split(":")[0].rstrip(".").lower()
        site = NAMES.get(host)
        if site not in SITES:
            text = "No site by that name here. Names: %s\n" % ", ".join(
                sorted(n for n, s in NAMES.items() if s in SITES))
            return self.send(404, text.encode(), "text/plain; charset=utf-8", body_too)
        path, code = find(SITES[site], self.path.split("?", 1)[0])
        if code == 301:
            self.send_response(301)
            self.send_header("Location", path)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        if path is None:
            return self.send(404, b"Nothing by that name.\n", "text/plain; charset=utf-8", body_too)
        ctype = TYPES.get(path.suffix.lower()) or mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        if ctype.startswith("text/") and "charset" not in ctype:
            ctype += "; charset=utf-8"
        self.send(code, path.read_bytes(), ctype, body_too)

    def send(self, code, body, ctype, body_too):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if body_too:
            self.wfile.write(body)

    def do_GET(self):
        self.answer(True)

    def do_HEAD(self):
        self.answer(False)


class DualStack(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def main(argv):
    if argv[:1] == ["list"]:
        for name, serves in sorted(NAMES.items()):
            if serves in SITES:
                print("%-36s %-6s %s" % (name, serves, SITES[serves]))
        return 0
    with DualStack(("", PORT), Static) as server:
        print("static: %s on :%d" % (", ".join(sorted(SITES)), PORT), flush=True)
        server.serve_forever()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
