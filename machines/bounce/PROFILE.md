# bounce: the Raspberry Pi

A Raspberry Pi 3 on the desk, the prototype of a member site with a crew: a box a business keeps on its own
network ([`bounce`](CREW.md) is its first job). Until it has its own browser on the monitor, the monitor
still shows the [`qr`](../qr/PROFILE.md) console over its leash. Machines: [docs/station.md](../../docs/station.md).

| | |
|---|---|
| model | Raspberry Pi 3 Model B Rev 1.2, 1 GB; Debian 13 (Raspberry Pi OS), kernel 6.18 rpt; boots to `multi-user.target`, no desktop |
| `names` | `linux Hostname bounce` (it was `qr`). Login `fcpm` by key only; password login is off |
| radio | the onboard Broadcom: AP mode, 2.4 GHz only. The bounce's island network |
| camera | a Logitech BRIO on the front hub, aimed at a phone dock. The Camera Module v2 (imx219) is not detected and unused |
| monitor | Samsung LF24T40, portrait with its top to the right. Dark at 1080p from this Pi, fine at 720p: `video=HDMI-A-1:1280x720@60D fbcon=rotate:3` |
| front hub | VIA VL813 hub with an Alcor AU6477 card reader (SD, CF, SM/xD, MS); keyboard and mouse here too. A Pi 3 shares about 1.2 A across its USB ports: a ring light here trips over-current |
| eyes | `eyes.service` on tty1 from `~/qr` (`QR_STATE`), leashed to the qr page on digitization by `~/.ssh/eyes`. Login on Alt+F2 |
