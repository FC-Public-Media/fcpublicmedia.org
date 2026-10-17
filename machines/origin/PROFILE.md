# origin

FCPM's git origin on its own box, so the origin does not leave with digitization's SD card. Today
it is the **standby**: digitization pushes every branch and tag here each minute (`../digitization/origin-standby`).
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
with the commit it names, each repository's size, and the box itself (system, kernel, processor,
memory, address, screen, load, free space, uptime, the kernel's clock). The page checks it ref by
ref against digitization's own origin and shows the evidence, not a verdict:

    origin.local                                                       FC Public Media  02:46
    FC-Public-Media                             23 in step with digitization · 23 with github
    fcpublicmedia.org         674c381  973 commits   9 branches             5.1M   1m
    pools                     ee2465d   75 commits     1 branch             344K   2d
    …
    HP t510 Thin Client                                           up 12m · 493M free of 845M
    Alpine Linux v3.24 · Linux 6.18.56-0-lts · VIA Eden X2 U4200 ×2 · 1.8G memory, 1.6G free
    10.209.1.133 · 1280x1024 · load 0.15 · clock synced · standby 02:45 · github 02:45

- one pane per owner, its bar counting how many repositories match digitization's and GitHub's;
- one line per repository, newest commit first (bold within the hour): main's hash on the box, the
  commits main holds, its branches (GitHub's `github/main`, intake's copy, is not counted) and tags,
  its size on the box, the age of main's last commit;
- a repository apart says how far and shows digitization's hash, `9 behind 674c381` (the box's main
  lacks 9 of our commits), `1 ref apart`, `not on the box`, on a muted wedge, red after five minutes.
  A main that differs from GitHub's says so in the same place (`github 2 ahead`, `3 not on github`);
- the box's own pane, its bar red with the trouble: the last standby run's complaint, the clock
  unsynchronized, the disk nearly full, intake unable to reach GitHub; red `not heard from` when the
  facts stop.

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
Take the stick out and power on: the standby fills the repositories within a minute or two.

**Promote it** (the card is gone): on each checkout, `git remote set-url origin git@origin.local:/srv/origin/<owner>/<repo>`.
