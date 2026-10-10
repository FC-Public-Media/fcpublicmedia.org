# `machines/fcpm`

Moved out of the file. Unreviewed.

## 1

Above `set -u`

fcpm — the crew's one switch on an FCPM machine: every verb a person runs
here, by name, the same in cmd and PowerShell. Alone, it is the watcher
(./watch). Verbs: `fcpm help`. Doc: docs/machines/README.md, "The crew's one switch".

## 2

Above `f=$1; shift`

The one way a .ps1 is run here: as the pool's logon task runs its own,
and as the crew's GRANTS names it.

## 3

Above `"$CODE/bin/refs" pull "$(basename "$REPO")" || exit`

Bring in what merged and put it in place: the mirrors, then the copies
run from ~/code (sync install). One verb, nothing left half done
(Autumn, 2026-10-10). The pool does the same by itself with `fcpm dev on`.
Only this repo: fcpm runs from it, and the other mirrors are reading
(Autumn, 2026-10-10). The reading mirrors are the weekly task's chore.

## 4

Above `f="${LOCALAPPDATA:-$HOME/.local/state}/fcpm/dev"`

On: the pool pulls GitHub every 5 minutes and places what merged
(Autumn, 2026-10-09). Off: the weekly pull and people, as before.

## 5

Above `uv=$(command -v uv 2>/dev/null || echo "${LOCALAPPDATA:-}/Microsoft/WinGet/Links/uv.exe")`

The production crew (crews/): what its supervisor keeps, asked
live. `serve` is what the crew's service runs; in a window, it tries it.

## 6

Above `uv=$(command -v uv 2>/dev/null || echo "${LOCALAPPDATA:-}/Microsoft/WinGet/Links/uv.exe")`

uv brings its own Python; a window opened before uv was installed may not
have it on PATH, so fall back to where winget puts it.
