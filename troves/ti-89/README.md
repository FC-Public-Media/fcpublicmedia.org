# The TI-89 trove

**If you have a TI-89, this is the gear that talks to it.** A graphing
calculator on a GraphLink cable: its screen, its files, and its operating
system, from a computer.

Status: started 2026-10-05 on the media node (kiosk-1). No calculator has been
connected yet. `link.py` has been run against an empty COM1, which opened and
got no answer, as expected.

    fcpm ti89 probe              is a calculator on COM1, and ready?
    fcpm ti89 screen [OUT.png]   its screen, as a PNG (160×100)
    fcpm ti89 probe --port COM3  another port

## How it reaches the calculator

**Over the gray GraphLink, on a real serial port, with nothing installed.** The
media node has one: COM1, on the motherboard (`ACPI\PNP0501`, up to 115200
baud). Any user can open it, and this box has no administrator, so this is
the route that works today. The gray cable is plain RS-232 at 9600 baud, 8N1.
It is powered from DTR and RTS, which `link.py` raises. The packets are TI's
link protocol, as the TiLP project documents it in libticalcs.

The box's second serial device, *PCI Serial Port* (`VEN_8086&DEV_1D3D`), is
the Intel management engine's serial-over-LAN. It has no driver and is not a
port for a cable.

| cable | how it connects | what it needs here |
|---|---|---|
| gray GraphLink | DB-9 serial, a real UART | nothing: COM1 |
| black GraphLink | serial, but the pins are toggled by software | TiLP's direct port access, which needs an administrator. Avoid it |
| Silver Link / USB | USB, `VID_0451&PID_E001` | a driver: TI Connect's, or libusb for TiLP. An administrator either way |
| TI-89 Titanium's own mini-USB | USB, `VID_0451&PID_E004` | the same |

So **the original TI-89 on a gray cable needs nothing installed**. A Titanium
can use the same gray cable through its I/O port.

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
  (`TI89Titanium_OS.89u`), and AMS 2.09 for the original TI-89. Both are still
  on education.ti.com.

**Where support stands.** TI discontinued the TI-89 Titanium at the start of
2025, and the original TI-89 long before that. The software is still
downloadable, but nothing new is coming. **The gap we make up** is `link.py`.
It needs no driver, no administrator, and no 2016 GTK runtime, and it grows
one verb at a time as we need one.

## Not yet

- **A calculator on the cable.** Find out which model and which cable we
  have. Then run `probe` and `screen` against it, and record what it answers
  in this README.
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
