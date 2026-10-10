# `troves/pools/episodes.py`

Moved out of the file. Unreviewed.

## 1

Above `import json`

Release hands an episode on, and this is what it is handed to (the production
crew runs `tick` every few minutes: crews/production/services). A held episode
is left alone. A released one is admitted to post (troves/post/README.md,
*Admission*): what releasing rendered (its show, out name, pipeline and
recordings) becomes a take, a folder on E:\POST that carries its whole route.
From there the pools page is no longer the one talking about it; post's
workers take its steps, and the disk is the record of how far it got.

What is admitted is the ejected config if releasing wrote one (what was
released is what runs), else what the pools server renders now: the show's
pipeline, read fresh, and the episode's recordings less what is marked for
removal. Admitting the same release twice finds the same take, so a pass that
is interrupted is simply run again.

The pools server stays the one writer of the groups: the episode is read from
it, and its admission comes back to it as an event on the episode (/supervised,
step `admit`). Nothing is remembered here.
