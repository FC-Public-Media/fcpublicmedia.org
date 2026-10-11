# qr

A Raspberry Pi 3 with a camera looking up from the desk: the scanner screen at `qr.local`. People hold
a code over it, or set a phone down in front of it, to redeem a grant: a pickup, an approval. It
reads; it does not decide. Grants are minted and signed by [`digitization`](../digitization/PROFILE.md).
Machines: [docs/station.md](../../docs/station.md).

| | |
|---|---|
| model | Raspberry Pi 3 Model B Rev 1.2, 1 GB; Debian 13 (Raspberry Pi OS), kernel 6.18 rpt; boots to `multi-user.target`, no desktop |
| `names` | `linux Hostname qr`. Login `fcpm` by key only; password login is off |
| camera | Camera Module v2 (imx219), fixed focus, pointed at the ceiling over the monitor's edge. Sharp at a few metres; a phone has to come close, which is the soft spot. A Logitech BRIO on the front hub is aimed at a phone dock, for long reads where nobody should have to hold still |
| monitor | Samsung LF24T40, portrait with its top to the right. Dark at 1080p from this Pi, fine at 720p: `video=HDMI-A-1:1280x720@60D fbcon=rotate:3` |
| front hub | VIA VL813 hub with an Alcor AU6477 card reader (SD, CF, SM/xD, MS). Keyboard and mouse live here too |
| state | `/home/fcpm/qr`: `inbox.json` (this machine's rows), `used.json`, `events.log`, the built font |

## The screen

`inbox.py`, on tty1 as `qr-inbox.service`, in panels:

- the bar: `qr.local`, the org, the clock;
- the inbox: one line per thing waiting, the item on a wedge pointing at its person, then its size. The row being picked up goes full yellow;
- `scanner`: the live picture while someone is there, dark while resting; its bar says `looking`, `reading 9/17 · frames · healed`, `caught` or `refused`. A pickup takes this pane over: `plug in your drive`, `drive ready`, `drive too small`;
- `latest`, on the last row: the last few events; its bar carries the platform, `power ok · 66°C`, and turns red with the trouble's name (USB over-current, under-voltage, throttling) when there is any. A Pi 3 shares about 1.2 A across its USB ports: a ring light on the front hub trips over-current.

Brand yellow is a surface, never text. Text is ANSI rotated by fbcon; the picture is written straight
into the framebuffer, a whole frame at a time. The camera is three jobs that never wait on each
other: a grabber keeps the newest frame, the display draws it, and the QR search runs in its own
process (full size, then half, then a third: a smaller copy shrinks the blur too). It wakes on a
jump above the room's own noise floor, so a lamp switched on settles back to rest.

## Codes

Only AC1 frames count: the bottles carrier from anecdote.channel (`composer/`, unchanged),
run by `bridge.mjs` under Node. It takes frames in any order, heals dents and missed frames
(fountain), refuses foreign tiles, and checks signatures. `friends.json` names the keys this station
trusts, today only digitization's. A plain QR is shown as ignored.

- `fcpm.pickup {pickup: <row id>}` lights the row and hands the scanner pane to the pickup. Demo rows
  (`"demo": true`) never spend their code or leave the inbox; real ones spend the code and leave
  when done. Inbox zero is the finished state.
- `fcpm.approval {say}` is logged as accepted.
- Every code works once (`used.json`).

`mint.mjs` runs on digitization, where its key lives (`~/.config/fcpm-qr/digitization.jwk`):
`node mint.mjs pickup <row-id>` writes one code; `--loop` pours it as a fountain page to play
from a phone.

Drives are only looked at: label, filesystem and size from `lsblk`. Nothing here mounts, writes or
ejects anyone's media. The copy for a real pickup is not built: a grant names its tagged file on
the tank in advance, so nothing is asked for freeform.

## Install

From a checkout on the Pi: `sudo machines/qr/install`. It installs `python3-zbar` and `nodejs`, adds
the monitor's mode and turn to the boot line, and runs the screen from the checkout with its state
in `/home/fcpm/qr`. Login moves to Alt+F2.
