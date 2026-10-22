# digitization

A Dell OptiPlex 9020M (asset 200-FCPubMedia) running Debian 13 XFCE live from an SD card, the first
Linux profile. It shares its name with the [`digitization`](CREW.md) crew,
which it is to take over from station-node. Not worn yet. Machines: [docs/station.md](../../docs/station.md).

| | |
|---|---|
| `names` | `linux Hostname digitization`. A live boot answers `debian`; the card's one-time setup (`settle-card.sh` on its toolbox partition, until this profile carries its own) reads this line from the origin and applies it: hostname, `/etc/hosts`, the desktop's login cookie, `digitization.local` |
| `services` | the crew's order: `intake every 1m`, from its own menu `../digitization.yml`, kept by `fcpm-crew@digitization` (`../crew.sh`) |; `follow every 5m` keeps this checkout on the origin's main with every trove at its pin, so a merge reaches the board by itself
| `pools.yml` | the landing (`/srv/landing`, label `fcpm-landing`) as a pool, served by the crew's `pools` line on 8091 (`../../troves/pools.yml`); an emulated pool beside it for `pools.py sample` |
| `gear.yml` | what the job stands on, apt names: `python3-yaml`, `git`, `gh`, `systemd-timesyncd`, `openssh-server`, `rsync`, `zenity`, `avahi-utils`, `vivaldi-stable`, `firefox-esr`; Claude Code by hand |
| the door | `../kiosk/door.py serve` on loopback :8081 behind nginx's port 80 (the `static` job's `nginx.conf`), started at login by `at-login` (`fcpm-digitization.desktop` in `/etc/xdg/autostart`), then Vivaldi opens maximized with its page as a pinned tab, never a window of its own (`open-page`). `digitization.local` on the LAN; at `localhost` the board also offers **Unlock** for the signing key, its passphrase asked on this screen (`../kiosk/askpass`) |
| `rest` | the screen never blanks or powers down (X and XFCE's power manager both told). Ten minutes without input, `../../brand/idle` comes up full screen, the mark and the clock, read from the checkout; the first touch takes it away. Started by `at-login` beside the door |
| static sites | the public site and the Wix copy are the [`static`](../static/CREW.md) job's, which this machine also wears; nginx serves their names (`fcpublicmedia.local`, `www.`, `wix.`) itself and hands every other name to the door |
| `lan.yml`, `mdns.allow` | the names this machine answers to under `fcpublicmedia.local`, held up by the crew's `names keep` line (`../lan.py publish`). See Names |
| the podcast studio's door | an iPad Air 2 in a landscape holder at the hallway door shows `http://digitization.local/room/podcast/` (Safari: Add to Home Screen, then Guided Access; the page never dims). Staff check in from their own phone on Helm at `http://digitization.local/host/?room=podcast` (`wizard:kiosk+host`); the replies land under `~/.local/state/media-node/replies` and `../kiosk/replies.py status` reads them. [`docs/kiosk.md`](../../docs/kiosk.md), Rooms and Replies |
| `check.sh` | each gear present (dpkg), the crew's supervisor up, the origin mounted, the clock synced and on Fort Collins time, SSH keys only, the door behind nginx, every LAN name held and served, and deep `.local` names resolving here: `ok` or `WANTED` with the fix. `fcpm check` |
| `zram-generator.conf`, `sysctl-zram.conf`, `earlyoom.default` | swap in compressed RAM, and earlyoom, so a memory shortage costs one process instead of the box. See Memory |
| `KEYHOLDERS` | who may prove themselves to this machine by key: the origin's SSH door. A slot is an office (as `role:` in `site/_data/hosts.yml`) and holds only a public key; revoking is emptying the line by merged PR. The secretary's slot is empty. The GitHub SSH key "FCPM Digitization" is the machine's own, not a keyholder's |
| role | FCPM's git origin and receiver, so work goes on through a cloud outage |

## Names

People reach things here by name, as deep as DNS goes, each an mDNS name of this machine beside
`digitization.local` (decided 2026-10-17). `lan.yml` says which, and the door serves each:

| name | serves |
|---|---|
| `helm.fcpublicmedia.local` | the board. Shared: any machine may hold it; the first to claim it does, and another asks again every 30 s, so it takes over when the holder goes |
| `fcpublicmedia.local`, `www.fcpublicmedia.local` | the public site, built here (shared the same way; the [`static`](../static/CREW.md) job) |
| `wix.fcpublicmedia.local` | the Wix site, photocopied, until the board retires it (shared; `static`) |
| `digitization.fcpublicmedia.local` | this machine's directory: its gear, and the shared names with who holds each |
| `atem-mini-pro.digitization.fcpublicmedia.local`, `aja-helo.…`, `rodecaster-pro-ii.…` | one piece of gear, named for its trove: its facts (`instrument.yml`) and where it is now, discovered (mDNS or this USB), never declared |

`digitization.local` and every path under it stay as they were (the board, the rooms, the host check-in).
The machine's part of each name is its `names` line, so a rename moves them all. Linux refuses names
past two labels by default (nss-mdns's heuristic); here `/etc/mdns.allow` is `mdns.allow`, and the hosts line
in `/etc/nsswitch.conf` is `files myhostname mdns4_minimal [NOTFOUND=return] dns mdns4`: two-label names
as before, deeper ones through `mdns4` after unicast DNS says no, so reverse lookups stay fast. Apple's
resolvers take the deep names as they are. Windows' is not tested yet. `python3 machines/lan.py` says who
holds each name now.

## Memory

7.7 GB, no disk swap, and a root on an SD card. On 2026-10-17 at 01:38 the box ran short with no swap: the kernel
evicted the programs' own code and read it back from the card, over and over, so every program stopped while the
kernel lived (SSH took the connection and said nothing) and the OOM killer never fired. Twenty minutes later
only the power button helped. Now there is a way out on its own:

- **zram** (`zram-generator.conf` → `/etc/systemd/zram-generator.conf`): half the RAM as compressed swap, zstd,
  and `sysctl-zram.conf` (`vm.swappiness = 180`, `vm.page-cluster = 0`) so the kernel uses it before evicting code.
- **earlyoom** (`earlyoom.default` → `/etc/default/earlyoom`): under 5% memory and 15% swap free it sends SIGTERM
  (SIGKILL at half that) to the biggest process, preferring browser tabs, headless Firefox captures, `node` and
  Claude's desktop app, and avoiding SSH, X, the session, `python3` (the crew, the door, pools) and Claude Code.
  The patterns have no spaces or quotes: systemd splits the line at spaces. `journalctl -u earlyoom` says what it
  ended; `earlyoom --dryrun -m 90 -s 100` shows what it would pick now.

## The origin

Bare repositories at `/srv/origin/<owner>/<repo>`: all of FC-Public-Media, and the four FCCN-ANTIBODY
repositories fcpublicmedia.org mounts. They live on the card's own `card-origin` partition (ext4, mounted by label), beside the system, not inside it.

`origin-intake` (started every minute by the crew's `intake` line; it asks GitHub every 10 minutes while `fcpm dev on`, otherwise weekly, or now with `--now`; and only while `/srv/origin` is mounted;
`--status` prints the last state) tracks GitHub's `main` only, one GraphQL query for every repository,
`gh` holding the login. Behind: fast-forward. Ahead: left alone. Both moved: a clean merge becomes our
own merge commit; a conflict is recorded in `/srv/origin/.intake/state.json` and `main` is untouched.
Nothing is forced or deleted, and every action is appended to `/srv/origin/.intake/actions.ndjson`.

A repository can also begin here, with no GitHub side: intake passes over it (it has no `github`
remote) and the standby carries it to origin.local like the rest. Making one is a deliberate act, not
a convenience: `git init --bare -b main`, the two `receive.deny*` settings, a `description`. The
first is `FC-Public-Media/broadcast` (2026-10-21), the broadcast job's look ([`../broadcast/PROFILE.md`](../broadcast/PROFILE.md)).

The LAN may push only authenticated fast-forwards (`receive.denyNonFastForwards`, `receive.denyDeletes`;
no pull requests here), through the SSH door, [`origin-door`](origin-door). Each key in
[`KEYHOLDERS`](KEYHOLDERS) is one line in `~/.ssh/authorized_keys`, forced to the door with its office and
holder (the crew's `keys` line writes them; every other line there is left alone). A keyholder's remote
is `user@digitization.local:<owner>/<repo>`: every repository fetches and takes pushes, but in one that
lives on GitHub, `main` and `github/*` are intake's alone; any other branch, and tags, wait here in view
until they go to GitHub (`door-hooks/pre-receive`). That is the seam: what is ready to go to GitHub, and
what is still to come from it. `init <owner>/<repo>` is the secretary's. Every fetch, push (each ref before and after) and refusal goes to
`/srv/origin/.door/actions.ndjson`. Tests: `bin/test_origin_door.py`.
