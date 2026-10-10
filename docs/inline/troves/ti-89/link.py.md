# `troves/ti-89/link.py`

Moved out of the file. Unreviewed.

## 1

Above `import argparse`

link.py -- a TI-89 on a GraphLink cable, on this host's serial port.

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

## 2

Above `BUF_W, BUF_H = 240, 128`

The TI-89 sends the TI-92's 240x128 buffer, one bit a pixel, high bit first,
1 = dark. Its own display is the 160x100 at the top left.

## 3

Above `name = "black"`

Line A is DTR out / DSR in, line B is RTS out / CTS in. True is
released (high), False is pulled low. Both idle released.

## 4

Above `s.dtr = s.rts = True`

True if pulling DTR pulls DSR: a black link. CTS is not checked, since
a calculator that is on answers there.

## 5

Above `if cmd in (DATA, 0x06, 0xC9, 0xA2):          # data, variable header, RTS, request`

ACK, CTS and friends carry no data even when the length field is used
for a status word.

## 6

Above `for i in range(tries):`

A ready check, retried: the first packet after the port opens can land
on a calculator already counting a stray bit, and it gives up after a
moment.

## 7

Above `mid, cmd, body = recv(link, check=False)`

This TI-89 (AMS 2.03) closes its screen with a checksum that is not the
sum of the screen (2026-10-06), though every pixel arrives intact. The
length is checked instead.

## 8

Above `stride = BUF_W // 8`

Crop to the TI-89's own display, then write a 1-bit greyscale PNG, where
0 is black: the calculator's 1 = dark, so every byte is inverted.

## 9

Above `RD_READY, RD_OK, RD_EXIT, RD_SIZE, RD_BLOCK, RD_DATA, RD_REPEAT = 0xAA55, 1, 2, 3, 5, 6, 7`

The dumper's own packets: a 16-bit command, a 16-bit length, data, and a
16-bit sum of everything before it. No machine ID.
