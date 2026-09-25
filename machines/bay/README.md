# The bay

**The bay is where an FCPM machine takes in outside software on purpose, as a
procedure rather than a command.** The idea and its stages are ablative's
(`docs/17-the-bay.md` there), from the operator on the day the first payload
came aboard:

> It's like the opposite of a release, obviously. It's an install. But it's like
> the engineering bay.

Ablative is personal and does not come to FCPM (`../../docs/STATION.md`). The
bay is the part of it that is not personal: any machine that takes in software
somebody else built has to say what arrived, what vouched for it, and what had
to bounce. This is that part, restated for Windows.

A directory here is not a profile: it has no `PROFILE.md`, so `binding` does
not count it (`../README.md`).

## The stages

| stage | what it does | what it leaves |
|---|---|---|
| **receive** | fetch the payload from where its vendor publishes it | the artifact, under `received\` |
| **verify** | hash against the vendor's own published value; Authenticode on every executable in it | the evidence, in the payload record |
| **stage** | unpack to a place nothing running uses | a staged copy that can wait indefinitely |
| **install** | swap it in at a declared restart tier, placing the grants it needs at the desk | the previous copy, kept as the rollback |
| **confirm** | check that it runs and does its job, and that it touched nothing it should not | the result, logged |

**Verify is Authenticode, not a designated requirement.** On macOS the check
that matters is the designated requirement, because TCC grants are keyed to it.
Windows has no TCC. What it has is a signature per file: the signer's name and
whether the chain is trusted. A payload whose executables are not all signed by
the vendor it came from is refused.

## Restart tiers

Ablative's table, with Windows' own words for the heavier two:

| tier | what bounces | cover needed |
|---|---|---|
| `none` | nothing; a file is replaced | none |
| `app` | one application | none, unless the app is itself a guard |
| `job` | a scheduled task: `End` then `Run` | the task's own gap |
| `session` | sign out and back in | nothing runs until somebody signs in (`../kiosk-1/PROFILE.md`, *Asked of IT*) |
| `machine` | restart | the same, and longer |

## Where things are written

On the host, under the profile's own folder in `%LOCALAPPDATA%`:

| | |
|---|---|
| `bay\received\` | artifacts as they arrived |
| `bay\staged\<payload>-<version>\` | unpacked, waiting |
| `bay\cellar\<payload>\<version>\` | the previous copy, kept at every install. *Verification is recoverable; custody of the previous version is not* (ablative) |
| `bay.ndjson` | the run log, one line per step, appended as it happens. A run that dies halfway says which half |

In this repository:

| | |
|---|---|
| a **procedure** | carried by whatever needs the payload: a trove (`../../troves/*/bay/`) or this folder. Every procedure has a `check` that changes nothing |
| a **payload record** | `../<profile>/bay/<payload>-<version>.yml`, one per arrival on one host. Its `status:` moves `staged → installed`, or `rolled-back`, or `installed-outside` when the thing arrived and the bay did not do it |

The record is the host's because an arrival is a fact about one machine on one
day. The procedure is the trove's because it is the same on every machine that
wears it.

## Not built

- A generic bay command. One procedure is not a pattern; the second will say
  what is shared. Ablative said the same.
- Unattended installs. Install is a desk step: its grants need an
  administrator, and a grant is placed with somebody there.
