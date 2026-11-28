# FCPM media node: the project

This directory is the project: Fort Collins Public Media's media node. Sessions start here.
Windows 10, IT-managed, **no administrator**. Profile: `machines/kiosk/PROFILE.md`; crew: `machines/kiosk/CREW.md`.

| this box answers to | |
|---|---|
| `kiosk` | what Autumn calls this root, the name its Claude sessions carry, and its profile in the site repo, `machines/kiosk` (`docs/station.md`, *Machines*) |
| the media node | what it is when it runs fcpublicmedia.org's services, as station-node runs discoverywritten.com's |
| `200-FCPANEDIT2` | what Windows answers to; `200-fcpanedit2.local` on the LAN |
| the old editing bay 2 | what it was. It is not today's bay 2 |
| `BAY1` | **not this box**: editing bay 1, which Autumn calls `production`. Check `$env:COMPUTERNAME` before trusting any guess |

## What we own

- **fcpublicmedia.org** (`FC-Public-Media/fcpublicmedia.org`, public): the site in `site/`, this node in `machines/kiosk/`.
- **enhance** (`FC-Public-Media/enhance`, private), at `.enhance-engine`: recordings go out and come back enhanced or stemmed. Capture model: `docs/CAPTURE.md`.
- **The depot**: the router's partitions at `\\10.209.1.1`, in at `TO ENHANCE`, out at `PODCAST`. Everything between is held in `%LOCALAPPDATA%\media-node\library\`.
- **The door**: the pages on :8080, and the TV wall it writes to `\\10.209.1.1\DIGISTATION\.wall\`.

| where | |
|---|---|
| `ref/` | read-only mirrors of every repo we read. **Never commit here.** Production calls its own `refs/` |
| `work/REPO@BRANCH` | a worktree per branch: `fcpm workshed` |
| `work/fcpublicmedia.org@media-node` | **the live checkout.** The door runs from it. Never edit here |
| `%LOCALAPPDATA%\media-node\` | the venv, `door.log`, the screens' browser profiles, the library wing |

## Work

- **One branch per change**, from `origin/main` in `fcpm workshed`. Commit, push to the origin; Autumn lands it (Helm, `/origin/`); `fcpm install` brings it in, and within 5 minutes the door rebases `media-node` onto main and restarts. **Never open a PR from `media-node`**: the door rebases it under the PR.
- **This file is read from the mirror** through `~/code/CLAUDE.md`. Change it in a worktree (`machines/kiosk/code/AGENTS.md`). Never edit the root's own `CLAUDE.md` or `AGENTS.md`: they are pointers.
- **Other machines are reached outward only**: code by commit (station-node mounts fcpublicmedia.org), media through the depot, conversation by session message (`rodecaster` is capture on station-node). Nothing connects in.
- `fcpm install` brings this checkout and this file from the origin. `door.py startup` (the logon task), `door.py screens` (the panels), `door.py sessions`, `door.py server`, `door.py` (the door). Log: `%LOCALAPPDATA%\media-node\door.log`.
- **No seat.** Sessions arrive through the root's Remote Control server, as on production. The door keeps it up and bounces it onto a new Claude after 15 calm minutes.
- Nobody types `fcpm` at this box; sessions do (`~/.local/bin/fcpm.cmd`, on PATH). Steps other machines leave to a person at the desk are a session's here, when Autumn asks. Don't hedge them back to her.
- Clear merged worktrees out of `work/`. Keep `media-node` clean, or the door stops rebasing. Waiting on IT: automatic sign-in, and inbound :8080.
- Surprises: `machines/kiosk/gotcha <tag> "assumed -> true"`, run from `media-node` (it commits there). Bring those lines to `main` by PR now and then.
- Building: Node 24 LTS (`%LOCALAPPDATA%\media-node\node`), `gh` and `uv` (`~/.local/bin`). `node --test test/*.test.mjs` in a site-worker checkout (FC-Public-Media/site-worker); `npx wrangler@4 dev --ip 127.0.0.1` serves the Worker on loopback; integration tests use invented `*.localhost` hosts and a DevTools virtual passkey authenticator. No production secrets. The Visual C++ fix is in the profile.

## Rules that bite

- **We commit source; station-node builds and deploys.** Local builds are jekyll-enough in a browser: no Ruby, no Jekyll.
- **Secrets never go in files or repos**: passwords in Credential Manager. The site repo is public: **no personal data in commits**, names from bookings included.
- The board's wording is authoritative (fcpublicmedia.org `AGENTS.md`). **Change only what was asked.** A moved thing keeps its size, colour and wording. What Autumn says about how it used to be is background, not a second instruction.
- Windows bites: CRLF from generators, Git Bash rewriting `/flags` and `a:b` paths (`MSYS_NO_PATHCONV=1`), tool calls eating backslashes in UNC paths. Read `GOTCHAS.log` first.
