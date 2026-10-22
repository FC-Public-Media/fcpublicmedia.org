# origin

FCPM's canonical git origin, on its own box (decided 2026-10-21: digitization released it). The box
does the work itself: it takes GitHub's main into every repository ([`intake`](intake)), keeps the
LAN's dev switch ([`dev`](dev)), and paints its own screen. Every workstation is a client: it
follows main from here and pushes here through its [`door`](door), by a key in [`KEYHOLDERS`](KEYHOLDERS). One job on this box:
nothing else is put on it.

The job is the whole of it. Any box that boots Alpine can wear it; nothing here asks what the box is.
Today's: the HP t510 in the control rack ([`../thin-client/PROFILE.md`](../thin-client/PROFILE.md)).

| | |
|---|---|
| `names` | `linux Hostname origin`: `origin.local` (avahi) |
| system | Alpine, installed to the box's own disk, no desktop, DHCP, the room's clock by chrony. [`install`](install), from digitization |
| `fcpm` | management, by key only, with sudo. Its key: digitization's |
| `git` | the repositories and intake. Every key it takes is forced through [`door`](door) (from #315), written from [`KEYHOLDERS`](KEYHOLDERS), which the box rereads from its own main every minute, so a key is a line by merged PR. A keyholder's remote is `git@origin.local:<owner>/<repo>`: every repository fetches and takes a push, but in one that lives on GitHub `main` and `github/*` are intake's (`door-hooks/pre-receive`, #318); any other branch or tag waits here, in view, for GitHub; `init <owner>/<repo>` is the secretary's; `dev on\|off\|status` is anyone's. Each action goes to `/srv/origin/.door/actions.ndjson`. Tests: `bin/test_origin_door.py` |
| intake | [`intake`](intake), as `git`, every minute by cron ([`run-intake`](run-intake), log `/var/log/fcpm/intake.log`). It paces itself: GitHub every 10 minutes while dev is on, weekly while off, `--now` whenever. GitHub's main only, one GraphQL query for all; behind: fast-forward; ahead: left alone; both moved: a clean merge, or a conflict recorded in `/srv/origin/.intake/state.json` with main untouched. A new repository on GitHub under FC-Public-Media or NCCV-OPINION gets its bare repository here by itself; FCCN-ANTIBODY's are the ones already here. A repository GitHub lacks began here and is left alone. Signed in to GitHub as whoever approved [`github-login`](github-login) |
| dev | the LAN's switch, `/srv/origin/.intake/dev`, through the door: `fcpm dev on\|off` from a workstation, or the board's switch |
| repos | `/srv/origin/<owner>/<repo>`, bare, as on digitization. Nothing is rewritten or deleted (`receive.denyNonFastForwards`, `receive.denyDeletes`, for every repository on the box) |
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
