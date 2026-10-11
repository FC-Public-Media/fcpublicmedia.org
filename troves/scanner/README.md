# scanner

A camera and a screen where grants are redeemed: a code held up, or a phone set down, read and
checked, and a pickup handed out. It reads; it does not decide. Grants are minted and signed by
[`digitization`](../../machines/digitization/PROFILE.md) (`mint.mjs`). Today: the
[`qr`](../../machines/qr/PROFILE.md) Pi, kiosk's pickup point ([machines](../../machines/README.md)).
Its gear and what each piece needs: [`gear.yml`](gear.yml).

## The screen

`inbox.py`, on tty1 as `scanner.service`, in panels:

- the bar: the host, the org, the clock;
- the inbox: one line per thing waiting, the item on a wedge pointing at its person, then its size.
  The row being picked up goes full yellow;
- `scanner`: the live picture while someone is there, dark while resting; its bar says `waiting`
  (muted: latched and ready), `looking`, `reading 9/17 · frames · healed`, `caught` or `refused`.
  A pickup takes this pane over: `plug in your drive`, `drive ready`, `drive too small`;
- `latest`, on the last row: the last few events. Its bar carries the platform, `power ok · 66°C`,
  and turns red with the trouble's name (USB over-current, under-voltage, throttling).

Brand yellow is a surface, never text. Text is ANSI rotated by fbcon; the picture is written straight
into the framebuffer, a whole frame at a time. The camera is three jobs that never wait on each
other: a grabber keeps the newest frame, the display draws it, and the QR search runs in its own
process (full size, then half, then a third: a smaller copy shrinks the blur too). It wakes on a
jump above the room's own noise floor, so a lamp switched on settles back to rest.

## Codes

Only AC1 frames count: the bottles carrier from anecdote.channel (`composer/`, unchanged), run by
`bridge.mjs` under Node. It takes frames in any order, heals dents and missed frames (fountain),
refuses foreign tiles, and checks signatures. `friends.json` names the keys this scanner trusts,
today only digitization's. A plain QR is shown as ignored.

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

## Install and state

From a checkout: `sudo troves/scanner/install`. It installs the packages in `gear.yml`, adds the
monitor's mode and turn to the boot line (the qr box's by default; `SCREEN_MODE`, `SCREEN_TURN`),
and runs the screen from the checkout. What changes lives apart from the code, in `$QR_STATE`
(`/home/fcpm/qr`): this machine's `inbox.json`, `used.json`, `events.log`, the built font, and any
`config.json` or `friends.json` of its own.
