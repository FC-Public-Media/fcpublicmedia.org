"""door — the one address the media node answers on.

    door.py serve              become the door, on [::]:8080
    door.py supervise          run `serve`, restart it when it exits, pull in the background
    door.py screens [--launch] are the screens in node.yml up and full-screen
    door.py                    is the door up

Written 2026-09-23 on the studio kiosk (the predecessor of editing bay 2),
after station-node's `bin/door`, whose rules it keeps:

  * ONE PORT, AND IT DOES NOT MOVE. 8080 is what somebody guesses, and an
    address that slides is not one anybody can bookmark. If 8080 is taken the
    door refuses to start rather than picking another.
  * NOT A WEB SERVER. There is no document root. Each surface below is named,
    and a file is served only if it is under a directory named here or is a
    QR image named by kiosk/welcome.yml.
  * DUAL-STACK. The machine's name resolves to IPv6 first. A listener bound
    only to IPv4 refuses a request made by name, and that looks exactly like
    the door being down.

    GET /                  the board: what this node shows
    GET /kiosk/            the welcome screen
    GET /kiosk/qr/<n>      the check-in QR for panel n, as welcome.yml names it
    GET /kiosk/wifi/<n>    Wi-Fi QR n, built in memory. See node.yml
    GET /kiosk/on          who is on, as JSON. The footer polls it
    GET /idle/             brand/idle/index.html (?say=... fills its slot)
    GET /wallpaper/<file>  brand/wallpaper/
    GET /revision          what a screen polls: <commit>-<kiosk revision>

THE BOUNCE. Content is read per request. Code is loaded once, so `serve`
watches the commit its worktree has checked out and exits with 75 when it
moves. `supervise` starts it again. Every page polls /revision and reloads
when it changes. `supervise` also fetches every five minutes and rebases
this branch onto origin/main, so a merge upstream (a new rota, say) reaches
the screens with nobody at the machine. If the rebase cannot finish cleanly
it is aborted and logged, and the screens keep showing what they had.

Runs from a fixed virtualenv (%LOCALAPPDATA%\\media-node\\venv, with pyyaml
and qrcode). A stable interpreter path means Windows Firewall asks about it
once. `uv run --with` built a fresh path each time, so it asked every time.
"""
import ctypes
import datetime
import html
import importlib.util
import json
import os
import pathlib
import socket
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PORT = 8080
BOUNCE = 75          # exit code meaning "my code changed, start me again"
PULL_EVERY = 300
STATE = pathlib.Path(os.environ.get("LOCALAPPDATA", ROOT)) / "media-node"
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

NAMED_DIRS = {"wallpaper": ROOT / "brand" / "wallpaper"}
TYPES = {".html": "text/html; charset=utf-8", ".svg": "image/svg+xml",
         ".png": "image/png", ".txt": "text/plain; charset=utf-8",
         ".json": "application/json"}


# ------------------------------------------------------------------- sources --
def git(*args):
    try:
        out = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True,
                             text=True, timeout=60, creationflags=NO_WINDOW)
        return out.stdout.strip() if out.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


def load(path):
    import yaml
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def welcome():
    return load(ROOT / "kiosk" / "welcome.yml")


def node():
    return load(HERE / "node.yml")


def revision():
    try:
        kiosk = str(welcome().get("revision", "?"))
    except Exception:
        kiosk = "unreadable"
    return "%s-%s" % (git("rev-parse", "--short", "HEAD") or "nogit", kiosk)


# ------------------------------------------------------------------ the rota --
DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


def on_now(now=None):
    """Who is on now, and who is next, from the sources in order.

    Only the default rota exists today. A calendar goes in front of it when
    one is chosen, and the rota keeps answering whenever the calendar cannot.
    """
    now = now or datetime.datetime.now()
    shifts = load(ROOT / "kiosk" / "rota.yml").get("shifts") or []
    current, upcoming = [], []
    for s in shifts:
        days = [d.lower()[:3] for d in s.get("days") or []]
        start = datetime.datetime.strptime(str(s["from"]), "%H:%M").time()
        end = datetime.datetime.strptime(str(s["to"]), "%H:%M").time()
        who = s.get("who") or []
        for ahead in range(8):
            day = now.date() + datetime.timedelta(days=ahead)
            if DAYS[day.weekday()] not in days:
                continue
            begins = datetime.datetime.combine(day, start)
            ends = datetime.datetime.combine(day, end)
            if begins <= now < ends:
                current += who
            elif begins > now:
                upcoming.append((begins, who))
                break
    nxt = None
    if upcoming:
        begins, who = min(upcoming, key=lambda u: u[0])
        when = begins.strftime("%a %I:%M %p").replace(" 0", " ").replace(":00", "")
        if begins.date() == now.date():
            when = begins.strftime("%I:%M %p").lstrip("0").replace(":00", "")
        nxt = {"who": who, "when": when}
    return {"now": current, "next": nxt, "source": "rota"}


# ---------------------------------------------------------------- the Wi-Fi --
class CREDENTIAL(ctypes.Structure):
    _fields_ = [("Flags", ctypes.c_uint32), ("Type", ctypes.c_uint32),
                ("TargetName", ctypes.c_wchar_p), ("Comment", ctypes.c_wchar_p),
                ("LastWritten", ctypes.c_uint64), ("CredentialBlobSize", ctypes.c_uint32),
                ("CredentialBlob", ctypes.POINTER(ctypes.c_ubyte)), ("Persist", ctypes.c_uint32),
                ("AttributeCount", ctypes.c_uint32), ("Attributes", ctypes.c_void_p),
                ("TargetAlias", ctypes.c_wchar_p), ("UserName", ctypes.c_wchar_p)]


def secret(target):
    """A generic credential's password from Windows Credential Manager, or None.

    `cmdkey /generic:<target> /pass` stores it as UTF-16. Only this Windows
    user can read it back, and it is never written anywhere by this file."""
    if os.name != "nt":
        return None
    adv = ctypes.windll.advapi32
    ptr = ctypes.POINTER(CREDENTIAL)()
    if not adv.CredReadW(target, 1, 0, ctypes.byref(ptr)):      # 1 = CRED_TYPE_GENERIC
        return None
    try:
        c = ptr.contents
        raw = bytes(c.CredentialBlob[:c.CredentialBlobSize])
        return raw.decode("utf-16-le") if raw else None
    finally:
        adv.CredFree(ptr)


def set_secret(target, user, password):
    """Store a generic credential that survives logoff (CRED_PERSIST_LOCAL_MACHINE).

    Raises OSError if Windows refuses, for example when policy forbids
    storing credentials. That is worth knowing loudly rather than finding out
    at the next reboot."""
    blob = password.encode("utf-16-le")
    buf = (ctypes.c_ubyte * len(blob)).from_buffer_copy(blob)
    cred = CREDENTIAL(Type=1, TargetName=target, UserName=user, Persist=2,
                      CredentialBlobSize=len(blob), CredentialBlob=buf)
    if not ctypes.windll.advapi32.CredWriteW(ctypes.byref(cred), 0):
        raise ctypes.WinError()


def wifi_password(ssid):
    """door.py wifi-password "<ssid>": prompt without echo, store it here."""
    import getpass
    known = [n["ssid"] for n in networks_declared()]
    if ssid not in known:
        print("not a network node.yml names: %r (it names %s)" % (ssid, ", ".join(map(repr, known))))
        return 2
    first = getpass.getpass("Password for %s: " % ssid)
    if not first or getpass.getpass("Again: ") != first:
        print("empty, or the two did not match. Nothing stored.")
        return 1
    set_secret("fcpm-wifi:" + ssid, ssid, first)
    print("stored in Windows Credential Manager as fcpm-wifi:%s" % ssid)
    return 0


def networks_declared():
    out = []
    for n in node().get("networks") or []:
        if n.get("from") == "wifi":
            out.append(dict(load(ROOT / "site" / "_data" / "wifi.yml").get("network") or {}))
        else:
            out.append({"ssid": n["ssid"]})
    return out


def _wifi_module():
    """site/bin/make-wifi-qr.py, for its payload(): one copy of the escaping."""
    spec = importlib.util.spec_from_file_location(
        "make_wifi_qr", ROOT / "site" / "bin" / "make-wifi-qr.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def networks():
    """The networks node.yml names, each resolved to ssid/security/label and
    whether a password is set here. The password itself is not returned."""
    out = []
    for n in node().get("networks") or []:
        if n.get("from") == "wifi":
            net = dict(load(ROOT / "site" / "_data" / "wifi.yml").get("network") or {})
            if not net.get("confirmed"):
                continue          # the site's own gate: an unconfirmed SSID is not shown
        else:
            net = {"ssid": n["ssid"], "security": n.get("security", "wpa")}
        net["label"] = n.get("label", "")
        is_open = (net.get("security") or "wpa").lower() == "open"
        net["ready"] = is_open or secret("fcpm-wifi:" + net["ssid"]) is not None
        out.append(net)
    return out


def wifi_svg(i):
    nets = networks()
    if not (0 <= i < len(nets)) or not nets[i]["ready"]:
        return None
    net = nets[i]
    password = secret("fcpm-wifi:" + net["ssid"]) or ""
    data, _ = _wifi_module().payload(net, password)
    import io
    import qrcode
    import qrcode.image.svg
    code = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H, border=0)
    code.add_data(data)
    code.make(fit=True)
    buf = io.BytesIO()
    code.make_image(image_factory=qrcode.image.svg.SvgPathImage).save(buf)
    return buf.getvalue()


# --------------------------------------------------------------------- pages --
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


BRAND = """:root { --record:#d93a26; --signal:#ffc61a; --slate:#232830; --ink:#121417;
  --paper:#f4f1ea; --dim:#a1a8b2; --rule:#2f363d; }
html,body { margin:0; background:var(--ink); color:var(--paper);
  font:18px/1.35 system-ui,-apple-system,"Segoe UI",sans-serif; }
a { color:inherit; }"""


def page(title, body, style=""):
    return with_poll("""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%s</title><style>%s
%s</style></head><body>%s</body></html>""" % (html.escape(title), BRAND, style, body))


def e(s):
    return html.escape(str(s or ""))


def board_page():
    rows = [("/kiosk/", "Welcome screen", "check-in, Wi-Fi, who is on"),
            ("/idle/", "Idle screen", "brand/idle: the lamp pointed at the room"),
            ("/idle/?say=On+air+now", "Idle, with its slot filled", "?say= fills the marked slot")]
    for f in sorted(NAMED_DIRS["wallpaper"].glob("*1050x1680.png")):
        rows.append(("/wallpaper/" + f.name, f.stem, "portrait wallpaper, this panel's size"))
    nets = "".join("<li>%s <span>%s</span></li>" % (
        e(n["ssid"]), "password set" if n["ready"] else "no password on this machine yet")
        for n in networks())
    items = "".join('<li><a href="%s">%s</a> <span>%s</span></li>' % (
        html.escape(h, quote=True), e(t), e(d)) for h, t, d in rows)
    body = """<main><h1>FC Public Media &middot; media node</h1>
<p class=dim>%s &middot; revision <code>%s</code></p><ul>%s</ul><h2>Wi-Fi codes</h2><ul>%s</ul></main>""" % (
        e(socket.gethostname().lower()), e(revision()), items, nets)
    return page("Media node", body, """main { max-width:44rem; margin:3rem auto; padding:0 16px; }
.dim, li span { color:var(--dim); } li { margin:.6rem 0; } li span { display:block; font-size:.85em; }""")


KIOSK_CSS = """
html, body { height:100%; overflow:hidden; }
body { display:grid; grid-template-rows:1fr 1fr auto; }
.half { position:relative; overflow:hidden; }
.checkin { background:var(--record); color:var(--paper); }
.wifi { background:var(--signal); color:var(--ink); }

/* The code sits ON a third line: the first third up top, the second third
   below. The words take the wider side of the line. */
.code { position:absolute; top:50%; transform:translate(-50%,-50%); }
.checkin .code { left:33.333%; }
.wifi .code { left:66.667%; display:flex; flex-direction:column; gap:3vh; }
.qr { display:block; background:#fff; padding:1.4vh; border-radius:1vh; box-sizing:border-box; }
.qr img { display:block; width:100%; height:100%; }
.checkin .qr { width:25vh; height:25vh; }
.wifi .qr { width:15vh; height:15vh; }
.net { display:flex; flex-direction:column; align-items:center; gap:.8vh; }
.net b { font-size:1.6vh; letter-spacing:.08em; text-transform:uppercase; font-weight:650; }
.slot { width:15vh; height:15vh; border:.3vh dashed currentColor; border-radius:1vh; opacity:.55;
  display:flex; align-items:center; justify-content:center; text-align:center; font-size:1.3vh;
  padding:1vh; box-sizing:border-box; }

.words { position:absolute; top:50%; transform:translateY(-50%); }
.checkin .words { left:calc(33.333% + 12.5vh + 5vw); right:5vw; }
.wifi .words { right:calc(33.333% + 7.5vh + 5vw); left:6vw; text-align:right; }
h1 { margin:0; font-size:min(6vh, 11vw); line-height:1; font-weight:750; letter-spacing:-.01em; }
.sub { margin:1.4vh 0 0; font-size:min(2.5vh, 4.4vw); line-height:1.25; font-weight:500; }

footer { background:var(--slate); color:var(--paper); display:flex; align-items:baseline;
  justify-content:space-between; gap:3vw; padding:2.4vh 5vw; }
.on { display:flex; align-items:baseline; gap:1.6vw; min-width:0; }
.on b { font-size:1.5vh; letter-spacing:.1em; text-transform:uppercase; color:var(--signal); white-space:nowrap; }
.on span { font-size:2.6vh; font-weight:600; }
.place { font-size:1.4vh; letter-spacing:.1em; text-transform:uppercase; color:var(--dim); white-space:nowrap; }
"""

FOOTER_JS = """<script>
(function () {
  var W = %s;
  function draw(d) {
    var label = document.getElementById('on-label'), who = document.getElementById('on-who');
    if (d.now && d.now.length) { label.textContent = W.on; who.textContent = d.now.join(', '); }
    else if (d.next) { label.textContent = W.next; who.textContent = d.next.who.join(', ') + ' \\u00b7 ' + d.next.when; }
    else { label.textContent = ''; who.textContent = W.none; }
  }
  function tick() { fetch('/kiosk/on', {cache:'no-store'}).then(function (r) { return r.json(); }).then(draw).catch(function () {}); }
  tick(); setInterval(tick, 60000);
})();
</script>"""


def kiosk_page():
    w, n = welcome(), node()
    words = n.get("wording") or {}
    ci, wf, ft = words.get("checkin") or {}, words.get("wifi") or {}, words.get("footer") or {}

    checkin = next((p for p in w.get("panels") or [] if isinstance(p.get("qr"), dict)), None)
    idx = (w.get("panels") or []).index(checkin) if checkin else -1
    code = ('<div class=qr><img src="/kiosk/qr/%d" alt="%s"></div>' % (
        idx, html.escape(checkin["qr"].get("alt", ""), quote=True))) if checkin else ""

    nets = []
    for i, net in enumerate(networks()):
        img = ('<div class=qr><img src="/kiosk/wifi/%d" alt="Wi-Fi code for %s"></div>' % (i, e(net["ssid"]))
               if net["ready"] else
               '<div class=slot>%s<br>needs its password set on this machine</div>' % e(net["ssid"]))
        nets.append('<div class=net>%s<b>%s</b></div>' % (img, e(net.get("label") or net["ssid"])))

    body = """
<section class="half checkin">
  <div class=code>%s</div>
  <div class=words><h1>%s</h1><p class=sub>%s</p></div>
</section>
<section class="half wifi">
  <div class=words><h1>%s</h1><p class=sub>%s</p></div>
  <div class=code>%s</div>
</section>
<footer><div class=on><b id=on-label></b><span id=on-who></span></div><div class=place>%s</div></footer>
%s""" % (code, e(ci.get("head")), e(ci.get("sub")), e(wf.get("head")), e(wf.get("sub")),
         "".join(nets), e(w.get("place")),
         FOOTER_JS % json.dumps({k: ft.get(k, "") for k in ("on", "next", "none")}))
    return page(w.get("place", "Welcome"), body, KIOSK_CSS)


# -------------------------------------------------------------------- server --
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
        data = path.read_bytes()
        if path.suffix.lower() == ".html":
            data = with_poll(data.decode("utf-8")).encode("utf-8")
        self.reply(200, data, TYPES.get(path.suffix.lower(), "application/octet-stream"))

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        route = self.path.split("?", 1)[0]
        tail = route.rsplit("/", 1)[-1]
        try:
            if route == "/":
                return self.reply(200, board_page())
            if route == "/revision":
                return self.reply(200, revision(), TYPES[".txt"])
            if route in ("/kiosk", "/kiosk/"):
                return self.reply(200, kiosk_page())
            if route == "/kiosk/on":
                return self.reply(200, json.dumps(on_now()), TYPES[".json"])
            if route.startswith("/kiosk/wifi/") and tail.isdigit():
                svg = wifi_svg(int(tail))
                return self.reply(200, svg, TYPES[".svg"]) if svg else self.file(None)
            if route.startswith("/kiosk/qr/") and tail.isdigit():
                panels = welcome().get("panels") or []
                n = int(tail)
                if n < len(panels) and isinstance(panels[n].get("qr"), dict):
                    rel = pathlib.PurePosixPath(panels[n]["qr"]["image"]).relative_to("site/assets")
                    return self.file(inside(ROOT / "site" / "assets", rel))
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
                % e(repr(exc))))


class DualStack(ThreadingHTTPServer):
    address_family = socket.AF_INET6
    daemon_threads = True

    def server_bind(self):
        self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        super().server_bind()


_logfh = None


def log(msg):
    global _logfh
    if _logfh is None:
        STATE.mkdir(parents=True, exist_ok=True)
        _logfh = open(STATE / "door.log", "a", encoding="utf-8")
    _logfh.write("%s %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg))
    _logfh.flush()


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


def pull_once():
    """Fetch, and rebase this branch onto origin/main if main moved.

    A dirty worktree or a rebase already in progress is left alone: somebody
    is working here. A rebase that stops on a conflict is aborted, so the
    worktree is never left half-applied under a running door."""
    if git("status", "--porcelain") != "":
        return log("pull: worktree has changes, not rebasing")
    if (ROOT / ".git").is_file():
        gitdir = pathlib.Path(git("rev-parse", "--git-dir") or "")
        if (gitdir / "rebase-merge").exists() or (gitdir / "rebase-apply").exists():
            return log("pull: a rebase is in progress, leaving it")
    if git("fetch", "--quiet", "origin") is None:
        return log("pull: fetch failed")
    if git("merge-base", "--is-ancestor", "origin/main", "HEAD") is not None:
        return                                       # already on top of main
    if git("rebase", "--quiet", "origin/main") is None:
        git("rebase", "--abort")
        return log("pull: rebase onto origin/main stopped on a conflict; aborted, still on %s"
                   % git("rev-parse", "--short", "HEAD"))
    log("pull: rebased onto origin/main, now %s" % git("rev-parse", "--short", "HEAD"))


def supervise():
    def puller():
        while True:
            try:
                pull_once()
            except Exception as exc:
                log("pull: %r" % exc)
            time.sleep(PULL_EVERY)
    threading.Thread(target=puller, daemon=True).start()
    while True:
        code = subprocess.run([sys.executable, __file__, "serve"], creationflags=NO_WINDOW).returncode
        time.sleep(1 if code == BOUNCE else 10)


# ------------------------------------------------------------------- screens --
def browser_windows(exe):
    """Visible top-level windows of a browser: title, rect, and whether it has
    a caption bar (full-screen windows do not)."""
    u = ctypes.windll.user32
    try:
        u.SetProcessDPIAware()
    except Exception:
        pass
    k = ctypes.windll.kernel32
    found = []

    class RECT(ctypes.Structure):
        _fields_ = [("l", ctypes.c_long), ("t", ctypes.c_long), ("r", ctypes.c_long), ("b", ctypes.c_long)]

    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    def each(h, _):
        if not u.IsWindowVisible(h):
            return True
        pid = ctypes.c_ulong()
        u.GetWindowThreadProcessId(h, ctypes.byref(pid))
        hp = k.OpenProcess(0x1000, False, pid.value)     # PROCESS_QUERY_LIMITED_INFORMATION
        name = ""
        if hp:
            buf = ctypes.create_unicode_buffer(1024)
            size = ctypes.c_ulong(1024)
            if k.QueryFullProcessImageNameW(hp, 0, buf, ctypes.byref(size)):
                name = pathlib.Path(buf.value).stem.lower()
            k.CloseHandle(hp)
        if name != exe:
            return True
        title = ctypes.create_unicode_buffer(512)
        u.GetWindowTextW(h, title, 512)
        if not title.value:
            return True
        r = RECT()
        u.GetWindowRect(h, ctypes.byref(r))
        style = u.GetWindowLongW(h, -16)
        found.append({"title": title.value, "rect": [r.l, r.t, r.r - r.l, r.b - r.t],
                      "fullscreen": not (style & 0x00C00000)})
        return True

    u.EnumWindows(each, 0)
    return found


def screens(launch=False):
    cfg = node()
    exe = cfg.get("browser", "msedge")
    wins = browser_windows(exe)
    bad = 0
    for s in cfg.get("screens") or []:
        x, y, w, h = s["rect"]
        hit = next((win for win in wins if win["fullscreen"]
                    and abs(win["rect"][0] - x) <= 8 and abs(win["rect"][1] - y) <= 8
                    and abs(win["rect"][2] - w) <= 16 and abs(win["rect"][3] - h) <= 16), None)
        if hit:
            print("ok       %-8s %-9s full-screen  %s" % (s["name"], s["display"], hit["title"]))
            continue
        bad += 1
        print("missing  %-8s %-9s nothing full-screen at %s" % (s["name"], s["display"], s["rect"]))
        if launch:
            url = "http://%s.local:%d%s" % (socket.gethostname().lower(), PORT, s["url"])
            path = {"msedge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                    "chrome": r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"}[exe]
            subprocess.Popen([path, "--new-window", "--start-fullscreen",
                              "--window-position=%d,%d" % (x, y), "--window-size=%d,%d" % (w, h), url])
            print("         launched %s there" % url)
    return 1 if bad and not launch else 0


def status():
    import urllib.request
    url = "http://%s.local:%d/" % (socket.gethostname().lower(), PORT)
    try:
        with urllib.request.urlopen(url + "revision", timeout=5) as r:
            print("up    %s   revision %s" % (url, r.read().decode()))
            return 0
    except Exception as exc:
        print("down  %s   (%s)" % (url, exc))
        print("log   %s" % (STATE / "door.log"))
        return 1


if __name__ == "__main__":
    verb = sys.argv[1] if len(sys.argv) > 1 else "status"
    if verb == "screens":
        sys.exit(screens(launch="--launch" in sys.argv))
    if verb == "wifi-password" and len(sys.argv) > 2:
        sys.exit(wifi_password(sys.argv[2]))
    sys.exit({"serve": serve, "supervise": supervise, "status": status}.get(verb, status)())
