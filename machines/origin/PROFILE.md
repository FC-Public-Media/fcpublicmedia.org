# origin

FCPM's git origin on its own box, so the origin does not leave with digitization's SD card. Today
it is the **standby**: digitization pushes every branch and tag here each hour (`../digitization/origin-standby`).
It becomes the primary when it holds its own GitHub login; then remotes point here and intake runs here.

The job is the whole of it. Any box that boots Alpine can wear it; nothing here asks what the box is.
Today's: the HP t510 in the control rack ([`../thin-client/PROFILE.md`](../thin-client/PROFILE.md)).

| | |
|---|---|
| `names` | `linux Hostname origin`: `origin.local` (avahi) |
| system | Alpine, installed to the box's own disk, no desktop, DHCP, the room's clock by chrony. [`install`](install), from digitization |
| `fcpm` | management, by key only, with sudo. Its key: digitization's |
| `git` | pushes, `git-shell` only. Its keys: digitization's standby key; keyholders' when it is primary. `ssh git@origin.local init <owner>/<repo>` makes an empty repository; the standby uses it for new ones |
| repos | `/srv/origin/<owner>/<repo>`, bare, as on digitization. Nothing is rewritten or deleted (`receive.denyNonFastForwards`, `receive.denyDeletes`, for every repository on the box) |
| screen | tty1 is its leash ([`../leash.py`](../leash.py)): one `ssh -T` to digitization, where [`page.py`](page.py) paints it. In pixels: on a box that boots by BIOS, the largest VESA mode the firmware offers, and Terminus Bold. A keyboard login stays on Alt+F2 |
| root | locked; no password logins at all |

## The screen

The box keeps nothing but the repositories, so its screen is painted where the page is kept. The
leash sends up what [`facts.py`](facts.py) sees every 30 s: every branch and tag of every repository
with the commit it names, each repository's size, and the box itself. The page checks it ref by ref
against digitization's own origin and draws what is there, in as few words as it can. Its font is
built on the box by the outfit ([`../console-font.py`](../console-font.py), JetBrains Mono Bold at
14x28) with the blocks, our own icons (◉ commit, ⑂ branch, a tag), the activity squares and a gauge.

- a bar per owner, the repositories under it in name order, so a place on the screen keeps its
  meaning. The bar doubles as a status line: the crew's git runs on digitization too, so the page
  watches it and says the step on the right (`pools → origin.local` for the standby,
  `scanner ← github` for intake, `github …` while intake asks GitHub), and keeps the last one,
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
  Then its size on the box (`.2M`, `5.3M`, `37M`); ◉ and the commits main holds; a ⑂ per branch:
  first, in GitHub's blue, `github/main`, the one intake brings from GitHub; then ours, newest
  first, bright with work this week, grey when quiet, dark once merged into main;
  its last commit (the time today, the weekday this week, the date after, dimmer with age);
  `github`, dim when GitHub's main is ours, lit `github↓2` when two commits there have not come in,
  `github↑3` for three of ours not on GitHub (another remote gets its own word); a tag by name;
  dim at the right the box's hash of main;
- a repository apart sits on a muted wedge, red once the standby has had its run and five minutes
  more (the page reads the standby's pace from its log), with how far where a tag would be: `−9` (the box's main lacks 9 of ours), `~1` (a branch or tag differs), `∅` (not on the box);
- the bottom bar is the room's: the box's disk and memory as outlined gauges (the bar's yellow
  shows through for what is used, black for what is free) each followed by what is free in G
  (`.48`, `1.6`), its load (processes wanting the processor, averaged over a minute; it has two),
  and the time. It goes red with the trouble: the standby's complaint, or its silence for two of
  its runs, GitHub out of
  reach, the clock, a full disk; `— 3m` when the box stops being heard.

The grant is one line in digitization's `authorized_keys`, which `install` writes:

    restrict,command="TZ=America/Denver /usr/bin/python3 <checkout>/machines/origin/page.py" ssh-ed25519 … origin screen

The box pins digitization's host key. musl looks up no `.local` names, so the box's `ssh` asks avahi.

## Installing it

From digitization, with the box booted into Alpine's live system from the recovery stick: log in as
`root`, then `setup-interfaces -ar`, `setup-sshd openssh` and
`mkdir -p .ssh && wget -qO .ssh/authorized_keys https://github.com/tiliv.keys`. Then:

    machines/origin/install root@HOST DISK SERIAL     erases DISK, installs, outfits, powers off
    machines/origin/install fcpm@origin.local         outfits a running origin again; no disk

`DISK` is named and must answer to `SERIAL` (`none` if it reports none); a disk in use, like the
live system's own, is refused. Everything after the disk is [`outfit`](outfit), safe to run again.
Take the stick out and power on: the standby fills the repositories on its next run, within the hour.

**Promote it** (the card is gone): on each checkout, `git remote set-url origin git@origin.local:/srv/origin/<owner>/<repo>`.
