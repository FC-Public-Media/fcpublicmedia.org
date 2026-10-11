#!/usr/bin/env python3
"""qr.local: the screen on the qr Pi, as panels.

  bar      qr.local, the org, the clock
  inbox    one line per thing waiting to be picked up: the item on a yellow wedge, who it's for, its size
  camera   the live picture, always in the same place; a pickup takes this panel over while it runs
  latest   the last few events, anchored to the bottom

The camera is three jobs that never wait on each other: a grabber keeps only the newest frame, the
display draws it as it lands, and the QR search runs in its own process on whatever frame is newest. zbar
only finds codes. AC1 frames go to bridge.mjs (the bottles carrier) for reading and signature checks.
Text is ANSI on tty1, rotated by fbcon; the picture is written straight into the framebuffer.
"""
import collections, json, mmap, os, signal, subprocess, sys, termios, threading, time

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.environ.get("QR_STATE") or HERE         # what changes: inbox, used codes, events, the built font
P = lambda name: os.path.join(HERE, name)          # the profile's files, read-only
ST = lambda name: os.path.join(STATE, name)

CFG = {"width": 1440, "height": 1080, "fps": 10, "shutter": 8000, "step": 2,
       "mirror_x": True, "mirror_y": False, "live_seconds": 15, "motion": 6.0,
       "console_font": "/usr/share/consolefonts/Uni2-TerminusBold28x14.psf.gz"}
for where in (P, ST):                              # the profile's config, then this machine's overrides
    try:
        CFG.update(json.load(open(where("config.json"))))
    except FileNotFoundError:
        pass
W, H = CFG["width"], CFG["height"]
STRIDE = CFG.get("stride") or (W + 63) // 64 * 64   # the camera pads each row to a 64-byte boundary
FRAME = STRIDE * H * 3 // 2

# Palette: 0 ink, 2 go, 3 brand yellow, 6 muted yellow, 7 paper. Yellow is a surface, never text.
PALETTE = "\x1b]P0121417\x1b]P22f9e5b\x1b]P3ffc61a\x1b]P6a8841a\x1b]P7ece8e1"
OFF, BOLD, GO, BAD = "\x1b[0m", "\x1b[1m", "\x1b[32m", "\x1b[31m"
ON_YELLOW, ON_MUTED, ON_BAD = "\x1b[43;30m", "\x1b[46;30m", "\x1b[41;37m"
YELLOW_EDGE, MUTED_EDGE = "\x1b[33m", "\x1b[36m"   # a wedge in the colour of the surface it ends
WEDGE = "\ue0b0"                            # from qr-font.psf; a plain fallback if it won't load
TONE = {"bad": BAD, "warn": BAD}            # colour points at trouble; everything else stays plain


def load(name, default):
    """This machine's copy if it has one, else the profile's."""
    for where in (ST, P):
        try:
            return json.load(open(where(name)))
        except (FileNotFoundError, ValueError):
            continue
    return default


def save(name, data):
    tmp = ST(name + ".tmp")
    with open(tmp, "w") as f:
        json.dump(data, f, indent=1)
    os.replace(tmp, ST(name))


def history():
    """The last few events from events.log, so a restart doesn't blank the latest pane."""
    try:
        lines = open(ST("events.log")).read().splitlines()[-40:]
    except FileNotFoundError:
        return []
    out = []
    for line in lines:
        parts = line.split(" ", 3)
        if len(parts) == 4 and parts[3] != "station up":
            out.append((parts[1][:5], parts[2].lower(), parts[3]))
    return out[-8:]


class State:
    def __init__(self):
        self.lock = threading.Lock()
        self.rows = load("inbox.json", [])
        self.used = set(load("used.json", []))
        self.log = collections.deque(history(), maxlen=8)
        self.live_until = 0.0
        self.awake = False        # someone's in front of the camera: the pane's bar lights up
        self.boxes = (0.0, [])    # (when, [(x0, x1, y0, y1)]) where the search last found codes
        self.catch = None         # the AC1 catch underway, or just finished
        self.drives = []          # removable drives plugged in right now (read-only view)
        self.platform = ""        # power and temperature, for the latest bar
        self.trouble = None       # the newest power trouble, shown until it has been quiet a while
        self.dirty = True

    def event(self, kind, text):
        with self.lock:
            self.log.append((time.strftime("%H:%M"), kind, text))
            self.dirty = True
        with open(ST("events.log"), "a") as f:
            f.write(f"{time.strftime('%F %T')} {kind.upper()} {text}\n")


S = State()


# ---- reading: AC1 frames through the carrier bridge ----------------------------------------------------

class Reader:
    def __init__(self):
        self.proc = None
        self.recent = {}          # transfer id -> last time we acted on it (a held-up code repeats)
        self.stats = None         # the catch underway: when it started, frames seen, new frames
        try:
            self.proc = subprocess.Popen(["node", P("bridge.mjs")], stdin=subprocess.PIPE,
                                         stdout=subprocess.PIPE, text=True, bufsize=1, env={**os.environ, "QR_STATE": STATE})
            threading.Thread(target=self.listen, daemon=True).start()
        except FileNotFoundError:
            S.event("warn", "reader off · no Node.js")

    def saw(self, fresh):
        now = time.time()
        if self.stats is None or now - self.stats["last"] > 30:
            self.stats = {"start": now, "last": now, "seen": 0, "new": 0}
        self.stats["last"] = now
        self.stats["seen"] += 1
        self.stats["new"] += fresh

    def send(self, text):
        if self.proc and self.proc.poll() is None:
            try:
                self.proc.stdin.write(json.dumps({"frame": text}) + "\n")
                self.proc.stdin.flush()
            except BrokenPipeError:
                pass

    def listen(self):
        for line in self.proc.stdout:
            try:
                msg = json.loads(line)
            except ValueError:
                continue
            if msg["type"] == "snapshot":
                with S.lock:
                    S.catch = {"snap": msg["snap"], "stats": dict(self.stats or {}), "at": time.time(), "done": None}
                    S.dirty = True
            elif msg["type"] == "result":
                t = (msg.get("transfers") or [{}])[0]
                with S.lock:
                    if S.catch:
                        good = msg["ok"] and t.get("ok")
                        S.catch["done"] = "ok" if good else "bad"
                        S.catch["who"] = t.get("name") or "unknown signer"
                        S.catch["at"] = time.time()
                    S.dirty = True
                self.stats = None
                self.result(msg)
        S.event("bad", "reader stopped")

    def result(self, msg):
        key = ",".join(msg.get("ids", []))
        now = time.time()
        if now - self.recent.get(key, 0) < 120:
            return                                   # same code still held up; already handled
        self.recent[key] = now
        for t in msg["transfers"]:
            if not t["ok"]:
                S.event("bad", "didn't verify · " + "; ".join(t["errors"] or ["?"]))
                continue
            if not t["trusted"]:
                S.event("warn", f"unknown signer …{(t['by'] or '')[-6:]} · refused")
                continue
            if key in S.used:
                S.event("warn", "used code · refused")
                continue
            who = t["name"] or "trusted"
            try:
                body = json.loads(t["text"] or "{}")
            except ValueError:
                body = {}
            if t["kind"] == "fcpm.pickup":
                self.pickup(body, key)
            elif t["kind"] == "fcpm.approval":
                self.spend(key)
                S.event("ok", f"approval {body.get('say', '')} · {who}")
            else:
                S.event("info", f"{t['kind']} · {who} · {t['size']} B")

    def pickup(self, body, key):
        with S.lock:
            row = next((r for r in S.rows if r["id"] == body.get("pickup")), None)
        if not row:
            S.event("warn", "pickup for nothing here")
            return
        if row.get("status") != "ready":
            S.event("warn", f"{row['what']} · busy")
            return
        if not row.get("demo"):
            self.spend(key)
        with S.lock:
            row["status"] = "picking up"
            row["since"] = time.time()
            S.dirty = True
        S.event("ok", f"{row['what']} → {row['for']}")

    def spend(self, key):
        with S.lock:
            S.used.add(key)
            save("used.json", sorted(S.used))


# ---- drives: what's plugged in for a pickup, read-only ------------------------------------------------
# lsblk only: label, filesystem, size. Nothing here mounts, writes, or ejects anyone's media.

def drives():
    try:
        tree = json.loads(subprocess.run(["lsblk", "-J", "-b", "-o", "NAME,SIZE,RM,TRAN,FSTYPE,LABEL,MOUNTPOINTS"],
                                         capture_output=True, text=True, timeout=5).stdout)
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return []
    found = []
    for disk in tree.get("blockdevices", []):
        if disk.get("tran") != "usb" or not disk.get("rm") or not int(disk.get("size") or 0):
            continue
        for part in disk.get("children") or [disk]:
            if int(part.get("size") or 0):
                found.append({"name": part["name"], "size": int(part["size"]), "fs": part.get("fstype") or "",
                              "label": part.get("label") or part["name"]})
    return found


def watch_drives():
    known = None                                     # what was already in at start isn't news
    while True:
        now = drives()
        names = {d["name"] for d in now}
        if known is None:
            known = names
        for d in now:
            if d["name"] not in known:
                S.event("info", f"drive in · {d['label']} · {gb(d['size'])}")
        for gone in known - names:
            S.event("info", f"drive out · {gone}")
        with S.lock:
            if names != known:
                S.dirty = True
            S.drives = now
        known = names
        time.sleep(2)


def gb(n):
    return f"{n / 1e9:.1f} GB" if n >= 1e9 else f"{n / 1e6:.0f} MB"


def size_bytes(text):
    try:
        num, unit = text.split()
        return float(num) * {"KB": 1e3, "MB": 1e6, "GB": 1e9, "TB": 1e12}[unit.upper()]
    except (ValueError, KeyError):
        return None


# ---- the platform: power and heat, for the latest bar ----------------------------------------------------
# The firmware's throttle flags (under-voltage now / since boot), the core temperature, and the kernel's
# own word on USB over-current. A Pi 3 shares about 1.2 A across its USB ports.

UNDER_NOW, UNDER_SINCE, HOT_NOW = 0x1, 0x10000, 0x4


def watch_platform():
    threading.Thread(target=watch_kernel, daemon=True).start()
    while True:
        try:
            flags = int(subprocess.run(["vcgencmd", "get_throttled"], capture_output=True, text=True,
                                       timeout=5).stdout.split("=")[1], 16)
        except (OSError, ValueError, IndexError, subprocess.TimeoutExpired):
            flags = 0
        try:
            temp = int(open("/sys/class/thermal/thermal_zone0/temp").read()) // 1000
        except (OSError, ValueError):
            temp = None
        if flags & UNDER_NOW:
            power = "under-voltage"
        elif flags & HOT_NOW:
            power = "throttled, hot"
        elif flags & UNDER_SINCE:
            power = "power dipped since boot"
        else:
            power = "power ok"
        text = power + (f" · {temp}°C" if temp is not None else "")
        with S.lock:
            if text != S.platform:
                S.platform = text
                S.dirty = True
            if flags & (UNDER_NOW | HOT_NOW):
                S.trouble = (time.time(), power)
        time.sleep(5)


def watch_kernel():
    """USB over-current and under-voltage, as the kernel reports them."""
    try:
        proc = subprocess.Popen(["journalctl", "-k", "-f", "-n", "0", "-o", "cat"], stdout=subprocess.PIPE,
                                stderr=subprocess.DEVNULL, text=True)
    except OSError:
        return
    for line in proc.stdout:
        low = line.lower()
        if "over-current" in low:
            port = line.split(":")[0].replace("usb ", "").strip()
            what = f"USB over-current · {port}"
        elif "under-voltage" in low or "undervoltage" in low:
            what = "under-voltage"
        else:
            continue
        with S.lock:
            fresh = not S.trouble or S.trouble[1] != what or time.time() - S.trouble[0] > 10
            S.trouble = (time.time(), what)
            S.dirty = True
        if fresh:
            S.event("warn", what)


# ---- the camera: three jobs that never wait on each other ---------------------------------------------

class Latest:
    def __init__(self):
        self.cond = threading.Condition()
        self.frame, self.seq = None, 0

    def put(self, y):
        with self.cond:
            self.frame, self.seq = y, self.seq + 1
            self.cond.notify_all()

    def wait(self, seq):
        with self.cond:
            self.cond.wait_for(lambda: self.seq != seq)
            return self.frame, self.seq


def grab(latest):
    cmd = ["rpicam-vid", "-t", "0", "-n", "--codec", "yuv420", "--width", str(W), "--height", str(H),
           "--framerate", str(CFG["fps"]), "--shutter", str(CFG["shutter"]), "-o", "-"]
    while True:
        cam = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        while True:
            buf = cam.stdout.read(FRAME)
            if len(buf) < FRAME:
                break
            latest.put(buf[:STRIDE * H])
        S.event("bad", "camera stopped · restarting")
        time.sleep(3)


def search_loop(name, todo, done):
    """The QR search, in its own process: zbar only finds codes and returns their text and corners."""
    import zbar
    from multiprocessing import shared_memory
    shm = shared_memory.SharedMemory(name=name)
    scanner = zbar.ImageScanner()
    scanner.parse_config("disable")
    scanner.parse_config("qrcode.enable")
    while True:
        todo.get()
        y = bytes(shm.buf[:STRIDE * H])
        found = []
        for k in (1, 2, 3):                          # a smaller copy shrinks the blur too: rescues soft codes
            if k == 1:
                img = zbar.Image(STRIDE, H, "Y800", y)
            else:
                small = b"".join(y[r * STRIDE:r * STRIDE + W:k] for r in range(0, H, k))
                img = zbar.Image(len(range(0, W, k)), len(range(0, H, k)), "Y800", small)
            scanner.scan(img)
            found = [(sym.data, [(x * k, yy * k) for x, yy in sym.location]) for sym in img]
            if found:
                break
        done.put(found)


class Search:
    def __init__(self):
        import multiprocessing as mp
        from multiprocessing import shared_memory
        ctx = mp.get_context("spawn")
        self.shm = shared_memory.SharedMemory(create=True, size=STRIDE * H)
        self.todo, self.done = ctx.Queue(), ctx.Queue()
        self.busy = False
        ctx.Process(target=search_loop, args=(self.shm.name, self.todo, self.done), daemon=True).start()

    def offer(self, y):
        if not self.busy:
            self.busy = True
            self.shm.buf[:STRIDE * H] = y
            self.todo.put(1)


def results(search, reader):
    seen = {}                                        # text -> last time sent/logged
    while True:
        found = search.done.get()
        search.busy = False
        now = time.time()
        boxes = []
        for text, pts in found:
            S.live_until = now + CFG["live_seconds"]
            if pts:
                boxes.append((min(p[0] for p in pts), max(p[0] for p in pts), min(p[1] for p in pts), max(p[1] for p in pts)))
            if text.startswith("AC1|"):
                reader.saw(text not in seen)
                if now - seen.get(text, 0) > 1:
                    reader.send(text)
                    seen[text] = now
            elif now - seen.get(text, 0) > 30:
                seen[text] = now
                S.event("info", "plain QR · ignored")
        S.boxes = (now, boxes)


def camera(reader, video, search):
    latest = Latest()
    threading.Thread(target=grab, args=(latest,), daemon=True).start()
    threading.Thread(target=results, args=(search, reader), daemon=True).start()
    # Wake on a clear jump above the room's own noise. The floor learns the noise (sensor grain, a lamp's
    # flicker) only from quiet frames, so a steady light settles back to rest and a hand still wakes it.
    prev, seq, snap_t, motion, floor, shot = None, 0, 0.0, 0.0, None, 0
    os.makedirs("/tmp/qr-shots", exist_ok=True)
    while True:
        y, seq = latest.wait(seq)
        now = time.time()
        grid = b"".join(y[r * STRIDE:r * STRIDE + W:16] for r in range(0, H, 16))
        if prev is not None:
            motion = sum(abs(a - b) for a, b in zip(grid, prev)) / len(grid)
            if floor is None:
                floor = motion
            if motion > floor + CFG["motion"]:
                S.live_until = now + CFG["live_seconds"]
            else:
                floor += 0.05 * (motion - floor)
        prev = grid
        if seq % 10 == 0:                            # what the wake check sees, for tuning it
            with open("/tmp/qr-motion", "w") as f:
                f.write(f"{time.strftime('%T')} motion {motion:.1f} floor {floor or 0:.1f} wake above "
                        f"{(floor or 0) + CFG['motion']:.1f} awake {now < S.live_until} for {max(0, S.live_until - now):.0f}s\n")
        awake = now < S.live_until
        if awake != S.awake:
            with S.lock:
                S.awake = awake
                S.dirty = True
        if awake or seq % 10 == 0:                   # someone's here: search every frame; else once a second
            search.offer(y)
        if awake:
            at, boxes = S.boxes
            video.draw(y, boxes if now - at < 0.6 else [])
        elif seq % 10 == 0:
            video.blank()                            # resting: the picture is off
        if now - snap_t > 0.5 and now < S.live_until:  # the last 40 awake frames, for checking aim and focus
            snap_t = now
            shot = (shot + 1) % 40
            with open(f"/tmp/qr-shots/{shot:02d}.pgm", "wb") as f:
                f.write(b"P5 %d %d 255\n" % (W, H) + b"".join(y[r * STRIDE:r * STRIDE + W] for r in range(H)))


# ---- the picture: camera pixels straight into the framebuffer, inside the camera panel ----------------

class Video:
    """The camera picture, unprocessed, in the panel the layout gives it.

    The panel stands portrait and fbcon rotates the text; fb0 stays landscape, so one framebuffer row is
    one column of the portrait screen. Each sampled camera column becomes one screen column (a strided
    slice down the frame), so the picture stays upright and 4:3. `step` sets the scale (2 = 640x480);
    mirror_x / mirror_y turn it to match how people stand at the screen. A frame is built whole, then
    landed in one burst, so the display never shows half of one.
    """

    def __init__(self):
        g = "/sys/class/graphics/fb0/"
        self.fbw, self.fbh = map(int, open(g + "virtual_size").read().split(","))
        self.stride = int(open(g + "stride").read())
        self.bpp = int(open(g + "bits_per_pixel").read())
        self.px = self.bpp // 8
        self.fb = mmap.mmap(os.open("/dev/fb0", os.O_RDWR), self.stride * self.fbh)
        self.step = CFG["step"]
        self.w = len(range(0, W, self.step))   # screen pixels across
        self.h = len(range(0, H, self.step))   # screen pixels down
        self.screen = (self.fbh, self.fbw)     # portrait width x height
        self.origin = None                     # set by the layout; None while the panel shows something else
        self.strip = 0                         # pixels under the picture for the progress strip
        grey = range(256)
        if self.bpp == 16:
            v = [((g >> 3) << 11) | ((g >> 2) << 5) | (g >> 3) for g in grey]
            self.lo, self.hi = bytes(x & 255 for x in v), bytes(x >> 8 for x in v)

    def convert(self, line):
        if self.bpp == 16:
            buf = bytearray(2 * len(line))
            buf[0::2], buf[1::2] = line.translate(self.lo), line.translate(self.hi)
        else:
            buf = bytearray(4 * len(line))
            buf[0::4] = buf[1::4] = buf[2::4] = line
        return buf

    COLOURS = {"ink": (0x12, 0x14, 0x17), "yellow": (0xff, 0xc6, 0x1a), "go": (0x2f, 0x9e, 0x5b),
               "bad": (0xc8, 0x3c, 0x32), "track": (0x2a, 0x2d, 0x31)}

    def pixel(self, name):
        r, g, b = self.COLOURS[name]
        if self.bpp == 16:
            return (((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)).to_bytes(2, "little")
        return bytes((b, g, r, 0))

    def under(self, prog):
        """The strip under each picture column: ink gap, then filled or empty bar, then ink. (cut, filled, empty)"""
        if self.strip < 8:
            return None
        gap, thick = self.strip // 4, self.strip // 2
        rest = self.strip - gap - thick
        ink = self.pixel("ink")
        if prog is None:
            blank = ink * self.strip
            return 0, blank, blank
        frac, colour = prog
        filled = ink * gap + self.pixel(colour) * thick + ink * rest
        empty = ink * gap + self.pixel("track") * thick + ink * rest
        return int(frac * self.w), filled, empty

    def paint(self, buf, j0, j1):
        green = b"\xe0\x07" if self.bpp == 16 else b"\x00\xff\x00\x00"
        for j in range(max(0, j0), min(self.h, j1 + 1)):
            buf[j * self.px:(j + 1) * self.px] = green

    def blank(self):
        """The picture is off: fill its panel with ink."""
        origin = self.origin
        if origin is None or not on_screen():
            return
        px0, py0 = origin
        ink = self.pixel("ink") * (self.h + self.strip)
        for i in range(self.w):
            off = (self.fbh - 1 - (px0 + i)) * self.stride + py0 * self.px
            self.fb[off:off + len(ink)] = ink

    def draw(self, y, boxes):
        origin = self.origin
        if origin is None or not on_screen():
            return
        px0, py0 = origin
        step, edge, cols = self.step, 2 * self.step, []
        under = self.under(progress())
        for i, cx in enumerate(range(0, W, step)):
            line = y[cx::STRIDE * step][:self.h]     # one camera column, top to bottom
            if CFG["mirror_y"]:
                line = line[::-1]
            buf = self.convert(line)
            for x0, x1, y0, y1 in boxes:
                if x0 - edge <= cx <= x1 + edge:
                    j0, j1 = y0 // step, y1 // step
                    if CFG["mirror_y"]:
                        j0, j1 = self.h - 1 - j1, self.h - 1 - j0
                    if abs(cx - x0) <= edge or abs(cx - x1) <= edge:
                        self.paint(buf, j0 - 2, j1 + 2)
                    else:
                        self.paint(buf, j0 - 2, j0)
                        self.paint(buf, j1, j1 + 2)
            if under:
                buf += under[1] if i < under[0] else under[2]
            col = px0 + (self.w - 1 - i if CFG["mirror_x"] else i)
            cols.append(((self.fbh - 1 - col) * self.stride + py0 * self.px, buf))
        if self.origin != origin:
            return                                   # the panel changed hands mid-frame
        fb = self.fb
        for off, buf in cols:
            fb[off:off + len(buf)] = buf


class Blind:
    origin = None

    def draw(self, y, boxes):
        pass

    def blank(self):
        pass


def on_screen():
    """Only draw while tty1 is showing; Alt+F2 must not get camera pixels across its login."""
    try:
        return open("/sys/class/tty/tty0/active").read().strip() == "tty1"
    except OSError:
        return False


# ---- the panels ----------------------------------------------------------------------------------------

def pad(text, width):
    text = text if len(text) <= width else text[:width - 1] + "…"
    return text + " " * (width - len(text))


def bar(have, total, width):
    full = min(width, have * width // total) if total else 0
    return "█" * full + "░" * (width - full)


def title(C, left, right="", bold=False, surface=ON_YELLOW):
    """A pane's title bar: what the pane is on the left, its live state on the right."""
    right = right + " " if right else ""
    return surface + (BOLD if bold else "") + pad(" " + left, C - len(right)) + right + OFF


def panel_bar(C):
    return [title(C, "qr.local", f"FC Public Media  {time.strftime('%H:%M')}", bold=True)]


def panel_inbox(C):
    """Line items: each item on a wedge pointing at its person, then the size. The one being picked up
    goes from muted to full yellow, and its person goes bold."""
    if not S.rows:
        return []
    tails = [r.get("size", "") if r.get("status") == "ready" else r.get("status", "") for r in S.rows]
    name_w = min(max(len(r["what"]) for r in S.rows) + 2, C // 2)
    size_w = max(len(t) for t in tails)
    for_w = C - name_w - 1 - size_w - 2
    lines = []
    for r, tail in zip(S.rows, tails):
        busy = r.get("status") != "ready"
        surface, edge, who = (ON_YELLOW, YELLOW_EDGE, BOLD) if busy else (ON_MUTED, MUTED_EDGE, "")
        lines.append(surface + pad(" " + r["what"], name_w) + OFF + edge + WEDGE + OFF
                     + " " + who + pad(r["for"], for_w) + OFF + tail.rjust(size_w) + " ")
    return lines


def panel_camera(C, top, cell_h):
    """The picture, or the pickup that has taken the panel over."""
    taken = next((r for r in S.rows if r.get("status") == "picking up"), None)
    lines = []
    rows = -(-VIDEO.h // cell_h) if VIDEO else 4
    if taken:
        if VIDEO:
            VIDEO.origin = None
        need = size_bytes(taken.get("size", ""))
        drive = S.drives[0] if S.drives else None
        if not drive:
            left, right = "plug in your drive", "picking up"
        elif need and drive["size"] < need:
            left, right = "drive too small", f"needs {taken['size']}"
        else:
            left, right = "drive ready", "demo · nothing to copy" if taken.get("demo") else "ready to copy"
        lines.append(title(C, left, right))
        lines += [BOLD + pad(f" {taken['what']}", C) + OFF, pad(f" for {taken['for']} · {taken.get('size', '')}", C)]
        for d in S.drives:
            lines.append(pad(f" {d['label']} · {d['fs']} · {gb(d['size'])}", C))
        lines += [""] * (rows + 1 - len(lines))
    else:
        left, right = catch_state()
        if not left:
            left, right = "scanner", "looking" if S.awake else "waiting"
        lines.append(title(C, left, right, surface=ON_MUTED if right == "waiting" else ON_YELLOW))
        if VIDEO:
            VIDEO.origin = ((VIDEO.screen[0] - VIDEO.w) // 2, (top + 1) * cell_h)
            VIDEO.strip = rows * cell_h - VIDEO.h        # the leftover under the picture holds the progress strip
        lines += [None] * rows                       # the picture's rows; text leaves them alone
    return lines


def catch_state():
    """The camera bar during a catch: what's happening on the left, the numbers on the right."""
    c = S.catch
    if not c:
        return "", ""
    snap, st = c["snap"], c["stats"]
    end = st.get("last", 0) if c["done"] else time.time()
    secs = int(end - st.get("start", end))
    clock = f"{secs // 60}:{secs % 60:02d}"
    if c["done"]:
        return "scanner", ("caught · " if c["done"] == "ok" else "refused · ") + f"{c['who']} · {clock}"
    have, total = caught(c)
    return "scanner", f"reading {have}/{total or '?'} · {st.get('seen', 0)} frames · {snap['damaged']} healed"


def progress():
    """(fraction, colour) for the strip under the picture, or None."""
    c = S.catch
    if not c:
        return None
    if c["done"]:
        return 1.0, "go" if c["done"] == "ok" else "bad"
    have, total = caught(c)
    return (min(1.0, have / total) if total else 0.0), "yellow"


def caught(c):
    """(have, need). A fountain solves in a cascade at the end, so pieces-solved sits near zero until it's
    nearly done; distinct droplets caught against the piece count is the number that climbs honestly."""
    have = need = 0
    for p in c["snap"]["present"]:
        need += p["total"] or 0
        have += p["have"] if p["mode"] != "fountain" else max(p["have"], min(p["total"] or 0, c["stats"].get("new", 0)))
    return have, need


def panel_latest(C, room):
    """Events stacked on a status bar on the very last row, newest nearest the bar; only as tall as it has events."""
    events = list(S.log)[-room:]
    lines = []
    for when, kind, text in events:
        lines.append(f" {when}  " + TONE.get(kind, "") + pad(text, C - 9) + OFF)
    trouble = S.trouble and time.time() - S.trouble[0] < 300
    if trouble:
        return lines + [title(C, "latest", f"{S.trouble[1]} {time.strftime('%H:%M', time.localtime(S.trouble[0]))}", surface=ON_BAD)]
    return lines + [title(C, "latest", S.platform)]


def render():
    size = os.get_terminal_size(sys.stdout.fileno()) if sys.stdout.isatty() else os.terminal_size((51, 45))
    C, R = size.columns, size.lines
    cell_h = VIDEO.screen[1] // R if VIDEO else 28
    with S.lock:
        latest = panel_latest(C, 3)
        cam_rows = 1 + (-(-VIDEO.h // cell_h) if VIDEO else 4)
        room = R - 1 - cam_rows - len(latest)       # the inbox flexes; everything below clings to the bottom
        inbox = panel_inbox(C)[:room]
        top = 1 + room
        out = panel_bar(C) + inbox + [""] * (room - len(inbox))
        out += panel_camera(C, top, cell_h) + latest
        S.dirty = False
    out = out[:R]
    sys.stdout.write("\x1b[H" + "\n".join("" if line is None else line + "\x1b[K" for line in out))
    sys.stdout.flush()


def housekeeping():
    now = time.time()
    with S.lock:
        c = S.catch
        if c and now - c["at"] > (20 if c["done"] else 30):
            if not c["done"]:
                got = ", ".join(f"{p['have']}/{p['total'] or '?'}" for p in c["snap"]["present"])
                S.log.append((time.strftime("%H:%M"), "warn", f"catch stopped {got} · {c['stats'].get('seen', 0)} frames"))
            S.catch = None
            S.dirty = True
        changed = False
        for row in S.rows:
            if row.get("status") == "picking up" and now - row.get("since", now) > 90:
                row["status"] = "ready" if row.get("demo") else "picked up"
                changed = True
        if changed:
            S.dirty = True
            save("inbox.json", S.rows)


# ---- main ----------------------------------------------------------------------------------------------

VIDEO = None


def main():
    global VIDEO, WEDGE
    tty_state = None
    if sys.stdin.isatty() and os.ttyname(0) == "/dev/tty1":
        tty_state = termios.tcgetattr(sys.stdin)
        quiet = termios.tcgetattr(sys.stdin)
        quiet[3] &= ~(termios.ECHO | termios.ICANON)
        termios.tcsetattr(sys.stdin, termios.TCSANOW, quiet)
        font = ST("qr-font.psf")
        if not os.path.exists(font):
            subprocess.run([sys.executable, P("font/make-font.py"), CFG["console_font"], font], stdout=subprocess.DEVNULL)
        if subprocess.run(["setfont", "-C", "/dev/tty1", font], stderr=subprocess.DEVNULL).returncode != 0:
            WEDGE = "▶"

    def stop(*_):
        sys.stdout.write("\x1b]R\x1b[?25h\x1b[0m\x1b[2J\x1b[H")
        sys.stdout.flush()
        if tty_state:
            termios.tcsetattr(sys.stdin, termios.TCSANOW, tty_state)
        os._exit(0)

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    sys.stdout.write(PALETTE + "\x1b[?25l\x1b[2J")
    try:
        VIDEO = Video()
    except OSError as e:
        S.event("warn", f"no picture · {e}")
    search = Search()                                # its own process; start it before the threads
    reader = Reader()
    threading.Thread(target=watch_drives, daemon=True).start()
    threading.Thread(target=watch_platform, daemon=True).start()
    threading.Thread(target=camera, args=(reader, VIDEO or Blind(), search), daemon=True).start()
    last_clock = ""
    while True:
        housekeeping()
        clock = time.strftime("%H:%M")
        if S.dirty or clock != last_clock:
            render()
            last_clock = clock
        time.sleep(0.2)


if __name__ == "__main__":
    main()
