#!/usr/bin/env python3
"""bounce -- the captive page of the island network: every name lands here, phones' probes open the sheet.

Serves page/ to anyone; a phone on the island (10.97.97.0/24) asking any other host is sent to the page.
GET /captive is the RFC 8908 API (captive until the phone presses release, and again once it rejoins). POST /release, POST /report.
Says what happens on the loudspeaker (BOUNCE_SAY, host:port); keeps reports only when a person sends one.
"""
import ipaddress, json, os, secrets, socket, sys, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAGE = HERE / "page"
STATE = Path(os.environ.get("BOUNCE_STATE", HERE / "state"))
BOX = os.environ.get("BOUNCE_ADDR", "10.97.97.1")
ISLAND = ipaddress.ip_network(os.environ.get("BOUNCE_NET", "10.97.97.0/24"))
SAY = os.environ.get("BOUNCE_SAY", "digitization.local:9797")
PORT = int(os.environ.get("BOUNCE_PORT", "80"))
LEASES = Path(os.environ.get("BOUNCE_LEASES", "/run/fcpm-bounce/leases"))
HOME = f"http://{BOX}/"

PROBES = {
    "/hotspot-detect.html": ("apple", 200, "text/html", "<HTML><HEAD><TITLE>Success</TITLE></HEAD><BODY>Success</BODY></HTML>"),
    "/library/test/success.html": ("apple", 200, "text/html", "<HTML><HEAD><TITLE>Success</TITLE></HEAD><BODY>Success</BODY></HTML>"),
    "/generate_204": ("android", 204, None, ""),
    "/gen_204": ("android", 204, None, ""),
    "/connecttest.txt": ("windows", 200, "text/plain", "Microsoft Connect Test"),
    "/ncsi.txt": ("windows", 200, "text/plain", "Microsoft NCSI"),
    "/canonical.html": ("firefox", 200, "text/html", '<meta http-equiv="refresh" content="0;url=https://support.mozilla.org/kb/captive-portal"/>'),
    "/success.txt": ("firefox", 200, "text/plain", "success\n"),
}
TYPES = {".html": "text/html; charset=utf-8", ".js": "text/javascript", ".css": "text/css", ".svg": "image/svg+xml", ".json": "application/json"}

released, seen = set(), set()


def say(what):
    print(what, flush=True)
    host, _, port = SAY.rpartition(":")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.sendto(f"bounce\t{what}\n".encode(), (host, int(port)))
    except OSError:
        pass


def watch_leases():
    """A lease whose expiry moves is a phone that just (re)joined or renewed: its release ends."""
    last, stamp = {}, None
    while True:
        try:
            st = LEASES.stat().st_mtime
            if st != stamp:
                stamp, now = st, {}
                for line in LEASES.read_text().splitlines():
                    f = line.split()
                    if len(f) >= 3:
                        now[f[2]] = f[0]
                for ip, exp in now.items():
                    if last.get(ip) not in (None, exp) and ip in released:
                        released.discard(ip)
                        say(f"{ip} rejoined: captive again")
                last = now
        except OSError:
            pass
        time.sleep(1)


class Door(BaseHTTPRequestHandler):
    server_version = "bounce"
    sys_version = ""

    def log_message(self, *a):
        pass

    def send(self, code, body=b"", ctype=None, extra=()):
        if isinstance(body, str):
            body = body.encode()
        self.send_response(code)
        if ctype:
            self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        for k, v in extra:
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def client(self):
        return self.client_address[0]

    def on_island(self):
        try:
            return ipaddress.ip_address(self.client()) in ISLAND
        except ValueError:
            return False

    def free(self):
        return self.client() in released

    def first(self, what):
        key = (self.client(), what)
        if key not in seen:
            seen.add(key)
            say(f"{self.client()} {what}")

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        host = (self.headers.get("Host") or "").split(":")[0]
        mine = host in (BOX, "") or not self.on_island()
        if path in PROBES and host != BOX:
            kind, code, ctype, body = PROBES[path]
            if self.free():
                say(f"{self.client()} {kind} probe: online")
                return self.send(code, body, ctype)
            say(f"{self.client()} {kind} probe: sheet")
            return self.send(302, "", None, [("Location", HOME)])
        if path == "/captive":
            self.first("asked the captive API")
            api = {"captive": not self.free(), "user-portal-url": HOME}
            return self.send(200, json.dumps(api), "application/captive+json")
        if not mine:
            return self.send(302, "", None, [("Location", HOME)])
        name = "index.html" if path in ("/", "") else path.lstrip("/")
        file = (PAGE / name).resolve()
        if file.parent != PAGE or not file.is_file():
            return self.send(404, "not here\n", "text/plain")
        if name == "index.html":
            say(f"{self.client()} opened the page" + (" from the link" if "from=link" in self.path else ""))
        extra = [("Content-Disposition", f'attachment; filename="{name}"')] if name.startswith("keep") else []
        self.send(200, file.read_bytes(), TYPES.get(file.suffix, "application/octet-stream"), extra)

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        size = int(self.headers.get("Content-Length") or 0)
        if size > 32768:
            return self.send(413, "too big\n", "text/plain")
        body = self.rfile.read(size)
        if path == "/release":
            released.add(self.client())
            say(f"{self.client()} released")
            return self.send(200, json.dumps({"captive": False}), "application/json")
        if path == "/report":
            try:
                report = json.loads(body)
            except ValueError:
                return self.send(400, "not json\n", "text/plain")
            (STATE / "reports").mkdir(parents=True, exist_ok=True)
            name = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()) + "-" + secrets.token_hex(3) + ".json"
            (STATE / "reports" / name).write_text(json.dumps(report, indent=1) + "\n")
            say(f"{self.client()} sent a report: {name}")
            return self.send(200, json.dumps({"kept": name}), "application/json")
        self.send(404, "not here\n", "text/plain")


class Server(ThreadingHTTPServer):
    def handle_error(self, request, address):
        if not isinstance(sys.exc_info()[1], (ConnectionError, TimeoutError)):
            super().handle_error(request, address)


if __name__ == "__main__":
    say(f"up on :{PORT}, the page at {HOME}")
    threading.Thread(target=watch_leases, daemon=True).start()
    Server(("0.0.0.0", PORT), Door).serve_forever()
