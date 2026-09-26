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
| network | Ethernet on the building's network, marked Private; the guest Wi-Fi. Neither reaches the depot at `10.209.1.1` |
| the repository | read in `~/code/refs/`, changed in `~/code/work/REPO@BRANCH` (`code/AGENTS.md`) |
| screens | two HP E273s at the desk, and the rolling TV (`../../instruments/roller-tv/`) |
| not ours | the OBS in Program Files, the browsers' profiles, display settings. People sit down to this machine every week |

## What this folder holds

A folder here is a claim to have the thing it names (`../README.md`).

| | |
|---|---|
| `names` | what the machine answers to |
| `MANIFEST` | what `../sync` carries of this machine's home: the `~/code` root |
| `code/` | that root, carried: `AGENTS.md`, `CLAUDE.md`, `bin/refs`, `bin/pool.ps1`, `refs.wanted` |
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
2. **This repository.** In Git Bash:

       mkdir -p ~/code/refs && cd ~/code/refs
       git clone https://github.com/fc-public-media/fcpublicmedia.org
       git config --global core.autocrlf false

   Then clone station-node's mirror beside it by hand, if this bay is to read it.
3. **Put the profile on.** `refs/fcpublicmedia.org/machines/sync` should find
   `editing-bay-1` by name, and list everything as missing. Then
   `machines/sync install` puts the `~/code` root in place and clones every
   mirror in `refs.wanted`. A person runs `install`.
4. **Developer Mode, at the desk.** Settings > System > For developers. It lets
   symlinks be made without elevation.
5. **Claude Code, at the desk.** The vendor's installer, into `~/.local/bin`.
   Open it once in `~/code` and accept the folder, which a background session
   needs before it can start there.
6. **The pool.** `bin\pool.ps1 install` registers the per-user logon task. From
   then on a session is waiting in `~/code` after every sign-in.
7. **Gear, through the bay.** `gh`, then `uv`, then Node, each from the
   vendor's portable archive, verified and recorded (`gear.yml`, `bay/`).
   `gh auth login` is the desk's.
8. **Check.** `machines/sync` again. What is still `WANTED` is what is left.

## Open

- **Running `check.ps1`.** Windows Home's default execution policy stops
  scripts, so `sync` cannot run the check yet. The pool's task passes
  `-ExecutionPolicy Bypass` for its own script; whether `sync` should, or the
  policy for this user should change, is Autumn's call, and was not decided by
  a session.
- **`bin/refs` is the media node's**, one line apart (`REF` is `refs/` here).
  Two copies drift. It belongs somewhere both machines read it from.
- **The depot.** How this bay joins the network it is on.
- **Which profile is worn is committed here for the first time.** Merging this
  is the decision that `EDIT2` is editing bay 1.
