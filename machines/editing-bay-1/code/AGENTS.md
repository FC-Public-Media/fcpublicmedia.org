> Block quotations are especially in the authority of the FC Public Media board.

# FCPM editing bay: the project

This directory is the project: an editing bay in Fort Collins Public Media's
studio, a `*-node` holding like the media node (the kiosk, `200-FCPANEDIT2`)
and synced with it. **Autumn calls this root `production`**: what goes on
when agents run here. The sticker says editing bay 1, and Windows answers to
`EDIT2`. That is not bay 2: the kiosk, once editing bay 2, is `200-FCPANEDIT2`,
and Autumn calls it `kiosk` (site repo `machines/README.md`, *What a machine is
called*). Sessions start here. Windows 11 Home, user `fcpub`. It is the strongest machine in the
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
> 5. Push when PR goals seem met or can be drafted
> 6. Reset .pr to main's version or none (with no ci)

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
| `bin/pool.ps1` | keeps the root's Remote Control server up: `status`, `pass`, `off`, `on`, `install`. See *Tending it* |
| `%LOCALAPPDATA%\editing-bay-1\` | the pool's `pool.log`, the server's `server.log`; later this bay's venv and scratch. Named for the profile |

No live checkout, and nothing long-running but the root's Remote Control server. A bay needs no `@<node>` branch
until it runs something that has to be rebased under it.

## How work moves

- **One branch per change**, made from `origin/main` with `bin/refs work`.
  Commit, push, then `gh pr create`. `gh` 2.101.0 is at
  `~/.local/bin/gh.exe` (the bay's record: `machines/editing-bay-1/bay/`),
  signed in. A shell that doesn't find it on PATH can use the full path.
  Autumn merges. Within 5 minutes the door rebases
  `media-node` onto main and restarts on the new code.
- **Every PR asks Autumn to review it** (Autumn, 2026-10-07). We push and
  open PRs as `fcpm-public`; she reviews as `tiliv`. Open each with
  `gh pr create ... --reviewer tiliv`, in any repository, drafts included,
  and add her (`gh pr edit N --add-reviewer tiliv`) to one opened without.
  Her one filter, "review requested", is then everything waiting on her,
  on the phone as on the desktop, without going repository by repository.
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
  - **A stack gets one worktree, not one per branch** (`gh stack`, pinned
    v0.1.1, 2026-09-26). Its metadata is per working tree, so make
    `work/REPO@<stack>` with `bin/refs work` and move between its layers
    inside it. A layer checked out in another worktree is invisible to it.
  - Each repo commits under its own `user.name`/`user.email`.
  - When the PR merges, `bin/refs done REPO BRANCH` and `bin/refs pull`.
    A worktree whose PR has merged is not reused: a commit made after the
    merge never lands.
  - This file is read from the mirror, through `~/code/CLAUDE.md`. Change
    it like any other file, in a worktree (`machines/editing-bay-1/code/
    AGENTS.md`). Never edit the root's own `CLAUDE.md` or `AGENTS.md`: they
    are pointers, and `fcpm install` puts them back.
- **How a session arrives is how it starts** (Autumn, 2026-10-05). The
  root keeps one thing up, a Remote Control server, and opens and names no
  session of its own (`--no-create-session-in-dir`). Each session is started from zero at claude.ai or
  the phone. A session starts no service, keeps no live checkout, and holds
  no long-running process. If it's closed, it picks back up from its
  worktree and its commits, and nothing revives it.
- **Push before telling Autumn a PR is ready.** Once a PR merges, a commit
  pushed after it never lands; open a new PR for it.
- **Other machines are reached outward only.** Code goes by commit
  (station-node mounts fcpublicmedia.org), media goes through the depot,
  and conversation goes by session message (`rodecaster` is capture on
  station-node). Nothing can connect *in* to this box.

## Tending it

- **`fcpm` is the one switch** (`machines/fcpm` in the site repo, 2026-09-26),
  the same in cmd and PowerShell once `fcpm install` has put it on PATH:
  `fcpm` (the watcher: what is going on, and a short menu), `fcpm check`, `fcpm refs ...`, `fcpm pool ...`,
  `fcpm runnables ...`, `fcpm screen ...`, `fcpm help`. When handing Autumn a step, hand her an
  `fcpm` verb, never a path, an interpreter or a choice of window. A step that
  needs one is a gap in `fcpm` to fill.
- `bin/refs pull` and `bin/refs status` keep the mirrors current.
- **Staying current is the pool's job, not an install** (Autumn, 2026-10-09).
  Each pass, when the mirror has moved, places what it carries
  (`machines/sync install`: this script, settings, PATH), and restarts the
  crew's supervisor if `crews/` or `troves/` moved under it. Any pull counts:
  a session's, the weekly task's, the watcher's. `pool.log` says
  `current: <commit> placed`.
- **`fcpm dev on`: GitHub reaches the bay by itself** (Autumn, 2026-10-09).
  With it on, each pass pulls the mirrors every 5 minutes (`bin/refs pull`,
  fast-forward only), and the step above places what merged. Nobody pulls.
  `fcpm dev off` leaves the weekly task and people to pull. `fcpm pool` shows
  it and the last pull, and `pool.log` says `dev: ... UPDATED` for each.
- Clear merged worktrees out of `work/`.
- **The pool** is `bin/pool.ps1`, run by the per-user task `editing-bay-1
  pool` at logon and every minute, with no window.
  - Each pass makes sure `claude remote-control --no-create-session-in-dir`
    is serving `~/code`, with no name. *Production* names the worktree
    (`work/fcpublicmedia.org@production`), never a session. A server started
    by hand in a terminal counts, and is left alone.
  - **Claude updates are when the server goes bad** (2026-10-09). An update
    swaps `claude.exe` under it and can revoke its sign-in, and it keeps
    running with no session able to reach it. So the pool bounces a server
    it started when the server is signed out (at once), and when it is older
    than the installed `claude.exe` (once calm for 15 minutes, as kiosk-1's
    door does). Its sessions end with it. `fcpm pool` says `current`, or why
    it is stale and what holds the bounce. `pool.log` has each change.
  - Nothing is revived, and no seat session is kept. That was tried twice,
    and it was not what Autumn asked for. A session that closes stays closed.
  - `fcpm pool` shows the task, the server and the sessions running.
    `fcpm pool off` is authoritative (Autumn, 2026-10-09): it ends every
    Remote Control server on this box, the pool's or one started by hand,
    with their sessions, keeps it off, and says `down` or the pid still up.
    `on` starts it again. `uninstall` removes the task.
  - The server needs `~/code` trusted first. It is.
  - Each pass also keeps the rolling TV's page up
    (`troves/kiosk-screen`, from the mirror): the wall in Edge, fullscreen,
    with a profile of its own. It uses the depot's copy when the depot
    answers, and a local render otherwise. `fcpm screen` shows it,
    `fcpm screen off|on` holds it off or lets it back, and
    `fcpm screen class|wall` switches between class mode and the wall.
    That Edge and the server are all that run between passes.
  - `fcpm screen`'s `kept` line says when the pool last kept the screen,
    from a heartbeat. If it says NO, the pool is not running: a change to
    the task's timing needs `fcpm pool install`.
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
