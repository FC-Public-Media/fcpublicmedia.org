# digitization

A Dell OptiPlex 9020M (asset 200-FCPubMedia) running Debian 13 XFCE live from a USB stick, the first
Linux profile. It shares its name with the [`digitization`](../../crews/digitization/CREW.md) crew,
which it is to take over from station-node. Not worn yet. Machines: [docs/station.md](../../docs/station.md).

| | |
|---|---|
| `names` | `linux Hostname digitization`. Not applied: the live boot answers `debian`, and `sudo hostnamectl hostname digitization` lasts until reboot |
| `KEYHOLDERS` | who may prove themselves to this machine by passkey. A slot is an office (as `role:` in `site/_data/hosts.yml`) and holds only a public key; revoking is removing the line by merged PR. The secretary's slot is empty. The GitHub SSH key "FCPM Digitization" is the machine's own, not a keyholder's |
| role | FCPM's git origin and receiver, so work goes on through a cloud outage |

## The origin

Bare repositories at `/srv/origin/<owner>/<repo>`: all of FC-Public-Media, and the four FCCN-ANTIBODY
repositories fcpublicmedia.org mounts. They live on an ext4 image on the RAID, not on the stick.

`origin-intake` (installed at `~/.local/bin/`, run every minute by `systemd/origin-intake.timer`;
`--status` prints the last state) tracks GitHub's `main` only, one GraphQL query for every repository,
`gh` holding the login. Behind: fast-forward. Ahead: left alone. Both moved: a clean merge becomes our
own merge commit; a conflict is recorded in `/srv/origin/.intake/state.json` and `main` is untouched.
Nothing is forced or deleted, and every action is appended to `/srv/origin/.intake/actions.ndjson`.

The LAN may push only authenticated fast-forwards (`receive.denyNonFastForwards`, `receive.denyDeletes`;
no pull requests here). The SSH door, keyed from `KEYHOLDERS`, is not open yet.
