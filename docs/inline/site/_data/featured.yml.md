# `site/_data/featured.yml`

Moved out of the file. Unreviewed.

## 1

Above `- kind: class`

What the homepage is currently featuring.

This is the whole "content management system." It is a list. Add an entry to
put something on the front page; it removes itself when `ends` passes.

Because expiry is evaluated at build time, a stale feature only disappears
when the site rebuilds. That is why .github/workflows/sync-cablecast.yml
rebuilds weekly even when nobody has pushed — so nothing advertises an event
that already happened.

kind:    class | event | show | notice — controls the small label on the card
title:   short. It is a headline, not a sentence.
blurb:   one or two lines. No paragraphs.
when:    human-readable date shown on the card. Free text.
url:     where the card goes. Internal or external.
cta:     button text. Defaults to "Details".
starts:  first day to show it. Optional; defaults to always.
ends:    last day to show it. Optional, but you almost always want it.

Order matters — the first entry gets the large treatment.

## 2

Archetypes to copy. Delete or keep as templates.

- kind: event
  title: Open House
  blurb: Tour the studios, meet the board, see what a membership gets you.
  when: Saturday, October 4
  url: /about/
  ends: 2026-10-04

- kind: show
  title: New episode of Larimer County Snapshot News
  blurb: Local reporting, produced in our studio.
  when: Premiered this week
  url: /podcasts/lcsnapshotnews/
  ends: 2026-09-01
