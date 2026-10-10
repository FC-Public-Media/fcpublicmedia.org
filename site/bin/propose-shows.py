#!/usr/bin/env python3
"""Propose a `site/_shows/` entry for anything in the catalog that looks like a series.

see docs/inline/site/bin/propose-shows.py.md#1"""

import argparse
import collections
import json
import pathlib
import re
import sys

DEFAULT_CATALOG = "site/_data/cablecast.json"
DEFAULT_SHOWS = "site/_shows"

# see docs/inline/site/bin/propose-shows.py.md#2
MIN_EPISODES = 3

# see docs/inline/site/bin/propose-shows.py.md#3
STOPWORDS = {
    "the", "a", "an", "and", "of", "in", "on", "at", "to", "for", "with",
    "my", "our", "your", "this", "that", "it", "is", "new", "part", "episode",
}

# Trailing tokens that are episode scaffolding rather than part of a name.
TRAILING = {"ep", "eps", "episode", "episodes", "part", "pt", "vol", "volume", "no", "num"}


def normalize(text):
    """see docs/inline/site/bin/propose-shows.py.md#4"""
    return re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).strip()


def words(text):
    return normalize(text).split()


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")


def title_case(text):
    """Words capitalised, except the small ones that read wrong capitalised."""
    small = {"the", "a", "an", "of", "in", "on", "at", "to", "for", "with", "and"}
    parts = text.split()
    return " ".join(
        word.capitalize() if index == 0 or word not in small else word
        for index, word in enumerate(parts)
    )




# ------------------------------------------------------------ known shows


def read_front_matter(path):
    """see docs/inline/site/bin/propose-shows.py.md#5"""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}

    block = text.split("---", 2)[1]
    front = {"slug": path.stem, "prefixes": [], "producers": []}

    key = None
    for line in block.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        inline = re.match(r"^(\w+):\s*\[(.*)\]\s*$", stripped)
        if inline and inline.group(1) in ("prefixes", "producers"):
            values = [v.strip().strip("\"'") for v in inline.group(2).split(",")]
            front[inline.group(1)] = [v for v in values if v]
            key = None
            continue

        if stripped in ("prefixes:", "producers:"):
            key = stripped[:-1]
            continue

        if key and stripped.startswith("- "):
            front[key].append(stripped[2:].strip().strip("\"'"))
            continue

        plain = re.match(r"^slug:\s*(.+)$", stripped)
        if plain:
            front["slug"] = plain.group(1).strip().strip("\"'")
        if not stripped.startswith("- "):
            key = None

    return front


def load_known(directory):
    path = pathlib.Path(directory)
    if not path.exists():
        return []
    return [read_front_matter(f) for f in sorted(path.glob("*.md"))]


def claimed_by(item, known):
    """Which configured show, if any, this episode belongs to."""
    title = normalize(item.get("title"))
    producer = normalize(item.get("producer"))

    for show in known:
        for prefix in show.get("prefixes", []):
            if prefix and title.startswith(normalize(prefix)):
                return show["slug"]
        for name in show.get("producers", []):
            if name and producer == normalize(name):
                return show["slug"]
    return None


# ---------------------------------------------------------------- clusters


# see docs/inline/site/bin/propose-shows.py.md#6
COVERAGE = 0.8


def common_prefix(items, coverage=COVERAGE):
    """The longest run of words MOST titles in the cluster begin with."""
    split = [words(item.get("title")) for item in items]
    needed = max(2, int(len(split) * coverage)) if len(split) > 2 else len(split)

    out = []
    for index in range(max(len(w) for w in split)):
        counts = collections.Counter(w[index] for w in split if len(w) > index)
        word, seen = counts.most_common(1)[0]
        if seen < needed:
            break
        out.append(word)
        # Only the titles still agreeing continue to vote on the next word.
        split = [w for w in split if len(w) > index and w[index] == word]
        needed = max(2, int(len(split) * coverage)) if len(split) > 2 else len(split)

    # see docs/inline/site/bin/propose-shows.py.md#7
    while len(out) > 1 and out[-1] in TRAILING:
        out.pop()
    return out


def propose(catalog, known, minimum=MIN_EPISODES):
    unclaimed = collections.defaultdict(list)
    for item in catalog:
        if claimed_by(item, known):
            continue
        head = words(item.get("title"))
        if not head or head[0] in STOPWORDS:
            continue
        unclaimed[head[0]].append(item)

    taken = {show["slug"] for show in known}
    proposals = []

    for head, items in unclaimed.items():
        if len(items) < minimum:
            continue

        name_words = common_prefix(items) or [head]
        prefix = " ".join(name_words)

        # see docs/inline/site/bin/propose-shows.py.md#8
        items = [i for i in items if normalize(i.get("title")).startswith(prefix)]
        if len(items) < minimum:
            continue

        name = title_case(prefix)
        slug = slugify(name)
        if not slug or slug in taken:
            continue
        taken.add(slug)

        by_producer = collections.Counter(
            item.get("producer") or "" for item in items
        ).most_common(1)
        producer = by_producer[0][0] if by_producer and by_producer[0][0] else ""

        recent = sorted(items, key=lambda i: i.get("date") or "", reverse=True)

        proposals.append(
            {
                "slug": slug,
                "name": name,
                # see docs/inline/site/bin/propose-shows.py.md#9
                "prefix": prefix,
                "producer": producer,
                "episodes": len(items),
                "local": sum(1 for i in items if i.get("local")),
                "first": min((i.get("date") or "") for i in items),
                "last": max((i.get("date") or "") for i in items),
                "samples": [i.get("title", "") for i in recent[:5]],
            }
        )

    # see docs/inline/site/bin/propose-shows.py.md#10
    proposals.sort(key=lambda p: -p["episodes"])
    return proposals


# ------------------------------------------------------------------ output


def stub(proposal):
    """The file a person is going to edit. Comments are for them, not for us."""
    samples = "\n".join(f"#   {title}" for title in proposal["samples"])
    local = "yes" if proposal["local"] else "no"

    return f"""---
title: {proposal['name']}
slug: {proposal['slug']}
kind: tv

# PROPOSED AUTOMATICALLY — please check the name before merging.
#
# It was guessed from what {proposal['episodes']} episodes have in common, which gets the
# grouping right far more often than the name. Recent titles in this cluster:
#
{samples}
#
# If that is not one show, close this. If the name is wrong, fix `title` and
# leave `slug` alone unless nothing links here yet.
proposed: true

# How episodes find their way here. `prefixes` matches the start of a title
# with punctuation and case ignored, so "Parker St." and "Parker St" are one
# show. Add more if this series has been listed under several names.
match:
  prefixes:
    - {proposal['prefix']}
  producers: []

producer: {proposal['producer']}
local: {local}

# Cablecast RECORD dates, not broadcast dates. Much of the older catalog was
# bulk-loaded — these 49 episodes all carry dates two days apart in 2020 —
# so treat this as "when we got it", not "when it aired". Real airing history
# is in site/_data/airings.json.
catalog_first: {proposal['first']}
catalog_last: {proposal['last']}
---

<!--
  Anything written here shows on the show's page. A sentence about what it is
  and who makes it is worth more than a long description nobody reads.
-->
"""


def body(proposal):
    """see docs/inline/site/bin/propose-shows.py.md#11"""
    samples = "\n".join(f"- {title}" for title in proposal["samples"])

    return f"""**{proposal['episodes']} episodes** in the archive look like one series, and there is no entry
for them yet. This proposes one.

Merging it makes `{proposal['name']}` a show: it gets a page at `/watch/{proposal['slug']}/`, its
episodes group under it in the archive, and it becomes searchable by name.

### Please check the name before merging

It was worked out from what the episodes have in common, which gets the
*grouping* right far more often than the *name*. The most recent titles here:

{samples}

- **Name wrong?** Edit `title` in the file and merge.
- **Not one show?** Close this. Nothing breaks — the episodes stay findable by
  title, they just stay ungrouped.
- **Missing episodes?** Add another entry under `match.prefixes`.

Producer on record: {proposal['producer'] or '(none)'} — {proposal['local']} of {proposal['episodes']} produced locally.

Delete the `proposed: true` line once somebody has looked at it. Until then the
show's own page says out loud that the name is a guess.
"""


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", default=DEFAULT_CATALOG)
    parser.add_argument("--shows", default=DEFAULT_SHOWS)
    parser.add_argument("--min", type=int, default=MIN_EPISODES)
    parser.add_argument("--json", action="store_true", help="print the plan and write nothing")
    parser.add_argument("--write", action="store_true", help="write the stub files")
    parser.add_argument("--only", help="just this slug")
    parser.add_argument("--body", help="print the pull request text for this slug")
    args = parser.parse_args(argv)

    catalog = json.loads(pathlib.Path(args.catalog).read_text(encoding="utf-8"))["shows"]
    known = load_known(args.shows)
    proposals = propose(catalog, known, args.min)

    if args.only:
        proposals = [p for p in proposals if p["slug"] == args.only]
        if not proposals:
            print(f"no proposal for {args.only}", file=sys.stderr)
            return 1

    if args.body:
        match = [p for p in proposals if p["slug"] == args.body]
        if not match:
            print(f"no proposal for {args.body}", file=sys.stderr)
            return 1
        print(body(match[0]))
        return 0

    if args.json:
        print(json.dumps(proposals, indent=2))
        return 0

    if not args.write:
        print(f"{len(known)} shows configured, {len(proposals)} proposed:")
        for p in proposals:
            print(f"  {p['episodes']:5} episodes  {p['slug']:28} {p['name']}")
        print("\nNothing written. Pass --write to create the files.")
        return 0

    directory = pathlib.Path(args.shows)
    directory.mkdir(parents=True, exist_ok=True)
    for p in proposals:
        path = directory / f"{p['slug']}.md"
        if path.exists():
            continue
        path.write_text(stub(p), encoding="utf-8")
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
