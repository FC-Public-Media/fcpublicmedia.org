# digitization

**Status: drafted 2026-10-09, not yet worn.** A Dell OptiPlex 9020M (asset
200-FCPubMedia), running Debian 13 XFCE live from a USB stick. The first Linux
profile here.

The name is the crew's on purpose (see `names`): for now this box and the
[`digitization`](../../crews/README.md) crew share it. It takes the crew over
from station-node, which can then vacate. The crew's contract
(`docs/crews/digitization/CREW.md`) has not arrived from station-node yet.

| | |
|---|---|
| wears | `digitization` (intended) |
| names | `names`: `linux Hostname digitization`, not applied yet |
| keyholders | `KEYHOLDERS`: the secretary's passkey slot, empty |
| role on the LAN | the FCPM git origin and receiver, so work can go on through a cloud outage (below) |

## The origin

Bare repos at `/srv/origin/<owner>/<repo>`: all of FC-Public-Media plus the
four FCCN-ANTIBODY repos fcpublicmedia.org mounts. Only FCPM's own things.
They live on an ext4 image on the RAID, not on the stick: the origin belongs to the box.

**Intake is automatic and tracks `main` only** (`origin-intake`, every minute
from `systemd/origin-intake.timer`). A merge on GitHub is when we pay
attention. Behind → fast-forward. Ahead → left alone. Both moved → a clean
merge becomes our own merge commit; a conflict is recorded in
`/srv/origin/.intake/state.json` and `main` is not touched. Nothing is forced.
Periodic until GitHub can call us with a webhook.

**What comes in from the LAN is authenticated fast-forwards only.** Every repo has
`receive.denyNonFastForwards` and `receive.denyDeletes`. The authenticated
door (SSH, keys from `KEYHOLDERS`) is not open yet. No pull requests here:
everyone has the code, so a station sends a fast-forward. If that turns out
to be a barrier, we'd rather hit it and take it down on purpose.

Not yet: publishing origin → GitHub, and the page. That will be a front end
for people at a nonprofit, not station-node's 8080 page. Borrowing its raw
views is fine, but they aren't the default.
