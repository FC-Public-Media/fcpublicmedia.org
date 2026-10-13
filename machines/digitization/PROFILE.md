# digitization

A Dell OptiPlex 9020M (asset 200-FCPubMedia) running Debian 13 XFCE live from a USB stick, the first
Linux profile. It shares its name with the [`digitization`](CREW.md) crew,
which it is to take over from station-node. Not worn yet. Machines: [docs/station.md](../../docs/station.md).

| | |
|---|---|
| `names` | `linux Hostname digitization`. A live boot answers `debian`; the boot step (`restore.sh` on the RAID, until this profile carries its own) reads this line from the origin and applies it: hostname, `/etc/hosts`, the desktop's login cookie, `digitization.local` |
| `services` | the crew's order: `intake every 1m`, from its own menu `../digitization.yml`, kept by `fcpm-crew@digitization` (`../crew.sh`) |; `follow every 5m` keeps this checkout on the origin's main, so a merge reaches the board by itself
| `gear.yml` | what the job stands on, apt names: `python3-yaml`, `git`, `gh`, `systemd-timesyncd`, `openssh-server`, `zenity`, `vivaldi-stable`; Claude Code by hand |
| the door | `../kiosk/door.py serve` on port 80, started at login by `at-login` (`fcpm-digitization.desktop` in `/etc/xdg/autostart`), its page then opened in Vivaldi. `digitization.local` on the LAN; at `localhost` the board also offers **Unlock** for the signing key, its passphrase asked on this screen (`../kiosk/askpass`) |
| `check.sh` | each gear present (dpkg), the crew's supervisor up, the origin mounted, the clock synced, SSH keys only, port 80 and the door: `ok` or `WANTED` with the fix. `fcpm check` |
| `KEYHOLDERS` | who may prove themselves to this machine by passkey. A slot is an office (as `role:` in `site/_data/hosts.yml`) and holds only a public key; revoking is removing the line by merged PR. The secretary's slot is empty. The GitHub SSH key "FCPM Digitization" is the machine's own, not a keyholder's |
| role | FCPM's git origin and receiver, so work goes on through a cloud outage |

## The origin

Bare repositories at `/srv/origin/<owner>/<repo>`: all of FC-Public-Media, and the four FCCN-ANTIBODY
repositories fcpublicmedia.org mounts. They live on an ext4 image on the RAID, not on the stick.

`origin-intake` (started every minute by the crew's `intake` line; it asks GitHub every minute only while `fcpm dev on`, otherwise weekly, or now with `--now`; and only while `/srv/origin` is mounted;
`--status` prints the last state) tracks GitHub's `main` only, one GraphQL query for every repository,
`gh` holding the login. Behind: fast-forward. Ahead: left alone. Both moved: a clean merge becomes our
own merge commit; a conflict is recorded in `/srv/origin/.intake/state.json` and `main` is untouched.
Nothing is forced or deleted, and every action is appended to `/srv/origin/.intake/actions.ndjson`.

The LAN may push only authenticated fast-forwards (`receive.denyNonFastForwards`, `receive.denyDeletes`;
no pull requests here). The SSH door, keyed from `KEYHOLDERS`, is not open yet.
