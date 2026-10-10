# `machines/sync`

Moved out of the file. Unreviewed.

## 1

Above `set -u`

sync — put on the profile this machine wears, or say how far off it is.

  machines/sync              status: which profile, what differs. Changes nothing
  machines/sync install      put the profile on: carried files, compiled settings, PATH, clone
                             missing mirrors. A person runs this, not a session
  machines/sync mirror       bring the machine's copies back into this checkout,
                             for a pull request. Refused in refs/
  machines/sync -p NAME ...  name the profile instead of asking the machine

After station-node's `machine/sync`, for the plural: which profile is worn is
ASKED, the way `binding` asks it, and the profile's own MANIFEST says what it
carries and where it goes. Same entry point on every platform; the profile
says the rest. A profile may carry `check.ps1` (Windows) or `check.sh`, which
status runs to report what files cannot: tools, settings, tasks. Those checks
change nothing either.

`install` never destroys: a home file that differs is moved aside to
<name>.pre-sync first, and a mirror already cloned is left alone.

Git Bash on Windows, sh elsewhere. No Python: this is what a bare machine
runs before it has one, and `binding` needs one.

## 2

Above `settings:status|settings:install)`

settings <profile> <home path>: the profile's GRANTS, compiled
(bin/runnables compile), in place for the harness to read. Never a
copy in the repository: it is generated from what is, so it cannot
drift from the answer that was merged.

## 3

Above `path:status|path:install)`

path <home dir>: on this user's PATH, so what is carried there is found
by name in any shell. Windows keeps a user PATH of its own; a new window
sees the change.

## 4

Above `if [ "${SYNC_CHECK:-1}" = 0 ]; then :`

SYNC_CHECK=0: the watcher, which wants only what differs (Autumn,
2026-10-09: bare fcpm runs no check). `fcpm check` runs it.
