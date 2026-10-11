# kiosk

The kiosk looks after the front door: the screens and the roller TV's page, check-in, and the pickup
point, where digitization's grants are redeemed. The old editing bay 2 (`200-FCPANEDIT2`) wears it
([`PROFILE.md`](PROFILE.md)). Jobs and the supervisor: [`machines/README.md`](../README.md); screens
and content: [`docs/kiosk.md`](../../docs/kiosk.md).

## Contract

What any machine wearing the kiosk owes, so a peer can step in beside it:

- It keeps the door on :8080 and one screen per panel in `node.yml`, and writes the wall to the depot share.
- It stays in the building and reaches out only: code by commit, media through the depot, talk by session message. Nothing connects in. `fcpm` tends it.
- Status is asked live (`door.py`, `door.py screens`, `door.py server`); nothing it shows was written down at start.
- One supervisor, with no window and nothing in Startup apps.
- It never asks GitHub on a timer: only when asked (`fcpm pull`), once a week (`fcpm weekly`), or while `fcpm dev on`. A LAN origin it may poll.

## Service

The README's service is a task from the computer's start, as the user via S4U, running `crew.py serve`.
Registering one needs an administrator, and the kiosk has none. Its degradation:

- A per-user scheduled task, `media-node door`, at sign-in and every five minutes (`door.py startup --install`, no administrator). It runs `door.py supervise` from the live checkout (`work/fcpublicmedia.org@media-node`) with the venv's `pythonw`, never a Python from PATH.
- The five-minute trigger is the restart: a named mutex (`Local\media-node-supervise`) sends a second supervisor away, so a fallen one is back within five minutes.
- It starts at sign-in, not at the computer's start: after a reboot nothing runs until somebody signs in (asked of IT). What it keeps needs the desktop anyway.
- Its order is the door's own, in `door.py` and `node.yml`, not a `services` file: `crew.py` does not run here.

Log: `%LOCALAPPDATA%\media-node\door.log`.

## Order

| job | what it does |
|---|---|
| bounce | `serve` exits 75 when the checkout's commit moves; `supervise` restarts it; pages reload on `/revision` |
| pull | every 5 min, rebases `media-node` onto `origin/main` as the mirror has it (`fcpm pull` and `fcpm weekly` move it); fetches first only when origin is not GitHub, or while `fcpm dev on`; a dirty tree or a conflict is left as it was |
| screens | every 30 s, one Edge kiosk per panel in `node.yml`, profile under `%LOCALAPPDATA%\media-node\screens\`: missing, astray, silent 120 s or moved is relaunched; covered is raised; none while a monitor is gone, or while stepped aside (a page's Minimize, until 10 min without input) |
| depot | scans the router's shares every 15 s; files are `declared` (a `.sha256` beside), `arriving` or `unwitnessed`; the index stays in memory |
| wall, turn | the wall, rewritten every 60 s to the depot share; `/turn/` is its shell on a panel here |
| server | every minute keeps `claude remote-control --no-create-session-in-dir` at `~/code` (output `server.*`); bounces it onto a newer `claude.exe` after 15 calm minutes; a killed one holds `~/code` a few minutes ("already served"); `door.py server` |
| sessions | starts none; snapshots `claude agents --json` to `sessions.json`, a record only; `door.py sessions` |
| camera | `door.py camera arm`, or the desk's button: a headless Edge reads a `wizard:kiosk+lights` reply; lights keep the screens awake |
| Dropbox | `TO DROPBOX` goes up to `dropbox.to`, removed once Dropbox holds the same bytes; off until `door.py dropbox link` |
| HELO | sets the AJA HELO's clock from this one when over 90 s out, never while it records |
| TI-89 | serves the runner from `ref/ti-89`, fast-forwarded with the pulls, by the same rule; the ROM only to this box |

When the LAN origin answers ([`digitization`](../digitization/PROFILE.md)), the mirrors' `origin` is
pointed there and the door polls it every five minutes, nothing else changed.
