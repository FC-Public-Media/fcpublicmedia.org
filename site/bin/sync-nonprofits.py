#!/usr/bin/env python3
"""Pull the nearby 501(c)(3) organizations out of the IRS master file.

Streams region 3 of the IRS Business Master File (~150 MB) and keeps Colorado,
Larimer County ZIPs, subsection 03, status 01. Not every nonprofit is listed,
so the page must always offer "not listed". See docs/payments.md#nonprofit-rate.
"""

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

# Region 3 holds Colorado; change this if the IRS reorganises its regions.
SOURCE = "https://www.irs.gov/pub/irs-soi/eo3.csv"

STATE = "CO"

# Larimer County, the service area, plus Windsor across the county line.
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
    """Stream the CSV rather than reading 150 MB whole."""
    request = urllib.request.Request(url, headers={"User-Agent": "fcpm-sync"})
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        yield from csv.DictReader(io.TextIOWrapper(response, encoding="utf-8", errors="replace"))


def fetch(url, attempts=ATTEMPTS, sleep=time.sleep):
    """A whole download or an exception; a dropped connection restarts from the top."""
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
    """Collapse whitespace."""
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

    # Sorted by name so upstream reordering does not churn the diff.
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
        # Never replace a good list with nothing after an upstream layout change.
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
