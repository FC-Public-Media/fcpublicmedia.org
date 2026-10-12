# thin-client

A donated HP t510 thin client in the control rack, under the headphone amp and above the switcher. It
boots HP ThinPro (Linux) into one remote desktop connection its last owner left, and is to be wiped.
Its job is the kiosk's overflow console, beside the scanner. The folder name is a placeholder until
the machine is named (`names`).

| | |
|---|---|
| model | HP t510, serial MXL2411TY7 |
| BIOS | AMI v02.67, system ROM 786R11 v1.03, no administrator password. Boots USB SD/MMC reader, then the flash, then network; F12 for a menu. Power on after power failure: Off. Clock in UTC |
| CPU | VIA Eden X2 U4200, two 64-bit cores at 1.0 GHz; SSSE3, SSE4.1, VIA PadLock (RNG, AES, SHA) |
| graphics | VIA Chrome9 HD (VX900), DVI-I and DVI-D, both at once; 128 MB from memory. Linux support is thin: a text console is safe, a browser on each screen may not be |
| memory | 2 GB DDR3 in one SO-DIMM socket (1920 MB after video); 4 GB modules are reported to work |
| storage | 1 GB flash on the 44-pin IDE header (`PM-1GB ATA Flash`), replaceable; two USB sockets inside, under the top cover |
| network | gigabit Ethernet, Broadcom BCM57780, `9C:8E:99:E9:58:3B`; network boot (MBA v12.2). Not on the studio LAN |
| ports, power | serial, parallel, two PS/2, USB 2.0 front and back, audio; 19 V barrel, about 8 W idle, 19 W running |

Model, serial, BIOS, memory, flash and hardware address are read from the box; the rest is from
[parkytowers' t510 page](https://www.parkytowers.me.uk/thin/hp/t510/).

## The job

The kiosk's overflow console, partnering the [`qr`](../qr/PROFILE.md) Pi's scanner. It is our own
thin client: like ThinPro it shows what is kept elsewhere, and keeps nothing itself.

- It runs the scanner's eyes (`eyes.py`, FC-Public-Media/scanner#2) with no camera. Its console goes
  up one `ssh -T` to where the inbox is kept, and that page paints it as it paints the Pi. No logic
  and no secrets live here, so any box can stand in.
- It is a text console, not a browser. Debian 13 carries no driver for its graphics chip (no
  `xserver-xorg-video-openchrome`), so only the firmware framebuffer is safe.
- It watches. Anything asked for here is approved elsewhere, the way a grant is.
- Standing beside the scanner, its page can point at it.

Open: whether both DVI screens show a console at once. The first boot is Debian 13 live from a stick
with no persistence. It changes nothing on the box and answers that.

## Reformatting

1. Storage: swap the flash module for 8 to 32 GB, or install to a USB stick in an inside socket.
2. Write the installer stick on the iMac; the kiosk and the bays cannot write a raw disk without an administrator.
3. Boot it with F12 and pick the stick (nothing in the BIOS is locked). Set power on after power failure to On.
