# `advocate.yml`

Moved out of the file. Unreviewed.

## 1

Above `version: 1`

advocate.yml — who speaks for this repository's continuance.

The only file the framework asks of us. Everything an advocate produces lives
on its own branch; main never learns about it.

WHY THIS REPOSITORY HAS ONE
---------------------------
Board terms here are about a year. The people who inherit this will not have
watched it being made, and almost everything is explained in a comment beside
the thing it explains — which works for whoever is already reading that file
and not at all for whoever does not know the file exists.

The advocates below exist so that a handful of facts that decay on their own
get noticed by somebody, rather than by nobody. See ADVOCATE.md.

EVERY SESSION IS `local`. Nothing calls out, nothing runs unattended, and no
credential is required to hold a seat. That is the intended resting state
rather than a stage on the way to something else — FCPM has no allegiance to
any particular model or vendor, and a seat that needed one would have picked
a vendor on the organisation's behalf. `backend:` is therefore absent: while
every session is local it is never consulted, and naming one would say
something we do not mean.

`writes: []` throughout, which is the honest default. An advocate proposes.
A person decides.

## 2

Above `branch: council`

One readable page, rewritten whole each round, on an orphan branch. This is
the thing to open when dipping back in — every seat, when it last spoke,
what is still forming. It exists so nobody has to keep a list of open
questions in their head.

## 3

Above `session: local`

Seated 2026-09-15 at Autumn's request: "FCPM will become exactly like what
we're prototyping over there" — station-node — "and FCPM as a repo can be a
node by construction." A seat rather than a plan, because what was asked
for is ONGOING STUDY of a prototype that is still moving, and a seat is the
thing that keeps looking. A plan written today describes it as of today.

Unlike the four above this is a study, not a decay check; see §6.
Constituency and voice are RELAYED — her words, carried, not simulated.
Still hers to sharpen.

## 4

Above `says: >`

NARROWED 2026-09-17, by Autumn:

  "FCPM does not need to take cues from station-node about what to
   keep in its library per se. It is definitely up to us what we are
   bringing over."

The prototype is borrowed from for its SHAPE. What goes in the
library is FCPM's own decision, so "station-node holds it" is not by
itself an argument that FCPM should. Saying where a borrowing came
from is still owed.

## 5

Above `says: >`

DECIDED 2026-09-16, by Autumn, and kept here as a goal rather than
deleted because the reasoning is the part that has to survive: a
later reader needs to know this was chosen, and on what grounds,
not merely that it is so.

  "i do think the site is the node because itll build with its
   resources handy in jekyll data. The -node paradigm gives us site
   clusters that share a build root context"

THIS REPOSITORY IS THE NODE. The argument is Jekyll's, and it only
works in one direction. A node's holdings sit under its own root, so
if the site IS the node, every holding is inside the build root and
reachable from `_data` — the library becomes readable by the site
that keeps it, for free, with no copying step and nothing to keep in
sync. Put the node in a sibling and the site becomes a holding
*inside* it; the site's build root is then a subdirectory that cannot
see its siblings, and every shared resource needs a mechanism.

The unit that buys is a SITE CLUSTER sharing one build root context,
which is what makes member-site provisioning (G4) a library admitting
a holding rather than a deployment problem.

DELIVERED 2026-09-17 as NODE.md, when the website moved into `site/`.
One correction it carries, because a later reader should have it
rather than the claim above: a holding is NOT reachable from `_data`
"with no copying step". Jekyll resolves `data_dir` through
`sanitized_path`, which refuses to leave `source:`, so no build root
can read its siblings — the boundary does not move when the root
does. A symlink crosses it and is a trap: measured here, it is read
by an ordinary build and SILENTLY ignored under `--safe`. What being
one repository actually buys is that the five existing syncs write
into `site/_data/` by a relative path in the same working tree,
rather than across a submodule pin. That is worth more than the
version that was claimed for it.

The goal stays open as maintenance: NODE.md has to keep being true.
