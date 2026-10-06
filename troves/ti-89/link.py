"""link.py -- a TI-89 on a gray GraphLink, on this host's serial port.

    link.py probe [--port COM1]            is a calculator there, and ready?
    link.py screen [--port COM1] [OUT.png] its screen, as a PNG

The gray GraphLink is a plain RS-232 line at 9600 baud, 8N1. It draws its power
from DTR and RTS, so both are raised. No driver, no TI software and no
administrator: Windows already owns COM1, and any user may open it.

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


def open_port(name):
    s = serial.Serial(name, 9600, bytesize=8, parity="N", stopbits=1, timeout=3)
    s.dtr = True
    s.rts = True
    s.reset_input_buffer()
    return s


def send(s, cmd, data=b""):
    pkt = struct.pack("<BBH", PC, cmd, len(data))
    if data:
        pkt += data + struct.pack("<H", sum(data) & 0xFFFF)
    s.write(pkt)


def recv(s):
    head = s.read(4)
    if len(head) < 4:
        raise TimeoutError("no answer: is the cable seated and the calculator on its home screen?")
    mid, cmd, n = struct.unpack("<BBH", head)
    # ACK, CTS and friends carry no data even when the length field is used
    # for a status word.
    if cmd in (DATA, 0x06, 0xC9, 0xA2):          # data, variable header, RTS, request
        body = s.read(n)
        chk = s.read(2)
        if len(body) < n or len(chk) < 2:
            raise TimeoutError("packet cut short (%d of %d bytes)" % (len(body), n))
        if struct.unpack("<H", chk)[0] != sum(body) & 0xFFFF:
            raise ValueError("checksum mismatch")
        return mid, cmd, body
    return mid, cmd, b""


def probe(s):
    send(s, RDY)
    mid, cmd, _ = recv(s)
    if cmd != ACK:
        raise ValueError("answered 0x%02X to a ready check, not ACK" % cmd)
    return mid


def screen(s):
    send(s, SCR)
    mid, cmd, _ = recv(s)
    if cmd != ACK:
        raise ValueError("answered 0x%02X to a screen request, not ACK" % cmd)
    mid, cmd, body = recv(s)
    if cmd != DATA:
        raise ValueError("sent 0x%02X where the screen was expected" % cmd)
    send(s, ACK)
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
    ap = argparse.ArgumentParser(description="A TI-89 on a gray GraphLink.")
    ap.add_argument("verb", nargs="?", default="probe", choices=["probe", "screen"])
    ap.add_argument("out", nargs="?", default="ti89-screen.png")
    ap.add_argument("--port", default="COM1")
    a = ap.parse_args()
    try:
        with open_port(a.port) as s:
            if a.verb == "probe":
                mid = probe(s)
                print("%s: a calculator answered, machine ID 0x%02X%s"
                      % (a.port, mid, "" if mid == CALC else " (not a TI-89's 0x98)"))
            else:
                png(screen(s), a.out)
                print("%s: screen written to %s" % (a.port, a.out))
    except (serial.SerialException, TimeoutError, ValueError) as e:
        print("%s: %s" % (a.port, e), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
