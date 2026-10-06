"""link.py -- a TI-89 on a GraphLink cable, on this host's serial port.

    link.py probe   [--port COM1] [--cable auto|black|gray]    is a calculator there, and ready?
    link.py version [--port COM1] [--cable ...]                its OS, boot code and hardware
    link.py screen  [--port COM1] [--cable ...] [OUT.png]      its screen, as a PNG
    link.py rom     [--port COM1] [--cable ...] [OUT.rom]      its whole ROM (about 11 minutes)

Two serial cables, and either works with no driver, no TI software and no
administrator: Windows already owns COM1, and any user may open it.

- The **gray** GraphLink is a plain RS-232 line at 9600 baud, 8N1, powered from
  DTR and RTS.
- The **black** GraphLink ("TI-GRAPH LINK for Windows") is only a level shifter.
  The calculator's two wires come out on the modem lines: DTR drives one and
  DSR reads it back, RTS drives the other and CTS reads it back. Bytes are
  clocked by hand, one handshake per bit, as libticables' serial cable does it.
  About 3 KB a second, measured.

`auto` tells them apart by that echo: on a black link, pulling DTR pulls DSR.
(A calculator that is switched on also answers on CTS, which is the first bit
of a byte to it. That is why every verb starts with a ready check, retried.)

The packets are TI's link protocol as the TiLP project documents it
(libticalcs, "TI-89 protocol"): a machine ID, a command, a 16-bit
little-endian length, then that many bytes of data and a 16-bit sum of them.

`rom` sends TiLP's ROM dumper to the calculator, starts it by remote keys, and
reads 4 KB blocks from it. The dumper is TiLP's (GPL-2.0), built into
libticalcs as rom89.h. It is fetched from there on first use and kept in the
prefix, and is not carried in this repo.

Needs pyserial:
    uv run --no-project --python 3.12 --with pyserial link.py
`fcpm ti89` does that.
"""
import argparse
import os
import re
import struct
import sys
import time
import urllib.request
import zlib

import serial

PC = 0x08        # computer -> TI-89 / TI-92 Plus / Voyage 200
CALC = 0x98      # TI-89 -> computer
CALC_ALT = 0x89  # TI-89 -> "CBL": what this TI-89 signs its answers to RDY and SCR with
RDY = 0x68
SCR = 0x6D
ACK = 0x56
DATA = 0x15
CTS = 0x09
VER = 0x2D
KEY = 0x87
RTS = 0xC9
EOT = 0x92

# The TI-89 sends the TI-92's 240x128 buffer, one bit a pixel, high bit first,
# 1 = dark. Its own display is the 160x100 at the top left.
BUF_W, BUF_H = 240, 128
LCD_W, LCD_H = 160, 100

NO_ANSWER = "no answer: is the calculator on, at its home screen, and its plug pushed all the way in?"

PREFIX = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~/.local/share")),
                      "media-node", "troves", "ti-89")
ROM89_H = ("https://raw.githubusercontent.com/debrouxl/tilibs/"
           "6dba390e7390c4b98ae96287b39a3971c331fbef/libticalcs/trunk/src/rom89.h")


class Gray:
    name = "gray"

    def __init__(self, s):
        self.s = s
        s.dtr = s.rts = True       # its power
        s.reset_input_buffer()

    def write(self, data):
        self.s.write(data)

    def read(self, n, timeout=3.0):
        self.s.timeout = timeout
        got = self.s.read(n)
        if len(got) < n:
            raise TimeoutError(NO_ANSWER if not got else "cut short (%d of %d bytes)" % (len(got), n))
        return got


class Black:
    """Line A is DTR out / DSR in, line B is RTS out / CTS in. True is
    released (high), False is pulled low. Both idle released."""
    name = "black"

    def __init__(self, s):
        self.s = s
        s.dtr = s.rts = True

    def _wait(self, line, level, deadline):
        read = (lambda: self.s.dsr) if line == "a" else (lambda: self.s.cts)
        while read() != level:
            if time.monotonic() > deadline:
                self.s.dtr = self.s.rts = True
                raise TimeoutError(NO_ANSWER)

    def write(self, data):
        for byte in data:
            for _ in range(8):
                deadline = time.monotonic() + 1.0
                if byte & 1:          # a 1: pull A, the calculator answers on B
                    self.s.dtr = False
                    self._wait("b", False, deadline)
                    self.s.dtr = True
                    self._wait("b", True, deadline)
                else:                 # a 0: pull B, the calculator answers on A
                    self.s.rts = False
                    self._wait("a", False, deadline)
                    self.s.rts = True
                    self._wait("a", True, deadline)
                byte >>= 1

    def read(self, n, timeout=3.0):
        out = bytearray()
        for i in range(n):
            byte = 0
            for _ in range(8):
                deadline = time.monotonic() + (timeout if not out and not byte else 1.0)
                while True:
                    a, b = self.s.dsr, self.s.cts
                    if not (a and b):
                        break
                    if time.monotonic() > deadline:
                        raise TimeoutError(NO_ANSWER if not out else "cut short (%d of %d bytes)" % (len(out), n))
                if not a:             # a 1: answer on B, wait for A's release
                    bit = 1
                    self.s.rts = False
                    self._wait("a", True, deadline + 1.0)
                    self.s.rts = True
                else:                 # a 0: answer on A, wait for B's release
                    bit = 0
                    self.s.dtr = False
                    self._wait("b", True, deadline + 1.0)
                    self.s.dtr = True
                byte = (byte >> 1) | (bit << 7)
            out.append(byte)
            timeout = 1.0
        return bytes(out)


def echoes(s):
    """True if pulling DTR pulls DSR: a black link. CTS is not checked, since
    a calculator that is on answers there."""
    s.dtr = s.rts = True
    time.sleep(0.05)
    s.dtr = False
    time.sleep(0.05)
    black = not s.dsr
    s.dtr = True
    time.sleep(0.05)
    return black


def open_link(port, cable):
    s = serial.Serial(port, 9600, bytesize=8, parity="N", stopbits=1, timeout=3)
    if cable == "auto":
        cable = "black" if echoes(s) else "gray"
    return (Black if cable == "black" else Gray)(s)


def send(link, cmd, data=b""):
    pkt = struct.pack("<BBH", PC, cmd, len(data))
    if data:
        pkt += data + struct.pack("<H", sum(data) & 0xFFFF)
    link.write(pkt)


def recv(link, timeout=3.0, check=True):
    mid, cmd, n = struct.unpack("<BBH", link.read(4, timeout))
    # ACK, CTS and friends carry no data even when the length field is used
    # for a status word.
    if cmd in (DATA, 0x06, 0xC9, 0xA2):          # data, variable header, RTS, request
        body = link.read(n)
        chk = link.read(2)
        if check and struct.unpack("<H", chk)[0] != sum(body) & 0xFFFF:
            raise ValueError("checksum mismatch")
        return mid, cmd, body
    return mid, cmd, b""


def expect(link, want, timeout=5.0):
    mid, cmd, body = recv(link, timeout)
    if cmd != want:
        raise ValueError("answered 0x%02X where 0x%02X was expected" % (cmd, want))
    return body


def probe(link, tries=4):
    """A ready check, retried: the first packet after the port opens can land
    on a calculator already counting a stray bit, and it gives up after a
    moment."""
    for i in range(tries):
        try:
            send(link, RDY)
            mid, cmd, _ = recv(link)
            if cmd != ACK:
                raise ValueError("answered 0x%02X to a ready check, not ACK" % cmd)
            return mid
        except (TimeoutError, ValueError):
            if i == tries - 1:
                raise
            time.sleep(2.5)


def version(link):
    send(link, VER)
    expect(link, ACK)
    send(link, CTS)
    expect(link, ACK)
    body = expect(link, DATA)
    send(link, ACK)
    return body


def describe(v):
    hw = {1: "TI-92 Plus", 3: "TI-89", 8: "Voyage 200", 9: "TI-89 Titanium"}
    return "AMS %x.%02x, boot code %x.%02x, hardware %d, %s%s" % (
        v[0], v[1], v[2], v[3], v[5], hw.get(v[-1], "hardware ID %d" % v[-1]),
        ", batteries low" if v[4] else "")


def screen(link):
    send(link, SCR)
    mid, cmd, _ = recv(link)
    if cmd != ACK:
        raise ValueError("answered 0x%02X to a screen request, not ACK" % cmd)
    # This TI-89 (AMS 2.03) closes its screen with a checksum that is not the
    # sum of the screen (2026-10-06), though every pixel arrives intact. The
    # length is checked instead.
    mid, cmd, body = recv(link, check=False)
    if cmd != DATA:
        raise ValueError("sent 0x%02X where the screen was expected" % cmd)
    send(link, ACK)
    if len(body) != BUF_W * BUF_H // 8:
        raise ValueError("screen was %d bytes, expected %d" % (len(body), BUF_W * BUF_H // 8))
    return body


def png(bits, out):
    # Crop to the TI-89's own display, then write a 1-bit greyscale PNG, where
    # 0 is black: the calculator's 1 = dark, so every byte is inverted.
    stride = BUF_W // 8
    rows = b"".join(b"\x00" + bytes(255 - b for b in bits[y * stride:y * stride + LCD_W // 8])
                    for y in range(LCD_H))

    def chunk(kind, data):
        return (struct.pack(">I", len(data)) + kind + data
                + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF))

    with open(out, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(chunk(b"IHDR", struct.pack(">IIBBBBB", LCD_W, LCD_H, 1, 0, 0, 0, 0)))
        f.write(chunk(b"IDAT", zlib.compress(rows)))
        f.write(chunk(b"IEND", b""))


# --- the ROM dump -----------------------------------------------------------

HOME, CLEAR, ENTER, LP, RP = 277, 263, 13, 40, 41
# The dumper's own packets: a 16-bit command, a 16-bit length, data, and a
# 16-bit sum of everything before it. No machine ID.
RD_READY, RD_OK, RD_EXIT, RD_SIZE, RD_BLOCK, RD_DATA, RD_REPEAT = 0xAA55, 1, 2, 3, 5, 6, 7


def dumper():
    """TiLP's romdump.89z, from the prefix, or fetched from libticalcs once."""
    path = os.path.join(PREFIX, "romdump.89z")
    if not os.path.exists(path):
        src = urllib.request.urlopen(ROM89_H, timeout=30).read().decode()
        arr = src[src.index("romDump89[]"):]
        arr = arr[arr.index("{") + 1:arr.index("}")]
        f = bytes(int(x, 16) for x in re.findall(r"0x([0-9a-fA-F]{2})", arr))
        os.makedirs(PREFIX, exist_ok=True)
        with open(path, "wb") as out:
            out.write(f)
    f = open(path, "rb").read()
    off = struct.unpack("<I", f[0x3C:0x40])[0]
    var = f[off + 4:-2]
    if f[:8] != b"**TI89**" or sum(var) & 0xFFFF != struct.unpack("<H", f[-2:])[0]:
        raise ValueError("%s is not an intact .89z" % path)
    return f[0x48], var


def key(link, code):
    link.write(struct.pack("<BBH", PC, KEY, code))
    expect(link, ACK)
    time.sleep(0.05)


def send_asm(link, name, vartype, var):
    send(link, RTS, struct.pack("<IBB", len(var), vartype, len(name)) + name + b"\0")
    expect(link, ACK)
    expect(link, CTS)
    send(link, ACK)
    send(link, DATA, b"\0\0\0\0" + var)
    expect(link, ACK)
    send(link, EOT)
    expect(link, ACK)


def rd_send(link, cmd, data=b""):
    head = struct.pack("<HH", cmd, len(data))
    link.write(head + data + struct.pack("<H", sum(head + data) & 0xFFFF))


def rd_recv(link, timeout=5.0):
    head = link.read(4, timeout)
    cmd, n = struct.unpack("<HH", head)
    if cmd > RD_REPEAT and cmd != RD_READY:
        raise ValueError("the dumper sent 0x%04X" % cmd)
    body = link.read(n) if n else b""
    if struct.unpack("<H", link.read(2))[0] != sum(head + body) & 0xFFFF:
        raise ValueError("checksum mismatch in a block")
    return cmd, body


def rd_ready(link, tries=5):
    for i in range(tries):
        try:
            rd_send(link, RD_READY)
            if rd_recv(link)[0] == RD_OK:
                return
        except (TimeoutError, ValueError):
            time.sleep(0.5)
    raise TimeoutError("the dumper on the calculator is not answering")


def rom(link, out, say=print):
    vartype, var = dumper()
    for k in (HOME, CLEAR, CLEAR):
        key(link, k)
    time.sleep(0.2)
    say("sending the dumper (main\\romdump, %d bytes)" % len(var))
    send_asm(link, b"main\\romdump", vartype, var)
    time.sleep(1.0)
    for k in [ord(c) for c in "main\\romdump"] + [LP, RP, ENTER]:
        key(link, k)
    time.sleep(1.0)
    rd_ready(link)
    rd_send(link, RD_SIZE)
    size = struct.unpack("<I", rd_recv(link)[1])[0]
    say("ROM is %d KB" % (size >> 10))
    t0 = time.monotonic()
    with open(out, "wb") as f:
        addr = 0
        while addr < size:
            if 0x10000 <= addr < 0x12000:
                # The certificate: read-protected, and TiLP fills it with FF too.
                f.write(b"\xff" * 4096)
                addr += 4096
                continue
            for attempt in range(6):
                try:
                    rd_send(link, RD_BLOCK, struct.pack("<I", addr))
                    cmd, body = rd_recv(link)
                    break
                except (TimeoutError, ValueError):
                    if attempt == 5:
                        raise
                    time.sleep(0.5)
                    rd_ready(link)
            if cmd == RD_REPEAT:          # a block of one byte repeated
                n, b = struct.unpack("<HH", body)
                body = bytes([b & 0xFF]) * n
            elif cmd != RD_DATA:
                raise ValueError("the dumper sent 0x%04X at 0x%06X" % (cmd, addr))
            f.write(body)
            addr += len(body)
            if addr % 0x40000 == 0:
                say("%4d of %d KB, %d s" % (addr >> 10, size >> 10, time.monotonic() - t0))
    time.sleep(0.2)
    rd_send(link, RD_EXIT)
    try:
        rd_recv(link)
    except (TimeoutError, ValueError):
        pass
    return size


def main():
    ap = argparse.ArgumentParser(description="A TI-89 on a GraphLink cable.")
    ap.add_argument("verb", nargs="?", default="probe", choices=["probe", "version", "screen", "rom"])
    ap.add_argument("out", nargs="?")
    ap.add_argument("--port", default="COM1")
    ap.add_argument("--cable", default="auto", choices=["auto", "black", "gray"])
    a = ap.parse_args()
    try:
        link = open_link(a.port, a.cable)
        with link.s:
            time.sleep(0.5)
            mid = probe(link)
            where = "%s (%s link)" % (a.port, link.name)
            if a.verb == "probe":
                print("%s: a calculator answered, machine ID 0x%02X%s"
                      % (where, mid, "" if mid in (CALC, CALC_ALT) else " (not a TI-89's)"))
            elif a.verb == "version":
                print("%s: %s" % (where, describe(version(link))))
            elif a.verb == "screen":
                out = a.out or "ti89-screen.png"
                png(screen(link), out)
                print("%s: screen written to %s" % (where, out))
            else:
                out = a.out or "ti89.rom"
                size = rom(link, out, say=lambda m: print("%s: %s" % (where, m), flush=True))
                print("%s: %d bytes written to %s" % (where, size, out))
    except (serial.SerialException, TimeoutError, ValueError, OSError) as e:
        print("%s (%s link): %s" % (a.port, a.cable, e), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
