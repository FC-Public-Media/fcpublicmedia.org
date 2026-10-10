# `site/bin/test_propose_shows.py`

Moved out of the file. Unreviewed.

## 1

Above `import importlib.util`

Tests for the show proposer.

The failures worth catching are the ones that produced a plausible-looking
wrong answer: a show split into three because its episodes have different
second words, or two shows merged because one name is a prefix of another.
Both look fine in a list and are wrong in the archive.

Fixtures are shaped like the real catalog, including the specific messes it
contains — Paltrocast's varying second word, Parker St.'s inconsistent full
stop, Stages numbering its own episodes.

## 2

Above `catalog = [`

The real failure: grouping on two words made Paltrocast into
"paltrocast cast", "paltrocast stars" and "paltrocast the".

## 3

Above `catalog = [`

"Parker St." and "Parker St" were two groups in the archive, which is
the kind of wrong nobody reports and everybody notices.

## 4

Above `catalog = [item(f"Under the Marquee - {n}") for n in "ABCD"]`

"under" would claim anything starting with it. A greedy match rule
silently swallows somebody else's show; a narrow one just shows up as
a missing episode, which somebody notices and reports.

## 5

Above `catalog = [`

Some series were listed under several unrelated titles. The producer
is the only thing they have in common.

## 6

Above `catalog = [item(f"Under the Marquee - {n}") for n in "ABCDEF"]`

The one that matters: a proposal is only useful if merging it
actually gathers the episodes it was made from. A mismatch between
what the proposer clusters and what the config matches would leave a
show page empty and nobody would know why.

## 7

Above `import json`

Not an assertion about any particular show — those change. This is
here so a change to the clustering that blows up on real titles fails
in CI rather than in a workflow run at three in the morning.
