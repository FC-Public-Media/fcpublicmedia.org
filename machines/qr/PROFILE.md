# qr

Kiosk's pickup point and the studio's intake by camera, carrying the [`scanner`](../../troves/scanner/README.md)
trove. Worn by [`digitization`](../digitization/PROFILE.md), which holds `qr.local` ([`lan.yml`](../digitization/lan.yml)'s
`bare`): the page, the inbox and the intake live here, so the role stands without any one camera box.
Machines: [docs/station.md](../../docs/station.md).

| | |
|---|---|
| `names` | `linux Hostname digitization` |
| page | `troves/scanner/page.py`: the console, painted from here to whatever screen is leashed to it |
| intake | the door's `POST /drop` and `machines/kiosk/replies.py`; `qr.local` serves the board, so the bays join at `http://qr.local/drop` over Helm |
| eyes | any box with a camera joins by running `eyes.py` with one forced-command line in digitization's `authorized_keys` (the scanner's README, Two halves). Today: the [`bounce`](../bounce/PROFILE.md) Pi's BRIO and monitor |
| screen | the leashed box's console. A browser tab of the same console is shelved |
