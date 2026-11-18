# bounce: the Raspberry Pi

A Raspberry Pi 3 on the desk, the prototype of a member site with a crew: a box a business keeps on its own
network ([`bounce`](CREW.md) is its first job). Until it has its own browser on the monitor, the monitor
still shows the [`qr`](../qr/PROFILE.md) console over its leash. Machines: [docs/station.md](../../docs/station.md).

| | |
|---|---|
| model | Raspberry Pi 3 Model B Rev 1.2, 1 GB; Debian 13 (Raspberry Pi OS), kernel 6.18 rpt; boots to `multi-user.target`, no desktop |
| `names` | `linux Hostname bounce` (it was `qr`). Login `fcpm` by key only; password login is off |
| radio | the onboard Broadcom, 2.4 GHz, WPA2 only. Joins `FC Public Media Helm` as a client ([`helm-wifi`](helm-wifi), the password from the keychain's `wifi-helm`), so the box is on Helm wherever that network reaches; the island is not made while it does |
| camera | a Logitech BRIO on the front hub, aimed at a phone dock. The Camera Module v2 (imx219) is not detected and unused |
| monitor | the biggest TV we own, portrait, standing on its left edge, behind a Blackmagic converter (EDID `BMD HDMI`, 80 MHz pixel clock at most). The TV wants 1080p and the converter passes 1080p30, so it is pinned from boot: `video=HDMI-A-1:1920x1080@30D fbcon=rotate:1` (the eyes draw at any turn) |
| front hub | VIA VL813 hub with an Alcor AU6477 card reader (SD, CF, SM/xD, MS); keyboard and mouse here too. A Pi 3 shares about 1.2 A across its USB ports: a ring light here trips over-current |
| eyes | `eyes.service` on tty1 from `~/qr` (`QR_STATE`), leashed to the qr page on digitization by `~/.ssh/eyes`. Login on Alt+F2 |
