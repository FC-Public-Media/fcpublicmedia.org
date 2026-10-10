# `site/bin/test_sync_feeds.py`

Moved out of the file. Unreviewed.

## 1

Above `import datetime as dt`

Tests for sync-feeds.py.

Two things here are worth real coverage. One is sanitizing: every string this
script emits was written by somebody else and ends up in our HTML, so the
stripping has to hold. The other is resilience — a member's host having a bad
morning must not empty the page or fail the build.

    python3 site/bin/test_sync_feeds.py

## 2

Above `YOUTUBE = """<?xml version="1.0"?>`

What YouTube actually sends: no atom:summary at all, and the description
tucked inside media:group. Reading only atom:summary left every YouTube
entry with no text.

## 3

Above `dirty = "&lt;script&gt;alert(1)&lt;/script&gt;"`

The case that matters: a feed that escaped its HTML, so the tags are
invisible to a single pass. Decoding first and stripping after is
what makes this work, and the second pass catches the rest.

## 4

Above `self.assertEqual(items[0]["enclosure"]["url"], "https://example.com/1.mp3")`

The file and a picture of the file are different things and live in
different fields. Only one of them belongs in an <img>.

## 5

Above `items = feeds.parse_feed(ATOM.encode())`

A self link points back at the feed, which would send every visitor
to an XML document.

## 6

Above `items = feeds.parse_feed(YOUTUBE.encode())`

YouTube omits atom:summary entirely, so reading only that left every
entry on the page with a title and nothing else.

## 7

Above `items = feeds.parse_feed(YOUTUBE.encode())`

The distinction that matters for submissions: a feed entry says a
program exists, and the enclosure says where the actual file is.
A thumbnail in that slot would make an image look like a master.

## 8

Above `def fetcher(url):`

The whole point. A member's host being down is not a reason for
everyone else's programs to vanish.

## 9

Above `mixed = b"""<?xml version="1.0"?><rss version="2.0"><channel>`

An undated item is not necessarily a new one, and sorting it to the
top would push real news down.

## 10

Above `items, _ = feeds.collect(`

Merged feeds lose their context otherwise, and "who made this" is
most of the point of showing it.

## 11

Above `def http_error(self, code, headers=None):`

YouTube's feed endpoint returns spurious 404s and 500s for channels
that plainly exist, varying by time of day. Observed live: four
consecutive attempts against a real channel returning 404, 404, 500, 404.

## 12

Above `opener = self.flaky(2, code=404)`

Not the obvious choice — a 404 usually means the URL is wrong. But
YouTube returns them spuriously, and retrying a genuinely dead URL
only costs time, since the failure is still reported afterwards.

## 13

Above `def previous(self, count=3, published="2026-07-01T12:00:00+00:00"):`

A failed fetch must not delete what that source published last time.

This matters more than the retrying does. Without it, a transient 500 at
sync time produces a data file missing that member's programs, and the
workflow commits it as the new truth — so an outage nobody noticed silently
removes someone's work from the site.

## 14

Above `before = self.previous()["A Show"]`

Not marked as stale, deliberately. A marker would make the file
differ during an outage and differ again on recovery, producing
commits that record nothing a visitor could see.

## 15

Above `items, _ = feeds.collect(`

Otherwise a source that fails forever keeps its items past the
cutoff indefinitely, and the window stops meaning anything.

## 16

Above `def run_twice(self, tmp, fetcher):`

The output carries a timestamp, so writing it unconditionally makes it
differ on every run — and the workflow commits whatever differs. That is a
commit every morning recording that a feed was checked.

## 17

Above `with tempfile.TemporaryDirectory() as tmp:`

The outage case. Carrying the previous items forward reproduces the
previous result exactly, so there is nothing to commit.

## 18

Above `with tempfile.TemporaryDirectory() as tmp:`

The build reads this file unconditionally. A missing one would be a
broken site rather than an empty section.

## 19

Above `with tempfile.TemporaryDirectory() as tmp:`

One host down is weather. All of them down, with no previous run to
fall back on, usually means the parser broke — and that should not
pass quietly.

fetch is replaced rather than pointed at a dead port, so the test
does not spend the real backoff sleeping.

## 20

Above `with tempfile.TemporaryDirectory() as tmp:`

A transient outage that costs nothing should not turn a daily job
red. The site still has the programs; there is nothing to look at.

## 21

Above `def test_member_program_fields_are_escaped_in_the_template(self):`

The other half of the sanitizing lives in Liquid. Keep it there.

Stripping in this script and escaping in the template are belt and braces
on purpose, and the template half is the one somebody could plausibly
delete while tidying up — it looks redundant right until a member's blog
gets hijacked.
