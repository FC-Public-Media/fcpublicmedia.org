"""One ATEM switcher over its network port (UDP 9910): stay joined, keep its state, send it commands."""
import random
import socket
import struct
import threading
import time

MODES = {0: "525i59.94", 1: "625i50", 2: "525i59.94 16:9", 3: "625i50 16:9", 4: "720p50", 5: "720p59.94",
         6: "1080i50", 7: "1080i59.94", 8: "1080p23.98", 9: "1080p24", 10: "1080p25", 11: "1080p29.97",
         12: "1080p50", 13: "1080p59.94", 14: "2160p23.98", 15: "2160p24", 16: "2160p25", 17: "2160p29.97",
         18: "2160p50", 19: "2160p59.94", 26: "1080p30", 27: "1080p60"}
PORTS = {1: "SDI", 2: "HDMI", 4: "component", 8: "composite", 16: "S-video", 0x100: "internal"}

HELLO, RELIABLE, ACK = 0x02, 0x01, 0x10


def _text(b):
    return b.split(b"\0")[0].decode("utf8", "replace")


class Switcher:
    def __init__(self, host, port=9910):
        self.addr = (host, port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(0.25)
        self.lock = threading.Lock()
        self.session = None
        self.out = 0
        self.heard = 0.0
        self.changed = 0.0
        self.ready = False
        self.state = self._empty()
        threading.Thread(target=self._run, daemon=True).start()

    @staticmethod
    def _empty():
        return {"product": None, "mode": None, "pgm": {}, "pvw": {}, "aux": {}, "mv": {}, "inputs": {},
                "mv_mode": {}, "down_mode": {}, "ftb": {}, "dsk": {}, "usk": {}, "warnings": []}

    def _hello(self):
        self.session = None
        self.ready = False
        sid = random.randint(0x1000, 0x7FFF)
        self.sock.sendto(bytes([0x10, 0x14]) + struct.pack(">H", sid) + bytes([0, 0, 0, 0, 0, 0x3A, 0, 0, 1]) + bytes(7), self.addr)
        self.heard = time.time()

    def _run(self):
        self._hello()
        while True:
            if time.time() - self.heard > 3:
                with self.lock:
                    self.state = self._empty()
                self._hello()
            try:
                pkt, _ = self.sock.recvfrom(4096)
            except (socket.timeout, OSError):
                continue
            self.heard = time.time()
            flags = pkt[0] >> 3
            length = ((pkt[0] & 7) << 8) | pkt[1]
            if flags & HELLO:
                self.sock.sendto(bytes([0x80, 0x0C]) + pkt[2:4] + bytes(8), self.addr)
                continue
            self.session = pkt[2:4]
            if flags & RELIABLE:
                self.sock.sendto(bytes([0x80, 0x0C]) + pkt[2:4] + pkt[10:12] + bytes(6), self.addr)
            body = pkt[12:length]
            i = 0
            with self.lock:
                while i + 8 <= len(body):
                    n = struct.unpack(">H", body[i:i + 2])[0]
                    if n < 8:
                        break
                    self._take(body[i + 4:i + 8].decode("latin1"), body[i + 8:i + n])
                    i += n

    def _take(self, name, d):
        s = self.state
        u16 = lambda o: struct.unpack(">H", d[o:o + 2])[0]
        if name == "_pin":
            s["product"] = _text(d)
        elif name == "VidM":
            s["mode"] = MODES.get(d[0], str(d[0]))
        elif name == "MvVM":
            s["mv_mode"][MODES.get(d[0], str(d[0]))] = MODES.get(d[1], str(d[1]))
        elif name == "DHVm":
            s["down_mode"][MODES.get(d[0], str(d[0]))] = MODES.get(d[1], str(d[1]))
        elif name == "InPr":
            s["inputs"][u16(0)] = {"id": u16(0), "name": _text(d[2:22]), "short": _text(d[22:26]),
                                   "ports": [v for k, v in PORTS.items() if u16(28) & k],
                                   "port": PORTS.get(u16(30), str(u16(30))),
                                   "aux": bool(d[34] & 1), "mv": bool(d[34] & 2), "me": bool(d[35] & 1)}
        elif name == "PrgI":
            s["pgm"][d[0]] = u16(2)
        elif name == "PrvI":
            s["pvw"][d[0]] = u16(2)
        elif name == "AuxS":
            s["aux"][d[0]] = u16(2)
        elif name == "MvIn":
            s["mv"].setdefault(d[0], {})[d[1]] = u16(2)
        elif name == "FtbS":
            s["ftb"][d[0]] = {"black": bool(d[1]), "moving": bool(d[2])}
        elif name == "DskS":
            s["dsk"][d[0]] = bool(d[1])
        elif name == "KeOn":
            s["usk"].setdefault(d[0], {})[d[1]] = bool(d[2])
        elif name == "Warn":
            s["warnings"] = (s["warnings"] + [_text(d)])[-5:]
        elif name == "InCm":
            self.ready = True
        self.changed = time.time()

    def send(self, name, data):
        if self.session is None:
            raise RuntimeError("not joined to the switcher")
        with self.lock:
            self.out = (self.out + 1) & 0x7FFF
            cmd = struct.pack(">HH", 8 + len(data), 0) + name.encode() + data
            total = 12 + len(cmd)
            pkt = bytes([0x08 | (total >> 8), total & 0xFF]) + self.session + bytes(6) + struct.pack(">H", self.out) + cmd
        self.sock.sendto(pkt, self.addr)

    def snapshot(self):
        with self.lock:
            s = dict(self.state)
            s["inputs"] = sorted(self.state["inputs"].values(), key=lambda x: x["id"])
            s["ready"] = self.ready
            s["heard"] = round(time.time() - self.heard, 1)
            return s

    # The verbs, one per thing a person presses.
    def program(self, src, me=0): self.send("CPgI", struct.pack(">BxH", me, src))
    def preview(self, src, me=0): self.send("CPvI", struct.pack(">BxH", me, src))
    def cut(self, me=0): self.send("DCut", struct.pack(">Bxxx", me))
    def auto(self, me=0): self.send("DAut", struct.pack(">Bxxx", me))
    def fade_to_black(self, me=0): self.send("FtbA", struct.pack(">BBxx", me, 2))
    def aux(self, out, src): self.send("CAuS", struct.pack(">BBH", 1, out, src))
    def multiview(self, window, src, mv=0): self.send("CMvI", struct.pack(">BBH", mv, window, src))

    def mode(self, name):
        code = {v: k for k, v in MODES.items()}[name]
        self.send("CVdM", struct.pack(">Bxxx", code))

    # Blackmagic's SDI camera control, carried by the switcher down its SDI outputs to each camera's SDI in.
    def camera(self, dest, category, parameter, dtype, values, relative=False):
        counts = [0] * 11
        counts[{0: 2, 1: 2, 2: 2, 3: 4, 4: 2, 5: 2, 128: 4}[dtype]] = len(values)
        body = struct.pack(">%d%s" % (len(values), {0: "?", 1: "b", 2: "h", 3: "i", 4: "q", 128: "h"}[dtype]), *values)
        body += bytes(-len(body) % 8 or (8 if not body else 0))
        self.send("CCmd", struct.pack(">5B", dest, category, parameter, int(relative), dtype) + bytes(counts) + body)

    def camera_format(self, name, dest=255):
        """Tell cameras (255 = every camera) to output the format named like the switcher's modes."""
        size, rest = name.split("p") if "p" in name else name.split("i")
        rate = rest.split()[0]
        fps, mrate = {"23.98": (24, 1), "24": (24, 0), "25": (25, 0), "29.97": (30, 1), "30": (30, 0),
                      "50": (50, 0), "59.94": (60, 1), "60": (60, 0)}[rate]
        interlaced = "i" in name and "p" not in name
        if interlaced:
            fps //= 2
        dims = {"720": 2, "1080": 3, "2160": 6}[size]
        self.camera(dest, 1, 0, 1, [fps, mrate, dims, int(interlaced), 0])

    def everything(self, name):
        """The switcher and every camera to one format, in one press."""
        self.camera_format(name)
        self.mode(name)
