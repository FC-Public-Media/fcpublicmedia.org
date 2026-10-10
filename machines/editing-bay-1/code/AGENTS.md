> Block quotations are especially in the authority of the FC Public Media board.

# FCPM editing bay: the project

This directory, `~/code`, is the project; sessions start here. Autumn calls it `production`: editing
bay 1 by sticker, `EDIT2` to Windows (11 Home, user `fcpub`). The kiosk (media-node) is `200-FCPANEDIT2`.

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

## Working here

- Never work or commit in `refs/`. Each change gets `work/REPO@BRANCH` from `bin/refs work REPO
  BRANCH` (off `origin/main`), one session per worktree, its branch named for its purpose. A `gh stack`
  gets one worktree, `work/REPO@<stack>`, and its layers are switched inside it.
- Commit each step as it lands; a draft Autumn wants to read first stays unpushed until she says. Push
  before telling her a PR is ready. Once it merges: `bin/refs done REPO BRANCH` and `bin/refs pull`;
  never reuse the worktree, and put any later commit in a new PR.
- Open every PR, drafts and any repo included, with `--reviewer tiliv` (`gh pr edit N --add-reviewer
  tiliv` if missed). We push as `fcpm-public`; `gh` is `~/.local/bin/gh.exe`. Autumn merges; within
  5 minutes the door rebases `media-node` onto `main`. No global git identity: each repo has its own.
- Change this file in a worktree (`machines/editing-bay-1/code/AGENTS.md`); it is read from the mirror.
  Never edit the root's `CLAUDE.md` or `AGENTS.md`: `fcpm install` restores them.
- A session starts no service, keeps no live checkout and runs nothing long; nothing revives it.
- Reach other machines outward only: code by commit, media through the depot, talk by session
  message. Peers: `kiosk` (media-node), `digitization` (station-node, where `rodecaster` captures).
- Hand Autumn an `fcpm` verb, never a path, interpreter or window; a step that needs one is a gap in
  `fcpm` to fill. Sessions use `bin/refs` directly. Log surprises with `machines/kiosk-1/gotcha`.
- The pool (`bin/pool.ps1`, task `editing-bay-1 pool`) places what the mirror moves to and keeps the
  root's server and the rolling TV up (`%LOCALAPPDATA%\editing-bay-1\pool.log`). `fcpm screen` saying
  `kept: NO` means it is not running; `fcpm pool off` ends every Remote Control server here. More:
  `docs/station.md`. The depot (`10.209.1.1`) is unreachable from here; joining is Autumn's call.
- We commit source; station-node builds and deploys. Build only with jekyll-enough in a browser.
- Secrets never go in files or repos (Credential Manager; the certificate store for the Microsoft 365
  key). The site repo is public: no personal data, names from bookings included.
- The board's wording is authoritative. `python` is the Store stub: use `uv run --no-project --python
  3.12 --with pyyaml ...`. Windows bites (read `GOTCHAS.log` first): CRLF from generators, Git Bash
  rewriting `/flags` and `a:b` (`MSYS_NO_PATHCONV=1`), tool calls eating backslashes in UNC paths.
