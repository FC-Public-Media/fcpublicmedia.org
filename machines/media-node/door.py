"""door — the one address the media node answers on.

    door.py serve        become the door, on [::]:8080
    door.py supervise    run `serve`, and start it again whenever it exits
    door.py              is the door up

Written 2026-09-23 on the studio kiosk (the predecessor of editing bay 2),
after station-node's `bin/door`, whose rules it keeps:

  * ONE PORT, AND IT DOES NOT MOVE. 8080 is what somebody guesses, and an
    address that slides is not one anybody can bookmark. If 8080 is taken the
    door refuses to start rather than picking another.
  * NOT A WEB SERVER. There is no document root. Each surface below is named,
    and a file is served only if it is under a directory named here or is a
    QR image named by kiosk/welcome.yml. A document root grows its own scope
    without anybody deciding it should.
  * DUAL-STACK. The machine's name resolves to IPv6 first. A listener bound
    only to IPv4 refuses a request made by name, and that looks exactly like
    the door being down.

    GET /                  the board: what this node shows
    GET /kiosk/            the welcome screen, rendered from kiosk/welcome.yml
    GET /kiosk/qr/<n>      the QR image for panel n, as welcome.yml names it
    GET /idle/             brand/idle/index.html (?say=... fills its slot)
    GET /wallpaper/<file>  brand/wallpaper/
    GET /revision          what a screen polls: <commit>-<kiosk revision>

THE BOUNCE. Content is read per request, so an edit shows on the next load.
Code is loaded once, so `serve` watches the commit its worktree has checked
out. When it moves (a pull or a rebase), serve exits with code 75 and
`supervise` starts it again. Every HTML page carries a small poller for
/revision and reloads when the value changes. Updating this worktree
therefore bounces the door and every screen showing it, without anybody
walking to the machine.

Stdlib plus PyYAML, which is what bin/build-kiosk.py already needs:

    uv run --no-project --with pyyaml python machines/media-node/door.py serve
"""
import html
import os
import pathlib
import socket
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = pathlib.Path(__file__).resolve().parents[2]
PORT = 8080
BOUNCE = 75          # exit code meaning "my code changed, start me again"
STATE = pathlib.Path(os.environ.get("LOCALAPPDATA", ROOT)) / "media-node"

NAMED_DIRS = {
    "wallpaper": ROOT / "brand" / "wallpaper",
}
TYPES = {".html": "text/html; charset=utf-8", ".svg": "image/svg+xml",
         ".png": "image/png", ".txt": "text/plain; charset=utf-8"}


def git(*args):
    try:
        out = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True,
                             text=True, timeout=10,
                             creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return out.stdout.strip() if out.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def welcome():
    import yaml
    with open(ROOT / "kiosk" / "welcome.yml", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def revision():
    try:
        kiosk = str(welcome().get("revision", "?"))
    except Exception:
        kiosk = "unreadable"
    return "%s-%s" % (git("rev-parse", "--short", "HEAD") or "nogit", kiosk)


# The poller every page carries. Twenty seconds is this machine's choice, not
# the kiosk file's (docs/KIOSK.md: "the interval is the renderer's business").
POLL = """<script>
(function () {
  var seen = null;
  function check() {
    fetch('/revision', {cache: 'no-store'}).then(function (r) { return r.text(); })
      .then(function (v) { if (seen === null) seen = v; else if (v !== seen) location.reload(); })
      .catch(function () {});
  }
  check(); setInterval(check, 20000);
})();
</script>"""


def with_poll(page):
    i = page.lower().rfind("</body>")
    return page[:i] + POLL + page[i:] if i >= 0 else page + POLL


def page(title, body, style=""):
    return with_poll("""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%s</title><style>
:root { --ink:#f4efe6; --dim:#b9b2a6; --ground:#16181c; --line:#2c3037; }
html,body { margin:0; background:var(--ground); color:var(--ink);
  font:18px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif; }
a { color:var(--ink); }
%s</style></head><body>%s</body></html>""" % (html.escape(title), style, body))


def board_page():
    rows = [
        ("/kiosk/", "Welcome screen", "kiosk/welcome.yml, as a guest sees it"),
        ("/idle/", "Idle screen", "brand/idle: the lamp pointed at the room"),
        ("/idle/?say=On+air+now", "Idle, with its slot filled", "?say= fills the marked slot"),
    ]
    for f in sorted(NAMED_DIRS["wallpaper"].glob("*1050x1680.png")):
        rows.append(("/wallpaper/" + f.name, f.stem, "portrait wallpaper, this panel's size"))
    items = "".join('<li><a href="%s">%s</a> <span>%s</span></li>' % (
        html.escape(h, quote=True), html.escape(t), html.escape(d)) for h, t, d in rows)
    body = """<main><h1>FC Public Media &middot; media node</h1>
<p class=dim>%s &middot; revision <code>%s</code></p><ul>%s</ul></main>""" % (
        html.escape(socket.gethostname().lower()), html.escape(revision()), items)
    return page("Media node", body, """main { max-width:44rem; margin:3rem auto; padding:0 16px; }
.dim, li span { color:var(--dim); } li { margin:.6rem 0; } li span { display:block; font-size:.85em; }""")


def kiosk_page():
    w = welcome()
    panels = []
    for i, p in enumerate(w.get("panels") or []):
        qr = ""
        if isinstance(p.get("qr"), dict):
            q = p["qr"]
            qr = '<img src="/kiosk/qr/%d" alt="%s"><p class=encodes>%s</p>' % (
                i, html.escape(q.get("alt", ""), quote=True), html.escape(q.get("encodes", "")))
        panels.append('<section><h2>%s</h2><p class=say>%s</p>%s%s</section>' % (
            html.escape(p.get("panel", "")), html.escape(p.get("say", "")), qr,
            '<p class=note>%s</p>' % html.escape(p["note"]) if p.get("note") else ""))
    body = """<header><p class=place>%s</p><h1>%s</h1></header>%s""" % (
        html.escape(w.get("place", "")), html.escape(w.get("greeting", "")), "".join(panels))
    return page(w.get("place", "Welcome"), body, """
body { min-height:100vh; box-sizing:border-box; padding:6vh 7vw; display:flex; flex-direction:column; gap:4vh; }
.place { color:var(--dim); letter-spacing:.08em; text-transform:uppercase; font-size:1.6vh; margin:0; }
h1 { font-size:3.4vh; line-height:1.25; font-weight:500; margin:.6vh 0 0; }
section { border-top:1px solid var(--line); padding-top:2.4vh; }
h2 { font-size:1.7vh; color:var(--dim); font-weight:500; letter-spacing:.06em; text-transform:uppercase; margin:0; }
.say { font-size:3vh; margin:.8vh 0; }
.note { color:var(--dim); font-size:1.8vh; margin:.6vh 0 0; }
img { width:22vh; height:22vh; background:#fff; padding:1.2vh; border-radius:.6vh; margin-top:1vh; }
.encodes { font-family:ui-monospace,Consolas,monospace; font-size:1.5vh; color:var(--dim); margin:.4vh 0; }""")


def inside(base, rel):
    """The file at base/rel, or None if rel steps outside base or is not a file."""
    target = (base / rel).resolve()
    if base.resolve() not in target.parents or not target.is_file():
        return None
    return target


class Door(BaseHTTPRequestHandler):
    server_version = "media-node-door"

    def log_message(self, fmt, *args):
        log("%s %s" % (self.address_string(), fmt % args))

    def reply(self, code, body, ctype="text/html; charset=utf-8"):
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(data)

    def file(self, path):
        if path is None:
            return self.reply(404, page("Not here", "<p>Nothing by that name.</p>"))
        ctype = TYPES.get(path.suffix.lower(), "application/octet-stream")
        data = path.read_bytes()
        if path.suffix.lower() == ".html":
            data = with_poll(data.decode("utf-8")).encode("utf-8")
        self.reply(200, data, ctype)

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        route = self.path.split("?", 1)[0]
        try:
            if route == "/":
                return self.reply(200, board_page())
            if route == "/revision":
                return self.reply(200, revision(), TYPES[".txt"])
            if route in ("/kiosk", "/kiosk/"):
                return self.reply(200, kiosk_page())
            if route.startswith("/kiosk/qr/"):
                panels = welcome().get("panels") or []
                n = route.rsplit("/", 1)[1]
                if n.isdigit() and int(n) < len(panels) and isinstance(panels[int(n)].get("qr"), dict):
                    return self.file(inside(ROOT / "site" / "assets", pathlib.Path(
                        panels[int(n)]["qr"]["image"]).relative_to("site/assets")))
                return self.file(None)
            if route in ("/idle", "/idle/"):
                return self.file(ROOT / "brand" / "idle" / "index.html")
            head, _, rest = route.strip("/").partition("/")
            if head in NAMED_DIRS and rest:
                return self.file(inside(NAMED_DIRS[head], rest))
            return self.file(None)
        except Exception as exc:          # a broken data file is a page, not a dead door
            log("error on %s: %r" % (route, exc))
            return self.reply(500, page("Something is wrong",
                "<main style='padding:5vh'><h1>This screen could not be drawn.</h1><p>%s</p></main>"
                % html.escape(repr(exc))))


class DualStack(ThreadingHTTPServer):
    address_family = socket.AF_INET6
    daemon_threads = True

    def server_bind(self):
        self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        super().server_bind()


_logfh = None


def log(msg):
    line = "%s %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg)
    if _logfh:
        _logfh.write(line)
        _logfh.flush()
    elif sys.stderr:
        sys.stderr.write(line)


def watch_commit(server):
    start = git("rev-parse", "HEAD")
    while True:
        time.sleep(15)
        now = git("rev-parse", "HEAD")
        if now and start and now != start:
            log("worktree moved %s -> %s; bouncing" % (start[:8], now[:8]))
            server.bounce = True
            server.shutdown()
            return


def serve():
    global _logfh
    STATE.mkdir(parents=True, exist_ok=True)
    _logfh = open(STATE / "door.log", "a", encoding="utf-8")
    try:
        server = DualStack(("::", PORT), Door)
    except OSError as exc:
        log("port %d unavailable, refusing to pick another: %s" % (PORT, exc))
        return 1
    server.bounce = False
    threading.Thread(target=watch_commit, args=(server,), daemon=True).start()
    log("door up on [::]:%d from %s at %s" % (PORT, ROOT, git("rev-parse", "--short", "HEAD")))
    server.serve_forever()
    server.server_close()
    return BOUNCE if server.bounce else 0


def supervise():
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    while True:
        code = subprocess.run([sys.executable, __file__, "serve"], creationflags=flags).returncode
        time.sleep(1 if code == BOUNCE else 10)


def status():
    import urllib.request
    url = "http://%s.local:%d/" % (socket.gethostname().lower(), PORT)
    try:
        with urllib.request.urlopen(url.replace("/", "/", 1) + "revision", timeout=5) as r:
            print("up    %s   revision %s" % (url, r.read().decode()))
            return 0
    except Exception as exc:
        print("down  %s   (%s)" % (url, exc))
        print("log   %s" % (STATE / "door.log"))
        return 1


if __name__ == "__main__":
    verb = sys.argv[1] if len(sys.argv) > 1 else "status"
    sys.exit({"serve": serve, "supervise": supervise, "status": status}.get(verb, status)())
