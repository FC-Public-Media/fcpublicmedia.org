# production

Production looks after the recordings after they land: the pools, their transcription, the episodes and
their release. Editing bay 1 (`EDIT2`) wears it. Crews and the supervisor: [`crews/README.md`](../README.md).

## Contract

What any machine wearing production owes, so a peer can step in beside it:

- It runs the lines in `crews/production/services`, each from a residency's menu.
- It stays in the building: LAN only, nothing to Cloudflare, no grants to anyone outside. `fcpm` tends it.
- Status is asked live; nothing it shows was written down at start.
- One supervisor, up before anyone signs in, with no window, nothing in Startup apps and no cost at sign-in.

## Service

- A scheduled task named `production`, triggered at the computer's start, run whether anyone is signed in or not. `fcpm crew install` registers it (administrator; `crews/crew.ps1`).
- It runs `crews/crew.py serve production` through uv, never a Python from PATH.
- It runs as this machine's user with no stored password (S4U): the local disks and the Drobo, not network shares or Credential Manager secrets. A share needs a stored credential.
- A task started with the computer has no desktop (session 0). The pool's every-minute task in the signed-in session runs the `desktop` lines (`crew.py desktop production`, from `machines/editing-bay-1/code/bin/pool.ps1`).

## Order

| line | when | from | what |
|---|---|---|---|
| `pools` | keep | `troves/pools` | the timeline, served on 8091 without its window |
| `episodes` | every 5m | `troves/pools` | admits each released episode to post as a take; held episodes are left alone |
| `post` | keep | `troves/post` | the post page on 8093 ([`troves/post/`](../../troves/post/README.md)) |
| `screen` | every 1m | `troves/kiosk-screen` | the rolling TV's page (a desktop line) |
| `remote-control` | held off | `crews/production` | the root's Remote Control server; uncomment its line in `services` to keep it |

`crews/production/post.yml` holds production's post steps: `enhance` is a door step (Adobe Podcast, by
hand) with a 7-day lease. Where the post partition is belongs to the machine (`machines/<profile>/post.yml`).
