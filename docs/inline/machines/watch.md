# `machines/watch`

Moved out of the file. Unreviewed.

## 1

Above `set -u`

watch — what `fcpm` alone does: show this machine's state, then offer pull,
send and install. `watch copy` makes the people's working copy, `watch weekly`
is the scheduled pull. Doc: machines/README.md, "fcpm on its own".

## 2

Above `at="$(git -C "$MIRROR" log -1 --format="%h, %cr" 2>/dev/null)"`

The mirror is what this machine runs: fcpm itself, and the source of the
copies sync places. Named, so nobody has to know refs/ is it (Autumn,
2026-10-10).
