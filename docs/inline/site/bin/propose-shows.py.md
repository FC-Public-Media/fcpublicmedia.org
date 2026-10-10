# `site/bin/propose-shows.py`

Moved out of the file. Unreviewed.

## 1

Above `import argparse`

WHY A CONFIG AND NOT A RULE
---------------------------
Cablecast titles are episode titles, not show titles, and no rule reads them
correctly. Grouping on the first two words splits Paltrocast into three shows
(`paltrocast cast`, `paltrocast stars`, `paltrocast the`) and splits Parker St.
in two on a full stop. Splitting on " - " misses "Beware Theater Frankenstein's
Daughter", which has no separator at all. And "Democracy Now" is 249 episodes
that share one title exactly.

So the catalog cannot tell us what a show is. A person has to, once — and after
that the config remembers. This script's job is to make that once as cheap as
possible: it finds the clusters, writes a starter file, and leaves the naming
to somebody who knows the difference.

WHAT IT GETS RIGHT AND WHAT IT DOES NOT
---------------------------------------
Clustering on the FIRST word and naming from the longest common word prefix
handles the two failures above — every Paltrocast episode starts with
"paltrocast", and normalising punctuation away merges "Parker St." with
"Parker St". That is why those are the rules rather than something cleverer.

It still gets names wrong in ways only a person can see. "Stages Ep. 1" and
"Stages Ep. 2" share the prefix "stages ep", so the proposed name comes out as
"Stages Ep" — right cluster, silly name. That is the expected case, not a bug
to fix here: the proposal is a starting point for an edit, and a script that
tried to be clever about it would be wrong in less obvious ways.

THE FLOW THIS IS BUILT FOR
--------------------------
One pull request per show. Not one pull request with thirty files — each show
has to be independently mergeable, because Paltrocast being right should not
wait on Parker St. being argued about. And the steady state, once the backlog
is done, is a new series appearing and producing exactly one pull request.

Merging it is what makes the show real. Editing it first is expected.

## 2

Above `MIN_EPISODES = 3`

Below this it is a one-off, not a series. Three is deliberately low: a show
that has aired three times is a show, and a proposal nobody wants is closed
in one click, while a series that never gets proposed stays invisible.

## 3

Above `STOPWORDS = {`

First words that group nothing useful. "The" collects thirty-one unrelated
programmes whose only shared property is English.

## 4

Above `return re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).strip()`

Lower case, and punctuation reduced to spaces.

This is the line that merges "Parker St." with "Parker St", which two
separate groups in the archive is exactly the kind of thing nobody notices
and everybody finds mildly wrong.

## 5

Above `text = path.read_text(encoding="utf-8")`

The few fields we need, without a YAML parser.

Deliberately shallow: slug, and the two match lists. Anything else in the
file is somebody else's business, and a full parse would make this script
care about fields it has no opinion about.

## 6

Above `COVERAGE = 0.8`

A prefix has to be shared by most of the cluster, not all of it. One
unrelated title beginning with the same word — "Under Pressure Rehearsal"
next to forty-nine "Under the Marquee" episodes — would otherwise drag the
shared prefix down to "under", which is both a useless name and a match rule
greedy enough to swallow somebody else's show.

## 7

Above `while len(out) > 1 and out[-1] in TRAILING:`

"Stages Ep. 1" and "Stages Ep. 2" share "stages ep", which is a cluster
named after its own numbering. Drop the scaffolding, keep the name.

## 8

Above `items = [i for i in items if normalize(i.get("title")).startswith(prefix)]`

Count and describe only what the proposed rule will actually claim.
Reporting the whole first-word cluster would promise episodes the
merged config then fails to gather, and the show page would come up
short with nothing to explain why.

## 9

Above `"prefix": prefix,`

The whole common prefix, not the first word that clustered
them: "under" would claim anything beginning with it, and a
match rule that is too greedy is worse than one too narrow —
a narrow one shows up as a missing episode, a greedy one
quietly swallows somebody else's show.

## 10

Above `proposals.sort(key=lambda p: -p["episodes"])`

Most episodes first: the big ones are the ones worth naming correctly,
and they are the ones somebody will recognise on sight.

## 11

Above `samples = "\n".join(f"- {title}" for title in proposal["samples"])`

The pull request description.

Here rather than in the workflow because it was a heredoc inside a YAML
block scalar inside a shell loop, which is three levels of quoting and one
of them was already wrong. Text belongs with the thing that knows it.
