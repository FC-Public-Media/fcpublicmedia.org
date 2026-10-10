#!/usr/bin/env python3
"""Pull member feeds into site/_data/member_programs.json at build time.

    python3 site/bin/sync-feeds.py
    python3 site/bin/sync-feeds.py --file some-feed.xml --name "Test"

RSS 2.0 and Atom. Feed text is untrusted; a failing feed keeps its last items.
See docs/programming.md.
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
        "error: PyYAML is needed to read site/_data/feeds.yml.\n"
        "       pip install pyyaml",
        file=sys.stderr,
    )
    raise SystemExit(1)

# site/bin/ is inside the Jekyll source; SITE is the build root.
SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(SITE, "_data", "feeds.yml")
OUTPUT = os.path.join(SITE, "_data", "member_programs.json")

ATOM = "{http://www.w3.org/2005/Atom}"
MEDIA = "{http://search.yahoo.com/mrss/}"
ITUNES = "{http://www.itunes.com/dtds/podcast-1.0.dtd}"

TIMEOUT = 20
USER_AGENT = "fcpublicmedia-feed-sync/1 (+https://www.fcpublicmedia.org/)"

MAX_TITLE = 200
MAX_SUMMARY = 400

TAGS = re.compile(r"<[^>]*>")
SPACES = re.compile(r"\s+")

# Tags become spaces ("a<br>b" is not "ab"); this closes the gap they leave before punctuation.
ORPHANED = re.compile(r"\s+([,.;:!?%)\]}»”’])")


# --------------------------------------------------------------- sanitizing


def clean(value, limit):
    """Plain, bounded text. Entities are decoded before tags are stripped."""
    if not value:
        return ""

    text = TAGS.sub(" ", html.unescape(str(value)))
    # A second pass catches markup the first one exposed.
    text = TAGS.sub(" ", text)
    text = ORPHANED.sub(r"\1", SPACES.sub(" ", text)).strip()

    if len(text) > limit:
        text = text[:limit].rstrip() + "…"
    return text


def safe_link(value):
    """The URL if it is http(s), else "": "javascript:" is a valid URL too."""
    if not value:
        return ""
    url = str(value).strip()
    return url if re.match(r"^https?://", url, re.IGNORECASE) else ""


# ------------------------------------------------------------------- dates


def parse_date(value):
    """RFC 822 (RSS) or ISO 8601 (Atom), else None. Undated items are kept and sort last."""
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
    """The media file itself, kept apart from the thumbnail in `image`."""
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
        # Prefer rel=alternate; the self link points back at the feed.
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
                # YouTube has no atom:summary; its text is media:description.
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


# 404 included: YouTube's feed endpoint returns spurious 404s and 500s for live channels.
RETRY_STATUS = {404, 408, 425, 429, 500, 502, 503, 504}

# About 22 s in all; a longer outage is what carrying items forward is for.
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
    """The previous run's file, or {} if it is missing or unreadable."""
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
            # Keep what this source published last time, so an outage does not delete it.
            kept = [
                item
                for item in previous.get(name, [])
                if not item.get("published")
                or (parse_date(item["published"]) or now) >= cutoff
            ][:per_source]

            # Unmarked, so an outage and its recovery produce no commit.
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

    # Newest first; undated last, since undated is not necessarily new.
    items.sort(key=lambda i: (i["published"] is not None, i["published"] or ""), reverse=True)
    return items[: int(config.get("total", 24))], errors


def status(sources, errors, carried):
    """Print the summary; exit 1 only when every feed failed and nothing was carried."""
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
            f"{os.path.relpath(args.config, SITE)}.",
            file=sys.stderr,
        )

    existing = read_output(args.out)
    previous = group_by_source(existing)

    print(f"Reading {len(sources)} feed(s)...", file=sys.stderr)
    items, errors = collect(sources, config, now, fetcher, previous=previous)
    carried = sum(error.get("carried", 0) for error in errors)

    # Unchanged items leave the file alone; its timestamp would otherwise make every run a commit.
    if items == existing.get("items") and os.path.exists(args.out):
        print("Nothing new.", file=sys.stderr)
        return status(sources, errors, carried)

    payload = {
        "_note": (
            "Generated by site/bin/sync-feeds.py from the feeds listed in "
            "site/_data/feeds.yml. Everything here was written by somebody else — "
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
