"""door — the one address the media node answers on.

    door.py serve              become the door, on [::]:8080
    door.py supervise          run `serve`, restart it when it exits, pull in the background
    door.py screens [--launch] are the screens in node.yml up and full-screen
    door.py startup            what starts the door at logon, and does it point here
    door.py startup --xml      the logon task this checkout implies, to stdout
    door.py startup --install  register that task, and retire the Startup shortcut
    door.py sessions [pin|--revive]  the Claude sessions that come back after a sign-in
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
    GET /kiosk/now         who is on, and the studio map, as JSON. The page polls it
    GET /depot/            what is on the studio drive, for the third panel
    GET /depot/now         the drive's index, as JSON. The page polls it
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

AT LOGON, after station-node's `com.autumn.station-door.plist`: the door is
the one job this node runs for itself, so it has a job of its own. Here that
is a per-user scheduled task, "media-node door", which needs no administrator.
It starts `supervise` at logon and again every five minutes, and a start
while one is already running is ignored. That is launchd's KeepAlive, with
five minutes of slack. `supervise` also holds a named mutex, so a second copy
started some other way leaves at once instead of fighting over 8080. Once the
door answers, `supervise` brings up any screen in node.yml that is missing,
and, if this user signed in since it last looked, resumes in the background
the Claude sessions that were running before (see "sessions" below).

What it cannot do is log on. After a power cut the box waits at the sign-in
screen until someone signs in, and signing in automatically needs an
administrator (PROFILE.md, "Asked of IT").
"""
import base64
import ctypes
import datetime
import html
import importlib.util
import json
import os
import pathlib
import re
import shutil
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


# -------------------------------------------------------------- the schedule --
DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


def occurrences(entries, now, days_ahead=8):
    """Weekly entries (days, from, to) as real spans that have not ended yet,
    soonest first. Yesterday is included so a span past midnight still counts."""
    out = []
    for s in entries:
        days = [d.lower()[:3] for d in s.get("days") or []]
        start = datetime.datetime.strptime(str(s["from"]), "%H:%M").time()
        end = datetime.datetime.strptime(str(s["to"]), "%H:%M").time()
        for ahead in range(-1, days_ahead):
            day = now.date() + datetime.timedelta(days=ahead)
            if DAYS[day.weekday()] not in days:
                continue
            begins = datetime.datetime.combine(day, start)
            ends = datetime.datetime.combine(day, end)
            if ends <= begins:
                ends += datetime.timedelta(days=1)
            if ends > now:
                out.append((begins, ends, s))
    return sorted(out, key=lambda o: o[0])


def when(t, now):
    """`3 PM` if it is today, `Thu 10:30 AM` otherwise."""
    s = t.strftime("%I:%M %p").lstrip("0").replace(":00", "")
    return s if t.date() == now.date() else t.strftime("%a ") + s


def on_now(now=None):
    """Who is on now, and who is next, from the sources in order.

    Only the default rota exists today. Calendars go in front of it when they
    are chosen, and the rota keeps answering whenever they cannot."""
    now = now or datetime.datetime.now()
    spans = occurrences(load(ROOT / "kiosk" / "rota.yml").get("shifts") or [], now)

    def who(s):
        names = ", ".join(s.get("who") or [])
        return names + (" · " + s["role"] if s.get("role") else "")
    current = [who(s) for b, _, s in spans if b <= now]
    later = [(b, s) for b, _, s in spans if b > now]
    nxt = {"who": who(later[0][1]), "when": when(later[0][0], now)} if later else None
    return {"now": current, "next": nxt, "source": "rota"}


WEEK = datetime.timedelta(days=7)


def helpers(activities, now):
    """Who can help with these activities this week, and when they are next in.

    From the rota: a person whose `crew:` tags meet the station's activities.
    A person with no tags counts as a host, who can help with anything; that is
    what being on the rota already says. Each person appears once, at their
    next shift, soonest first, and three at most: a line, not a roster."""
    rota = load(ROOT / "kiosk" / "rota.yml")
    crew = rota.get("crew") or {}
    seen, out = set(), []
    for begins, _, s in occurrences(rota.get("shifts") or [], now):
        if begins > now + WEEK:
            break
        for person in s.get("who") or []:
            tags = set(crew.get(person) or [])
            if person in seen or (tags and not tags & set(activities)):
                continue
            seen.add(person)
            # Non-breaking inside an entry: the line may wrap between people,
            # never between a name and its time.
            out.append(("%s %s" % (person, "now" if begins <= now else when(begins, now))).replace(" ", " "))
            if len(out) == 3:
                return out
    return out


def stations(now=None):
    """The studio map: each group of stations, lit while in use.

    Bookings are ranked across the WHOLE map, not per station. People come in
    one at a time, so the single next appointment anywhere is the solid pill,
    the one after it is the outline pill, and anything else inside the week is
    soft. Nothing past a week is shown. A station with nothing booked this week
    says who can help with it and when instead. Coupled rooms are one group,
    because booking either one takes both."""
    now = now or datetime.datetime.now()
    cfg = node()
    wanted = cfg.get("facilities") or []
    facilities = {f["name"]: f for f in load(ROOT / "site" / "_data" / "facilities.yml") or []}
    groups, placed = [], set()
    for name in wanted:
        f = facilities.get(name)
        if not f or name in placed:
            continue
        if f.get("stations"):
            single = name[:-1] if name.endswith("s") else name
            groups += [{"names": ["%s %d" % (single, i + 1)], "activities": f.get("activities") or []}
                       for i in range(int(f["stations"]))]
            placed.add(name)
            continue
        names = [name]
        acts = list(f.get("activities") or [])
        if f.get("couples_with") in wanted:
            names.append(f["couples_with"])
            acts += (facilities.get(f["couples_with"]) or {}).get("activities") or []
        placed.update(names)
        groups.append({"names": names, "activities": acts})
    for s in cfg.get("stations") or []:
        groups.append({"names": [s["name"]], "note": s.get("note", ""),
                       "activities": s.get("activities") or [],
                       "preparing": bool(s.get("preparing"))})

    sample = cfg.get("bookings") == "sample"
    entries = (load(HERE / "bookings.sample.yml").get("bookings") or []) if sample else []
    upcoming = []
    for g in groups:
        g["coupled"] = len(g["names"]) > 1
        spans = [] if g.get("preparing") else occurrences(
            [b for b in entries if b.get("station") in g["names"]], now)
        live = [sp for sp in spans if sp[0] <= now]
        g["lit"] = bool(live)
        g["until"] = when(max(sp[1] for sp in live), now) if live else None
        g["next"] = []
        upcoming += [(sp[0], g, sp[2]) for sp in spans if now < sp[0] <= now + WEEK]

    # A booking may name who it is for. The sample week names nobody real, so
    # its bookings are for "Sample", which is also how the screen says the map
    # is not the real day.
    for rank, (begins, g, b) in enumerate(sorted(upcoming, key=lambda u: u[0])):
        if len(g["next"]) < 2:
            g["next"].append({"when": when(begins, now), "rank": min(rank, 2),
                              "who": b.get("who") or ("Sample" if sample else "")})
    for g in groups:
        g["helpers"] = [] if (g["next"] or g["lit"] or g.get("preparing")) else helpers(g["activities"], now)
        del g["activities"]
    return {"groups": groups, "sample": sample}


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


# ----------------------------------------------------------------- the depot --
# What is on the studio drive: the router's Samba share, eight partitions.
# docs/DESIGN-NOTES.md, "Showing what is on the network drive", is the design
# and this follows it:
#
#   * A browser cannot speak SMB. This process can, because Windows can, under
#     the credential saved for the router. It walks the shares and the page
#     renders the index.
#   * Completeness cannot be observed, so a file's state is one of three:
#       declared     its writer left `<name>.sha256` beside it. Trustworthy.
#       arriving     it grew between two scans. Trustworthy in the negative.
#       unwitnessed  present, not growing, nobody declared it. A guess, and
#                    the name says so.
#     The state is a name, never an ordinal. arriving -> unwitnessed is the
#     moment the only signal was lost, not progress.
#   * `growth_last_observed` is a frozen instant, written once when growth
#     stops. Its absence means this file was never seen growing.
#
# KNOWN AND UNKNOWN SHARES. node.yml lays out the shares we know by name, in
# rows. The router is also asked what it shares, every scan, so a partition
# nobody has told this file about still appears: in the group whose `match`
# prefix fits its name, listed plainly under that group's rows. Nothing on the
# drive goes unseen for want of a config line.
#
# The index lives only in this process. It names people's files, so it is not
# written to disk and never goes near the repository. A restart forgets the
# growth history, which is the honest cost: everything reads `unwitnessed`
# until it is seen again.
DEPOT_EVERY = 15
_depot = {"at": None, "shares": [], "files": {}}
_depot_lock = threading.Lock()


def share_root(server, share):
    return "\\\\%s\\%s\\" % (server, share)


def discover_shares(server):
    """The disk shares the router offers, by asking it (`net view`). An empty
    list if it cannot be asked, and then only the configured shares show."""
    try:
        out = subprocess.run(["net", "view", "\\\\" + server], capture_output=True, text=True,
                             timeout=20, creationflags=NO_WINDOW).stdout
    except (OSError, subprocess.SubprocessError):
        return []
    found = []
    for line in out.splitlines():
        m = re.match(r"^(\S.*?)\s{2,}Disk\b", line)
        if m:
            found.append(m.group(1))
    return found


def depot_layout(cfg, discovered):
    """Every share to scan: [(group, row, share-config)], row None for unknowns."""
    out, known = [], set()
    for group in cfg.get("groups") or []:
        for r, row in enumerate(group.get("rows") or []):
            for sh in row.get("shares") or []:
                known.add(sh["share"])
                out.append((group, r, dict(sh, files=row.get("files", True))))
    groups = cfg.get("groups") or []
    for name in discovered:
        if name in known or not groups:
            continue
        home = next((g for g in groups if g.get("match") and name.upper().startswith(g["match"].upper())),
                    groups[0])
        out.append((home, None, {"share": name, "label": name, "files": True}))
    return out


def scan_depot(now=None, discovered=None):
    cfg = node().get("depot") or {}
    server = cfg.get("server")
    now = now or time.time()
    if discovered is None:
        discovered = discover_shares(server) if server else []
    prev, files, shares = _depot["files"], {}, []
    for group, row, sh in depot_layout(cfg, discovered):
        root = sh.get("path") or share_root(server, sh["share"])     # `path` is for tests
        entry = {"share": sh["share"], "label": sh.get("label", sh["share"]),
                 "group": group["name"], "row": row, "files": sh["files"], "ok": False, "items": []}
        try:
            usage = shutil.disk_usage(root)
            entry.update(ok=True, total=usage.total, free=usage.free)
            for dirpath, dirnames, filenames in os.walk(root):
                # Dot-directories are other machines' bookkeeping
                # (.Spotlight-V100 is on every partition), not deliveries.
                dirnames[:] = [d for d in dirnames if not d.startswith(".")]
                for f in filenames:
                    if f.startswith(".") or f.endswith(".sha256"):
                        continue
                    full = os.path.join(dirpath, f)
                    try:
                        size = os.stat(full).st_size
                    except OSError:
                        continue
                    old = prev.get(full)
                    growing = bool(old) and size != old["size"]
                    stopped = growing is False and bool(old) and old["growing"]
                    rec = {"size": size, "seen": old["seen"] if old else now, "growing": growing,
                           "growth_last_observed": now if stopped else (old or {}).get("growth_last_observed")}
                    files[full] = rec
                    state = ("declared" if os.path.exists(full + ".sha256")
                             else "arriving" if growing else "unwitnessed")
                    rel = os.path.relpath(full, root).replace("\\", "/")
                    entry["items"].append({"name": rel, "size": size, "state": state,
                                           "seen": rec["seen"],
                                           "growth_last_observed": rec["growth_last_observed"]})
        except OSError as exc:
            entry["error"] = exc.strerror or str(exc)
        entry["items"].sort(key=lambda i: -i["seen"])
        shares.append(entry)
    with _depot_lock:
        _depot.update(at=now, shares=shares, files=files)


def watch_depot():
    while True:
        try:
            scan_depot()
        except Exception as exc:
            log("depot: %r" % exc)
        time.sleep(DEPOT_EVERY)


def depot_now():
    with _depot_lock:
        return {"at": _depot["at"], "now": time.time(), "shares": _depot["shares"]}


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


BRAND = """:root { --signal:#ffc61a; --slate:#232830; --ink:#121417;
  --paper:#f4f1ea; --dim:#a1a8b2; --soft:#9ba3ad; --rule:#2f363d; }
html,body { margin:0; background:var(--ink); color:var(--paper);
  font:18px/1.35 system-ui,-apple-system,"Segoe UI",sans-serif; }
a { color:inherit; }
/* THE MARK: the brand square, and a shape any page here may reuse. Signal
   yellow, hard edges, leaning -8deg: counterclockwise, always (brand/README.md,
   "The tilt"). Unlit it is slate, as in brand/idle. */
.mark { background:var(--signal); rotate:-8deg; }
.mark.unlit { background:var(--slate); }
/* The clock mark: the same square with clock hands drawn on top of whatever
   it holds (site/_includes/clock-hands.html). */
.mark.clock { position:relative; }"""


def clock_hands():
    """The clock-hands fragment, the same file the site includes."""
    return (ROOT / "site" / "_includes" / "clock-hands.html").read_text(encoding="utf-8")


def clock_mark(inner="", cls=""):
    """The mark with a live clock in it, drawn over `inner` (the check-in QR)."""
    return '<div class="mark clock%s">%s%s</div>' % (" " + cls if cls else "", inner, clock_hands())


def page(title, body, style=""):
    return with_poll("""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%s</title><style>%s
%s</style></head><body>%s</body></html>""" % (html.escape(title), BRAND, style, body))


def e(s):
    return html.escape(str(s or ""))


def board_page():
    rows = [("/kiosk/", "Welcome screen", "check-in, Wi-Fi, who is on"),
            ("/depot/", "Depot", "what is on the studio drive"),
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
.checkin { background:var(--slate); }
.map { background:var(--ink); }

/* Check-in: the code IS the mark, sitting on the first-third line. */
.checkin .mark { position:absolute; left:33.333%; top:50%; translate:-50% -50%;
  width:25vh; height:25vh; padding:1.1vh; box-sizing:border-box; }
.checkin .mark img { display:block; width:100%; height:100%; }
.checkin .mark .ticks { display:none; }
.checkin .words { position:absolute; top:50%; translate:0 -50%;
  left:calc(33.333% + 15vh + 3vw); right:4vw; }
h1 { margin:0; font-size:min(5.2vh, 8.2vw); line-height:1; font-weight:750;
  letter-spacing:-.01em; white-space:nowrap; }
.sub { margin:1.4vh 0 0; font-size:min(2.5vh, 4.4vw); line-height:1.25; white-space:pre-line; font-weight:500; color:var(--soft); }

/* The map: what can be booked, lit when in use. */
.stations { position:absolute; left:6vw; right:6vw; top:50%; translate:0 -50%;
  display:flex; flex-direction:column; gap:2.6vh; }
.group { display:grid; grid-template-columns:2.4vh 1fr; column-gap:1.6vw; align-items:center; }
.group .mark { width:2.4vh; height:2.4vh; }
.names { display:flex; flex-direction:column; gap:.4vh; }
.names span { font-size:2.3vh; font-weight:600; line-height:1.15; }
.times { grid-column:2; display:flex; flex-wrap:wrap; align-items:center; gap:.9vh 1vw; margin-top:1vh; }
.times:empty { display:none; }
.pill { font-size:1.5vh; font-weight:650; padding:.35vh 1.05vh; border-radius:99px;
  border:.25vh solid var(--signal); font-variant-numeric:tabular-nums; white-space:nowrap; }
.pill.solid { background:var(--signal); color:var(--ink); }
.pill.outline { color:var(--signal); }
.pill.soft { color:var(--dim); border-color:var(--rule); font-weight:500; }
.names .until { font-size:1.6vh; font-weight:650; color:var(--signal); white-space:nowrap; }
.note { font-size:1.7vh; color:var(--dim); }
.group.preparing .names span { color:var(--dim); }
.group.preparing .mark { opacity:.6; }

.wifi { position:absolute; right:4vw; bottom:3vh; display:flex; gap:2.4vw; }
.qr { display:block; width:10vh; height:10vh; background:#fff; padding:.9vh; box-sizing:border-box; }
.qr img { display:block; width:100%; height:100%; }
.net { display:flex; flex-direction:column; align-items:center; gap:.9vh; }
.net b { font-size:1.25vh; letter-spacing:.1em; text-transform:uppercase; font-weight:650; white-space:nowrap; }
.slot { width:10vh; height:10vh; border:.25vh dashed var(--dim); color:var(--dim);
  display:flex; align-items:center; justify-content:center; text-align:center; font-size:1.2vh;
  padding:1vh; box-sizing:border-box; }

footer { background:var(--slate); display:flex; align-items:baseline;
  justify-content:space-between; gap:3vw; padding:2.4vh 5vw; }
.on { display:flex; align-items:baseline; gap:1.6vw; min-width:0; }
.on b { font-size:1.5vh; letter-spacing:.1em; text-transform:uppercase; color:var(--signal); white-space:nowrap; }
.on span { font-size:2.2vh; font-weight:600; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.place { font-size:1.4vh; letter-spacing:.1em; text-transform:uppercase; color:var(--dim); white-space:nowrap; }
"""

NOW_JS = """<script>
(function () {
  var W = %s;
  function el(tag, cls, text) { var n = document.createElement(tag); if (cls) n.className = cls;
    if (text != null) n.textContent = text; return n; }
  function footer(d) {
    var label = document.getElementById('on-label'), who = document.getElementById('on-who');
    if (d.now.length) { label.textContent = W.on; who.textContent = d.now.join(', '); }
    else if (d.next) { label.textContent = W.next; who.textContent = d.next.who + ' \\u00b7 ' + d.next.when; }
    else { label.textContent = ''; who.textContent = W.none; }
  }
  function map(m) {
    var box = document.getElementById('stations'); box.textContent = '';
    m.groups.forEach(function (g) {
      var row = el('div', 'group' + (g.coupled ? ' coupled' : '') + (g.preparing ? ' preparing' : ''));
      row.appendChild(el('div', 'mark' + (g.lit ? '' : ' unlit')));
      var names = el('div', 'names');
      g.names.forEach(function (n) { names.appendChild(el('span', null, n)); });
      row.appendChild(names);
      var times = el('div', 'times');
      if (g.preparing && g.note) times.appendChild(el('span', 'note', g.note));
      if (g.until) names.appendChild(el('span', 'until', W.until + ' ' + g.until));
      g.next.forEach(function (b) {
        times.appendChild(el('span', 'pill ' + ['solid', 'outline', 'soft'][b.rank], b.when + (b.who ? ' \\u00b7 ' + b.who : '')));
      });
      if (g.helpers.length) times.appendChild(el('span', 'note', g.helpers.join(' \\u00b7 ')));
      row.appendChild(times);
      box.appendChild(row);
    });
  }
  function tick() {
    fetch('/kiosk/now', {cache: 'no-store'}).then(function (r) { return r.json(); })
      .then(function (d) { footer(d.on); map(d.map); }).catch(function () {});
  }
  tick(); setInterval(tick, 60000);
})();
</script>"""


def qr_image(n):
    """The file behind the check-in QR for panel n, or None."""
    panels = welcome().get("panels") or []
    if n < len(panels) and isinstance(panels[n].get("qr"), dict):
        rel = pathlib.PurePosixPath(panels[n]["qr"]["image"]).relative_to("site/assets")
        return inside(ROOT / "site" / "assets", rel)
    return None


def checkin_mark(inline=False):
    """The check-in code on the mark, with the clock over it. Inline, the code
    travels inside the page as data, for pages written to a share."""
    panels = welcome().get("panels") or []
    idx = next((i for i, p in enumerate(panels) if isinstance(p.get("qr"), dict)), None)
    if idx is None:
        return ""
    src = "/kiosk/qr/%d" % idx
    if inline:
        img = qr_image(idx)
        if not img:
            return ""
        src = "data:%s;base64,%s" % (TYPES.get(img.suffix.lower(), "application/octet-stream"),
                                     base64.b64encode(img.read_bytes()).decode())
    return clock_mark('<img src="%s" alt="%s">' % (src, html.escape(panels[idx]["qr"].get("alt", ""), quote=True)))


def kiosk_page(wall=False, map_only=False):
    """The welcome screen. For the wall it carries its QR inside itself and no
    Wi-Fi codes: a page on a share is readable by the whole network. The wall
    draws check-in in its own header, so its studio module is the map alone
    (map_only). On the desk, a class soon or on takes over the check-in words
    (docs/KIOSK.md, "The class on now"); the code stays, for joining late."""
    w, n = welcome(), node()
    words = n.get("wording") or {}
    ci, mp, ft = words.get("checkin") or {}, words.get("map") or {}, words.get("footer") or {}

    code = checkin_mark(inline=wall)

    nets = []
    for i, net in enumerate([] if wall else networks()):
        img = ('<div class=qr><img src="/kiosk/wifi/%d" alt="Wi-Fi code for %s"></div>' % (i, e(net["ssid"]))
               if net["ready"] else
               '<div class=slot>%s<br>needs its password set on this machine</div>' % e(net["ssid"]))
        nets.append('<div class=net>%s<b>%s</b></div>' % (img, e(net.get("label") or net["ssid"])))

    body = """
<section class="half checkin">
  %s
  <div class=words><h1>%s</h1><p class=sub>%s</p></div>
  <div class="words class" id=class hidden></div>
  <div class=wifi>%s</div>
</section>
<section class="half map">
  <div class=stations id=stations></div>
</section>
<footer><div class=on><b id=on-label></b><span id=on-who></span></div><div class=place>%s</div></footer>
%s""" % (code, e(ci.get("head")), e(ci.get("sub")), "".join(nets),
         e(w.get("place")),
         NOW_JS % json.dumps({"on": ft.get("on", ""), "next": ft.get("next", ""),
                              "none": ft.get("none", ""), "until": mp.get("until", "until")}))
    if map_only:
        body = body[body.index('<section class="half map">'):]
        return page(w.get("place", "Welcome"), body, KIOSK_CSS + MAP_ONLY_CSS)
    if not wall:
        body += class_js() + DESK_CLASS_JS
    return page(w.get("place", "Welcome"), body, KIOSK_CSS + CLASS_CSS + DESK_CLASS_CSS)


MAP_ONLY_CSS = "body { grid-template-rows:1fr auto; }"

# The desk's card is the check-in words' size: the code stays beside it, and
# the Wi-Fi codes below it.
DESK_CLASS_CSS = """
.checkin .class { top:40%; }
.checkin .class .kicker { font-size:1.5vh; }
.checkin .class .title { margin-top:.8vh; font-size:3.4vh; }
.checkin .class .room { margin-top:1vh; font-size:2vh; }
.checkin .class .when { margin-top:.3vh; font-size:2vh; }
.checkin .class .join { margin-top:1.4vh; }
"""

DESK_CLASS_JS = """<script>
(function () {
  var K = window.FCPMClass, box = document.getElementById('class'),
      words = document.querySelector('.checkin .words:not(.class)');
  function draw() {
    var s = K.pick();
    if (s) K.card(box, s);
    box.hidden = !s; words.hidden = !!s;
  }
  draw(); setInterval(draw, 15000);
})();
</script>"""


DEPOT_CSS = """
html, body { height:100%; overflow:hidden; }
body { display:grid; grid-template-rows:auto auto 1fr; }
/* The gateway strip: the check-in footer turned over. Where the files are,
   and how many partitions it offers. */
.gateway { background:var(--slate); border-bottom:.15vh solid var(--rule); display:flex;
  align-items:baseline; justify-content:space-between; gap:3vw; padding:2.2vh 6vw; }
.gateway .on { display:flex; align-items:baseline; gap:1.6vw; }
.gateway .on b { font-size:1.5vh; letter-spacing:.1em; text-transform:uppercase; color:var(--signal); }
.gateway .on span { font-size:2.2vh; font-weight:600; }
.gateway .ip { font-size:1.6vh; letter-spacing:.06em; color:var(--soft); font-variant-numeric:tabular-nums; }
header { background:var(--slate); padding:3.6vh 6vw 3.4vh; display:flex; align-items:center; gap:4vw; }
header .mark { width:7vh; height:7vh; flex:none; }
header h1 { margin:0; font-size:5.2vh; line-height:1; font-weight:750; letter-spacing:-.01em; }
header p { margin:1vh 0 0; font-size:1.7vh; color:var(--soft); }
main { padding:3.4vh 6vw; display:flex; flex-direction:column; gap:3.6vh; overflow:hidden; }
h2 { margin:0 0 1.6vh; font-size:1.5vh; letter-spacing:.14em; text-transform:uppercase; color:var(--signal); font-weight:650; }
.rows { display:flex; flex-direction:column; gap:3vh; }

/* A row of known shares sits side by side, one column each. */
.row { display:flex; gap:4vw; }
.row > .share { flex:1 1 0; min-width:0; }
/* The name line: name, a soft note (a file count), and the free-space badge. */
.head { display:flex; align-items:center; gap:.6vw; }
.share b { flex:0 1 auto; min-width:0; font-size:2.15vh; font-weight:600; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.note { flex:none; font-size:1.45vh; color:var(--dim); white-space:nowrap; }
.free { flex:none; margin-left:auto; background:var(--slate); border-radius:.9vh; padding:.45vh .65vh;
  display:flex; flex-direction:column; align-items:center; line-height:1; font-variant-numeric:tabular-nums; }
.free span { font-size:1.55vh; font-weight:650; }
.free small { font-size:1vh; letter-spacing:.1em; color:var(--dim); margin-top:.3vh; }
.bar { height:.45vh; background:var(--slate); margin-top:.9vh; }
.bar i { display:block; height:100%; background:var(--signal); }

.items { list-style:none; margin:1.4vh 0 0; padding:0; display:flex; flex-direction:column; gap:1.1vh; }
.items li { display:grid; grid-template-columns:1.5vh 1fr; column-gap:.9vw; align-items:start; }
.items .mark { width:1.5vh; height:1.5vh; box-sizing:border-box; margin-top:.35vh; }
.items .mark.arriving { background:transparent; border:.25vh solid var(--signal); }
.items li > div { min-width:0; }
.items .name { display:block; font-size:1.6vh; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.items .state { display:block; font-size:1.3vh; color:var(--dim); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.more { font-size:1.35vh; color:var(--dim); margin:1vh 0 0; }
.error { font-size:1.45vh; color:var(--signal); margin:.8vh 0 0; }

/* A share nobody has described: the plain full-width line, beneath the rows. */
.unknown { display:flex; flex-direction:column; gap:2vh; }
.unknown .share b { display:inline; }
"""

DEPOT_JS = """<script>
(function () {
  var MAX = 3;
  function el(tag, cls, text) { var n = document.createElement(tag); if (cls) n.className = cls;
    if (text != null) n.textContent = text; return n; }
  function size(b) {
    var u = ['B', 'KB', 'MB', 'GB'], i = 0;
    while (b >= 1000 && i < u.length - 1) { b /= 1000; i++; }
    return (i ? b.toFixed(b < 10 ? 1 : 0) : b) + '\\u00a0' + u[i];
  }
  function ago(s) {
    s = Math.max(0, Math.round(s));
    return s < 60 ? s + 's' : s < 3600 ? Math.round(s / 60) + ' min' : Math.round(s / 3600) + ' h';
  }
  function state(it, now) {
    if (it.state === 'declared') return 'declared';
    if (it.state === 'arriving') return 'arriving';
    // unwitnessed: say what we did see, never that it is done.
    return it.growth_last_observed ? 'stopped growing ' + ago(now - it.growth_last_observed) + ' ago'
                                   : 'unwitnessed';
  }
  function share(s) {
    var col = el('div', 'share'), head = el('div', 'head');
    head.appendChild(el('b', null, s.label)); col.appendChild(head);
    if (s.error) { col.appendChild(el('p', 'error', 'Cannot reach it')); return col; }
    if (!s.files && s.items.length)
      head.appendChild(el('span', 'note', s.items.length + (s.items.length === 1 ? ' file' : ' files')));
    // The badge: free space, number over unit. An estimate: this much, give
    // or take what is being written right now.
    var free = el('div', 'free'), f = size(s.free).split('\\u00a0');
    free.appendChild(el('span', null, f[0])); free.appendChild(el('small', null, f[1]));
    head.appendChild(free);
    var bar = el('div', 'bar'), fill = el('i');
    fill.style.width = (100 * (1 - s.free / s.total)).toFixed(1) + '%';
    bar.appendChild(fill); col.appendChild(bar);
    if (s.files && s.items.length) {
      var ul = el('ul', 'items');
      s.items.slice(0, MAX).forEach(function (it) {
        var li = el('li'), text = el('div');
        li.appendChild(el('div', 'mark' + (it.state === 'declared' ? '' : it.state === 'arriving' ? ' arriving' : ' unlit')));
        text.appendChild(el('span', 'name', it.name));
        text.appendChild(el('span', 'state', size(it.size) + '  \\u00b7  ' + state(it, d_now)));
        li.appendChild(text); ul.appendChild(li);
      });
      col.appendChild(ul);
      if (s.items.length > MAX) col.appendChild(el('p', 'more', '+ ' + (s.items.length - MAX) + ' more'));
    }
    return col;
  }
  var d_now = 0;
  function draw(d) {
    d_now = d.now;
    document.getElementById('partitions').textContent =
      d.shares.length + (d.shares.length === 1 ? ' partition' : ' partitions');
    document.getElementById('scanned').textContent =
      d.at ? 'Checked ' + ago(d.now - d.at) + ' ago' : 'Not checked yet';
    var boxes = {};
    Array.prototype.forEach.call(document.querySelectorAll('[data-group]'), function (b) {
      b.textContent = ''; boxes[b.getAttribute('data-group')] = {box: b, rows: {}, unknown: null};
    });
    d.shares.forEach(function (s) {
      var g = boxes[s.group]; if (!g) return;
      if (s.row === null) {
        if (!g.unknown) { g.unknown = el('div', 'unknown'); }
        g.unknown.appendChild(share(s));
        return;
      }
      if (!g.rows[s.row]) { g.rows[s.row] = el('div', 'row'); }
      g.rows[s.row].appendChild(share(s));
    });
    Object.keys(boxes).forEach(function (k) {
      var g = boxes[k];
      Object.keys(g.rows).sort(function (a, b) { return a - b; }).forEach(function (r) { g.box.appendChild(g.rows[r]); });
      if (g.unknown) g.box.appendChild(g.unknown);
    });
  }
  function tick() {
    fetch('/depot/now', {cache: 'no-store'}).then(function (r) { return r.json(); }).then(draw).catch(function () {});
  }
  tick(); setInterval(tick, 10000);
})();
</script>"""


def depot_page():
    cfg = node().get("depot") or {}
    words = (node().get("wording") or {}).get("depot") or {}
    sections = "".join('<section><h2>%s</h2><div class=rows data-group="%s"></div></section>' % (
        e(g.get("title", g["name"])), html.escape(g["name"], quote=True)) for g in cfg.get("groups") or [])
    body = """<div class=gateway><div class=on><b>%s</b><span id=partitions></span></div><div class=ip>%s</div></div>
<header>%s<div><h1>%s</h1><p><span>%s</span> &middot; <span id=scanned></span></p></div></header>
<main>%s</main>%s""" % (e(words.get("gateway", "Gateway")), e(cfg.get("server", "")), clock_mark(),
                        e(words.get("head", "Files")), e(words.get("sub", "")), sections, DEPOT_JS)
    return page("Depot", body, DEPOT_CSS)


# ------------------------------------------------------------------- classes --
# THE CLASS ON NOW, and the ones coming up. The contract is docs/KIOSK.md, "The
# class on now": build-kiosk.py puts the schedule in welcome.yml's classes
# panel, and every renderer decides "now" from its own clock with pickSession
# from site/assets/js/classes.js. The door copies that function out of the file
# each time it draws a page, so the screens and the website cannot disagree.
CLASSES_JS = ROOT / "site" / "assets" / "js" / "classes.js"


def pick_session_js():
    """pickSession, byte for byte from classes.js, minus its `export`."""
    src = CLASSES_JS.read_text(encoding="utf-8")
    m = re.search(r"^export (function pickSession\(.*?^\})$", src, re.S | re.M)
    if not m:
        raise ValueError("pickSession not found in %s" % CLASSES_JS)
    return m.group(1)


def class_config(now=None):
    """The classes panel's config, as pickSession takes it. Only what the
    public calendar says: title, room, times, summary. `classes: sample` in
    node.yml invents three, a day and more ahead, all marked as samples."""
    if node().get("classes") == "sample":
        base = (now or datetime.datetime.now()).astimezone()

        def at(days, hour):
            d = (base + datetime.timedelta(days=days)).replace(hour=hour, minute=0, second=0, microsecond=0)
            return d.isoformat()
        rows = [(1, 18, "Podcasting 101 (sample)", "Podcast Studio"),
                (3, 18, "Social Media Marketing 101 (sample)", "Video Studio"),
                (8, 10, "Digitizing Home Movies (sample)", "Digitization")]
        return {"leadMinutes": 90, "lateMinutes": 45, "sample": True,
                "sessions": [{"title": t, "room": r, "starts": at(d, h), "ends": at(d, h + 2),
                              "summary": "A made-up class, so the screen has something to show."}
                             for d, h, t, r in rows]}
    panel = next((q for q in welcome().get("panels") or [] if isinstance(q.get("classes"), dict)), {})
    c = panel.get("classes") or {}
    keep = ("title", "room", "starts", "ends", "summary")
    return {"leadMinutes": c.get("leadMinutes", 90), "lateMinutes": c.get("lateMinutes", 45),
            "sessions": [{k: x[k] for k in keep if k in x}
                         for x in c.get("sessions") or [] if isinstance(x, dict) and not x.get("cancelled")]}


def class_words():
    w = (node().get("wording") or {}).get("classes") or {}
    return {"soon": w.get("soon", "Starting soon"), "now": w.get("now", "Happening now"),
            "starts": w.get("starts", "Starts"), "until": w.get("until", "Until"),
            "join": w.get("join", "Join until"), "next": w.get("next", "Next class"),
            "head": w.get("head", "Classes"), "none": w.get("none", "No classes on the calendar yet."),
            "sample": w.get("sample", "Sample classes"),
            "hint_wall": w.get("hint_wall", "Check in with the code above.")}


# The clock and the formatting every class view shares. `?at=<ISO time>` on a
# page pretends it is that moment, so a takeover can be looked at before it
# happens (and so an attendant can check one).
CLASS_JS = """<script>
(function () {
  var C = @CONFIG@, W = @WORDS@;
  @PICK@
  var at = Date.parse(new URLSearchParams(location.search).get('at') || ''), skew = isNaN(at) ? 0 : at - Date.now();
  function now() { return Date.now() + skew; }
  function time(ms) { return new Date(ms).toLocaleTimeString([], {hour: 'numeric', minute: '2-digit'}); }
  function day(ms) { return new Date(ms).toLocaleDateString([], {weekday: 'short', month: 'short', day: 'numeric'}); }
  function el(tag, cls, text) { var n = document.createElement(tag); if (cls) n.className = cls;
    if (text != null) n.textContent = text; return n; }
  function upcoming(n) {
    var t = now();
    return (C.sessions || []).map(function (s) {
      return {title: s.title, room: s.room, summary: s.summary, starts: Date.parse(s.starts), ends: Date.parse(s.ends)};
    }).filter(function (s) { return s.starts > t; })
      .sort(function (a, b) { return a.starts - b.starts; }).slice(0, n);
  }
  // The takeover card: what is on, where, and until when. Late also says how
  // long there is to walk in.
  function card(box, s, hint) {
    box.textContent = '';
    box.appendChild(el('p', 'kicker', s.phase === 'soon' ? W.soon : W.now));
    box.appendChild(el('h2', 'title', s.title));
    if (s.room) box.appendChild(el('p', 'room', s.room));
    box.appendChild(el('p', 'when', s.phase === 'soon' ? W.starts + ' ' + time(s.starts) : W.until + ' ' + time(s.ends)));
    if (s.phase === 'late') {
      var j = el('p', 'join'); j.appendChild(el('span', 'pill solid', W.join + ' ' + time(s.starts + (C.lateMinutes == null ? 45 : C.lateMinutes) * 60000)));
      box.appendChild(j);
      if (hint) box.appendChild(el('p', 'hint', hint));
    }
  }
  window.FCPMClass = {config: C, words: W, now: now, time: time, day: day, el: el, card: card, upcoming: upcoming,
                      pick: function () { return pickSession(C, now()); }};
})();
</script>"""

CLASS_CSS = """
.class .kicker { margin:0; font-size:1.7vh; letter-spacing:.14em; text-transform:uppercase; font-weight:700; color:var(--signal); }
.class .title { margin:1vh 0 0; font-size:5vh; line-height:1.05; font-weight:750; letter-spacing:-.01em; }
.class .room { margin:1.2vh 0 0; font-size:2.4vh; font-weight:600; }
.class .when { margin:.6vh 0 0; font-size:2.4vh; color:var(--soft); font-variant-numeric:tabular-nums; }
.class .join { margin:1.8vh 0 0; }
.class .hint { margin:1.2vh 0 0; font-size:1.8vh; color:var(--dim); }
.class .pill { font-size:1.6vh; font-weight:650; padding:.4vh 1.2vh; border-radius:99px;
  border:.25vh solid var(--signal); font-variant-numeric:tabular-nums; white-space:nowrap; }
.class .pill.solid { background:var(--signal); color:var(--ink); }
"""


def class_js():
    return (CLASS_JS.replace("@CONFIG@", json.dumps(class_config()).replace("</", "<\\/"))
            .replace("@WORDS@", json.dumps(class_words()))
            .replace("@PICK@", pick_session_js()))


CLASSES_CSS = """
html, body { height:100%; overflow:hidden; }
main { padding:5vh 6vw; }
h1 { margin:0 0 3.4vh; font-size:1.7vh; letter-spacing:.14em; text-transform:uppercase; color:var(--signal); font-weight:700; }
ol { list-style:none; margin:0; padding:0; display:flex; flex-direction:column; gap:3.2vh; }
li { display:grid; grid-template-columns:auto 1fr; column-gap:4vw; align-items:start; }
.day { background:var(--slate); border-radius:1.2vh; padding:1vh 1.4vh; min-width:7vh; text-align:center;
  display:flex; flex-direction:column; gap:.3vh; line-height:1; }
.day small { font-size:1.2vh; letter-spacing:.1em; text-transform:uppercase; color:var(--dim); }
.day b { font-size:3vh; font-weight:750; }
.what b { display:block; font-size:2.6vh; font-weight:700; line-height:1.15; }
.what span { display:block; margin-top:.6vh; font-size:1.8vh; color:var(--soft); font-variant-numeric:tabular-nums; }
.what p { margin:.8vh 0 0; font-size:1.6vh; color:var(--dim); line-height:1.3; }
.empty { font-size:2.4vh; color:var(--soft); }
.flag { margin:3.4vh 0 0; font-size:1.4vh; letter-spacing:.1em; text-transform:uppercase; color:var(--dim); }
"""

CLASSES_LIST_JS = """<script>
(function () {
  var K = window.FCPMClass, box = document.getElementById('upcoming');
  function draw() {
    var list = K.upcoming(5); box.textContent = '';
    if (!list.length) { box.appendChild(K.el('p', 'empty', K.words.none)); return; }
    var ol = K.el('ol');
    list.forEach(function (s) {
      var li = K.el('li'), d = K.el('div', 'day'), w = K.el('div', 'what'), when = new Date(s.starts);
      d.appendChild(K.el('small', null, when.toLocaleDateString([], {weekday: 'short'})));
      d.appendChild(K.el('b', null, String(when.getDate())));
      d.appendChild(K.el('small', null, when.toLocaleDateString([], {month: 'short'})));
      w.appendChild(K.el('b', null, s.title));
      w.appendChild(K.el('span', null, K.time(s.starts) + '\\u2013' + K.time(s.ends) + (s.room ? '  \\u00b7  ' + s.room : '')));
      if (s.summary) w.appendChild(K.el('p', null, s.summary));
      li.appendChild(d); li.appendChild(w); ol.appendChild(li);
    });
    box.appendChild(ol);
  }
  draw(); setInterval(draw, 60000);
})();
</script>"""


def classes_page():
    """Upcoming classes, as a list and never as a calendar grid."""
    w, cfg = class_words(), class_config()
    body = '<main><h1>%s</h1><div id=upcoming></div>%s</main>%s%s' % (
        e(w["head"]), '<p class=flag>%s</p>' % e(w["sample"]) if cfg.get("sample") else "",
        class_js(), CLASSES_LIST_JS)
    return page(w["head"], body, CLASSES_CSS)


# ---------------------------------------------------------------------- wall --
# THE WALL: pages for screens elsewhere on the network, the studio's rolling
# TV first. Nothing on the network can reach this box's port (Windows calls the
# network Public, and blocks this interpreter inbound; both need an
# administrator). So the door does not wait to be asked. It builds the pages
# here, where the credentials and the drive are, and writes them to a share
# every screen can already open. Privileged in construction, ungated in
# rendering: what lands there is plain HTML that fetches nothing.
#
# The shell is the check-in page's header, turned over into the colour plan
# of icon-inverted.svg, over a stage that moves through the modules by itself
# (Autumn, 2026-09-26: "rotate on its own while keeping the checkin version of
# the header block"). Each turn loads a fresh frame, named for its module, and
# drops the old one, so a frame never gathers history for Back to walk into.
# Hold stops the turning for a reader (WCAG 2.2.1), and lets go by itself
# after three minutes, since nobody stands at this screen to let go of it.
# A class soon or on takes the stage over (docs/KIOSK.md, "The class on
# now"); otherwise the bar names the next one.
WALL_PAGES = {
    "kiosk": (lambda: kiosk_page(wall=True, map_only=True), "/kiosk/now",
              lambda: {"on": on_now(), "map": stations()}),
    "depot": (depot_page, "/depot/now", depot_now),
    "classes": (classes_page, None, None),
}

WALL_SHIM = """<script>
(function () {
  var snap = %s, real = window.fetch;
  window.fetch = function (url) {
    if (Object.prototype.hasOwnProperty.call(snap, url))
      return Promise.resolve(new Response(JSON.stringify(snap[url]),
        {headers: {'Content-Type': 'application/json'}}));
    return real ? real.apply(this, arguments) : Promise.reject(new Error('offline'));
  };
})();
</script>"""

WALL_CSS = """html, body { height:100%; overflow:hidden; }
body { display:grid; grid-template-rows:auto 1fr auto; user-select:none; }

/* The superheader: check-in with the colours inverted. A plane of signal at
   the brand's tilt, cropped off left, right and top, so its one edge is the
   divider at the bottom, rising to the right: -8deg, counterclockwise
   (brand/README.md, "The tilt"). 14.05vw is the rise, tan 8deg of the width. */
.super { background:var(--signal); color:var(--ink); display:flex; align-items:center; gap:6vw;
  clip-path:polygon(0 0, 100% 0, 100% calc(100% - 14.05vw), 0 100%);
  padding:4.5vh 7vw calc(3vh + 14.05vw); }
/* The square goes black, as in icon-inverted.svg, and the code sits on a
   light inset inside it: a phone reads dark on light, not the other way. */
.super .mark { flex:none; width:21vh; height:21vh; padding:1.1vh; box-sizing:border-box; background:#000; }
.super .mark img { display:block; width:100%; height:100%; box-sizing:border-box; padding:1.8vh; background:#fff; }
.super .mark .ticks { display:none; }
/* The hands fit the code, not the frame: over the whole mark they reached the
   code's corner squares. !important, over the fragment's inline style. */
.super .mark svg.clock { inset:2.9vh !important; width:calc(100% - 5.8vh) !important; height:calc(100% - 5.8vh) !important; }
.super h1 { margin:0; font-size:6vh; line-height:1; font-weight:750; letter-spacing:-.01em; }
.super .sub { margin:1.4vh 0 0; font-size:2.6vh; line-height:1.25; white-space:pre-line; font-weight:600;
  color:rgba(18,20,23,.7); }

.stage { position:relative; overflow:hidden; }
.stage iframe { position:absolute; inset:0; width:100%; height:100%; border:0; background:var(--ink);
  opacity:0; transition:opacity .6s; }
.stage iframe.shown { opacity:1; }
.stage.taken iframe { visibility:hidden; }
.takeover { position:absolute; inset:0; padding:5vh 7vw 4vh; background:var(--ink); }
.takeover .title { font-size:6.5vh; }
.takeover .room, .takeover .when { font-size:3vh; }

/* The bar: small, because this screen gets a pointer at most. */
.bar { background:var(--slate); padding:1.1vh 4vw 1.3vh; display:flex; flex-direction:column; gap:.9vh; }
.nextclass { margin:0; font-size:1.8vh; font-weight:600; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.nextclass b { margin-right:1.4vw; font-size:1.3vh; letter-spacing:.12em; text-transform:uppercase; color:var(--signal); }
nav { display:flex; align-items:center; gap:1.2vw; }
.showing { margin:0 auto 0 0; font-size:1.3vh; letter-spacing:.1em; text-transform:uppercase; color:var(--dim); }
.showing b { color:var(--paper); letter-spacing:.06em; }
nav button { padding:.5vh 1.6vw; border:.2vh solid var(--rule); border-radius:99px; background:transparent;
  color:var(--soft); font:inherit; font-size:1.35vh; font-weight:650; cursor:pointer; }
nav button[aria-current=true] { background:var(--signal); border-color:var(--signal); color:var(--ink); }
nav #hold[aria-pressed=true] { border-color:var(--signal); color:var(--signal); }
nav.taken button[data-m] { display:none; }"""

WALL_JS = """<script>
(function () {
  var M = @MODS@, EVERY = @EVERY@, RELOAD = @RELOAD@, HOLD_FOR = 180,
      K = window.FCPMClass, qs = location.search, born = Date.now(),
      stage = document.getElementById('stage'), card = document.getElementById('class'),
      nav = document.querySelector('nav'), showing = document.getElementById('showing'),
      hold = document.getElementById('hold'), next = document.getElementById('nextclass'),
      buttons = document.querySelectorAll('nav button[data-m]'),
      cur = 0, timer = null, held = 0, taken = false;
  function find(name) { for (var i = 0; i < M.length; i++) if (M[i].name === name) return i; return 0; }
  function show(i) {
    cur = (i + M.length) %% M.length;
    var m = M[cur], f = document.createElement('iframe');
    f.title = m.label; f.src = m.name + '.html' + qs;
    f.addEventListener('load', function () {
      f.classList.add('shown');
      Array.prototype.forEach.call(stage.querySelectorAll('iframe'), function (o) {
        if (o !== f) setTimeout(function () { o.remove(); }, 700);
      });
    });
    stage.insertBefore(f, card);
    buttons.forEach(function (b) { b.setAttribute('aria-current', b.dataset.m === m.name); });
    showing.textContent = m.label;
    try { history.replaceState(null, '', qs + '#' + m.name); } catch (e) {}
    arm();
  }
  function arm() {
    clearTimeout(timer);
    if (!held && !taken) timer = setTimeout(function () { show(cur + 1); }, EVERY * 1000);
  }
  function setHold(on) {
    held = on ? Date.now() : 0; hold.setAttribute('aria-pressed', !!on); arm();
  }
  function classes() {
    var s = K.pick(), was = taken;
    taken = !!s;
    if (s) K.card(card, s, K.words.hint_wall);
    card.hidden = !taken; stage.classList.toggle('taken', taken); nav.classList.toggle('taken', taken);
    if (taken) { clearTimeout(timer); showing.textContent = K.words.head; }
    else if (was) show(cur);
    var u = taken ? null : K.upcoming(1)[0];
    next.hidden = !u;
    if (u) next.lastChild.textContent = u.title + '  \\u00b7  ' + K.day(u.starts) + ', ' + K.time(u.starts);
  }
  buttons.forEach(function (b) { b.addEventListener('click', function () { show(find(b.dataset.m)); }); });
  hold.addEventListener('click', function () { setHold(!held); });
  document.addEventListener('contextmenu', function (ev) { ev.preventDefault(); });
  setInterval(function () {
    if (held && Date.now() - held > HOLD_FOR * 1000) setHold(false);
    // The shell reloads now and then, for a change in its modules or classes;
    // never while held.
    if (!held && Date.now() - born > RELOAD * 1000) location.reload();
  }, 10000);
  show(find(location.hash.slice(1)));
  classes(); setInterval(classes, 15000);
})();
</script>"""


def wall_cfg():
    return node().get("wall") or {}


def wall_modules():
    return [m for m in wall_cfg().get("modules") or []
            if m.get("page") in WALL_PAGES and re.fullmatch(r"[a-z0-9-]+", str(m.get("name", "")))]


def wall_files():
    """Every file of the wall, by name: the shell, then one per module."""
    cfg = wall_cfg()
    every, rotate = int(cfg.get("every", 60)), int(cfg.get("rotate", 45))
    mods = wall_modules()
    files = {}
    for m in mods:
        build, url, data = WALL_PAGES[m["page"]]
        shim = WALL_SHIM % json.dumps({url: data()}).replace("</", "<\\/") if url else ""
        files[m["name"] + ".html"] = build().replace(POLL, "").replace("</head>", shim + "</head>", 1)
    ci = (node().get("wording") or {}).get("checkin") or {}
    rail = "".join('<button type=button data-m="%s">%s</button>' % (
        html.escape(m["name"], quote=True), e(m.get("label", m["name"]))) for m in mods)
    body = """<header class=super>%s<div><h1>%s</h1><p class=sub>%s</p></div></header>
<main class=stage id=stage><div class="class takeover" id=class hidden></div></main>
<footer class=bar>
  <p class=nextclass id=nextclass hidden><b>%s</b><span></span></p>
  <nav aria-label="Wall"><p class=showing>%s <b id=showing></b></p>%s<button type=button id=hold aria-pressed=false title="Hold this screen still for three minutes">%s</button></nav>
</footer>
%s%s""" % (checkin_mark(inline=True), e(ci.get("head")), e(ci.get("sub")),
           e(class_words()["next"]), e(cfg.get("showing", "Showing")), rail, e(cfg.get("hold", "Hold")),
           class_js(),
           WALL_JS.replace("%%", "%").replace("@MODS@", json.dumps(
               [{"name": m["name"], "label": m.get("label", m["name"])} for m in mods]))
           .replace("@EVERY@", str(rotate)).replace("@RELOAD@", str(every * 10)))
    files["index.html"] = page("Studio wall", body, WALL_CSS + CLASS_CSS).replace(POLL, "")
    return files


def wall_target():
    cfg, server = wall_cfg(), (node().get("depot") or {}).get("server")
    if not (cfg.get("share") and server):
        return None
    return pathlib.Path(share_root(server, cfg["share"])) / cfg.get("folder", ".wall")


def write_wall():
    """Write the wall to its share, each file whole or not at all. Returns
    what went wrong, or None. Files the wall no longer has are removed: the
    folder is this node's to keep tidy."""
    target = wall_target()
    if target is None:
        return "no wall share in node.yml"
    files = wall_files()
    target.mkdir(exist_ok=True)
    ctypes.windll.kernel32.SetFileAttributesW(str(target), 0x2)   # hidden, for Explorer
    for name, body in files.items():
        part = target / (name + ".part")
        part.write_bytes(body.encode("utf-8"))
        os.replace(part, target / name)
    for old in target.iterdir():
        if old.is_file() and old.name not in files:
            old.unlink()
    return None


def watch_wall():
    said = ...                                       # so the first outcome is logged too
    while True:
        try:
            err = write_wall()
        except Exception as exc:
            err = repr(exc)
        if err != said:                              # log changes, not every beat
            log("wall: " + (err or "writing to %s" % wall_target()))
            said = err
        time.sleep(int(wall_cfg().get("every", 60)))


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
            if route in ("/depot", "/depot/"):
                return self.reply(200, depot_page())
            if route == "/depot/now":
                return self.reply(200, json.dumps(depot_now()), TYPES[".json"])
            if route == "/kiosk/now":
                return self.reply(200, json.dumps({"on": on_now(), "map": stations()}), TYPES[".json"])
            if route.startswith("/kiosk/wifi/") and tail.isdigit():
                svg = wifi_svg(int(tail))
                return self.reply(200, svg, TYPES[".svg"]) if svg else self.file(None)
            if route.startswith("/kiosk/qr/") and tail.isdigit():
                return self.file(qr_image(int(tail)))
            if route == "/wall" or route.startswith("/wall/"):
                files = wall_files()           # the same bytes the share gets
                name = tail or "index.html"
                return self.reply(200, files[name]) if name in files else self.file(None)
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
    threading.Thread(target=watch_depot, daemon=True).start()
    threading.Thread(target=watch_wall, daemon=True).start()
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
    # Held for this process's life, released by Windows when it goes. The
    # logon task starts supervise every five minutes; this is what makes a
    # start that finds one already running a no-op.
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    k.CreateMutexW.restype = ctypes.c_void_p
    k.CloseHandle.argtypes = [ctypes.c_void_p]
    mutex = k.CreateMutexW(None, False, "Local\\media-node-supervise")
    if ctypes.get_last_error() == 183:                  # ERROR_ALREADY_EXISTS
        log("supervise: already running; this one leaves")
        return 0
    me = pathlib.Path(__file__).read_bytes()

    def raise_screens():
        # Once, when supervise starts: at logon, or after it was restarted.
        # Not on a timer: a panel somebody closed on purpose stays closed.
        for _ in range(60):
            if door_answers():
                return screens(launch=True, say=log)
            time.sleep(2)
        log("screens: the door did not answer in two minutes; not launching")

    def puller():
        while True:
            try:
                pull_once()
            except Exception as exc:
                log("pull: %r" % exc)
            time.sleep(PULL_EVERY)
    threading.Thread(target=puller, daemon=True).start()
    threading.Thread(target=raise_screens, daemon=True).start()
    threading.Thread(target=keep_sessions, daemon=True).start()
    while True:
        code = subprocess.run([sys.executable, __file__, "serve"], creationflags=NO_WINDOW).returncode
        if code == BOUNCE and pathlib.Path(__file__).read_bytes() != me:
            # supervise's own code moved too. Restarting only `serve` would
            # leave this process on the old code for the rest of the sign-in
            # (2026-09-25: session revival merged mid-day, and the supervise
            # started at 00:41 never took a snapshot). Hand over: let go of
            # the mutex, start a fresh supervise, and leave.
            log("supervise: my code changed; starting a fresh one")
            k.CloseHandle(mutex)
            subprocess.Popen([sys.executable, "-X", "utf8", __file__, "supervise"], close_fds=True,
                             creationflags=NO_WINDOW | getattr(subprocess, "DETACHED_PROCESS", 0))
            return 0
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


BROWSERS = {"msedge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            "chrome": r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"}


def launch_screen(exe, s, url):
    """One browser instance per screen, in kiosk mode, with a profile folder of
    its own. The separate profile is what makes it work: a plain --new-window
    is handed to whatever browser is already open, which restores its last
    session and ignores --start-fullscreen (2026-09-24, after a reboot left four
    half-sized windows). Kiosk mode is InPrivate, so a public screen keeps
    nothing between starts."""
    x, y, w, h = s["rect"]
    args = [BROWSERS[exe], "--user-data-dir=%s" % (STATE / "screens" / s["name"]),
            "--no-first-run", "--kiosk", url,
            "--window-position=%d,%d" % (x, y), "--window-size=%d,%d" % (w, h)]
    if exe == "msedge":
        args.append("--edge-kiosk-type=fullscreen")
    subprocess.Popen(args)


def screens(launch=False, say=print):
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
            say("ok       %-8s %-9s full-screen  %s" % (s["name"], s["display"], hit["title"]))
            continue
        bad += 1
        say("missing  %-8s %-9s nothing full-screen at %s" % (s["name"], s["display"], s["rect"]))
        if launch:
            url = "http://%s.local:%d%s" % (socket.gethostname().lower(), PORT, s["url"])
            launch_screen(exe, s, url)
            say("         launched %s there" % url)
    return 1 if bad and not launch else 0


# ------------------------------------------------------------------ sessions --
# The Claude sessions working on this node, brought back after a power cut the
# way the screens are. `supervise` writes down what is running every pass; at
# its first pass after a sign-in, it resumes whatever was running before, in the
# background, where Remote Control reaches it. Session ids stay here, in
# LOCALAPPDATA, never in the repo.
SESSIONS = STATE / "sessions.json"
CLAUDE = shutil.which("claude") or str(pathlib.Path.home() / ".local" / "bin" / "claude.exe")


def claude(*args, cwd=None):
    try:
        out = subprocess.run([CLAUDE, *args], capture_output=True, text=True, timeout=120,
                             cwd=cwd, creationflags=NO_WINDOW, encoding="utf-8", errors="replace")
        return out.returncode, (out.stdout + out.stderr).strip()
    except (OSError, subprocess.SubprocessError) as exc:
        return None, repr(exc)


def running_sessions():
    """What `claude agents --json` lists as live, interactive and background.
    None if it could not be asked, which is not the same as nothing running."""
    code, out = claude("agents", "--json")
    if code != 0:
        return None
    try:
        rows = json.loads(out[out.index("["):])
    except ValueError:
        return None
    return [{"id": r["sessionId"], "name": r.get("name") or r["sessionId"][:8],
             "cwd": r.get("cwd"), "kind": r.get("kind")} for r in rows if r.get("sessionId")]


def booted_at():
    ms = ctypes.windll.kernel32.GetTickCount64
    ms.restype = ctypes.c_ulonglong
    return time.time() - ms() / 1000


def signed_in_at():
    """When this user's sign-in began, from LSA. Sessions die with the sign-in,
    not the boot, and the boot can't be trusted: with Fast Startup on (the
    default; it is on here) Shut down hibernates the kernel, so the uptime
    runs on across a power-off while every session is gone. Falls back to
    the boot if LSA won't say."""
    from ctypes import wintypes as W

    class LUID(ctypes.Structure):
        _fields_ = [("Low", W.DWORD), ("High", W.LONG)]

    class STATS(ctypes.Structure):          # TOKEN_STATISTICS
        _fields_ = [("TokenId", LUID), ("AuthenticationId", LUID), ("ExpirationTime", ctypes.c_longlong),
                    ("TokenType", ctypes.c_int), ("ImpersonationLevel", ctypes.c_int),
                    ("DynamicCharged", W.DWORD), ("DynamicAvailable", W.DWORD),
                    ("GroupCount", W.DWORD), ("PrivilegeCount", W.DWORD), ("ModifiedId", LUID)]

    class USTR(ctypes.Structure):           # LSA_UNICODE_STRING
        _fields_ = [("Length", W.USHORT), ("MaximumLength", W.USHORT), ("Buffer", W.LPWSTR)]

    class LOGON(ctypes.Structure):          # SECURITY_LOGON_SESSION_DATA, as far as LogonTime
        _fields_ = [("Size", W.ULONG), ("LogonId", LUID), ("UserName", USTR), ("LogonDomain", USTR),
                    ("AuthenticationPackage", USTR), ("LogonType", W.ULONG), ("Session", W.ULONG),
                    ("Sid", ctypes.c_void_p), ("LogonTime", ctypes.c_longlong)]

    adv, k32, sec = ctypes.windll.advapi32, ctypes.windll.kernel32, ctypes.windll.secur32
    k32.GetCurrentProcess.restype = W.HANDLE
    adv.OpenProcessToken.argtypes = [W.HANDLE, W.DWORD, ctypes.POINTER(W.HANDLE)]
    k32.CloseHandle.argtypes = [W.HANDLE]
    tok, st, n, data = W.HANDLE(), STATS(), W.DWORD(), ctypes.POINTER(LOGON)()
    if not adv.OpenProcessToken(k32.GetCurrentProcess(), 0x0008, ctypes.byref(tok)):     # TOKEN_QUERY
        return booted_at()
    try:
        if not adv.GetTokenInformation(tok, 10, ctypes.byref(st), ctypes.sizeof(st), ctypes.byref(n)):
            return booted_at()
    finally:
        k32.CloseHandle(tok)
    if sec.LsaGetLogonSessionData(ctypes.byref(st.AuthenticationId), ctypes.byref(data)) != 0 or not data:
        return booted_at()
    try:
        return data.contents.LogonTime / 1e7 - 11644473600        # FILETIME, 1601 UTC -> Unix
    finally:
        sec.LsaFreeReturnBuffer(data)


def read_sessions():
    try:
        return json.loads(SESSIONS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"taken": 0, "sessions": [], "pins": {}}


def write_sessions(book):
    STATE.mkdir(parents=True, exist_ok=True)
    tmp = SESSIONS.with_suffix(".tmp")
    tmp.write_text(json.dumps(book, indent=1), encoding="utf-8")
    os.replace(tmp, SESSIONS)


def snapshot_sessions():
    live = running_sessions()
    if live is None:
        return log("sessions: could not list them; keeping the last snapshot")
    book = read_sessions()
    book.update(taken=time.time(), sessions=live)
    write_sessions(book)


def revive(s, say=log):
    """Background, same id. A session born interactive is woken with Remote
    Control and its name. One already in the background kept its options
    (Remote Control included) and is woken without flags: flags would start a
    copy under a new id (2026-09-25, tried on throwaways)."""
    if s.get("kind") == "background":
        args = ["--bg", "--resume", s["id"]]
    else:
        args = ["--bg", "--resume", s["id"], "--name", s["name"], "--remote-control"]
    cwd = s.get("cwd") if s.get("cwd") and os.path.isdir(s["cwd"]) else None
    code, out = claude(*args, cwd=cwd)
    last = out.splitlines()[-1] if out else ""
    say("sessions: %s %s (%s)%s" % ("revived" if code == 0 else "could not revive",
                                    s["name"], s["id"][:8], "" if code == 0 else ": " + last))
    return code == 0


def revive_sessions(force=False, say=log):
    """Resume what was running before this sign-in. Only after one: supervise
    also restarts mid-session, and a session somebody closed on purpose since
    must stay closed. Pins override: `in` always comes back, `out` never."""
    book = read_sessions()
    if not force and book.get("taken", 0) > signed_in_at():
        return 0
    live = running_sessions()
    if live is None:
        say("sessions: could not list them; not reviving")
        return 1
    live_ids = {s["id"] for s in live}
    pins = book.get("pins") or {}
    want = {s["id"]: s for s in book.get("sessions") or []}
    want.update({i: p for i, p in pins.items() if p.get("pin") == "in"})
    bad = 0
    for sid, s in want.items():
        s = dict(s, id=sid)
        if sid in live_ids or (pins.get(sid) or {}).get("pin") == "out":
            continue
        bad += not revive(s, say=say)
    return 1 if bad else 0


def keep_sessions():
    # Revive before the first snapshot, which would otherwise record the
    # empty machine a boot leaves and forget what was running.
    try:
        revive_sessions()
    except Exception as exc:
        log("sessions: revive %r" % exc)
    while True:
        try:
            snapshot_sessions()
        except Exception as exc:
            log("sessions: %r" % exc)
        time.sleep(PULL_EVERY)


def sessions(argv):
    """door.py sessions                   what ran at the last snapshot, and what runs now
    door.py sessions pin in|out <id>   always bring it back, or never
    door.py sessions pin clear <id>    back to following the snapshot
    door.py sessions --revive          bring back what is missing now, boot or not"""
    book = read_sessions()
    if argv[:1] == ["--revive"]:
        return revive_sessions(force=True, say=print)
    if argv[:1] == ["pin"] and len(argv) == 3 and argv[1] in ("in", "out", "clear"):
        how, key = argv[1], argv[2]
        known = {s["id"]: s for s in (running_sessions() or []) + (book.get("sessions") or [])}
        known.update({i: dict(p, id=i) for i, p in (book.get("pins") or {}).items()})
        hits = [s for i, s in known.items() if i.startswith(key) or s.get("name") == key]
        if len(hits) != 1:
            print("%s session matches %r" % ("no" if not hits else "more than one", key))
            return 1
        s = hits[0]
        pins = book.setdefault("pins", {})
        if how == "clear":
            pins.pop(s["id"], None)
        else:
            pins[s["id"]] = {"pin": how, "name": s.get("name"), "cwd": s.get("cwd"), "kind": s.get("kind")}
        write_sessions(book)
        print("pinned %s  %s (%s)" % (how, s.get("name"), s["id"][:8]))
        return 0
    if argv:
        print(sessions.__doc__)
        return 2
    live = running_sessions()
    live_ids = {s["id"] for s in live or []}
    taken = book.get("taken") or 0
    print("snapshot  %s%s" % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(taken)) if taken else "never",
                             "  (before this sign-in: the next supervise start revives)" if taken and taken < signed_in_at() else ""))
    pins = book.get("pins") or {}
    rows = {s["id"]: s for s in book.get("sessions") or []}
    rows.update({s["id"]: s for s in live or []})
    rows.update({i: dict(p, id=i) for i, p in pins.items() if i not in rows})
    for sid, s in rows.items():
        state = "running" if sid in live_ids else ("unknown" if live is None else "stopped")
        pin = (pins.get(sid) or {}).get("pin")
        print("%-8s %-11s %s  %-24s %s" % (state, s.get("kind") or "", sid[:8], s.get("name") or "",
                                           "pinned " + pin if pin else ""))
    return 0


def door_url():
    return "http://%s.local:%d/" % (socket.gethostname().lower(), PORT)


def door_answers():
    """The revision, if the door answers by name, else None."""
    import urllib.request
    try:
        with urllib.request.urlopen(door_url() + "revision", timeout=5) as r:
            return r.read().decode()
    except Exception:
        return None


def status():
    rev = door_answers()
    if rev:
        print("up    %s   revision %s" % (door_url(), rev))
        return 0
    print("down  %s" % door_url())
    print("log   %s" % (STATE / "door.log"))
    return 1


# ------------------------------------------------------------------- startup --
TASK = "media-node door"
VENV_PYTHONW = STATE / "venv" / "Scripts" / "pythonw.exe"
SHORTCUT = (pathlib.Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" /
            "Start Menu" / "Programs" / "Startup" / "media-node door.lnk")


def whoami():
    return "%s\\%s" % (os.environ.get("USERDOMAIN", ""), os.environ.get("USERNAME", ""))


def task_xml(here=HERE):
    """The logon task, with this checkout's paths resolved now.

    Generated rather than written, like station-node's `bin/door plist`, so a
    moved worktree is one command and not an edit. The fixed venv's pythonw:
    one interpreter path, so the firewall asks once, and no console window.
    `-X utf8` stands in for PYTHONUTF8, which a task action cannot set."""
    esc = html.escape
    user = esc(whoami())
    return """<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>The media node's door and screens. Generated by machines\\kiosk-1\\door.py startup --xml; regenerate rather than edit.</Description>
  </RegistrationInfo>
  <Triggers>
    <LogonTrigger>
      <Enabled>true</Enabled>
      <UserId>%(user)s</UserId>
    </LogonTrigger>
    <!-- The keep-alive. Not a repetition on the logon trigger: that one only
         arms at a logon, so a task registered mid-session would have none
         until the next one. A time trigger in the past repeats from now. -->
    <TimeTrigger>
      <Enabled>true</Enabled>
      <StartBoundary>2026-01-01T00:00:00</StartBoundary>
      <Repetition>
        <Interval>PT5M</Interval>
        <StopAtDurationEnd>false</StopAtDurationEnd>
      </Repetition>
    </TimeTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>%(user)s</UserId>
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <Enabled>true</Enabled>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>%(py)s</Command>
      <Arguments>-X utf8 "%(door)s" supervise</Arguments>
      <WorkingDirectory>%(root)s</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
""" % {"user": user, "py": esc(str(VENV_PYTHONW)),
       "door": esc(str(here / "door.py")), "root": esc(str(here.parents[1]))}


def installed_task():
    """The registered task's XML, or None. Asked of Task Scheduler every time,
    never remembered."""
    out = subprocess.run(["schtasks", "/Query", "/TN", TASK, "/XML"],
                         capture_output=True, text=True, creationflags=NO_WINDOW)
    return out.stdout if out.returncode == 0 else None


def startup(argv):
    if "--xml" in argv:
        print(task_xml(), end="")
        return 0
    if "--install" in argv:
        path = STATE / "door-task.xml"
        STATE.mkdir(parents=True, exist_ok=True)
        path.write_text(task_xml(), encoding="utf-16")
        out = subprocess.run(["schtasks", "/Create", "/TN", TASK, "/XML", str(path), "/F"],
                             capture_output=True, text=True, creationflags=NO_WINDOW)
        path.unlink()
        if out.returncode != 0:
            print("could not register the task: %s" % (out.stderr or out.stdout).strip())
            return 1
        print("registered  task %r -> %s" % (TASK, HERE / "door.py"))
        if SHORTCUT.exists():
            # Two things starting supervise at logon is two pullers; the
            # task alone is the startup now.
            SHORTCUT.unlink()
            print("removed     the Startup shortcut, which the task replaces")
        print("\nA door already running from before keeps running. The task will not")
        print("start another while it lives. To hand over now: stop it, then")
        print('  schtasks /Run /TN "%s"' % TASK)
        return 0

    bad = 0
    xml = installed_task()
    want = str(HERE / "door.py")
    if xml is None:
        bad += 1
        print("task      %r is not registered.  door.py startup --install" % TASK)
    elif want.lower() in xml.lower():
        print("task      %r starts %s at logon" % (TASK, want))
    else:
        bad += 1
        print("task      %r points elsewhere; regenerate from the checkout the door runs from" % TASK)
    if SHORTCUT.exists():
        print("shortcut  %s still exists%s" % (SHORTCUT.name, "; --install removes it" if xml else ""))
    rev = door_answers()
    print("door      %s" % ("up, revision " + rev if rev else "not answering"))
    print("logon     manual. Signing in automatically needs an administrator (PROFILE.md)")
    return 1 if bad else 0


if __name__ == "__main__":
    verb = sys.argv[1] if len(sys.argv) > 1 else "status"
    if verb == "screens":
        sys.exit(screens(launch="--launch" in sys.argv))
    if verb == "startup":
        sys.exit(startup(sys.argv[2:]))
    if verb == "sessions":
        sys.exit(sessions(sys.argv[2:]))
    if verb == "wifi-password" and len(sys.argv) > 2:
        sys.exit(wifi_password(sys.argv[2]))
    sys.exit({"serve": serve, "supervise": supervise, "status": status}.get(verb, status)())
