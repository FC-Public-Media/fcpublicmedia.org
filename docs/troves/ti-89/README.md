# The TI-89 trove

**If you have a TI-89, this is the gear that talks to it.** A graphing
calculator on a GraphLink cable: its screen, its files, and its operating
system, from a computer.

Status: started 2026-10-05 on the media node (kiosk-1). The calculator is
Autumn's original TI-89 (not a Titanium). Its cable is on COM1 and reads as a
**black** link. **It answered on 2026-10-06**: AMS 2.03 (dated 12/08/1999),
boot code 1.07, hardware revision 1. Its ROM has been dumped.

    fcpm ti89 probe              is a calculator on COM1, and ready?
    fcpm ti89 version            its OS, boot code and hardware
    fcpm ti89 screen [OUT.png]   its screen, as a PNG (160×100)
    fcpm ti89 rom [OUT.rom]      its whole ROM, 2 MB, in about 10 minutes
    fcpm ti89 probe --port COM3  another port; --cable black|gray to skip the guess

**The ROM never goes in this repo.** It is TI's code, and this repo is public.
It lives in the prefix, `%LOCALAPPDATA%\media-node\troves\ti-89\`, beside the
dumper that made it.

## What the calculator answered (2026-10-06)

- **Speed**: about 3.3 KB a second over the black link, clocked through the
  serial API. A screen takes about a second, and the ROM takes 612 s.
- **The ROM**: 2,097,152 bytes. Its reset vectors point into itself (stack
  `0x4800`, start `0x200132`, with the ROM at `0x200000`), and its test menu
  reads "2.03, 12/08/1999". 172 of its 512 blocks are blank flash. The
  certificate block (`0x10000` to `0x12000`) is read-protected, and is filled
  with FF the way TiLP does it.
- **How the dump runs**: `rom` sends TiLP's dumper (`main\romdump`, 1,329
  bytes, fetched once from libticalcs' `rom89.h`), types
  `main\romdump()` ENTER by remote keys, and asks it for 4 KB blocks. The
  program stays on the calculator afterwards; delete it there if it's in the
  way.
- **Surprises**:
  - With the calculator on, auto-detect used to call the cable gray, because
    the calculator answers on CTS when DTR is pulled. Now only DSR is checked.
  - That test, and opening the port, can each feed the calculator a stray
    bit, so the first packet after opening is lost. Every verb starts with a
    ready check, retried.
  - This calculator signs some answers `0x89` (libticalcs' "TI-89 to CBL")
    instead of `0x98`. The two are treated alike.
  - Its screen packet ends in a checksum that is not the screen's sum, though
    every pixel is right. The screen's length is checked instead.

## How it reaches the calculator

**Over a serial GraphLink, on a real serial port, with nothing installed.** The
media node has one: COM1, on the motherboard (`ACPI\PNP0501`, up to 115200
baud). Any user can open it, and this box has no administrator, so this is
the route that works today. The packets are TI's link protocol, as the TiLP
project documents it in libticalcs.

**The cable on COM1** is labelled *Texas Instruments TI-GRAPH LINK™ for
Windows™*, in a charcoal housing. It is a black link. The test was made
2026-10-05: each output line reads back on its partner (DTR on DSR, RTS on
CTS), which is how a black link passes the calculator's two wires through. A
gray link would not do that. `link.py` clocks bytes over those lines one
handshake per bit, as libticables' serial cable does. Every step is an
ordinary serial-port call, so it needs no administrator, though it is slow.

The box's second serial device, *PCI Serial Port* (`VEN_8086&DEV_1D3D`), is
the Intel management engine's serial-over-LAN. It has no driver and is not a
port for a cable.

| cable | how it connects | what it needs here |
|---|---|---|
| gray GraphLink | DB-9 serial, a real UART | nothing: COM1 |
| black GraphLink | serial, but the pins are toggled by software | nothing: `link.py` toggles them through the serial API. **This is ours** |
| Silver Link / USB | USB, `VID_0451&PID_E001` | a driver: TI Connect's, or libusb for TiLP. An administrator either way |
| TI-89 Titanium's own mini-USB | USB, `VID_0451&PID_E004` | the same |

So **a TI-89 on either serial cable needs nothing installed**. A Titanium can
use the same cables through its I/O port.

## The gear, found online (2026-10-05)

Details and sources are in `gear.yml`.

- **TI Connect 4.0** (`TI-Connect-4.0.0.218.exe`). TI's link software, still
  offered, and still the one TI names for TI-89 OS updates. Its installer
  brings USB drivers, so it needs an administrator: a request to IT. Note
  that **TI Connect CE is a different program and does not support the TI-89.**
- **TiLP II 1.18** (2016) on ticalc.org. Open source, and it handles every cable.
  This is the program we would bring through the bay into
  `%LOCALAPPDATA%\media-node\troves\ti-89\`. It is old: on Windows it needs a
  GTK+ 2 runtime placed beside it by hand. Debian still builds it from git
  (2023), so the code is alive even though the Windows build is not.
- **The calculator's OS**: OS 3.10 for the TI-89 Titanium
  (`TI89Titanium_OS.89u`) is a direct download. **AMS 2.09 for the original
  TI-89** (2003-05-06) is listed on education.ti.com, but it is now behind
  TI's *protected download request form*, which emails the link to whoever
  asks.

**Where support stands.** TI discontinued the TI-89 Titanium at the start of
2025, and the original TI-89 long before that. The software is still
downloadable, but nothing new is coming. **The gap we make up** is `link.py`.
It needs no driver, no administrator, and no 2016 GTK runtime, and it grows
one verb at a time as we need one.

## Not yet

What the cable can carry, and the scenarios it opens (calculator VMs, a pad
for multiplayer, piloting the kiosk, an IDE), are in
[`docs/troves/ti-89/SCENARIOS.md`](SCENARIOS.md).

- **Files**: list folders, back up variables, and send a program. These are the
  next verbs for `link.py`, in the same protocol.
- **OS installs.** Send them from TiLP or TI Connect, not from `link.py`. A
  failed OS send has to be recovered on the calculator, so use a tool that has
  been doing it for twenty years.
- **TiLP through the bay**: unpack it into the prefix, and find out whether it
  runs without an administrator.
- **TI Connect 4.0**: ask IT, if a Silver Link or the Titanium's USB is ever
  wanted.
- **An instrument for it**, if the calculator becomes something the crew
  plays, such as a screen mirrored to a panel.
