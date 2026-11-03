#!/usr/bin/env python3
"""Fort Collins' open data, both portals, as one list.

    python3 bin/city-catalog.py [--out DIR]     writes DIR/catalog.json and DIR/catalog.md

The city's portal moved in 2026: opendata.fcgov.com now says "This site has moved" and sends
people to an Esri ArcGIS Hub. The Tyler/Socrata portal it replaced is still live and still
updated, at fortcollins.data.socrata.com, where every old deep link works with the host
swapped (/d/<id>). The Hub holds fewer datasets, and some of its descriptions are unfilled
templates ("{{description}}"), so each Hub item's own ArcGIS record is read too.

Both answer without a key. Every dataset lands once, matched by title, saying where it lives
now: both portals, Socrata only, or the Hub only. Its description and columns are the label
reducer's first corpus. Reads only; nothing is sent but the requests. Default DIR: ~/fcpm/city.
"""

import argparse
import datetime
import html
import json
import pathlib
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

SOCRATA = "fortcollins.data.socrata.com"    # where the Tyler portal answers now
SOCRATA_DOMAIN = "opendata.fcgov.com"       # the name Socrata's catalog still files it under
CATALOG = "https://api.us.socrata.com/api/catalog/v1"
HUB = "https://open-data-fcgov.hub.arcgis.com"
ITEM = "https://www.arcgis.com/sharing/rest/content/items/"
PAGE = 100
TIMEOUT = 60
ATTEMPTS = 4


def fetch(url, attempts=ATTEMPTS, sleep=time.sleep):
    """GET a URL as JSON, asking again after a pause when the network or the server stumbles."""
    for attempt in range(attempts):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "fcpm-city-catalog"})
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                return json.load(response)
        except (urllib.error.URLError, TimeoutError, ValueError):
            if attempt == attempts - 1:
                raise
            sleep(2 ** attempt)


def plain(text):
    """Markup and entities out, whitespace folded; a template left unfilled reads as nothing."""
    text = html.unescape(re.sub(r"<[^>]+>", " ", text or ""))
    text = re.sub(r"\s+([.,;:!?])", r"\1", re.sub(r"\s+", " ", text)).strip()
    return "" if re.fullmatch(r"\{\{[^}]*\}\}", text) else text


def key(title):
    """What two portals' titles share. The Hub renamed some as it copied them: BikeFacilities for
    Bike Facilities, "(30-day rolling)" added, "Current " and "Fort Collins " dropped, DEPR added."""
    t = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", title or "")          # BikeFacilities -> Bike Facilities
    t = re.sub(r"\([^)]*\)", " ", t.lower()).replace("&", " and ")
    t = re.sub(r"[^a-z0-9]+", " ", t).strip()
    t = re.sub(r"^(city of )?(fort collins )?(current )?", "", t)
    return re.sub(r"\s+depr$", "", t).strip()


# ---- Socrata (Tyler) --------------------------------------------------------------------------

def socrata(get=fetch, counts=True):
    out, offset = [], 0
    while True:
        page = get("%s?%s" % (CATALOG, urllib.parse.urlencode(
            {"domains": SOCRATA_DOMAIN, "limit": PAGE, "offset": offset})))
        results = page.get("results") or []
        for r in results:
            out.append(socrata_entry(r, get if counts else None))
        offset += len(results)
        if not results or offset >= page.get("resultSetSize", 0):
            return out


def socrata_entry(r, get=None):
    res, cls = r.get("resource") or {}, r.get("classification") or {}
    rid = res.get("id")
    cols = [{"name": n, "field": f, "type": t, "description": plain(d)}
            for n, f, t, d in zip(res.get("columns_name") or [], res.get("columns_field_name") or [],
                                  res.get("columns_datatype") or [], res.get("columns_description") or [])
            if not f.startswith("meta_row_")]
    e = {"id": rid, "title": res.get("name"), "kind": res.get("type"),
         "description": plain(res.get("description")), "category": cls.get("domain_category"),
         "tags": cls.get("domain_tags") or [], "updated": (res.get("updatedAt") or "")[:10],
         "created": (res.get("createdAt") or "")[:10], "link": "https://%s/d/%s" % (SOCRATA, rid),
         "columns": cols, "views": (res.get("page_views") or {}).get("page_views_total"),
         "downloads": res.get("download_count")}
    if res.get("type") == "dataset":
        e["api"] = "https://%s/resource/%s.json" % (SOCRATA, rid)
        if get:
            try:
                e["rows"] = int(get(e["api"] + "?$select=count(*)%20as%20n")[0]["n"])
            except (urllib.error.URLError, TimeoutError, ValueError, KeyError, IndexError, TypeError):
                e["rows"] = None
    return e


# ---- ArcGIS Hub (Esri) ------------------------------------------------------------------------

def hub(get=fetch, counts=True):
    feed = get(HUB + "/api/feed/dcat-us/1.1.json")
    return [hub_entry(d, get, counts) for d in feed.get("dataset") or []]


def hub_entry(d, get=fetch, counts=True):
    ident = d.get("identifier") or ""
    m = re.search(r"[?&]id=([0-9a-f]{32})", ident)
    iid = m.group(1) if m else ident
    service = next((x.get("accessURL") for x in d.get("distribution") or []
                    if "GeoServices" in (x.get("format") or "")), None)
    e = {"id": iid, "title": d.get("title"), "kind": "dataset", "description": plain(d.get("description")),
         "tags": d.get("keyword") or [], "updated": (d.get("modified") or "")[:10],
         "created": (d.get("issued") or "")[:10], "link": d.get("landingPage"), "api": service, "columns": []}
    if not e["description"] and m:
        # The feed's own text was an unfilled template; the item's record says what it is.
        try:
            item = get(ITEM + iid + "?f=json")
            e["description"] = plain(item.get("description")) or plain(item.get("snippet"))
            e["description_from"] = "item"
        except (urllib.error.URLError, TimeoutError, ValueError):
            pass
    if service:
        try:
            layer = get(service + "?f=json")
            e["kind"] = (layer.get("type") or "dataset").lower()
            e["columns"] = [{"name": f.get("alias") or f.get("name"), "field": f.get("name"),
                             "type": (f.get("type") or "").replace("esriFieldType", ""), "description": ""}
                            for f in layer.get("fields") or []
                            if not (f.get("name") or "").startswith("meta_row_") and f.get("name") != "ObjectId"]
            if counts:
                e["rows"] = get(service + "/query?where=1%3D1&returnCountOnly=true&f=json").get("count")
        except (urllib.error.URLError, TimeoutError, ValueError):
            pass
    return e


# ---- one list -----------------------------------------------------------------------------------

def join(soc, hb):
    entries = {}
    for side, items in (("socrata", soc), ("hub", hb)):
        for e in items:
            k = key(e["title"])
            entry = entries.setdefault(k, {"title": e["title"], "socrata": None, "hub": None})
            if entry[side] is None:
                entry[side] = e
            else:                       # one title twice on a portal (a dataset and its map): the dataset leads
                if e.get("kind") == "dataset" and entry[side].get("kind") != "dataset":
                    entry[side], e = e, entry[side]
                entry.setdefault(side + "_more", []).append(e)
    for entry in entries.values():
        entry["where"] = "both" if entry["socrata"] and entry["hub"] else "socrata" if entry["socrata"] else "hub"
    return sorted(entries.values(), key=lambda e: (e["where"], (e["title"] or "").lower()))


def first(text, n=140):
    s = re.split(r"(?<=[.!?])\s", text or "", maxsplit=1)[0]
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def markdown(cat):
    es = cat["entries"]
    count = lambda w: sum(1 for e in es if e["where"] == w)
    data = [e for e in es if (e["socrata"] or {}).get("kind") == "dataset" or e["hub"]]
    lines = ["# Fort Collins open data, both portals", "",
             "Pulled %s by `bin/city-catalog.py`. Socrata (Tyler): https://%s. ArcGIS Hub (Esri): %s." % (
                 cat["pulled"], SOCRATA, HUB), "",
             "- %d titles in all: %d on both portals, %d on Socrata only, %d on the Hub only." % (
                 len(es), count("both"), count("socrata"), count("hub")),
             "- %d Hub descriptions were unfilled templates and came from the item's own record." % sum(
                 1 for e in es if (e["hub"] or {}).get("description_from") == "item"),
             "- %d more titles are Socrata's charts, maps, filters, links and stories, built on its datasets; "
             "they are in catalog.json, not in the table." % (len(es) - len(data)),
             "- Titles are matched loosely (case, spacing, \"Fort Collins\", \"Current\", parentheses, DEPR); "
             "a dataset the Hub renamed further shows up twice, once per portal.", "",
             "| where | title | updated | rows | columns | says |", "| --- | --- | --- | --- | --- | --- |"]
    for e in data:
        s = e["socrata"] if e["socrata"] and e["socrata"].get("kind") == "dataset" else None
        h = e["hub"]
        main = s or h
        updated = max((x.get("updated") or "") for x in (s, h) if x)
        rows = next((x.get("rows") for x in (h, s) if x and x.get("rows") is not None), None)
        link = "[%s](%s)" % ((e["title"] or "").replace("|", "/"), main["link"])
        lines.append("| %s | %s | %s | %s | %d | %s |" % (
            e["where"], link, updated, "" if rows is None else "{:,}".format(rows), len(main["columns"]),
            first(main["description"] or (h or {}).get("description") or "").replace("|", "/")))
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default=str(pathlib.Path.home() / "fcpm" / "city"))
    ap.add_argument("--no-counts", action="store_true", help="skip asking each dataset for its row count")
    a = ap.parse_args(argv)
    soc, hb = socrata(counts=not a.no_counts), hub(counts=not a.no_counts)
    cat = {"pulled": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
           "sources": {"socrata": {"site": "https://" + SOCRATA, "items": len(soc)},
                       "hub": {"site": HUB, "items": len(hb)}},
           "entries": join(soc, hb)}
    out = pathlib.Path(a.out).expanduser()
    out.mkdir(parents=True, exist_ok=True)
    (out / "catalog.json").write_text(json.dumps(cat, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    (out / "catalog.md").write_text(markdown(cat), encoding="utf-8")
    print("city-catalog: %d Socrata items, %d Hub datasets -> %s" % (len(soc), len(hb), out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
