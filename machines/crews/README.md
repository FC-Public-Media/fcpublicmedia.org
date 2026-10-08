# crews: responsibilities a machine puts on

**Status: proposal, 2026-10-07, Autumn's naming.** A named crew is a set of
responsibilities with a contract: what it looks after, and what services it
offers, compliantly. A machine puts a crew on; the crew is not the machine.

> Production is the name of your crew. That crew is going to live alongside
> another crew for any other bay to take on, so that they're drawing from the
> same things, but in different configurations. And so this way, it's very
> clear what it looks like to put on a responsibility and to offer compliant
> services. Even if another computer had to step in and offer them in
> addition as a peer, it would be perfect that way still. The contract would
> be clearly articulated.
> — Autumn, 2026-10-07

## What a crew is here

| | |
|---|---|
| **the crew** | `crews/<name>/`: its contract (`CREW.md`: what it is responsible for, what it serves, what counts as serving it), and its order (`services`: the lines it runs) |
| **what it draws on** | the same troves and residencies as every other crew (`../../troves/`, the mounted repositories' `residency.yml`). Crews differ in configuration, not in having their own copies of things |
| **who wears it** | a machine profile names the crews it has on (`../<profile>/wears`). Putting one on is a commit, so wearing leaves a line, as station-node settled (`docs/the-crew.md` there) |
| **its supervisor** | one service per machine, named for what it wears (`production` on editing bay 1), running the order of every crew it has on. Never one service per line |
| **peers** | a second machine can put the same crew on and offer the same services beside the first. The contract is what makes them interchangeable: same services, same addresses on their own hosts, same behaviour |

`../crew.yml` stays what it is: who can be mustered on an FCPM machine at all
(agents, and how). A named crew is the next step that file was waiting for: it
says `supervisor:` is absent because there is none, and production is where
there first is one.

## The crews

| crew | what it looks after | worn by |
|---|---|---|
| [`production`](production/CREW.md) | the recordings after they land: pools, transcription, episodes and their release, the door at the bay | editing bay 1 (`EDIT2`), proposed |
| `digitization` | capture: arming, presence, the ledger, the recorders. Today station-node's, on its Mac | station-node; a bay could put it on so station-node can vacate |

## Why this way

- **Station-node can vacate.** What it does stops being "what that Mac does"
  and becomes crews another machine can put on, one at a time, with nothing
  lost but the Mac.
- **A bay is a bay.** Any bay can take on any crew; production and
  digitization are where the work is, not where the hardware is.
- **FCPM is a canonical, dedicated place.** Station-node is built to be reached
  from several places because it is a person's own; here a crew's profile is
  the studio's, and its services stay in the building.
