# digitization

A Dell OptiPlex 9020M (asset 200-FCPubMedia) running Debian 13 XFCE live from an SD card, the first
Linux profile. It shares its name with the [`digitization`](CREW.md) crew,
which it is to take over from station-node. Not worn yet. Machines: [docs/station.md](../../docs/station.md).

| | |
|---|---|
| `names` | `linux Hostname digitization`. A live boot answers `debian`; the card's one-time setup (`settle-card.sh` on its toolbox partition, until this profile carries its own) reads this line from the origin and applies it: hostname, `/etc/hosts`, the desktop's login cookie, `digitization.local` |
| `services` | the crew's order, from its own menu `../digitization.yml`, kept by `fcpm-crew@digitization` (`../crew.sh`): `follow every 5m` keeps this checkout on origin.local's main with every trove at its pin, so a merge reaches the board by itself |
| `pools.yml` | the landing (`/srv/landing`, label `fcpm-landing`) as a pool, served by the crew's `pools` line on 8091 (`../../troves/pools.yml`); an emulated pool beside it for `pools.py sample` |
| `post.yml`, `post-receive`, `post-senders.yml`, `known_hosts` | where the bays deliver finished post work: `/srv/landing/post`, beside the raws. A bay's key, merged into `post-senders.yml`, is let in within a minute by the crew's `senders` line and may only `receive` one sealed folder; it is kept only whole, never overwritten, and only while the landing is mounted. `post.py status` here shows each take's request, what is in, and `fulfilled`. `known_hosts` is this machine's host keys, for the bays to pin ([post](../../troves/post/README.md), Delivery) |
| `gear.yml` | what the job stands on, apt names: `python3-yaml`, `git`, `gh`, `systemd-timesyncd`, `openssh-server`, `rsync`, `zenity`, `npm`, `avahi-utils`, `vivaldi-stable`, `firefox-esr`; Claude Code by hand |
| the door | `../kiosk/door.py serve` on loopback :8081 behind nginx's port 80 (the `static` job's `nginx.conf`), started at login by `at-login` (`fcpm-digitization.desktop` in `/etc/xdg/autostart`), then Vivaldi opens maximized with its page as a pinned tab, never a window of its own (`open-page`). `digitization.local` on the LAN; at `localhost` the board also offers **Unlock** for the signing key, its passphrase asked on this screen (`../kiosk/askpass`) |
| `rest` | the screen never blanks or powers down (X and XFCE's power manager both told). Ten minutes without input, `../../brand/idle` comes up full screen, the mark and the clock, read from the checkout; the first touch takes it away. Started by `at-login` beside the door |
| static sites | the public site and the Wix copy are the [`static`](../static/CREW.md) job's, which this machine also wears; nginx serves their names (`fcpublicmedia.local`, `www.`, `wix.`) itself and hands every other name to the door |
| `lan.yml`, `mdns.allow` | the names this machine answers to under `fcpublicmedia.local`, held up by the crew's `names keep` line (`../lan.py publish`). See Names |
| the podcast studio's door | an iPad Air 2 in a landscape holder at the hallway door shows `http://digitization.local/room/podcast/` (Safari: Add to Home Screen, then Guided Access; the page never dims). Staff check in from their own phone on Helm at `http://digitization.local/host/?room=podcast` (`wizard:kiosk+host`); the replies land under `~/.local/state/media-node/replies` and `../kiosk/replies.py status` reads them. [`docs/kiosk.md`](../../docs/kiosk.md), Rooms and Replies |
| `check.sh` | each gear present (dpkg), the crew's supervisor up, origin.local answering as this checkout's origin, the clock synced and on Fort Collins time, SSH keys only, the door behind nginx, every LAN name held and served, deep `.local` names resolving here, and every key in `keys.yml` held: `ok` or `WANTED` with the fix. `fcpm check` |
| `keys.yml`, `keys` | the keychain: every secret FCPM's deploys and jobs use, by group, and where each lives. See Keys |
| `zram-generator.conf`, `sysctl-zram.conf`, `earlyoom.default` | swap in compressed RAM, and earlyoom, so a memory shortage costs one process instead of the box. See Memory |
| role | the workstation: it builds, and it is a client of the [origin](../origin/PROFILE.md) (origin.local holds FCPM's repositories since 2026-10-21) |

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

## The model over the tailnet

Bay 1's model (`machines/production/model.yml`) admits only the switched network, 10.209.1.0/24. An operator away from
the building reaches it through this machine: `model-relay` (crew line, `keep`) listens on this machine's tailnet
address, port 9931, and nowhere else. Every connection is asked of Tailscale (`tailscale whois`); a device tagged
`tag:operator` is joined to `10.209.1.20:9931`, any other is refused. Both are logged in
`~/.local/state/fcpm/model-relay.log`. The tailnet's own policy may be wider; this is where the scope is kept.
The tailnet has no MagicDNS, so a client is set to this machine's tailnet address (`tailscale ip -4`;
100.115.246.115 today): `http://100.115.246.115:9931/v1`, model `qwen3.5-4b`, no key. When bay 1's model is
off, a passed connection finds nothing to join and closes, which is the model being off, not the relay failing.

## Questions for the model

A person asks bay 1's model through a bottle, never directly: `wizard:model+ask` carries OpenAI-enough messages
(a role and its text, the question last; no model, no bay, no session), and anything they want remembered is
quoted in. The door's intake (`replies.py`) checks it against `shapes/ask.yml` and queues it; `asks` (crew line,
`keep`) answers the oldest first, one at a time, as the shape says: our role first, their own instructions
inside it. The question is then reduced to a label (`shapes/label.yml`), so a phone can filter a category.
Each answer is `asks/answers/<nonce>.json` under the door's state, named for the question's nonce, which the
asker's phone already holds: that is how its inbox finds its own in the public loop. While the model is off,
questions wait. `machines/digitization/asks status` says what waits and what was answered.

Every answer is also bottled for the public loop (`pour.mjs`: unsigned AC1 fountain frames, `asks/bottles/`), and an
index bottle names the last day's answers: each question's nonce, its label and its bottle's id. Every frame names
its bottle by id. A phone catches everything in the loop, not only its own: its own answers go in its notebook,
and everyone else's it carries to the people they answer, who weren't there to read them ("Show it" pours one
again). Each pass shows each bottle K and a bit fresh droplets and moves on, so the loop flows; the next pass
shows the next droplets of its stock. An answer rides the loop for ten minutes (`replies.URGENT`), then falls off
it and stays on hand; a recall code (`wizard:loop+recall`, the ask page's "Ask the loop for it") brings it
back, at once and then out of the way (takeover), or into the running loop (inject). `/loop/?up=2` or `?up=4`
puts several bottles up at once, and `?tiles=N` is the press's collage (anecdote.channel press/broadcast.mjs):
N pieces of the same bottle at once. The phone's reader reads each frame in overlapping windows, so it catches
them all together. The door's
`/loop/` draws the index and the answers in turn (`?fps=`, `?index=`; asked again every pass, so it follows the set
as it changes) on any screen, over plain http: it only draws. `/ask/` is the wizard: the box, the outbox (the
code to show the camera) and the notebook kept on the phone, whose ticked answers are quoted into the next
question. On plain http a phone has no WebCrypto, so the page brings SHA-256 (`site/assets/js/sha256.mjs`) and
its bottles are real fountains, unsigned. The same page is on the public site (`/ask/`, `site/you/wizards/ask.md`,
offline with the kit), a secure page: there the bottle is signed, and "Catch it from the loop" reads the loop
with the phone's camera (`catch.mjs`, `camera.mjs`) until its own answer has come by. One script, `site/assets/js/ask.js`,
serves both; the LAN's copy also offers "Set it down here" and asks the door for the answer.

qr.local's own screen (`troves/scanner/page.py`) is the station's inbox and its broadcast. Each bottle is poured
twice: the loop's frames, and console frames (20 bytes a frame, each with its QR modules: a version-6 code, 41
modules, printed in half blocks on the 51-column screen). `asks` keeps `asks/state.json` (what it answers, by
whom, up or off, what it is on, any trouble), and `replies.inbox()` lists what the door took, newest first.

## Keys

This machine holds FCPM's secrets for now (decided 2026-10-23), and deploys that need them run here by hand.
`keys.yml` is the ledger: each group's keys, what each may do, where it came from and how to get another,
the file it lives in and what reads it. Values never enter the repository. A group is one file, mode 600, in
`~/.config/fcpm/keys/` on the card's encrypted home (Cablecast's and YouTube's single values keep their own
files beside it). Keys used together sit in one file, so a test key never meets a live one.

- `keys` lists what is held and what is wanted, never a value; `fcpm check` says the same.
- `keys take GROUP KEY` asks for a value in a window on this screen and refuses the wrong prefix.
- `keys offer GROUP DEVICE` asks for the group's wanted keys on a one-time page (an hour, closed once all are held) that only that tailnet device can open, for when nobody is at this screen.
- `keys run GROUP... -- CMD` hands groups to one command as environment variables.
- In a site-worker checkout (FC-Public-Media/site-worker): `keys run cloudflare stripe-live -- sh bin/deploy`
  deploys it, the Stripe key to wrangler on stdin; `keys run stripe-test -- node try-checkout.mjs` starts one
  test-mode Checkout Session through its own code, here, and prints its page.

GitHub's repository secrets are not part of it: nothing is kept there that this relies on. Where the keychain
lives later (a vault on the LAN, a card of its own) is open; moving it is the `dir:` line and the files. The
card's home is the only copy today, so losing it means issuing each key again, from the `from:` lines.

## Replies

Every form on the site (joining, a studio request, wanting to teach, a program, a message, equipment)
sends its reply to the site-worker, which keeps it in a tank in Cloudflare KV and nothing more. The crew's
`drain` line brings them here every hour: [`drain`](drain) runs the site-worker's own
`bin/drain.mjs`, from the checkout beside this one (`~/code/work/site-worker`, kept on the origin's main by
`follow`), with the keychain's `cloudflare` group. Each reply becomes one file,
`~/fcpm/answers/<tank>/<received>--<reference>.json`, written, read back and compared before its key in KV
is deleted, so a reply is always in one place or both, never neither. A failure leaves it in KV for the
next pass. KV keeps a reply until something deletes it (the worker sets no expiry), so an hour costs
nothing in safety, and a pass that finds nothing is one list operation: 24 a day.

The archive is the list from then on: on the card's encrypted home, private (700/600), never in a
repository, since it holds names, emails, phones and addresses. Nothing is deleted from it. Carrying it to
the log in Microsoft 365 (or an email) is a later line that reads these files at its own pace; KV is not
asked again. `drain --keep` writes the archive and deletes nothing; `drain --tank NAME` drains one tank.
A form shown to our camera instead of sent (`wizard:site+answers`, `../kiosk/replies.py`) is filed in the
same archive, `origin: "camera"`.

[`answers`](answers) reads it: `answers` (readable), `answers --csv > replies.csv` (a spreadsheet),
`answers --tank program`. No key, nothing changed. The drain's own log, one line an hour, is
`~/.local/state/fcpm/crew/drain.log`.

What it survives: losing `persistence.dat` (the archive is on the card's home, not the overlay, and the
crew line and keys come back with the home and the checkout). What it does not: losing the card itself.
Once a reply is drained, the archive is its only copy, until the log in Microsoft 365 holds it too.

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

FCPM's origin is [origin.local](../origin/PROFILE.md), released to it 2026-10-21: it takes GitHub in,
keeps the LAN's dev switch and paints its own screen. This machine is a client. `follow` points this
checkout's `origin` and every submodule at it (`fcpm-origin:/srv/origin/...`: `~/.ssh/config`'s `fcpm-origin`, the name
for its git account, by this machine's key, a line in [`../origin/KEYHOLDERS`](../origin/KEYHOLDERS)),
and `fcpm dev on|off` or the board's switch flips its dev.

The card's `card-origin` partition at `/srv/origin` is what this machine held until then: nothing
writes to it now. It stays mounted as a copy until the card is rebuilt.
