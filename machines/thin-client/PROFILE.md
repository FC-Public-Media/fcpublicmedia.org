# thin-client

A donated HP t510 thin client in the control rack, under the headphone amp and above the switcher. It
came with HP ThinPro (a 2011 image, Ubuntu 10.04) on its flash; that image is kept on the RAID
(`linux-persist/thinpro-MXL2411TY7-flash-2026-10-13.img.zst`), and the flash now runs Alpine.
Its job is the kiosk's overflow console, beside the scanner. The folder name is a placeholder until
the machine is named (`names`).

| | |
|---|---|
| model | HP t510, serial MXL2411TY7 |
| BIOS | AMI v02.67, system ROM 786R11 v1.03, no administrator password. Boots USB SD/MMC reader, then the flash, then network; F12 for a menu. Power on after power failure: previous state (back on only if it was on). Clock in UTC |
| CPU | VIA Eden X2 U4200, two 64-bit cores at 1.0 GHz; SSSE3, SSE4.1, VIA PadLock (RNG, AES, SHA) |
| graphics | VIA Chrome9 HD (VX900), DVI-I and DVI-D showing the same picture; 128 MB from memory. No VGA socket (the 9-pin one is serial). Its VESA goes up to 1280x1024; Linux has no driver for it, so its console is that mode on the kernel's simple framebuffer |
| memory | 2 GB DDR3 in one SO-DIMM socket (1920 MB after video); 4 GB modules are reported to work |
| storage | 1 GB flash on the 44-pin IDE header (`PM-1GB ATA Flash`), replaceable; two USB sockets inside, under the top cover. Alpine takes 230 MB of it |
| network | gigabit Ethernet, Broadcom BCM57780, `9C:8E:99:E9:58:3B`; network boot (MBA v12.2). On the studio LAN by DHCP |
| ports, power | serial, parallel, two PS/2, USB 2.0 front and back, audio; 19 V barrel, about 8 W idle, 19 W running |

Model, serial, BIOS, memory, flash and hardware address are read from the box; the rest is from
[parkytowers' t510 page](https://www.parkytowers.me.uk/thin/hp/t510/).

Today it wears [`origin`](../origin/PROFILE.md), from its own flash since 2026-10-15; this job waits
for another box. Until then the origin was a Debian stick in an outside port, and someone pulling it
on 2026-10-13 took the box down mid-run: nothing a job needs should hang outside a box.

## The job

The kiosk's overflow console, partnering the [`qr`](../qr/PROFILE.md) Pi's scanner. It is our own
thin client: like ThinPro it shows what is kept elsewhere, and keeps nothing itself.

- It runs the scanner's eyes (`eyes.py`, FC-Public-Media/scanner#2) with no camera. Its console goes
  up one `ssh -T` to where the inbox is kept, and that page paints it as it paints the Pi. No logic
  and no secrets live here, so any box can stand in.
- It is a text console, not a browser. Neither Debian 13 nor Alpine carries a driver for its
  graphics chip, so its console is the firmware's best VESA mode (below).
- It watches. Anything asked for here is approved elsewhere, the way a grant is.
- Standing beside the scanner, its page can point at it.

First boot (2026-10-13), Debian 13.7 live `standard`: about a minute on `microcode: no support for
this CPU vendor` (harmless: VIA), then a prompt; DHCP gives IPv4. Alpine 3.24 live and installed:
the `pata_via` flash, the `tg3` network and the firmware console all work.

## Its screen (2026-10-17)

Left alone it shows the BIOS's 80x25 text, 720x400 pixels, which a 1080p monitor stretches about
2.7 times into a blur. The origin's outfit asks the firmware for its modes (`hwinfo --framebuffer`)
and boots with the largest, `vga=0x031b` (1280x1024, 24-bit); Terminus Bold 14x28 makes that 91x36.
On the Dell S2409Wb in the rack (1920x1080, DVI-D), the panel scales 1280x1024 about 1.05 times.

Native 1920x1080 needs the chip's own driver. openchrome 0.6.0 builds for Alpine (Debian's source,
without DRI, `shadowUpdatePackedWeak` renamed, linked `-z lazy` for musl's loader) and finds the
chip, but on DVI it drives a SiI 164 that the BIOS keeps powered down, so the monitor only blinks;
the BIOS feeds both DVI sockets some other way. Its VGA path, the analog pins of the DVI-I socket,
is untried: a passive DVI-I to VGA adapter into a monitor's VGA input would show whether it holds.
