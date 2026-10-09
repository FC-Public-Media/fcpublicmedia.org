# crews: the work FCPM's machines take on

**Status: built for production, 2026-10-07, Autumn's naming.** A crew is the
work a machine takes on, with a contract: what it looks after, and what
services it offers, compliantly. FCPM's machines are a plural identity:
clearly different crews, run in parallel, each with its own name. A crew is
not the hardware, and a machine can wear more than one.

> Production is the name of your crew. That crew is going to live alongside
> another crew for any other bay to take on, so that they're drawing from the
> same things, but in different configurations. And so this way, it's very
> clear what it looks like to put on a responsibility and to offer compliant
> services. Even if another computer had to step in and offer them in
> addition as a peer, it would be perfect that way still. The contract would
> be clearly articulated.
> — Autumn, 2026-10-07

## Three layers, side by side

| layer | named for | lives at |
|---|---|---|
| troves | a discipline's gear | [`../troves/`](../troves/README.md) |
| crews | the work: `production`, `kiosk`, `digitization` | `crews/` (here) |
| machines | the hardware: `editing-bay-1`, `kiosk-1` | [`../machines/`](../machines/README.md) |

Machines keep their instance names. `kiosk-1` is a computer, and `kiosk` is
the job it does.

## The same model as station-node's

Station-node is adopting the same model: digitization is a crew, station-node
wears it, and a bay can take it over. So underneath, a crew here looks like
one there (a supervisor, residencies, crews, contracts, status asked live),
and a crew can move between machines on either side.

The difference is only in what a person sees. Station-node's page on 8080 is a
record for whoever tends the station. Production's door is for members: a way
in, not a console (`production/CREW.md`).

## What a crew is here

| | |
|---|---|
| **the crew** | `crews/<name>/`: its contract (`CREW.md`: what it is responsible for, what it serves, what counts as serving it), and its order (`services`: the lines it runs) |
| **what it draws on** | the same troves and residencies as every other crew (`../troves/`, the mounted repositories' `residency.yml`). Crews differ in configuration, not in having their own copies of things |
| **who wears it** | a machine wears one or more crews; its hardware record (`../machines/<bay>/`: names, gear) says which (`wears`). Putting one on is a commit, so wearing leaves a line, as station-node settled (`docs/the-crew.md` there) |
| **its supervisor** | each crew a machine wears has its own supervisor there, one service named for the crew (`production` on editing bay 1), running that crew's order. Never one service per line |
| **peers** | if another computer has to step in, it can put the same crew on and offer the same services beside the first. The contract is what makes them interchangeable: same services, same addresses on their own hosts, same behaviour |

[`../machines/crew.yml`](../machines/crew.yml) stays what it is: who can be
mustered on an FCPM machine at all (agents, and how). A named crew is the
next step that file was waiting for: it says `supervisor:` is absent because
there is none, and production is where there first is one.

## The crews

| crew | what it looks after | worn by |
|---|---|---|
| [`production`](production/CREW.md) | the recordings after they land: pools, transcription, episodes and their release, the door at the bay | editing bay 1 (`EDIT2`) |
| `kiosk` | the media node: the door at the front, the screens, check-in. Its profile is `../machines/kiosk-1/` today | kiosk-1 (`200-FCPANEDIT2`) |
| `digitization` | capture: arming, presence, the ledger, the recorders, the tank. Its contract: [`digitization/CREW.md`](digitization/CREW.md) | station-node; editing bay 1 is a member (it hosts the tank, the Drobo's 1 TB partition shared as `enhance`, and drives the rolling TV) |

## Why this way

- **Station-node can vacate.** What it does stops being "what that Mac does"
  and becomes crews another machine can put on, one at a time, with nothing
  lost but the Mac.
- **A bay is a bay.** Any bay can take on any crew; production and
  digitization are where the work is, not where the hardware is.
- **FCPM is a canonical, dedicated place.** Station-node is built to be reached
  from several places because it is a person's own; here a crew's profile is
  the studio's, and its services stay in the building.

## What the supervisor assumes today (from editing bay 1, 2026-10-08)

`crew.py` and `crew.ps1` were written and proved on one Windows machine. The
model above (crews, residencies, the order, status asked live) is not tied to
it; this code is. Written down for the first crew host that is not editing
bay 1, which is `../machines/digitization/` (Debian).

**Windows only, with what Linux would use instead:**

| in `crew.py` / `crew.ps1` | on Windows | on Linux |
|---|---|---|
| the one service | a scheduled task at the computer's start, S4U (`crew.ps1`) | a systemd unit, `WantedBy=multi-user.target` |
| one supervisor per crew | a named mutex (`single`, `supervising`) | a lock file held with `fcntl.flock` |
| has a desktop | session id is not 0 (`has_desktop`) | a display in the environment (`DISPLAY` / `WAYLAND_DISPLAY`); a system unit has none |
| children with no window | `CREATE_NO_WINDOW`, `CREATE_NEW_PROCESS_GROUP` | `start_new_session=True` |
| stopping a line and its children | `taskkill /T /F` | kill the process group |
| `alive: {process: ...}` | `Get-CimInstance Win32_Process` via PowerShell | `/proc/*/cmdline` |
| uv | winget's links, then its package folder | `uv` on PATH |

**Tied to editing bay 1, a bug anywhere else:** `crew.py` keeps its logs
under `%LOCALAPPDATA%\editing-bay-1\crew\` (`PROFILE`, hard-coded), and
`troves/pools/episodes.py` stages admissions under the same name. Both should
take the machine's profile (`machines/sync`) instead.

**Learned while proving it:**

- **A task started with the computer has no desktop** (session 0). Lines that
  need one are marked `desktop: true` and run from the signed-in session
  (editing bay 1's pool task: `crew.py desktop`). A Linux system unit is the
  same: no display, so the same split applies.
- **Running with no stored password reaches no network shares** and no
  stored secrets (S4U). The local disks and the Drobo are fine.
- **An `alive: {process: ...}` pattern can match the shell that launched a
  test**, when the pattern's text is in that shell's command line. Keep the
  patterns specific (`remote-control`'s is), and test from a script file.
- **Not yet proved: the install itself.** It needs an administrator, and
  had not been run when this was written.
