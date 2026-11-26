# Issues

A repository's issues are one file at its root, on main: `.issues`. Plain text, so it goes wherever the
repository goes, and it is read whole, in one look. There is nothing to page, filter or crawl.

## A line

One issue a line: a label, a space, a title.

    c The relay tries to carry bay1-identity on every beat and is refused every time, because …

The title is the whole issue. It says what the thing is to someone who has read nothing else, at whatever
length that takes. A title that has gone stale or unclear is revised.

The label is a draft letter. Lowercase is a draft, and each revision of the line moves it on one: `a`, `b`,
`c`. Capital means ready, and may start again at `A`. Any other label is allowed and is shown as written.

## Its story

Because the letter moves, every revision changes the line, so git already holds each issue's history: the
commits that touched its line, each with what it said. Anything longer than the title is said there, in the
commit that revises the line. A commit that revises one line and says why keeps the story exact; one that
revises neighbouring lines together gives them one story from there back.

    fcpm issues                 every line: its label, how many commits touched it, since when; and how
                                many lines the file held a week and 30 days ago
    fcpm issues PATH            the same, of the repository at PATH
    fcpm issues story WORDS     one issue's commits, oldest first, with the line as each left it (a few
                                words of the line in any order, or its line number)

It reads the file as committed, asks nothing of the network, and writes nothing (`machines/issues.py`;
tests `machines/test_issues.py`).

## Two branches, one line

`.gitattributes` merges `.issues` by union: a merge keeps both sides' lines and never stops on this file.
Lines added on two branches both land. A line revised differently on two branches lands twice, and
`fcpm issues` says `forked` under both, naming the other; a line caught beside one comes through twice and
is `said twice`. A line removed on one side and revised on the other comes back. Each is put right by the
next commit to the file, which is one more turn in that line's story.

The origin merges GitHub's main into ours by the same rule ([its profile](../machines/origin/PROFILE.md)).
GitHub's merge button does not: there, two branches that each change the file collide until main is merged
into the later one.
