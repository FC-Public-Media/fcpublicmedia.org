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
A host that is down, or serving HTML where XML was promised, is reported and
skipped. It must not fail the run: a member's hosting provider having a bad
morning is not a reason for this repository to go red, and it is not a reason
for everyone else's programs to vanish from the page.

The exception is *everything* failing, which usually means this script broke
rather than the whole internet, and is worth a red mark.

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


def parse_rss(root):
    channel = root.find("channel")
    if channel is None:
        return []

    items = []
    for node in channel.findall("item"):
        enclosure = node.find("enclosure")
        items.append(
            {
                "title": clean(_text(node, "title"), MAX_TITLE),
                "summary": clean(_text(node, "description"), MAX_SUMMARY),
                "link": safe_link(_text(node, "link")),
                "published": parse_date(_text(node, "pubDate")),
                "media": safe_link(enclosure.get("url")) if enclosure is not None else "",
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

        thumbnail = node.find(f".//{MEDIA}thumbnail")

        items.append(
            {
                "title": clean(_text(node, f"{ATOM}title"), MAX_TITLE),
                "summary": clean(
                    _text(node, f"{ATOM}summary", f"{ATOM}content"), MAX_SUMMARY
                ),
                "link": safe_link(link),
                "published": parse_date(
                    _text(node, f"{ATOM}published", f"{ATOM}updated")
                ),
                "media": safe_link(thumbnail.get("url")) if thumbnail is not None else "",
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


def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        return response.read()


# ---------------------------------------------------------------------- main


def collect(sources, config, now, fetcher=fetch):
    """Read every source. Returns (items, errors)."""
    per_source = int(config.get("per_source", 6))
    months = int(config.get("months", 18))
    cutoff = now - dt.timedelta(days=months * 31)

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
            errors.append({"name": name, "error": f"{type(error).__name__}: {error}"})
            print(f"  {name}: {error}", file=sys.stderr)
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

    print(f"Reading {len(sources)} feed(s)...", file=sys.stderr)
    items, errors = collect(sources, config, now, fetcher)

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

    print(f"{len(items)} item(s) from {len(sources) - len(errors)} feed(s).", file=sys.stderr)
    if errors:
        print(f"{len(errors)} feed(s) could not be read.", file=sys.stderr)

    # One host being down is normal. Every host being down usually means this
    # script is broken, which is worth failing over.
    if sources and len(errors) == len(sources):
        print("Every feed failed — check the parser before blaming the hosts.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
