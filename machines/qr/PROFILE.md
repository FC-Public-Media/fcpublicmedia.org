# qr

A Raspberry Pi 3 on the desk with a camera looking up over the monitor's edge: kiosk's pickup point
at `qr.local` ([crews](../../crews/README.md)). It carries the [`scanner`](../../troves/scanner/README.md)
trove: the screen, the camera, the codes. Machines: [docs/station.md](../../docs/station.md).

| | |
|---|---|
| model | Raspberry Pi 3 Model B Rev 1.2, 1 GB; Debian 13 (Raspberry Pi OS), kernel 6.18 rpt; boots to `multi-user.target`, no desktop |
| `names` | `linux Hostname qr`. Login `fcpm` by key only; password login is off |
| camera | Camera Module v2 (imx219), fixed focus, pointed at the ceiling. Sharp at a few metres; a phone has to come close, which is the soft spot. A Logitech BRIO on the front hub is aimed at a phone dock, for long reads where nobody should have to hold still |
| monitor | Samsung LF24T40, portrait with its top to the right. Dark at 1080p from this Pi, fine at 720p: `video=HDMI-A-1:1280x720@60D fbcon=rotate:3`, the scanner's install defaults |
| front hub | VIA VL813 hub with an Alcor AU6477 card reader (SD, CF, SM/xD, MS); keyboard and mouse here too. A Pi 3 shares about 1.2 A across its USB ports: a ring light here trips over-current |
| scanner | `scanner.service` on tty1, from a checkout; state in `/home/fcpm/qr`. Login on Alt+F2 |
