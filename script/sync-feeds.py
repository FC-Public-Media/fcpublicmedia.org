#!/usr/bin/env python3
"""Pull member feeds into _data/member_programs.json at build time.

Members publish wherever they already publish — a podcast host, a YouTube
channel, a blog — and this reads the feed. Same shape as sync-cablecast.py and
sync-calendar.py: fetch a remote source, write a data file, let the build use
it. Nothing is fetched in anyone's browser.

    python3 script/sync-feeds.py
    python3 script/sync-feeds.py --file some-feed.xml --name "Test"

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
"""

import argparse
import datetime as dt
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

try:
    import yaml
except ImportError:  # pragma: no cover - environment problem, not logic
    print(
        "error: PyYAML is needed to read _data/feeds.yml.\n"
        "       pip install pyyaml",
        file=sys.stderr,
    )
    raise SystemExit(1)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(ROOT, "_data", "feeds.yml")
OUTPUT = os.path.join(ROOT, "_data", "member_programs.json")

ATOM = "{http://www.w3.org/2005/Atom}"
MEDIA = "{http://search.yahoo.com/mrss/}"
ITUNES = "{http://www.itunes.com/dtds/podcast-1.0.dtd}"

TIMEOUT = 20
USER_AGENT = "fcpublicmedia-feed-sync/1 (+https://www.fcpublicmedia.org/)"

# Long enough for a real title or a useful summary, short enough that a feed
# with a novel in its description field cannot bloat the data file.
MAX_TITLE = 200
MAX_SUMMARY = 400

TAGS = re.compile(r"<[^>]*>")
SPACES = re.compile(r"\s+")

# Tags become a space rather than nothing, so "a<br>b" does not read as "ab".
# The cost is a gap before punctuation — "<b>something</b>." leaves "something
# ." — which this closes up again.
ORPHANED = re.compile(r"\s+([,.;:!?%)\]}»”’])")


# --------------------------------------------------------------- sanitizing


def clean(value, limit):
    """Flatten anything a feed might contain into plain, bounded text.

    Entities are decoded *before* stripping tags, so a description containing
    "&lt;script&gt;" is reduced the same way a literal "<script>" would be.
    Decoding afterwards would leave the tag intact.
    """
    if not value:
        return ""

    text = TAGS.sub(" ", html.unescape(str(value)))
    # A second pass: unescaping can reveal markup that the first sub could not
    # see, and a third pass has nothing left to find.
    text = TAGS.sub(" ", text)
    text = ORPHANED.sub(r"\1", SPACES.sub(" ", text)).strip()

    if len(text) > limit:
        text = text[:limit].rstrip() + "…"
    return text


def safe_link(value):
    """Return the URL only if it is one we are willing to put in an href.

    Feeds are third-party content and "javascript:" is a valid URL. Anything
    that is not plainly http(s) is dropped rather than rendered — an item
    without a link is a small loss; an item with a hostile one is not.
    """
    if not value:
        return ""
    url = str(value).strip()
    return url if re.match(r"^https?://", url, re.IGNORECASE) else ""


# ------------------------------------------------------------------- dates


def parse_date(value):
    """RFC 822 (RSS) or ISO 8601 (Atom). Returns None rather than raising.

    A missing or unparseable date is not a reason to drop an item — plenty of
    feeds are sloppy about it — so undated items are kept and sort last.
    """
    if not value:
        return None
    text = str(value).strip()

    try:
        parsed = parsedate_to_datetime(text)
        if parsed:
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=dt.timezone.utc)
    except (TypeError, ValueError, IndexError):
        pass

    try:
        parsed = dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=dt.timezone.utc)
    except ValueError:
        return None


# ------------------------------------------------------------------ parsing


def _text(node, *names):
    """First non-empty child matching any of the given tag names."""
    for name in names:
        found = node.find(name)
        if found is not None and (found.text or "").strip():
            return found.text
    return ""


def _image(node):
    """A picture of the thing: media:thumbnail, or a podcast's itunes:image."""
    thumbnail = node.find(f".//{MEDIA}thumbnail")
    if thumbnail is not None:
        return safe_link(thumbnail.get("url"))

    art = node.find(f".//{ITUNES}image")
    if art is not None:
        return safe_link(art.get("href"))

    return ""


def _enclosure(node):
    """The thing itself: an audio file, a video file, a download.

    Kept apart from the thumbnail, which had been sharing a field with it.
    They are not the same and only one of them is safe to put in an <img>.

    This is also the field that matters for submissions — a feed entry tells
    us a program exists, and the enclosure is what tells us where the actual
    file is. Members keep large artifacts out of their repositories, so the
    feed pointing at one is how the file ever reaches us.
    """
    found = node.find("enclosure")
    if found is None:
        for link in node.findall(f"{ATOM}link"):
            if link.get("rel") == "enclosure":
                found = link
                break
    if found is None:
        return {}

    url = safe_link(found.get("url") or found.get("href"))
    if not url:
        return {}

    return {
        "url": url,
        "type": clean(found.get("type"), 80),
        "bytes": int(found.get("length") or found.get("size") or 0) or None,
    }


def parse_rss(root):
    channel = root.find("channel")
    if channel is None:
        return []

    items = []
    for node in channel.findall("item"):
        items.append(
            {
                "title": clean(_text(node, "title"), MAX_TITLE),
                "summary": clean(_text(node, "description"), MAX_SUMMARY),
                "link": safe_link(_text(node, "link")),
                "published": parse_date(_text(node, "pubDate")),
                "image": _image(node),
                "enclosure": _enclosure(node),
            }
        )
    return items


def parse_atom(root):
    items = []
    for node in root.findall(f"{ATOM}entry"):
        # Prefer the alternate link; some feeds emit several with different
        # rels, and the self link would point back at the feed itself.
        link = ""
        for candidate in node.findall(f"{ATOM}link"):
            rel = candidate.get("rel", "alternate")
            if rel == "alternate":
                link = candidate.get("href", "")
                break
        if not link:
            first = node.find(f"{ATOM}link")
            link = first.get("href", "") if first is not None else ""

        items.append(
            {
                "title": clean(_text(node, f"{ATOM}title"), MAX_TITLE),
                # YouTube puts the description in media:description rather
                # than atom:summary, and leaves atom:summary out entirely —
                # so without this every YouTube entry has no text at all.
                "summary": clean(
                    _text(
                        node,
                        f"{ATOM}summary",
                        f".//{MEDIA}description",
                        f"{ATOM}content",
                    ),
                    MAX_SUMMARY,
                ),
                "link": safe_link(link),
                "published": parse_date(
                    _text(node, f"{ATOM}published", f"{ATOM}updated")
                ),
                "image": _image(node),
                "enclosure": _enclosure(node),
            }
        )
    return items


def parse_feed(payload):
    """Parse bytes into items. Raises ValueError on anything unusable."""
    try:
        root = ET.fromstring(payload)
    except ET.ParseError as error:
        raise ValueError(f"not valid XML ({error})")

    if root.tag == "rss" or root.find("channel") is not None:
        items = parse_rss(root)
    elif root.tag == f"{ATOM}feed":
        items = parse_atom(root)
    else:
        raise ValueError(f"not RSS or Atom (root element is {root.tag!r})")

    # An item with neither a title nor a link is not something we can render.
    return [item for item in items if item["title"] or item["link"]]


# ------------------------------------------------------------------ fetching


def _open(url):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/atom+xml, application/rss+xml, application/xml;q=0.9, */*;q=0.5",
        },
    )
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        return response.read()


# Statuses worth trying again.
#
# 404 is in here, which is not the obvious choice — normally it means the URL
# is wrong and no amount of retrying will fix it. But YouTube's feed endpoint
# returns spurious 404s and 500s for channels that plainly exist, varying by
# time of day, and it is the single most likely source a member will hand us.
#
# Retrying a genuinely dead URL costs a few seconds and still reports the
# failure afterwards, so the only thing lost is time. Being wrong in the other
# direction loses a member's programs off the page.
RETRY_STATUS = {404, 408, 425, 429, 500, 502, 503, 504}

# Five attempts with backoff is about 22 seconds of patience, which is cheap
# in a daily job and covers the short blips. A longer outage is not a retry
# problem — that is what carrying the previous run's items forward is for.
ATTEMPTS = 5
BACKOFF = 1.5


def fetch(url, opener=_open, sleeper=time.sleep, attempts=ATTEMPTS):
    """Fetch with backoff, raising the last error if it never succeeds."""
    last = None

    for attempt in range(attempts):
        try:
            return opener(url)
        except urllib.error.HTTPError as error:
            last = error
            if error.code not in RETRY_STATUS:
                raise
            # A server that told us how long to wait knows better than we do.
            pause = error.headers.get("Retry-After") if error.headers else None
            delay = float(pause) if (pause or "").strip().isdigit() else BACKOFF * (2**attempt)
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            last = error
            delay = BACKOFF * (2**attempt)

        if attempt < attempts - 1:
            print(f"    retrying in {delay:.0f}s ({last})", file=sys.stderr)
            sleeper(min(delay, 30))

    raise last


# ---------------------------------------------------------------------- main


def read_output(path):
    """The previous run's file, or an empty payload.

    A first run has nothing, and a half-written file is not worth crashing
    over — either way the answer is "no history".
    """
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return {}


def group_by_source(payload):
    """Previous items keyed by source, so a failing feed can keep its own."""
    grouped = {}
    for item in (payload or {}).get("items", []):
        grouped.setdefault(item.get("source", ""), []).append(item)
    return grouped


# Kept for callers that only want the grouping.
def load_previous(path):
    return group_by_source(read_output(path))


def collect(sources, config, now, fetcher=fetch, previous=None):
    """Read every source. Returns (items, errors)."""
    per_source = int(config.get("per_source", 6))
    months = int(config.get("months", 18))
    cutoff = now - dt.timedelta(days=months * 31)
    previous = previous or {}

    items, errors = [], []

    for source in sources:
        name = (source.get("name") or "").strip()
        url = source.get("url") or ""

        if not name or not url:
            errors.append({"name": name or url or "(unnamed)", "error": "missing name or url"})
            continue

        try:
            parsed = parse_feed(fetcher(url))
        except Exception as error:  # noqa: BLE001 — one bad host, not a crash
            # Keep what this source published last time rather than dropping
            # it. Without this, a transient 500 at sync time would quietly
            # delete a member's programs from the site and the commit would
            # record that as the new truth — a worse outcome than the outage,
            # and one nobody would notice until the member did.
            kept = [
                item
                for item in previous.get(name, [])
                if not item.get("published")
                or (parse_date(item["published"]) or now) >= cutoff
            ][:per_source]

            # Carried items are kept byte-identical rather than marked. A
            # marker would make the file differ on every outage and differ
            # again when it recovered, producing commits that record nothing a
            # visitor could see.
            items.extend(kept)
            errors.append(
                {
                    "name": name,
                    "error": f"{type(error).__name__}: {error}",
                    "carried": len(kept),
                }
            )
            print(f"  {name}: {error} — kept {len(kept)} from last time", file=sys.stderr)
            continue

        kept = 0
        for item in parsed:
            if kept >= per_source:
                break
            when = item["published"]
            if when and when < cutoff:
                continue

            items.append(
                {
                    **item,
                    "published": when.isoformat() if when else None,
                    "source": name,
                    "kind": source.get("kind") or "",
                    "owner": clean(source.get("owner"), MAX_TITLE),
                }
            )
            kept += 1

        print(f"  {name}: {kept} of {len(parsed)}", file=sys.stderr)

    # Newest first; undated last rather than first, because an undated item is
    # not necessarily new and pretending otherwise would push real news down.
    items.sort(key=lambda i: (i["published"] is not None, i["published"] or ""), reverse=True)
    return items[: int(config.get("total", 24))], errors


def status(sources, errors, carried):
    """The exit code, and the summary that explains it.

    Every feed failing usually means this script broke rather than the whole
    internet, so it earns a red mark — but only when it actually cost
    something. If the last run's items carried through, the site is intact and
    a transient outage should not turn a daily job red for nothing.
    """
    if errors:
        print(f"{len(errors)} feed(s) could not be read.", file=sys.stderr)
    if carried:
        print(f"{carried} item(s) kept from the previous run.", file=sys.stderr)

    if sources and len(errors) == len(sources) and not carried:
        print("Every feed failed and nothing was kept.", file=sys.stderr)
        return 1
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--config", default=CONFIG, help="feeds.yml to read")
    parser.add_argument("--out", default=OUTPUT, help="where to write the data file")
    parser.add_argument("--file", help="parse a local file instead of fetching")
    parser.add_argument("--name", default="Local file", help="name for --file")
    parser.add_argument("--now", help="override the clock, for tests. ISO 8601.")
    args = parser.parse_args(argv)

    now = dt.datetime.fromisoformat(args.now) if args.now else dt.datetime.now(dt.timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=dt.timezone.utc)

    if args.file:
        config = {"per_source": 100, "total": 100, "months": 12000}
        sources = [{"name": args.name, "url": args.file}]
        fetcher = lambda path: open(path, "rb").read()  # noqa: E731
    else:
        with open(args.config, encoding="utf-8") as handle:
            config = yaml.safe_load(handle) or {}
        sources = config.get("sources") or []
        fetcher = fetch

    if not sources:
        print(
            "No feeds configured. Add entries under `sources:` in "
            f"{os.path.relpath(args.config, ROOT)}.",
            file=sys.stderr,
        )

    existing = read_output(args.out)
    previous = group_by_source(existing)

    print(f"Reading {len(sources)} feed(s)...", file=sys.stderr)
    items, errors = collect(sources, config, now, fetcher, previous=previous)
    carried = sum(error.get("carried", 0) for error in errors)

    # Nothing new, nothing written.
    #
    # The output carries a timestamp, so rewriting it unconditionally makes the
    # file differ on every single run — and the workflow commits whatever
    # differs. That would be a commit every morning recording that a feed was
    # checked, which is not a thing anyone needs in the history.
    #
    # Comparing the items alone also means a failed fetch that carried
    # everything forward produces no commit at all, because the result is
    # genuinely unchanged.
    if items == existing.get("items") and os.path.exists(args.out):
        print("Nothing new.", file=sys.stderr)
        return status(sources, errors, carried)

    payload = {
        "_note": (
            "Generated by script/sync-feeds.py from the feeds listed in "
            "_data/feeds.yml. Everything here was written by somebody else — "
            "markup is already stripped, and templates escape it again."
        ),
        "generated": now.isoformat(),
        "items": items,
        "errors": errors,
    }

    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=1, ensure_ascii=False)
        handle.write("\n")

    return status(sources, errors, carried)


if __name__ == "__main__":
    sys.exit(main())
