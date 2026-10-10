# `site/bin/sync-cablecast.py`

Moved out of the file. Unreviewed.

## 1

Above `import json`

Pull the Cablecast catalog into site/_data/cablecast.json.

Cablecast's public API needs no key and sends Access-Control-Allow-Origin: *,
so this could run in the browser. It runs at build time instead, because a
snapshot in the repository means the archive is real HTML: indexable by search
engines, readable without JavaScript, and still there if Cablecast is down.

Run it by hand, or let .github/workflows/sync-cablecast.yml run it weekly.

    python3 site/bin/sync-cablecast.py

Standard library only, on purpose. There is nothing to install.

## 2

Above `RECENT = 24`

How many recent shows the homepage and /watch/ pull from. The full archive
page uses everything.

## 3

Above `LOCAL_PREFIXES = ("Local", "Fort Collins", "FoCo")`

Which Cablecast categories count as locally produced.

This matters because the raw "most recent" list is dominated by syndicated
programming — Free Speech TV and Paltrocast alone account for hundreds of
entries — which buries the work Fort Collins people actually made. The site
features LOCAL_PREFIXES separately so local production leads.

This is a starting guess based on the existing category names. Correct it:
it is the one judgement call in this script.

## 4

Above `if not (s.get("title") or "").strip():`

426 records in the catalog have no title at all, and none of them
have a VOD. Published, they become blank clickable rows — a third of
the archive rendering as nothing. They are almost certainly stubs or
deleted entries rather than programs anyone can watch.

Dropped here rather than hidden in the template, so the count is
visible on the archive page and someone can go fix the records.

## 5

Above `watchable = bool(s.get("vods"))`

A show with no VOD cannot be watched on the site — it aired on cable
and was never encoded. Keep it in the archive anyway; it is still a
record that the program exists, which is more than we have today.

## 6

Above `stamp = os.environ.get("SYNC_STAMP")`

Keep the timestamp out of the payload when running locally so that a
no-op sync produces no diff and the weekly job stays quiet.
