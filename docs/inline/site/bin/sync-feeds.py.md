# `site/bin/sync-feeds.py`

Moved out of the file. Unreviewed.

## 1

Above `import argparse`

Members publish wherever they already publish — a podcast host, a YouTube
channel, a blog — and this reads the feed. Same shape as sync-cablecast.py and
sync-calendar.py: fetch a remote source, write a data file, let the build use
it. Nothing is fetched in anyone's browser.

    python3 site/bin/sync-feeds.py
    python3 site/bin/sync-feeds.py --file some-feed.xml --name "Test"

RSS 2.0 and Atom, which between them cover essentially everything a member is
likely to be publishing on.

ON TRUST
--------
Every title and description here was written by somebody else on a server we
do not run, and it ends up inside our HTML. So: markup is stripped, entities
are decoded and stripped again, links that are not http(s) are dropped, and
everything is length-capped. The template escapes on top of that. Both halves
are deliberate — a feed can be hijacked, and a member's blog getting owned
should not become our problem.

ON ONE BAD FEED
---------------
Feeds fail, and YouTube's fails a lot: it returns 404 and 500 for channels
that plainly exist, varying by time of day, from any client. Observed here as
fifteen consecutive failures against a channel that had worked an hour before,
with plain curl failing the same way. Three things handle it, in order of how
much they matter:

  1. RETRY. Five attempts with backoff, and 404 is treated as retryable even
     though it normally means "wrong URL" — see RETRY_STATUS.

  2. CARRY FORWARD. When a source still fails, its items from the previous run
     are kept. This is the important one: without it a transient outage
     produces a file missing that member's programs, and the workflow commits
     that as the new truth. An outage nobody noticed would silently remove
     someone's work from the site.

  3. DO NOT REWRITE. If the items come out identical, the file is left alone.
     The payload carries a timestamp, so writing unconditionally would make it
     differ every run and generate a commit every morning recording that a
     feed was checked.

The run only fails when every feed failed *and* nothing was carried — which
means this script broke rather than the whole internet.

WHY PyYAML HERE WHEN mint-claim.py AVOIDS DEPENDENCIES
------------------------------------------------------
Different audience. mint-claim.py is run by staff on a laptop, possibly years
from now, and having to resolve a dependency first would be a real obstacle.
This runs in CI, where installing a package is one line in a workflow — and
reading a commented YAML config with a hand-rolled parser would be a worse
trade than the dependency.

## 2

Above `SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))`

`site/bin/` is inside the Jekyll source, so a path here is relative to the
site rather than to the repository. SITE is the build root; REPO is the node.

## 3

Above `MAX_TITLE = 200`

Long enough for a real title or a useful summary, short enough that a feed
with a novel in its description field cannot bloat the data file.

## 4

Above `ORPHANED = re.compile(r"\s+([,.;:!?%)\]}»”’])")`

Tags become a space rather than nothing, so "a<br>b" does not read as "ab".
The cost is a gap before punctuation — "<b>something</b>." leaves "something
." — which this closes up again.

## 5

Above `if not value:`

Flatten anything a feed might contain into plain, bounded text.

Entities are decoded *before* stripping tags, so a description containing
"&lt;script&gt;" is reduced the same way a literal "<script>" would be.
Decoding afterwards would leave the tag intact.

## 6

Above `text = TAGS.sub(" ", text)`

A second pass: unescaping can reveal markup that the first sub could not
see, and a third pass has nothing left to find.

## 7

Above `if not value:`

Return the URL only if it is one we are willing to put in an href.

Feeds are third-party content and "javascript:" is a valid URL. Anything
that is not plainly http(s) is dropped rather than rendered — an item
without a link is a small loss; an item with a hostile one is not.

## 8

Above `if not value:`

RFC 822 (RSS) or ISO 8601 (Atom). Returns None rather than raising.

A missing or unparseable date is not a reason to drop an item — plenty of
feeds are sloppy about it — so undated items are kept and sort last.

## 9

Above `found = node.find("enclosure")`

The thing itself: an audio file, a video file, a download.

Kept apart from the thumbnail, which had been sharing a field with it.
They are not the same and only one of them is safe to put in an <img>.

This is also the field that matters for submissions — a feed entry tells
us a program exists, and the enclosure is what tells us where the actual
file is. Members keep large artifacts out of their repositories, so the
feed pointing at one is how the file ever reaches us.

## 10

Above `link = ""`

Prefer the alternate link; some feeds emit several with different
rels, and the self link would point back at the feed itself.

## 11

Above `"summary": clean(`

YouTube puts the description in media:description rather
than atom:summary, and leaves atom:summary out entirely —
so without this every YouTube entry has no text at all.

## 12

Above `RETRY_STATUS = {404, 408, 425, 429, 500, 502, 503, 504}`

Statuses worth trying again.

404 is in here, which is not the obvious choice — normally it means the URL
is wrong and no amount of retrying will fix it. But YouTube's feed endpoint
returns spurious 404s and 500s for channels that plainly exist, varying by
time of day, and it is the single most likely source a member will hand us.

Retrying a genuinely dead URL costs a few seconds and still reports the
failure afterwards, so the only thing lost is time. Being wrong in the other
direction loses a member's programs off the page.

## 13

Above `ATTEMPTS = 5`

Five attempts with backoff is about 22 seconds of patience, which is cheap
in a daily job and covers the short blips. A longer outage is not a retry
problem — that is what carrying the previous run's items forward is for.

## 14

Above `try:`

The previous run's file, or an empty payload.

A first run has nothing, and a half-written file is not worth crashing
over — either way the answer is "no history".

## 15

Above `kept = [`

Keep what this source published last time rather than dropping
it. Without this, a transient 500 at sync time would quietly
delete a member's programs from the site and the commit would
record that as the new truth — a worse outcome than the outage,
and one nobody would notice until the member did.

## 16

Above `items.extend(kept)`

Carried items are kept byte-identical rather than marked. A
marker would make the file differ on every outage and differ
again when it recovered, producing commits that record nothing a
visitor could see.

## 17

Above `items.sort(key=lambda i: (i["published"] is not None, i["published"] or ""), reverse=True)`

Newest first; undated last rather than first, because an undated item is
not necessarily new and pretending otherwise would push real news down.

## 18

Above `if errors:`

The exit code, and the summary that explains it.

Every feed failing usually means this script broke rather than the whole
internet, so it earns a red mark — but only when it actually cost
something. If the last run's items carried through, the site is intact and
a transient outage should not turn a daily job red for nothing.

## 19

Above `if items == existing.get("items") and os.path.exists(args.out):`

Nothing new, nothing written.

The output carries a timestamp, so rewriting it unconditionally makes the
file differ on every single run — and the workflow commits whatever
differs. That would be a commit every morning recording that a feed was
checked, which is not a thing anyone needs in the history.

Comparing the items alone also means a failed fetch that carried
everything forward produces no commit at all, because the result is
genuinely unchanged.
