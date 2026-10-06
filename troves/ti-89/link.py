"""link.py -- a TI-89 on a GraphLink cable, on this host's serial port.

    link.py probe  [--port COM1] [--cable auto|black|gray]    is a calculator there, and ready?
    link.py screen [--port COM1] [--cable ...] [OUT.png]      its screen, as a PNG

Two serial cables, and either works with no driver, no TI software and no
administrator: Windows already owns COM1, and any user may open it.

- The **gray** GraphLink is a plain RS-232 line at 9600 baud, 8N1, powered from
  DTR and RTS.
- The **black** GraphLink ("TI-GRAPH LINK for Windows") is only a level shifter.
  The calculator's two wires come out on the modem lines: DTR drives one and
  DSR reads it back, RTS drives the other and CTS reads it back. Bytes are
  clocked by hand, one handshake per bit, as libticables' serial cable does it.
  Slow, but every step is an ordinary serial-port call.

`auto` tells them apart by that echo: on a black link, each output line reads
back on its partner.

The packets are TI's link protocol as the TiLP project documents it
(libticalcs, "TI-89 protocol"): a machine ID, a command, a 16-bit
little-endian length, then that many bytes of data and a 16-bit sum of them.

Needs pyserial:
    uv run --no-project --python 3.12 --with pyserial link.py
`fcpm ti89` does that.
"""
import argparse
import struct
import sys
import time
import zlib

import serial

PC = 0x08        # computer -> TI-89 / TI-92 Plus / Voyage 200
CALC = 0x98      # TI-89 -> computer
RDY = 0x68
SCR = 0x6D
ACK = 0x56
DATA = 0x15

# The TI-89 sends the TI-92's 240x128 buffer, one bit a pixel, high bit first,
# 1 = dark. Its own display is the 160x100 at the top left.
BUF_W, BUF_H = 240, 128
LCD_W, LCD_H = 160, 100

NO_ANSWER = "no answer: is the calculator on, at its home screen, and its plug pushed all the way in?"


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
    """True if each output line reads back on its partner: a black link."""
    for dtr, rts in ((True, True), (False, True), (True, False), (True, True)):
        s.dtr, s.rts = dtr, rts
        time.sleep(0.05)
        if (s.dsr, s.cts) != (dtr, rts):
            return False
    return True


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


def recv(link, timeout=3.0):
    mid, cmd, n = struct.unpack("<BBH", link.read(4, timeout))
    # ACK, CTS and friends carry no data even when the length field is used
    # for a status word.
    if cmd in (DATA, 0x06, 0xC9, 0xA2):          # data, variable header, RTS, request
        body = link.read(n)
        chk = link.read(2)
        if struct.unpack("<H", chk)[0] != sum(body) & 0xFFFF:
            raise ValueError("checksum mismatch")
        return mid, cmd, body
    return mid, cmd, b""


def probe(link):
    send(link, RDY)
    mid, cmd, _ = recv(link)
    if cmd != ACK:
        raise ValueError("answered 0x%02X to a ready check, not ACK" % cmd)
    return mid


def screen(link):
    send(link, SCR)
    mid, cmd, _ = recv(link)
    if cmd != ACK:
        raise ValueError("answered 0x%02X to a screen request, not ACK" % cmd)
    mid, cmd, body = recv(link)
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


def main():
    ap = argparse.ArgumentParser(description="A TI-89 on a GraphLink cable.")
    ap.add_argument("verb", nargs="?", default="probe", choices=["probe", "screen"])
    ap.add_argument("out", nargs="?", default="ti89-screen.png")
    ap.add_argument("--port", default="COM1")
    ap.add_argument("--cable", default="auto", choices=["auto", "black", "gray"])
    a = ap.parse_args()
    try:
        link = open_link(a.port, a.cable)
        with link.s:
            if a.verb == "probe":
                mid = probe(link)
                print("%s (%s link): a calculator answered, machine ID 0x%02X%s"
                      % (a.port, link.name, mid, "" if mid == CALC else " (not a TI-89's 0x98)"))
            else:
                png(screen(link), a.out)
                print("%s (%s link): screen written to %s" % (a.port, link.name, a.out))
    except (serial.SerialException, TimeoutError, ValueError) as e:
        print("%s (%s link): %s" % (a.port, a.cable if a.cable != "auto" else "auto", e), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
