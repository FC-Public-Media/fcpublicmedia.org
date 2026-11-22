# origin

FCPM's canonical git origin, on its own box (decided 2026-10-21: digitization released it). The box
does the work itself: it takes GitHub's main into every repository ([`intake`](intake)), keeps the
LAN's dev switch ([`dev`](dev)), and paints its own screen. Every workstation is a client: it
follows main from here and pushes here through its [`door`](door), by a key in [`KEYHOLDERS`](KEYHOLDERS). Until FCPM has another box, this one also wears the
[`keychain`](../keychain/PROFILE.md), and the library will join them: the control box, what every
other machine gives up to the controller.

The job is the whole of it. Any box that boots Alpine can wear it; nothing here asks what the box is.
Today's: the HP t510 in the control rack ([`../thin-client/PROFILE.md`](../thin-client/PROFILE.md)).

| | |
|---|---|
| `names` | `linux Hostname origin`: `origin.local` (avahi) |
| system | Alpine, installed to the box's own disk, no desktop, DHCP, the room's clock by chrony. [`install`](install), from digitization |
| `fcpm` | management, by key only, with sudo. Its key: digitization's |
| `git` | the repositories and intake. Every key it takes is forced through [`door`](door) (from #315), written from [`KEYHOLDERS`](KEYHOLDERS), which the box rereads from its own main every minute, so a key is a line by merged PR. A keyholder's remote is `git@origin.local:<owner>/<repo>`: every repository fetches and takes a push, `main` included (fast-forward only: the repositories refuse rewriting); in one that lives on GitHub only `github/*` is intake's (`door-hooks/pre-receive`); any other branch or tag waits here, in view, for GitHub; `hear main` answers with one line when any repository's main next moves (a push, or intake), or with nothing after five minutes, so a follower waits instead of asking (digitization's `follow`); `init <owner>/<repo>` is the secretary's; `dev on\|off\|status` is anyone's. `look`, `land` and `hold` are traffic's (below). Each action goes to `/srv/origin/.door/actions.ndjson`. Tests: `bin/test_origin_door.py` |
| intake | [`intake`](intake), as `git`, every minute by cron ([`run-intake`](run-intake), log `/var/log/fcpm/intake.log`). It paces itself to the clock: **the beat**, one pass in each ten minutes (:00, :10, :20), so anyone can be told "every ten minutes on the clock". GitHub is asked on the beat while dev is on; off, weekly, and the beat goes on without it (landed branches, below); `--now` whenever. GitHub's main only, one GraphQL query for all, into our main, which keyholders push; behind: fast-forward; ahead: left alone (relay carries it out); both moved: a clean merge, by our main's own `.gitattributes` (so [`.issues`](../../docs/issues.md) keeps both sides' lines), or a conflict recorded in `/srv/origin/.intake/state.json` with main untouched. Before GitHub's main is taken, how it is ahead of ours is read and kept with the take (`screen` in `state.json` and `actions.ndjson`: commits, files, bytes, the largest file, each pin moved): a reading, which holds nothing back yet. A new repository on GitHub under FC-Public-Media gets its bare repository here by itself; FCCN-ANTIBODY's are the ones already here. A repository GitHub lacks began here and is left alone. Signed in to GitHub as whoever approved [`github-login`](github-login) |
| dev | the LAN's switch, `/srv/origin/.intake/dev`, through the door: `fcpm dev on\|off` from a workstation, or the board's switch |
| kept | every beat, after the orders: each branch [`KEPT`](KEPT) names (read from this box's own main, by merged PR) takes in its repository's main: a fast-forward when it holds nothing of its own, else a clean merge by its own `.gitattributes`, as a commit of the origin's. One that collides is said so and left alone. Landed never lets a kept branch go. `kept` through the door says how each fared on the last beat (`fcpm keep`) |
| landed | every beat, in each repository that lives on GitHub too: a branch whose work main already holds is let go by the origin itself. **merged**: main holds its last commit; **spent**: merging it into main would change nothing (a squash), and its last commit is kept at `refs/landed/<branch>` so nothing is lost. Its record is kept first, one commit on `retain/origin` in fcpublicmedia.org: `branches/<owner>/<repo>/<branch>/origin.scopes`, flat lines ([workshed.md](../../docs/workshed.md#scopes)): the branch, its last commit, how it landed, the merge that brought it in and when, GitHub's number for it when the merge says one, its commits, when it was let go. Never `main`, `github/*`, the library's branches, a branch sitting on main's own commit (just cut), or one in a repository that began here (broadcast's branches are looks to switch between). No record kept, nothing removed. A name pushed again is a branch again. Each is a line in `actions.ndjson` (`state: landed`). Machines learn it as they fetch: [workshed.md](../../docs/workshed.md) |
| traffic | the origin's face for merging and issues: there are no pull requests, only branches and each repository's [`.issues`](../../docs/issues.md). `look [owner/repo]` through the door answers with everything here in one JSON reading ([`traffic.py`](traffic.py)): each repository's main, its tape, and every branch with its last commit, how far it is ahead of main and behind, whether it lands clean or collides (and on which files), and the `.issues` lines it brings; then the orders waiting, in turn, and the last ones done. What a merge would do is kept by main and tip in `.intake/look.json`, so a look costs little. `land <owner>/<repo> <branch> <commit>` is a traffic order: that branch, at the commit it was seen at, lands in main on the next beat; `hold` takes it back. Each beat, before landed, intake lands the orders in the order given, each on the main the one before left, by main's own `.gitattributes`, as a merge commit saying who ordered it; landed then lets the branch go and the relay carries main out, on the same beat. One that collides, or moved after it was ordered, is said so and main is left alone. Never main, `github/*` or the library's branches. The orders are a tape, `.intake/orders.ndjson`, appended to and never rewritten. Helm's `/origin/` page shows the reading and gives the orders (by this machine's key, from the page itself). Tests: `bin/test_origin_traffic.py` |
| relay | the origin's mode, `/srv/origin/.intake/relay`, through the door (`fcpm relay on\|off`). **On** (a full relay): on each beat that asks GitHub it carries out to GitHub `main` wherever ours is ahead of GitHub's, and each branch and tag a keyholder pushed through the door since the last pass, fast-forward only, never forced, never `github/*`, never a repository that began here, never the library's branches (`retain/*`, `library`, `librarians`: `LAN_ONLY`, recorded as `lan only`); one GitHub will not fast-forward (a rebase) is recorded as diverged in `actions.ndjson` and left for a person. Any other refusal is recorded as an error and tried again each pass. The origin never asks for GitHub's `workflow` scope: a branch that changes `.github/workflows` is refused, and workflows change on GitHub, by hand. Only what came through the door is carried, so a branch GitHub merged and deleted is not brought back. **Off** (LAN-only, or an outage): it pulls; what is pushed waits here. Tests: `bin/test_origin_relay.py`. Pushed to GitHub as the account `github-login` signed in |
| repos | `/srv/origin/<owner>/<repo>`, bare, as on digitization. Nothing is rewritten, and nobody's push deletes (`receive.denyNonFastForwards`, `receive.denyDeletes`, for every repository on the box): only the origin lets a branch go, once main holds it (landed) |
| screen | tty1 is its leash ([`../leash.py`](../leash.py)) with [`page.py`](page.py) on the box itself, from its own repositories and intake's log; no other machine holds it. In pixels: on a box that boots by BIOS, the largest VESA mode the firmware offers, and Terminus Bold. A keyboard login stays on Alt+F2 |
| root | locked; no password logins at all |

## The screen

The leash hands the page what [`facts.py`](facts.py) sees every 30 s: every branch and tag of every repository
with the commit it names, each repository's size, and the box itself. The page checks it ref by ref
against the origin and draws what is there, in as few words as it can. Its font is
built on the box by the outfit ([`../console-font.py`](../console-font.py), JetBrains Mono Bold at
14x28) with the blocks, our own icons (◉ commit, ⑂ branch, a tag), the activity squares and a gauge.

- a bar per owner, the repositories under it in name order, so a place on the screen keeps its
  meaning. The bar doubles as a status line: intake's git runs on the box, so the page watches it
  and says the step on the right (`scanner ← github` while intake fetches, `github …` while it
  asks GitHub, `pools ← push` for a push from a workstation), and keeps the last one,
  dimmer, with its time. The repository being worked on flickers softly in blue underneath;
- per repository: its history, one centred square per block that grows with commits a day, the
  same rule in every block (a period under 1 a day, a small square from 1, a square from 3, a full
  one from 8; empty where there were none). The seven days ending today are the strongest, in the
  colour of the repository's kind, which it declares by the file it carries (`show.yml` a show,
  pink; `instrument.yml` an instrument, orange; `gear.yml` gear, green; `residency.yml` an engine,
  violet; the rest paper). Ten blocks behind them reach back about seven months, each step longer,
  and cool as they recede: the kind's colour, then blue, then deep blue. Full squares fill the
  cell, so full days meet into a bar; inside a run every second one loses its left column, so the
  run still counts, and a lone one always shows what full looks like.
  Then its size on the box (`.2M`, `5.3M`, `37M`); ◉ and the commits main holds; a ⑂ per other
  branch, newest first, bright with work this week, grey when quiet, dark once merged into main;
  its last commit (the time today, the weekday this week, the date after, dimmer with age);
  `github`, dim when GitHub's main is ours, lit `github↓2` when two commits there have not come in,
  `github↑3` for three of ours not on GitHub (another remote gets its own word); a tag by name;
  dim at the right the box's hash of main;
- a repository apart sits on a muted wedge, red after five minutes, with how far where a tag would
  be: `−9` (the box's main lacks 9 of ours), `~1` (a branch or tag differs), `∅` (not on the box);
- the bottom bar is the room's: the box's disk and memory as outlined gauges (the bar's yellow
  shows through for what is used, black for what is free) each followed by what is free in G
  (`.48`, `1.6`), its load (processes wanting the processor, averaged over a minute; it has two),
  and the time. It goes red with the trouble: intake's complaint or silence, GitHub out of
  reach, the clock, a full disk.

musl looks up no `.local` names, so the box's `ssh` asks avahi.

## Installing it

From digitization, with the box booted into Alpine's live system from the recovery stick: log in as
`root`, then `setup-interfaces -ar`, `setup-sshd openssh` and
`mkdir -p .ssh && wget -qO .ssh/authorized_keys https://github.com/tiliv.keys`. Then:

    machines/origin/install root@HOST DISK SERIAL     erases DISK, installs, outfits, powers off
    machines/origin/install fcpm@origin.local         outfits a running origin again; no disk

`DISK` is named and must answer to `SERIAL` (`none` if it reports none); a disk in use, like the
live system's own, is refused. Everything after the disk is [`outfit`](outfit), safe to run again.
Take the stick out and power on. Then sign its git account in to GitHub:

    machines/origin/github-login                     a window on this screen shows GitHub's code

and fill it from GitHub the first time with `ssh fcpm@origin.local sudo -u git /bin/sh /usr/local/lib/fcpm/run-intake --now`.
A workstation's checkout follows it with `git remote set-url origin git@origin.local:/srv/origin/<owner>/<repo>`;
digitization's `follow` does that, and every submodule, by itself.

## Taking a project out

How NCCV-OPINION came out (#401). For an owner, or for some of an owner's repositories:

1. Look first. In each of its repositories, `main` = `github/main` and there are no other refs, and
   `/srv/origin/.intake/carry.json` has nothing pending for it. Then GitHub holds all of it, and removing loses nothing.
   A repository with no `github` remote began here: removing it is losing it.
2. Look at its submodules. An engine that only this project calls on goes too. One that FCPM's own repositories
   also call on stays.
3. Take it out of [`intake`](intake)'s `KEEP`, by PR, or intake makes it again from GitHub.
4. Install that intake: `machines/origin/install fcpm@origin.local` after the merge, or only that file before it.
5. Remove it as `git`, under intake's lock:
   `ssh fcpm@origin.local sudo -u git flock /srv/origin/.intake/lock rm -rf /srv/origin/<owner>[/<repo>]`.
6. `ssh fcpm@origin.local sudo -u git /usr/local/lib/fcpm/intake --now`, then check: the directory has not come back,
   and `.intake/state.json` does not name it.
7. Do the same to any other copy (digitization's old `/srv/origin`).
8. Search the checkout for the name. Whatever reads from the origin goes too. Whatever reads from GitHub
   (a static site's `export_from: github`, a keychain group) stays until someone says otherwise.
