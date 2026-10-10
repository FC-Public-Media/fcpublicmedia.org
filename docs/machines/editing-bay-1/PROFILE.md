# editing bay 1

**Status: described, 2026-09-26, on the machine.** The studio calls it bay 1;
it answers to `EDIT2`. It is the studio's strongest machine, and the one the
bays' future is being built on, so this page says how to bring it back from
nothing as well as what it is.

The first draft of this page assumed macOS, like both bays. This one is
Windows 11 Home, and the questions that draft asked are answered below.

## What is known

| | |
|---|---|
| name | `EDIT2` (`$env:COMPUTERNAME`), in `names` |
| system | Windows 11 Home. i7-13700KF (24 threads), 32 GB, RTX 4080, 2 TB on `D:` |
| user | one local account. No administrator is assumed for anything below |
| shells | Git Bash (with Git) and Windows PowerShell 5.1. `python` on PATH is the Store stub |
| network | Ethernet on the building's managed network, and the guest Wi-Fi. Public is the intended category: the network is isolated, and what matters is what we do inside. The depot at `10.209.1.1` is reachable only by opt-in Wi-Fi while its subnet is worked on |
| the repository | read in `~/code/refs/`, changed in `~/code/work/REPO@BRANCH` (`code/AGENTS.md`, which `~/code/CLAUDE.md` points at in the mirror) |
| screens | two HP E273s at the desk, and the rolling TV (`../../instruments/roller-tv/`) |
| not ours | the OBS in Program Files, the browsers' profiles, display settings. People sit down to this machine every week |

## What this folder holds

A folder here is a claim to have the thing it names (`docs/machines/README.md`).

| | |
|---|---|
| `names` | what the machine answers to |
| `MANIFEST` | what `../sync` carries of this machine's home: the `~/code` root |
| `code/` | that root: `AGENTS.md` (its instructions, read in place from the mirror), and the carried `bin/refs`, `bin/pool.ps1`, `refs.wanted` |
| `home/code/` | what is placed at the root instead of a copy: a `CLAUDE.md` that imports `code/AGENTS.md` from the mirror, and an `AGENTS.md` that says where it is |
| `home/git/ignore` | the user's global git ignore: `.pr`, the branch's plan, stays out of every repository. This repository tracks its own `.pr`, which an ignore cannot reach |
| `gear.yml` | what the crew stands on here. Replaces `../gear.yml` whole |
| `check.ps1` | what files cannot say: gear present, Developer Mode, line endings, the pool's task, folder trust, the depot. Changes nothing |
| `bay/` | one record per payload the bay took in |

`../sync` on this machine says which of the carried files differ from what is
in place and runs `check.ps1`. Everything it reports as `WANTED` is on the list
below.

## Bringing it up from nothing

Day 0, in order. Each step is either a person's, at the desk, or something a
session can do once the step before it is done. Nothing here needs an
administrator except where it says so.

1. **Git, at the desk.** `winget install --id Git.Git --exact`. This is the
   one thing that has to arrive before these bytes can.
2. **The start line, once.** Copy it from the repository's front page on
   GitHub (`README.md`, *Setting up a machine*) into any window, cmd or
   PowerShell. It gets this repository, or updates it, and runs `fcpm
   install`. Clone station-node's mirror beside it by hand, if this bay is to
   read it.
3. **What that put on.** `fcpm install` finds `editing-bay-1` by name and
   puts on everything the MANIFEST carries: the `~/code` root, every mirror in
   `refs.wanted`, the compiled settings and `fcpm` itself on PATH. It also
   makes the people's working copy (`work/fcpublicmedia.org@production`) and
   registers the weekly pull. **From then on, in a new window, it is
   `fcpm`**: `fcpm` shows what is going on and offers what to do, `fcpm install` puts the profile on. A person
   runs `install`, never a session.
4. **Developer Mode, at the desk.** Settings > System > For developers. It lets
   symlinks be made without elevation.
5. **Claude Code, at the desk.** The vendor's installer, into `~/.local/bin`.
   Open it once in `~/code` and accept the folder. The root's server can't
   start there until the folder is trusted.
6. **The pool.** `fcpm pool install` registers the per-user logon task. From
   then the root is reachable after every sign-in: a Remote Control server
   with no session open and none named, where sessions start from
   claude.ai or the phone (`docs/machines/README.md`, *What a machine is called*).
7. **Gear, through the bay.** `gh`, then `uv`, then Node, each from the
   vendor's portable archive, verified and recorded (`gear.yml`, `bay/`).
   `gh auth login` is the desk's.
8. **Check.** `fcpm`, and `fcpm check`. What is still `WANTED` is what is left.

**No raw commands after step 3.** Every verb here is `fcpm <verb>`, the same in
cmd and PowerShell (`fcpm help`). A step that needs a path, an interpreter or a
choice of window is a gap in `fcpm`, not a thing to type.

## Baseline, 2026-09-26

Run directly, as research: `powershell -NoProfile -ExecutionPolicy Bypass -File
machines\editing-bay-1\check.ps1`. Windows Home's default execution policy
stops `sync` from running it itself, and nothing about that policy is being
changed while the machine may move to Pro (Autumn: network and policy powers go
through the network tooling teams).

| | |
|---|---|
| ok | git, Claude Code, gh; Developer Mode; `core.autocrlf` false; the pool's task; `~/code` trusted |
| wanted | uv, Node (through the bay); the depot (opt-in Wi-Fi only) |
| noted | Ethernet and Wi-Fi both Private at the time |

**Machine settings may revert after a gap, and that is expected.** Windows'
settings screens often show the old value for a while after something has
switched it back. `check.ps1` reports what it reads at the time; a later run
disagreeing with this table is data, not a fault.

## Open

- **The execution policy.** `sync` and `fcpm` run `.ps1` files with
  `-ExecutionPolicy Bypass`, as the pool's task does for its own script, rather
  than change the machine's policy while Home or Pro is undecided.
- **`bin/refs` is the media node's**, one line apart (`REF` is `refs/` here).
  Two copies drift. It belongs somewhere both machines read it from.
- **The depot.** Reachable only by the opt-in Wi-Fi for now; the subnet is
  being worked on.
- **Which profile is worn is committed here for the first time.** Merging this
  is the decision that `EDIT2` is editing bay 1.
