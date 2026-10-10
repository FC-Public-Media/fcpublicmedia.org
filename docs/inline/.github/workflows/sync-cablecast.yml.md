# `.github/workflows/sync-cablecast.yml`

Moved out of the file. Unreviewed.

## 1

Above `on:`

Two jobs in one, both on the same weekly tick:

  1. Refresh site/_data/cablecast.json from the station's Cablecast catalog, so
     new programs appear in the archive without anyone doing anything.
  2. Rebuild the site even when nothing changed, so date-windowed entries in
     site/_data/featured.yml actually expire. A feature that ended on Tuesday
     should not still be on the homepage on Friday just because nobody
     pushed a commit.

Monday morning, and on demand from the Actions tab.

## 2

Above `- name: Fetch the airing history`

The airing history, from the same source on the same tick. It is a
join on the show ids the step above just fetched, so running them apart
would let the archive show counts for programs it no longer lists.

## 3

Above `- name: Rebuild anyway so expired features drop off`

A push from the step above triggers deploy.yml on its own. This only
fires when nothing changed, so expiring features still get published.
