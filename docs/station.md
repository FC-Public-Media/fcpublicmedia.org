# Station

This repository is the website and the station: it owns what it means to be on an FCPM machine. It
is checked out on several machines at once, and every checkout is the same repository. station-node,
DiscoveryWritten's workstation in the studio, is the prototype; FCPM copies its shape, not its role.

## Public repository

- Only what works by the encrypted-by-specification path is built here; a capability that needs a
  secret in the repository stays out. So a clone on any machine is safe, and is a backup. Check
  every addition against that.
- Secrets live in Credential Manager or the certificate store (non-exportable). No personal data in
  commits, including names from bookings.
- station-node's private-client configurations do not come here. Splitting work and granting it
  securely to other workstations does.

## Rules

- The website builds and serves throughout; everything else is background to it. Its domain may change.
- We commit source; station-node builds and deploys. This repository is mounted in its library at
  `library/FCPM/fcpublicmedia.org`, and publishing stays there: no FCPM machine grows a publishing
  path. How the live site is built: [site.md](site.md).
- Station-like services move from station-node onto FCPM machines. One repository, one journal.
- There is no escalation system. Failed work that needs somebody told goes to the board president.
- Machines reach each other outward only: code by commit, media through the depot, talk by session.

## Machines

| called | profile | answers to | what it is |
|---|---|---|---|
| production | [`editing-bay-1`](../machines/editing-bay-1/PROFILE.md) | `EDIT2` | sticker "editing bay 1"; Windows 11 Home, the strongest machine |
| kiosk | [`kiosk-1`](../machines/kiosk-1/PROFILE.md) | `200-FCPANEDIT2` | the old editing bay 2, now the media node: door and screens ([kiosk.md](kiosk.md)) |
| | [`editing-bay-2`](../machines/editing-bay-2/PROFILE.md) | unfilled | a macOS bay that schedules Cablecast material |
| | [`digitization`](../machines/digitization/PROFILE.md) | `digitization` | Debian: FCPM's git origin; takes the `digitization` crew from station-node |
| | [`thin-client`](../machines/thin-client/PROFILE.md) | unfilled | a donated HP t510 in the control rack, to be reformatted |

Both Windows names end in `EDIT2`; in conversation use the called name (`machines/<profile>/called`).
The bays share one account with a PIN; identity there is a browser profile. [Crews](../crews/README.md).

## Profiles

A profile is a directory in `machines/` with a `PROFILE.md`. It describes its machine so an agent
arriving there does not have to work the environment out. It may also hold `names`, `called`,
`MANIFEST`, `GRANTS`, its own `gear.yml`, `crew.yml` or `toolkits`, a `check.ps1` or `check.sh`
(what files cannot say: tools, settings, tasks; changes nothing), `bay/` (payload records and
proofs), `code/` (the `~/code` root) and `home/` (files placed in the home). A file or folder is a
claim to have the thing it names; absence is a complete answer, so add one only when it is real.

`machines/binding` prints which profile this checkout wears. `names` is intent, one
`platform key value` line per platform; the machine is asked at run time: `darwin LocalHostName`
(`scutil --get LocalHostName`), `windows ComputerName` (`%COMPUTERNAME%`, else `hostname`), `linux
Hostname` (`hostname`). Which profile is worn is never committed, since that file would be copied
to every other machine. The key must be its platform's (macOS's `ComputerName` is not Windows'
`COMPUTERNAME`); a bad line is reported and ignored. Matching is case-insensitive. No match is the
clean state and exits 0; two profiles claiming one host exits 1. Tests: `bin/test_binding.py`.

## Crew and gear

`machines/crew.yml` (who can be started on a machine, and how: a roster, not a startup script),
`machines/gear.yml` (software put there on purpose, and who may replace it) and `machines/toolkits`
(`<language> <tool> <arrives by>`) are the default, Windows and winget. A profile's own copy replaces
it whole, never merged. Why an agent runs here is [advocate.md](advocate.md)'s, not the crew's.

Gear on Windows is whatever winget owns. An entry has `gear`, `for`, `package` (winget id) or `at` (a
path), `provisioner` (`winget`, `bay`, `hand`), `updates`, `restart-tier` and `holds` (what an
upgrade must not lose). Presence is never written: `check.ps1` finds it, and an absent entry is
`WANTED`. A macOS profile's own `gear.yml` uses `bundle:` and `brew | mas | hand`.

## fcpm

`machines/fcpm` is the crew's one switch: every verb a person runs is `fcpm <verb>`, the same in cmd
and PowerShell (`fcpm help`). A step that needs a path, an interpreter or a choice of shell is a gap
in `fcpm`. Verbs are for people; a task names the tool itself, because a grant pins the tool's blob.
`fcpm`'s own blob is pinned by a proof, so change it only with a new one. On Windows,
`~/.local/bin/fcpm.cmd` runs the mirror's `machines/fcpm` with Git's bash.

| verb | does |
|---|---|
| (none) | the watcher, `machines/watch` |
| `status`, `install` | `sync`; `install` also makes the people's working copy and the `fcpm weekly` task |
| `pull` | `bin/refs pull fcpublicmedia.org`, then `sync install` |
| `check`, `weekly`, `pool`, `runnables` | the profile's check; the weekly pull; `~/code/bin/pool.ps1`; `bin/runnables` |
| `dev on`, `dev off` | on: the pool pulls this repository every 5 minutes and places what merged |
| `audition`, `drobo`, `share`, `audit` | the profile's own `.ps1` of that name |
| `recorder`, `screen`, `crew`, `pools`, `post`, `camera`, `ti89` | [troves](../troves/README.md) and [crews](../crews/README.md) |

`fcpm` alone shows the machine, `gh`'s sign-in, how far the mirror `~/code/refs/fcpublicmedia.org`
is behind GitHub, edits and unsent commits in the people's working copy
(`work/fcpublicmedia.org@<called>`), placed files that differ, the root's server, the screen and the
last weekly pull. It offers only what applies: *Make my working copy*, *Bring in the latest*, *Send
my changes up* (commit, catch up with `main`, push `<called>`, open or join a PR), *Install the
updates on this computer*. If edits and the latest change the same lines, it stops; nothing is lost.

`fcpm weekly` runs at sign-in and 7am and works once a week: it pulls every mirror and fast-forwards
the working copy, never merging, sending or installing (`%LOCALAPPDATA%\fcpm\weekly.log`). A bare
machine starts from the start line in [README.md](../README.md), *Setting up a machine*.

## Sync and MANIFEST

`machines/sync [-p PROFILE] [status | install | mirror]` is shell, for machines without Python. It
finds the profile the way `binding` does and reads its `MANIFEST`. `status` (default) says what
differs and runs the check (`SYNC_CHECK=0` skips it). `install` puts the profile on; a person runs it,
never a session, and it never destroys (a differing file goes to `<name>.pre-sync`, an existing clone
is left). `mirror` copies the machine's files back into a `work/` worktree for a PR.

| `MANIFEST` mode | `mode  path in the profile  path under ~` |
|---|---|
| `mirror` | a carried file, copied, not linked |
| `clone` | a file of repository URLs; any missing is cloned. This repository and station-node's mirror are cloned by hand |
| `settings` | the named profile's GRANTS, compiled, written to the path. Never stored in the repository |
| `path` | a home folder put on the user's PATH |

## Sessions

- A machine's root is `~/code`: read-only mirrors in `refs/` and a worktree per branch in
  `work/REPO@BRANCH`, kept by `bin/refs`. Its instructions are the profile's `code/AGENTS.md`, which
  `~/code/CLAUDE.md` points at in the mirror (`@refs/fcpublicmedia.org/machines/<profile>/...`).
- At sign-in the root runs an unnamed Remote Control server, `claude remote-control
  --no-create-session-in-dir`. Sessions start from zero at claude.ai or on the phone; none is
  revived or kept. A server is bounced when signed out, and when older than the installed
  `claude.exe` once calm for 15 minutes; its sessions end with it. Production does this in
  `code/bin/pool.ps1`, the kiosk in its door.

## Runnables

| layer | says | where | written by |
|---|---|---|---|
| census | every runnable this checkout carries, and its blob | `bin/runnables`, printed | nobody |
| claim | per verb: its narrowest shape, and what it touches | `machines/RUNNABLES` | the tool's author |
| proof | this holder, at this blob, does what it claims here | `machines/<profile>/bay/runnables.proven` | `bin/runnables prove` |
| answer | what this crew may run without asking | `machines/<profile>/GRANTS` | the crew, by merged PR |

A `RUNNABLES` line is `holder | run | shape | class | says`; `run` is `sh` (Git Bash), `python` or
`powershell`; `shape` follows the holder on the command line (` *`: any further arguments, `-`:
none). Classes, with their default answer: `read` (changes nothing) and `inside` (writes only in the
checkout) allow; `outside` (the host, the depot) and `desk` (a person or an administrator) ask;
`secret` (a credential) and `service` (a job's own verb) deny.

- Being on the census grants nothing; a runnable with no claim is undeclared and matches no rule.
- In auto mode the harness honours narrow allow rules and suspends broad ones (`Bash(*)`, wildcarded
  interpreters). A compound command needs every part to match. Rules are read from the directory a
  session starts in (`~/code`) and are relative to it. A rule names the script, never the interpreter.
- An unproven allow is left off, not made an ask (a background session cannot answer one).
  Admission is a merge to `main`; a profile may narrow an answer, never loosen one.

`bin/runnables prove <profile> <holder> --by <who> [--exercise]`, from a `work/` worktree, needs the
holder worn, committed and unchanged. It runs each `read` verb as the canonical Bash runner starts
it; nothing may change in the checkout or `%LOCALAPPDATA%\<profile>\bay` and `troves`. It appends
`holder blob date ran:... [exercised:...] [deps:<path>@<blob>;...] by:<who>`; `inside` verbs ride on
that line, and `--by` names who read the code. `--exercise` also runs the GRANTS cycle, watched.

## GRANTS

`bin/runnables compile <profile>` turns GRANTS into harness settings; `sync install` places them at
`~/code/.claude/settings.json`.

| line | means |
|---|---|
| `checkout <path>` | where the admitted code is, relative to `~/code` |
| `runner <run> <tool> [prefix]` | how a `run` is typed. The first per run is the only allow form; every form gets the denies |
| `wears <holder>` | answer only for these holders; with none, for every claim |
| `narrow <answer> <holder> \| <shape>` | tighter than the class, never looser |
| `host <ask\|deny> <rule>` | a command not ours. Never an allow |
| `depends <holder> \| <path>` | a file the holder reads at run time; its blob is part of the proof |
| `exercise <holder> \| <shape> ; ...` | the cycle `prove --exercise` runs. `untouched <path>`: listed the same after it; `quiet <image>`: not running before or after; `expect <file> <text>`: text it must append |
| `admit allow <holder> \| <shape>` | an `outside` verb, allowed once proven and exercised at its blob |

`{LOCALAPPDATA}`, `{APPDATA}`, `{USERPROFILE}` expand on the host. A deny matches typed text, not
the act: it is a floor under the classifier, and a secret is walled by where it lives.

## Bay

The bay is how an FCPM machine takes in outside software on purpose: receive (from the vendor), verify
(the vendor's hash; Authenticode on every executable), stage (unpack where nothing running looks),
install (at its restart tier, keeping the previous copy), confirm (it runs, and touched nothing else).

- Every executable must be signed by its vendor. A vendor that ships no Authenticode may be accepted
  on a GitHub build attestation (`gh attestation verify <file> --repo <vendor>/<repo>`), recorded
  with its workflow, tag and commit.
- Install needs an administrator for its grants, so it is a desk step; nothing installs unattended.
  Restart tiers: `none`, `app`, `job` (a task's `End` then `Run`), `session` (sign out and in), `machine`.

| where | holds |
|---|---|
| `%LOCALAPPDATA%\<profile>\bay\`, `bay.ndjson` | `received\`, `staged\<payload>-<version>\`, `cellar\<payload>\<version>\` (the rollback); the run log, a line per step |
| `troves/<trove>/bay/` | a procedure, with a `check` that changes nothing |
| `machines/<profile>/bay/<payload>-<version>.yml` | the record; `status:` `staged`, `installed`, `rolled-back`, `installed-outside`, `held`, `refused` |
| `machines/<profile>/bay/runnables.proven` | proofs of our own runnables |

## Engines

An engine is a submodule at the node root; the submodule is the declaration. Mounting one or moving
a pin is its own pull request by whoever owns it. In order of arrival:

| engine | state |
|---|---|
| `.advocate-engine` | mounted first |
| `.contact-sheets-engine`, `.library-engine`, `.enhance-engine` | mounted together. contact-sheets and enhance are private, `update = none`; library's residency wants are unanswered |
| `.tell-engine`, `.atlas-engine` | mounted together. We are our own Atlas, and our Tell registers to it |
| `.journal-engine`, `.proofing-engine` | wanted. The journal is a second build at the node root, apart from `site/` |
| ablative, bottles | ablative's tooling does not come, its observation is wanted; bottles not yet |

FCPM's library is the `library` branch, not a folder on `main`. It holds what is relevant to the
station where it is deployed, not an archive of all media: `trade`, `city` and `voices`.

## Intermediates

An intermediate is what we hand station-node to deploy ([members.md](members.md)): per domain,
`_intermediates/<domain>/` at the repository root, outside `site/`, built by jekyll-enough in a
browser with no Ruby. Nothing builds one yet.

- It holds `INTERMEDIATE.yml` (the manifest), `_site/` (rendered, preferred when fresh), baked
  `_layouts/`, `_includes/` and pages (collection documents as plain pages at their URL), and
  `_data/` and `_config.yml` only if some file could not be baked.
- A file's degree is `rendered` (final HTML), `baked` (site data resolved, forwarding includes
  collapsed, Liquid only on `page.*` or `content`) or `source` (the original, with what it needs).
- The manifest has `domain`, `kind: source-distribution`, `prefers: _site`, `built_from` (sha256 over
  every source's sorted path and sha256), `builder`, `files` and their degrees, `gaps`, and a
  `signature` by FCPM's key. A stale or missing intermediate falls through to rendering from
  source, never a refusal or a blank. Liquid a consumer cannot run is shown visibly uninterpreted.
