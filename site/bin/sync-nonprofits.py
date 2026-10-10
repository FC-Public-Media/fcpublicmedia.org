#!/usr/bin/env python3
"""Pull the nearby 501(c)(3) organizations out of the IRS master file.

see docs/inline/site/bin/sync-nonprofits.py.md#1"""

import argparse
import csv
import http.client
import io
import json
import pathlib
import sys
import time
import urllib.error
import urllib.request

# see docs/inline/site/bin/sync-nonprofits.py.md#2
SOURCE = "https://www.irs.gov/pub/irs-soi/eo3.csv"

STATE = "CO"

# see docs/inline/site/bin/sync-nonprofits.py.md#3
ZIPS = {
    "80512", "80513", "80515", "80517", "80521", "80522", "80523", "80524",
    "80525", "80526", "80527", "80528", "80532", "80535", "80536", "80537",
    "80538", "80539", "80541", "80545", "80547", "80549", "80550", "80553",
}

SUBSECTION_501C3 = "03"
STATUS_UNCONDITIONAL = "01"

TIMEOUT = 300


ATTEMPTS = 4


def stream(url):
    """see docs/inline/site/bin/sync-nonprofits.py.md#4"""
    request = urllib.request.Request(url, headers={"User-Agent": "fcpm-sync"})
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        yield from csv.DictReader(io.TextIOWrapper(response, encoding="utf-8", errors="replace"))


def fetch(url, attempts=ATTEMPTS, sleep=time.sleep):
    """see docs/inline/site/bin/sync-nonprofits.py.md#5"""
    last = None
    for attempt in range(attempts):
        try:
            return collect(stream(url))
        except (urllib.error.URLError, http.client.HTTPException, OSError) as error:
            last = error
            if attempt < attempts - 1:
                delay = 2 ** attempt
                print(f"  download failed ({error}); retrying in {delay}s", file=sys.stderr)
                sleep(delay)
    raise last


def wanted(row):
    return (
        row.get("STATE") == STATE
        and (row.get("ZIP") or "")[:5] in ZIPS
        and row.get("SUBSECTION") == SUBSECTION_501C3
        and row.get("STATUS") == STATUS_UNCONDITIONAL
    )


def tidy(name):
    """see docs/inline/site/bin/sync-nonprofits.py.md#6"""
    return " ".join(name.split()).strip()


def collect(rows):
    seen = set()
    out = []
    for row in rows:
        if not wanted(row):
            continue
        ein = (row.get("EIN") or "").strip()
        # The file carries the occasional duplicate EIN across filing periods.
        if not ein or ein in seen:
            continue
        seen.add(ein)
        out.append([ein, tidy(row.get("NAME", "")), tidy(row.get("CITY", "")).title()])

    # see docs/inline/site/bin/sync-nonprofits.py.md#7
    out.sort(key=lambda entry: (entry[1], entry[0]))
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="site/assets/nonprofits.json")
    parser.add_argument("--source", default=SOURCE)
    args = parser.parse_args(argv)

    try:
        orgs = fetch(args.source)
    except Exception as error:  # noqa: BLE001 - reported, not swallowed
        print(f"could not download the IRS file: {error}", file=sys.stderr)
        return 1

    if not orgs:
        # see docs/inline/site/bin/sync-nonprofits.py.md#8
        print("no organizations matched — refusing to overwrite", file=sys.stderr)
        return 1

    payload = {"source": args.source, "county": "Larimer", "orgs": orgs}
    text = json.dumps(payload, separators=(",", ":")) + "\n"

    out = pathlib.Path(args.out)
    if out.exists() and out.read_text(encoding="utf-8") == text:
        print(f"{len(orgs)} organizations, unchanged")
        return 0

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(f"{len(orgs)} organizations written to {out} ({len(text) // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
