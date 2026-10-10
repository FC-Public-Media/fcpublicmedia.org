# FCPM media node: the project

This directory is the project: Fort Collins Public Media's media node.
Sessions start here. Windows 10, IT-managed, **no administrator**.

**Autumn calls this root `kiosk`.** It answers to every one of these, and they
all mean this box (site repo `docs/machines/README.md`, *What a machine is called*):

| | |
|---|---|
| `kiosk` | what Autumn calls it, and the name its Claude sessions carry |
| the media node | what it is when it runs fcpublicmedia.org's services, the way station-node runs discoverywritten.com's |
| `kiosk-1` | its profile in the site repo, `machines/kiosk-1` |
| `200-FCPANEDIT2` | what Windows answers to, and `200-fcpanedit2.local` on the LAN |
| the old editing bay 2 | what it was before it became the kiosk. It is not today's bay 2 |

**`EDIT2` is not this box.** It is editing bay 1, which Autumn calls
`production`. Both Windows names end in `EDIT2`, so check `$env:COMPUTERNAME`
before trusting anyone's guess, including your own.

## What we own

- **fcpublicmedia.org** (GitHub `FC-Public-Media/fcpublicmedia.org`, public).
  The site lives in `site/`. The node's own pieces are in `machines/kiosk-1/`:
  `door.py`, `node.yml`, `GOTCHAS.log`, and this file.
- **enhance** (`FC-Public-Media/enhance`, private). Recordings go out to the
  enhance suite and come back enhanced or stemmed. It is mounted in the site
  repo at `.enhance-engine`. The capture model is in `docs/CAPTURE.md`.
- **The depot**: the router's partitions at `\\10.209.1.1`. The partitions
  are a hand-off: in at `TO ENHANCE`, out at `PODCAST`. Everything in between
  is held here, in `%LOCALAPPDATA%\media-node\library\`.
- **The cloud wing**: Microsoft 365's app folder (`Apps/FC Public Media Booking`
  in the organization's SharePoint): a library backend, like the file store or
  IPFS. It is content-addressed: bytes live at `blobs/sha256/<2 hex>/<digest>`,
  and the `library` branch maps library paths to digests. It can't be listed,
  and doesn't need to be. The node mints pre-signed upload and download links
  per digest with `machines/kiosk-1/m365-token.ps1`.
- **The door**: the pages on :8080 (kiosk and depot panels), and the TV wall
  it writes to `\\10.209.1.1\DIGISTATION\.wall\`.

## Where things are

| | |
|---|---|
| `ref/` | read-only mirrors of every repo we read. **Never commit here.** Production calls its own `refs/` |
| `work/REPO@BRANCH` | a worktree per branch. Make one with `bin/refs work REPO BRANCH`, and remove it with `bin/refs done REPO BRANCH` once it's merged |
| `work/fcpublicmedia.org@media-node` | **the live checkout.** The door runs from it. Never edit here |
| `work/fcpublicmedia.org@kiosk` | **the people's working copy**, once somebody makes it with `fcpm`. It is for whoever sits down here to tinker and send their edits up. A session leaves it alone unless asked |
| `bin/refs` | the mirrors and worktrees. Carried in this profile as `code/bin/refs` |
| `%LOCALAPPDATA%\media-node\` | the venv, `door.log`, the screens' browser profiles, and the library wing |

## How work moves

- **One branch per change**, made from `origin/main` with `bin/refs work`.
  Commit, push, then `gh pr create`. `gh` is in `~/.local/bin`, with its
  login in the keyring. Autumn merges. Within 5 minutes the door rebases
  `media-node` onto main and restarts on the new code.
- **Never open a PR from `media-node` itself.** The door rebases it, and a
  pushed `media-node` is rewritten under the PR.
- **Push before telling Autumn a PR is ready.** Once a PR merges, a commit
  pushed after it never lands; open a new PR for it. Autumn merges within
  minutes, so check `gh pr view <n> --json state` just before each push to an
  existing PR branch.
- **This file is read from the mirror**, through `~/code/CLAUDE.md`. Change it
  like any other file, in a worktree (`machines/kiosk-1/code/AGENTS.md`).
  Never edit the root's own `CLAUDE.md` or `AGENTS.md`: they are pointers.
- **Other machines are reached outward only.** Code goes by commit
  (station-node mounts fcpublicmedia.org), media goes through the depot,
  and conversation goes by session message (`rodecaster` is capture on
  station-node). Nothing can connect *in* to this box.

## Tending it

- `bin/refs pull` and `bin/refs status` keep the mirrors current. A pull
  brings this file with it.
- `door.py startup` checks the logon task, `door.py screens` checks the
  panels, `door.py sessions` lists the Claude sessions, and `door.py` alone
  checks the door. The log is `%LOCALAPPDATA%\media-node\door.log`.
- **No seat** (Autumn, 2026-10-09). The door no longer keeps a `startup`
  session. Sessions arrive through the root's Remote Control server, as on
  production (site repo `docs/machines/README.md`). The door keeps that server up,
  and bounces it onto a new Claude after 15 calm minutes. `door.py server`
  says whether it is current and what holds the bounce.
- **The weekly pull is the gate, and sessions here run it** (Autumn,
  2026-10-05). This box has no keyboard or mouse. It is out of people's reach,
  and its ports are not for playing with; people meet it only through its
  screens. So nobody sits down here to type `fcpm`. The task `fcpm weekly`
  (registered 2026-10-05) brings in the latest once a week, so the box sets
  the stage for what the studio runs that week. Keep it registered
  (`machines/watch weekly install`). If it can't run, a session does the pull
  itself. The steps other machines leave to a person at the desk are a
  session's here, when Autumn asks. Don't hedge them back to her.
- Clear merged worktrees out of `work/`. Keep `media-node` clean, or the
  door stops rebasing.
- Surprises go in the log: `machines/kiosk-1/gotcha <tag> "assumed -> true"`
  (run it from `media-node`; it commits there). Bring those lines to `main`
  by PR every so often.
- Things still waiting on IT: automatic sign-in, and inbound :8080 (see
  `docs/machines/kiosk-1/PROFILE.md`).

## Building and testing here

This box is a builder, provisioned on purpose (2026-09-24). Node 24 LTS lives in
`%LOCALAPPDATA%` under `media-node/node`, on the user's PATH; `gh` and `uv` are in
`~/.local/bin`. The broker's tests run with `node --test worker/test/*.test.mjs`, and
`npx wrangler@4 dev --ip 127.0.0.1` serves the real Worker on loopback. Integration
tests use invented `*.localhost` hosts (Edge sends them to loopback) and a virtual
passkey authenticator over the DevTools protocol. No production secrets are needed.
Details, including the Visual C++ runtime fix, are in `docs/machines/kiosk-1/PROFILE.md`.

## Rules that bite

- **We commit source; station-node builds and deploys.** Local build
  viability means jekyll-enough in a browser. No Ruby, no real Jekyll.
- **Secrets never go in files or repos.** Passwords go in Credential Manager,
  and the Microsoft 365 key goes in the certificate store (non-exportable).
  The site repo is public, so **no personal data in commits**, and that
  includes names from bookings.
- The board's wording is authoritative (fcpublicmedia.org `AGENTS.md`).
- **Change only what was asked.** When Autumn asks to move something, it
  moves and keeps its size, colour and wording. What she says about how it
  used to be is background, not a second instruction.
- Windows bites: CRLF from generators, Git Bash rewriting `/flags` and
  `a:b` paths (`MSYS_NO_PATHCONV=1`), and tool calls eating backslashes in
  UNC paths. Read `GOTCHAS.log` first.
