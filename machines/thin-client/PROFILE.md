# thin-client

**Status: profiled 2026-10-09 from its BIOS, not yet reformatted.** A donated
HP t510 thin client in the control rack, under the headphone amp and above the
switcher. It boots HP ThinPro (Linux underneath) straight into one remote
desktop connection its last owner left, and does nothing else. It is to be
wiped and given a job here.

The folder name is a placeholder until Autumn names it (`names`).

| | |
|---|---|
| model | **HP t510**, serial MXL2411TY7 (read from the BIOS) |
| BIOS | AMI v02.67, system ROM 786R11 v1.03. **No administrator password**; setup opened without one |
| CPU | VIA Eden X2 U4200, two 64-bit cores at 1.0 GHz. SSSE3 and SSE4.1, plus VIA's PadLock unit: a hardware random number generator, AES and SHA |
| graphics | VIA Chrome9 HD on the VX900 chipset: DVI-I and DVI-D, 128 MB taken from memory |
| memory | 2 GB DDR3 in one SO-DIMM socket (the BIOS shows 1920 MB once video takes its share). 4 GB modules are reported to work |
| storage | a 1 GB flash module on the 44-pin IDE header (`PM-1GB ATA Flash`), replaceable. Two USB sockets inside the case, under the top cover |
| network | gigabit Ethernet, Broadcom BCM57780, hardware address `9C:8E:99:E9:58:3B`. It can boot over the network (Broadcom MBA v12.2). Not on the studio LAN on 2026-10-09 |
| other ports | serial, parallel, two PS/2, USB 2.0 front and back, mic and headphone |
| power | 19 V on a barrel plug. About 8 W idle and 19 W running |

The model, serial, BIOS, memory, flash and hardware address are from the box.
The rest is from [parkytowers' t510 page](https://www.parkytowers.me.uk/thin/hp/t510/).

## As found in the BIOS

- Boot order: a USB SD/MMC card reader first, then the 1 GB flash, then the
  network. F12 at power-on gives a boot menu.
- **Power on after a power failure: Off.** For a machine that has to come back
  on its own, this needs to be On.
- The clock keeps UTC, which is what Debian expects.

## Two screens

The hardware drives both DVI ports at once. Showing only one screen is how
ThinPro is set up, not a limit of the box. Linux support for VIA's graphics is
thin, though, so a text console is safe and a browser on each screen may not
be.

## What it could be

**Autumn is leaning toward the origin** (2026-10-09): the front man. If only
one of our machines had connectivity, this is the one we would want it to be.
It isn't a strong machine, and that's part of the point: it isn't a juicy
target, just one doing a job. It shouldn't be remote and unknowable either.

What that suggests:

- **One job.** Minimal Debian with no desktop, and two ways in: SSH for
  keyholders' fast-forwards (`../digitization/KEYHOLDERS`), and a read-only
  page.
- **A face.** One of its screens shows its own ledger: what it holds, when it
  last heard from GitHub, the last fast-forwards and whose key made each, and
  anything waiting. The same page is readable on the LAN with no login.
- **Nothing worth stealing.** It reads from GitHub and never holds write access
  there. After an outage, a session elsewhere publishes with its own login.
  Every commit it holds also exists on the machine that pushed it, so a fresh
  install and a clone rebuild it.
- **Found by name.** A reserved address on the router and a `.local` name.

Hosting an origin takes very little power: our repos come to a few hundred MB,
and pushes are fast-forwards over the LAN. `../digitization/names` already says
the origin is meant to move on under a new name. This box could be where it
goes.

## Reformatting

1. **Storage.** 1 GB won't hold Debian comfortably. Either swap the IDE flash
   module for a bigger one (8–32 GB), or install to a USB stick in one of the
   sockets inside the case, where it can't get knocked out.
2. **Make the installer stick on the iMac.** Kiosk-1 and the bays can't write
   a raw disk without an administrator.
3. **Boot it** with F12 and pick the stick. Nothing in the BIOS is locked.
4. **In the BIOS,** set power-on after power failure to On.

## Not known yet

- Where its network cable goes, since it isn't the studio LAN.
- What it is called (`names`).
