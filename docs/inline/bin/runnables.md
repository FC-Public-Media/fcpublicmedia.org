# `bin/runnables`

Moved out of the file. Unreviewed.

## 1

Above `set -u`

THIS IS THE OSTENSIBLY AVAILABLE LIST, AND BEING ON IT GRANTS NOTHING. It
shows what the repository carries (machines/RUNNABLES says what each verb
claims to do) so a crew's answer can be read against it. Nothing here writes a
setting. docs/RUNNABLES.md.

The identity it prints is the file's git blob at HEAD: the same bytes on every
host that has this commit. A file changed since HEAD is marked, because what
a claim was proven against is the committed file, never the working copy.

Read-only. Git Bash on Windows; no Python, because a bay may not have one yet.

## 2

Above `discover() {`

Where runnables live. A trove's bay procedures and runtime verbs are the
recorder's and the screens' own; the rest are the repository's.

## 3

Above `depends_of() {`

A GRANTS file's `depends <holder> | <path>` lines, as holder|path, for one
holder or (with "") all of them.

## 4

Above `p=${2:-}; G="$ROOT/machines/$p/GRANTS"; PROVEN="$ROOT/machines/$p/bay/runnables.proven"`

Boring on purpose: a machine that grants permissions should have no
judgment in it. It prints; `machines/sync` is what puts it in place.

## 5

Above `lad=$(printf '%s' "${LOCALAPPDATA:-}" | tr '\\' '/')`

{LOCALAPPDATA} in a runner is this host's, with forward slashes: a rule
matches the text a session types, so the committed file names the place
and the compiled one names the path.

## 6

Above `depblobs=$(depends_of "$G" "" | while IFS='|' read -r dh dp; do`

depends <holder> | <path>: a file the holder reads at run time. Its blob
is part of the proof, so a change to it revokes the grant exactly as an
edit to the holder would.

## 7

Above `r = l; sub(/^[ \t]*host[ \t]+[a-z]+[ \t]+/, "", r); r = trim(r)`

A command that is not ours: it can be held back, never let through.
Only a proven holder of ours is ever allowed.

## 8

Above `rest = l; sub(/^[ \t]*admit[ \t]+[a-z]+[ \t]+/, "", rest)`

The one widening. An `outside` verb becomes an allow, and only
once the bay has exercised it; the line itself is admitted by the
merge that brings it. desk, secret and service are never admitted.

## 9

Above `nd = split(depblobs, dl, "\n")`

A proof counts only if every file its holder depends on is recorded
in it at the blob that file has now.

## 10

Above `if (nwears && !(h in wears)) next`

A profile that names what it wears answers for nothing else: the
bays do not run the door, and its rules are not theirs to carry.

## 11

Above `if (a == "allow" && !((h " " blob[h]) in ok)) {`

Unproven is left OFF the list, not turned into `ask`: an ask rule
forces a prompt even where the harness would have let it through, and
a background session has nobody to answer one.

## 12

Above `p=${2:-}; h=${3:-}; by=""; exercise=""`

THE BAY'S QUESTION, ASKED OF OUR OWN BYTES. A payload from outside is
proven by the vendor's digest and signature; a tool of ours by its blob,
and by doing what it claims on the machine that will run it. This runs
every `read` verb of the holder, exactly as the profile's canonical
runner starts it, and requires that nothing changed: not this checkout,
and not the profile's bay or troves folders. Then it writes one line.

It proves the read verbs by running them, and nothing else. An `inside`
verb is allowed on the strength of the same line, so `--by` names who
read the rest of the holder's code and vouches for it. A proof is a
commit, and admission is still the merge.

## 13

Above `exercised=""`

--exercise: THE CYCLE A TASK WILL RUN, run once, watched. What an
`admit` may allow is what this proved. GRANTS declares it as data:
  exercise <holder> | <shape> ; <shape> ; ...   the cycle, in order
  untouched <path>      must list the same (names, sizes, times) after
  quiet <image>         none may run before it starts, none after it ends
Files may change under the profile's troves folder and nowhere else the
bay watches: not this checkout, not its bay folder or run log.

## 14

Above `expects=$(awk '$1 == "expect" { $1 = ""; sub(/^ /, ""); print }' "$G")`

expect <file> <text>: something the cycle appends to <file> must
contain <text>, such as a stop that closed rather than killed.
