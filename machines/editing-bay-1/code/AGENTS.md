> Block quotations are especially in the authority of the FC Public Media board.

# FCPM editing bay: the project

This directory is the project: an editing bay in Fort Collins Public Media's
studio, a `*-node` holding like the media node (the kiosk, `200-FCPANEDIT2`)
and synced with it. This box answers to `EDIT2`; Autumn calls it Bay 1. Sessions
start here. Windows 11 Home, user `fcpub`. It is the strongest machine in the
studio (i7-13700KF, 24 threads, 32 GB, RTX 4080, 2 TB on `D:`), so it takes
heavy work when media-node or station-node grants it. No grants have been
placed yet.

> From the board:
> 
> You're on the FCPM Secretary (Autumn's) credentials as we move into
> looking at what board-provisioned credentials can/should/must do.
> 
> She (I) sits on the boards of nonprofits: NCCV, FCPM, and potentially FCR
> with another FCPM board member. Her open-source work is FCCN-ANTIBODY.
> She operates a static host via Cloudflare SaaS built geographically.
>
> station-node is discoverywritten.com's version of your media-node.
> You are fcpublicmedia.org's LAN services. We have a mission to leave
> behind the durable malleable A11Y tools that reach workflow itself
> for a non-technical board into the future, by their superceding authority.
>
> station-node runs an origin/ at their root, which we intend to do too.
> The conceipt of the origin is that we will be managing physical-space
> pull request branches from QR comms, and GitHub will be a satellite
> we merge to us and we fast-forward them.
> 
> Bylaws allow 2 terms of 2 years per. Her first began September 2025.
>
> station-node vacate date: TBD


## Working in git

> 0. Use worktrees via refs/
> 0. Eagerly consume ALL submodule updates, but keep bare things bare
> 0. Test tracked PRs when new turns start.
> 1. Feature branch
> 2. Make .pr (ignored machine-globally) contain the plan progression
> 3. Commit as we go
> 4. Revise .pr steps ahead as we go; the progressive goal is visible and malleable
> 5. Push 
> 6. Destroy .pr when you've sent the equivalent to your origin PR

## What we own

- **Nothing of our own yet.** fcpublicmedia.org is media-node's to run; here
  it is read in `refs/` and changed in `work/`. Which profile this box wears
  (`machines/editing-bay-1`, with a `windows ComputerName EDIT2` line in its
  `names`) is Autumn's call and not yet committed.
- **Proposed, not decided: capture for digitization.** The capture hardware,
  lossless masters on `D:`, per-source MKV splitting, and transcodes. Station-node
  keeps arming, presence and the ledger. Waiting on Autumn, HDCP testing, and a
  home for masters (the depot's partitions are ~3.6 GiB each).

## Where things are

| | |
|---|---|
| `refs/` | read-only mirrors of every repo we read. **Never commit here.** |
| `work/REPO@BRANCH` | a worktree per branch. Make one with `bin/refs work REPO BRANCH`, and remove it with `bin/refs done REPO BRANCH` once it's merged |
| `bin/refs` | media-node's script. Diverges from media-node by one line: `REF` points at `refs/`, which is this bay's name for it (2026-09-25) |
| `bin/pool.ps1` | this bay's session pool: `status`, `pass`, `revive`, `pin`, `install`. See *Tending it* |
| `%LOCALAPPDATA%\editing-bay-1\` | the pool's `sessions.json` and `pool.log`; later this bay's venv and scratch. Named for the profile, pending Autumn |

No live checkout and no long-running service: a bay needs no `@<node>` branch
until it runs something that has to be rebased under it.

## How work moves

- **One branch per change**, made from `origin/main` with `bin/refs work`.
  Commit, push, then `gh pr create`. `gh` 2.101.0 is at
  `~/.local/bin/gh.exe` (the bay's record: `machines/editing-bay-1/bay/`),
  signed in. A shell that doesn't find it on PATH can use the full path.
  Autumn merges. Within 5 minutes the door rebases
  `media-node` onto main and restarts on the new code.
- **Commit as we go** (Autumn, 2026-09-25). On a work branch, commit each
  step as it lands rather than holding a pile of changes. Committing is
  local and cheap; pushing and opening the PR are still separate, and a
  draft Autumn wants to read first stays unpushed until she says so.
  This box has no global git identity and gets none: each repo in `refs/`
  carries `user.name`/`user.email` in its own config, set the first time
  it is committed from.
- **Worktrees** (Autumn, 2026-09-25):
  - `refs/` is never worked in. Every change gets `work/REPO@BRANCH`, and
    only one session works in a given worktree. Several sessions can share
    this `~/code` at once, so a branch name should say what it is for.
  - Each repo commits under its own `user.name`/`user.email`.
  - When the PR merges, `bin/refs done REPO BRANCH` and `bin/refs pull`.
    A worktree whose PR has merged is not reused: a commit made after the
    merge never lands.
  - Shared files outside `refs/` and `work/` (this one, `CLAUDE.md`) belong
    to every session here. Re-read before writing, and tell the others
    what changed.
- **A pool, not a service.** Each install site keeps sessions and
  worktrees available, but idle until called for. A session here waits to
  be asked. It starts no service, keeps no live checkout, and holds no
  long-running process. If it's closed or restarted, it resumes from its
  worktree and its commits, not from anything still running.
- **Push before telling Autumn a PR is ready.** Once a PR merges, a commit
  pushed after it never lands; open a new PR for it.
- **Other machines are reached outward only.** Code goes by commit
  (station-node mounts fcpublicmedia.org), media goes through the depot,
  and conversation goes by session message (`rodecaster` is capture on
  station-node). Nothing can connect *in* to this box.

## Tending it

- `bin/refs pull` and `bin/refs status` keep the mirrors current.
- Clear merged worktrees out of `work/`.
- **The pool** is `bin/pool.ps1`, run by the per-user task `editing-bay-1
  pool` at logon and every 5 minutes, with no window. Each pass snapshots
  what `claude agents --json` lists.
  - On the first pass after a logon, it revives every session from the
    snapshot under its own id, in the background with Remote Control, like
    media-node's `door.py sessions`.
  - Then, if nothing is running in `~/code`, it starts one idle background
    session there named `bay1`.
  - Later passes revive nothing, so a session closed during the day stays
    closed.
  - The clock is the logon, not the boot, because Fast Startup keeps the
    boot time old across a shutdown.
  - `bin\pool.ps1 status` shows the pool, and `pin in|out <id|name>` always
    or never brings a session back. `uninstall` removes the task.
  - A background session needs its folder trusted first. `~/code` is.
- Peers over Remote Control: `kiosk` (media-node) and `digitization`
  (station-node). They appear in the session list only while this session has
  Remote Control on.
- **The depot is not reachable from here yet.** Ethernet is `10.1.10.x` and the
  Wi-Fi is the guest network (`192.168.3.x`); the depot is `10.209.1.1`, on
  neither. Media-node reaches it wired as `10.209.1.x`. How this bay joins is
  Autumn's call.
- Surprises are media-node's to log (`machines/kiosk-1/gotcha`), or this
  profile's own log once it has one.

## Building and testing here

Mostly not provisioned. It has git 2.55, winget 1.29, and Claude Code at
`~/.local/bin`. The `python` on PATH is a Store stub. **uv 0.12.19** is
installed per-user by winget (2026-09-26; hash verified, Authenticode valid,
signed by *OpenAI OpCo, LLC*). Python comes from it: `uv run --no-project
--python 3.12 --with pyyaml ...` runs `door.py` here, and it rendered the wall
for the roller. Shells started before that need the full path,
`%LOCALAPPDATA%\Microsoft\WinGet\Packages\astral-sh.uv_Microsoft.Winget.Source_8wekyb3d8bbwe\uv.exe`.
winget here can also install Node LTS, gh and ffmpeg directly; check their
signatures either way. `core.autocrlf` is `true` system-wide (Git for Windows' default) and
`false` for `fcpub` (2026-09-25), so checkouts arrive LF.

## Rules that bite

- **We commit source; station-node builds and deploys.** Local build
  viability means jekyll-enough in a browser. No Ruby, no real Jekyll.
- **Secrets never go in files or repos.** Passwords go in Credential Manager,
  and the Microsoft 365 key goes in the certificate store (non-exportable).
  The site repo is public, so **no personal data in commits**, and that
  includes names from bookings.
- The board's wording is authoritative (fcpublicmedia.org `AGENTS.md`).
- Windows bites: CRLF from generators, Git Bash rewriting `/flags` and
  `a:b` paths (`MSYS_NO_PATHCONV=1`), and tool calls eating backslashes in
  UNC paths. Read `GOTCHAS.log` first.
