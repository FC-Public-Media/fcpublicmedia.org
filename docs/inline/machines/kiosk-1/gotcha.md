# `machines/kiosk-1/gotcha`

Moved out of the file. Unreviewed.

## 1

Above `set -eu`

gotcha — append one environment stumbling block to the media node's log.

  machines/kiosk-1/gotcha net "assumed X -> actually Y"

After station-node's bin/gotcha. Commit-title length. The NATURE of the issue
and what was missing, never the context or the fix. The value is in the count
going down, and a log nobody can skim has no count.

GOTCHAS.log is `merge=union` (.gitattributes), so appends from different
branches never conflict. Union does not sort, so this re-sorts on every
append and the file heals the next time anybody uses it.

IT COMMITS, on `media-node` only. That branch is the one the services run
from, and the door's background rebase skips a dirty worktree, so a line
left uncommitted would quietly stop the screens from updating. Committing
bounces the door, which is harmless: three seconds, and the screens reload.
On any other branch it appends and says so, rather than putting telemetry
into somebody's pull request.

## 2

Above `tmp="$log.$$"`

Re-sort by the date column, stably. Header lines start with '#', which sorts
ahead of any digit, so they stay on top. Temp file and rename, so an
interrupted run leaves the log whole.
