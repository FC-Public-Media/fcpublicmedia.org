#!/usr/bin/env python3
"""see docs/inline/site/bin/sync-cablecast.py.md#1"""

import json
import os
import sys
import urllib.request

BASE = "https://reflect-fcpublicmedia.cablecast.tv/cablecastapi/v1"
OUT = os.path.join(os.path.dirname(__file__), "..", "_data", "cablecast.json")

# see docs/inline/site/bin/sync-cablecast.py.md#2
RECENT = 24

# see docs/inline/site/bin/sync-cablecast.py.md#3
LOCAL_PREFIXES = ("Local", "Fort Collins", "FoCo")
LOCAL_EXTRA = {"PSA - FCPM", "Nonprofit Awareness", "Church Services", "Meetings"}


def is_local(category):
    return category.startswith(LOCAL_PREFIXES) or category in LOCAL_EXTRA


def get(path):
    req = urllib.request.Request(
        BASE + path, headers={"Accept": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=120) as response:
        return json.load(response)


def main():
    print("Fetching categories and producers...")
    categories = {c["id"]: c["name"].strip() for c in get("/categories")["categories"]}
    producers = {
        p["id"]: (p.get("name") or "").strip() for p in get("/producers")["producers"]
    }

    print("Fetching shows...")
    total = get("/shows?page_size=1")["meta"]["count"]
    raw = get("/shows?page_size=%d" % (total + 100))["shows"]
    print("  %d shows" % len(raw))

    shows = []
    untitled = 0
    for s in raw:
        # see docs/inline/site/bin/sync-cablecast.py.md#4
        if not (s.get("title") or "").strip():
            untitled += 1
            continue

        # see docs/inline/site/bin/sync-cablecast.py.md#5
        watchable = bool(s.get("vods"))

        thumb = (s.get("thumbnailImage") or {}).get("url") or ""

        shows.append(
            {
                "id": s["id"],
                "title": (s.get("title") or "").strip(),
                "date": (s.get("eventDate") or "")[:10],
                "category": categories.get(s.get("category"), ""),
                "producer": producers.get(s.get("producer"), ""),
                "notes": (s.get("comments") or "").strip(),
                "local": is_local(categories.get(s.get("category"), "")),
                "seconds": s.get("totalRunTime") or 0,
                "thumb": thumb,
                "watchable": watchable,
                "watch_url": (
                    "https://reflect-fcpublicmedia.cablecast.tv"
                    "/internetchannel/show/%d" % s["id"]
                ),
                "embed_url": (
                    "https://reflect-fcpublicmedia.cablecast.tv"
                    "/internetchannel/watch-vod-embed?showId=%d" % s["id"]
                ),
            }
        )

    # Newest first, undated last.
    shows.sort(key=lambda s: (s["date"] or "0000", s["id"]), reverse=True)

    counts = {}
    for s in shows:
        name = s["category"] or "Uncategorized"
        counts[name] = counts.get(name, 0) + 1

    data = {
        "fetched": None,  # stamped by the workflow; see below
        "total": len(shows),
        "untitled_omitted": untitled,
        "watchable": sum(1 for s in shows if s["watchable"]),
        "categories": sorted(
            ({"name": k, "count": v} for k, v in counts.items()),
            key=lambda c: (-c["count"], c["name"]),
        ),
        "local_total": sum(1 for s in shows if s["local"]),
        "recent": shows[:RECENT],
        "recent_local": [s for s in shows if s["local"]][:RECENT],
        "shows": shows,
    }

    # see docs/inline/site/bin/sync-cablecast.py.md#6
    stamp = os.environ.get("SYNC_STAMP")
    if stamp:
        data["fetched"] = stamp

    with open(OUT, "w") as f:
        json.dump(data, f, indent=1, sort_keys=True)
        f.write("\n")

    print(
        "Wrote %s: %d shows, %d watchable, %d categories"
        % (OUT, data["total"], data["watchable"], len(data["categories"]))
    )
    if untitled:
        print("  omitted %d catalog records with no title" % untitled)


if __name__ == "__main__":
    sys.exit(main())
