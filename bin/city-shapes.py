#!/usr/bin/env python3
"""The city's shapes as facts the library can search: parks, natural areas, Transfort's routes and stops.

    python3 bin/city-shapes.py DIR [--commit] [--catalog]

DIR is a checkout of the library branch, the one in the library shed. This writes DIR/library/city/:
parks/<name>/ and natural-areas/<name>/ (facts.yml, shape.geojson), transit/routes/<route>/ (facts.yml,
shape.geojson), transit/stops/<code>.yml and README.md; with --catalog, catalog.md (bin/city-catalog.py).
Each place's facts name the city's own page for it first, and the stops and routes near it.

Every source is asked whether it changed (ETag, Last-Modified), and what it last said is kept in
~/.cache/fcpm/city, so a day with no change costs the city a 304 and writes the same bytes. --commit commits
what changed and pushes the branch to origin. Doc: docs/library.md, The city.
"""
import argparse
import csv
import datetime
import io
import json
import math
import os
import pathlib
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile

HUB = "https://services1.arcgis.com/dLpFH5mwVvxSN4OE/arcgis/rest/services/%s/FeatureServer/0/query?where=1%%3D1&outFields=*&outSR=4326&resultRecordCount=2000&f=geojson"
GTFS = "https://ridetransfort.com/wp-content/uploads/transfort_gtfs.zip"
GTFS_TERMS = "https://ridetransfort.com/wp-content/uploads/2023/12/Transfort_GTFS_License_Agreement.pdf"
PAGES = "https://www.fortcollins.gov/Parks-and-Natural-Areas-Directory/"
UA = "fcpm-library/1 (+https://www.fcpublicmedia.org)"
CACHE = pathlib.Path(os.environ.get("FCPM_CITY_CACHE") or pathlib.Path.home() / ".cache" / "fcpm" / "city")
NEAR = 400                                   # metres from a place's edge that a stop counts as near it: a five-minute walk
RECHECK = 7                                  # days before a city page is asked again


def say(what):
    print(what, flush=True)


# ------------------------------------------------------------------ fetching --
def fetch(name, url):
    """The source's bytes and when it says it last changed: asked conditionally, the cached copy on a 304."""
    CACHE.mkdir(parents=True, exist_ok=True)
    body, meta_file = CACHE / name, CACHE / (name + ".json")
    meta = json.loads(meta_file.read_text()) if meta_file.exists() and body.exists() else {}
    headers = {"User-Agent": UA}
    if meta.get("etag"):
        headers["If-None-Match"] = meta["etag"]
    if meta.get("modified"):
        headers["If-Modified-Since"] = meta["modified"]
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=180) as r:
            data = r.read()
            meta = {"url": url, "etag": r.headers.get("ETag"), "modified": r.headers.get("Last-Modified")}
        body.write_bytes(data)
        meta_file.write_text(json.dumps(meta, indent=1))
        say("%-14s changed (%s)" % (name, meta.get("modified") or "no date"))
        return data, meta
    except urllib.error.HTTPError as exc:
        if exc.code == 304 and body.exists():
            say("%-14s the same (%s)" % (name, meta.get("modified") or "no date"))
            return body.read_bytes(), meta
        raise


def page_answers(url, checked):
    """Whether the city's page answers 200 at url, asked at most once a week (checked is the cache)."""
    today = datetime.date.today().isoformat()
    was = checked.get(url)
    if was and (datetime.date.today() - datetime.date.fromisoformat(was[1])).days < RECHECK:
        return was[0] == 200
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60) as r:
            code = r.status if r.geturl().rstrip("/") == url.rstrip("/") else 0
    except urllib.error.HTTPError as exc:
        code = exc.code
    except OSError:
        code = None
    if code not in (0, 200, 404):                                # refused or unreachable: keep what it said before
        return bool(was and was[0] == 200)
    checked[url] = [code, today]
    return code == 200


# --------------------------------------------------------------------- words --
def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def titled(name):
    """SPRING PARK as Spring Park; short words and the city's abbreviations kept as people write them."""
    keep = {"NA": "NA", "CSU": "CSU", "MAX": "MAX", "ADA": "ADA", "FLEX": "FLEX", "II": "II"}
    out = []
    for w in re.split(r"(\s+|-|/|\()", name.strip()):
        out.append(keep.get(w.upper()) or (w[:1].upper() + w[1:].lower() if w.isupper() or w.islower() else w))
    s = re.sub(r"(?<=.)\b(And|Of|At|The)\b", lambda m: m.group(1).lower(), "".join(out))
    return re.sub(r"\bMc([a-z])", lambda m: "Mc" + m.group(1).upper(), s)


def page_names(name):
    """The ways the city's directory spells a place's address, likeliest first: Mallard's as Mallards, St as Street,
    Edora Community Park as Edora Park, Oak St Plaza Park as Oak Street Plaza."""
    base = re.sub(r"\bSt\b", "Street", name.replace("'", ""))
    out = []
    for n in (base, base.replace(" Community Park", " Park"), re.sub(r" Park$", "", base)):
        n = "-".join(re.sub(r"[^A-Za-z0-9 ]+", " ", n).split())
        if n and n not in out:
            out.append(n)
    return out


def yml(facts):
    """Plain YAML, a fact a line (a list as dashes below its key), quoted only where YAML needs it."""
    def scalar(v):
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return str(v)
        s = str(v)
        if not s or re.search(r"(^[\s\-?:,\[\]{}#&*!|>'\"%@`])|(: )|( #)|(\s$)", s) or s.lower() in ("yes", "no", "true", "false", "null", "on", "off"):
            return json.dumps(s, ensure_ascii=False)
        return s
    lines = []
    for k, v in facts.items():
        if v is None or v == [] or v == "":
            continue
        if isinstance(v, list):
            lines.append("%s:" % k)
            lines.extend("  - %s" % scalar(x) for x in v)
        else:
            lines.append("%s: %s" % (k, scalar(v)))
    return "\n".join(lines) + "\n"


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def feature_json(props, geometry):
    """One feature, coordinates at about a metre (6 places), keys sorted: the same shape writes the same bytes."""
    def r(c):
        return [r(x) for x in c] if isinstance(c, list) and c and isinstance(c[0], list) else [round(x, 6) for x in c]
    g = {"type": geometry["type"], "coordinates": r(geometry["coordinates"])}
    return json.dumps({"type": "Feature", "properties": props, "geometry": g}, sort_keys=True, separators=(",", ":")) + "\n"


# --------------------------------------------------------------------- shapes --
LAT0 = 40.57                                  # Fort Collins: metres per degree of longitude are figured here


def xy(lon, lat):
    return lon * 111320 * math.cos(math.radians(LAT0)), lat * 110540


def rings(geometry):
    c = geometry["coordinates"]
    polys = c if geometry["type"] == "MultiPolygon" else [c]
    return [[xy(*p[:2]) for p in ring] for poly in polys for ring in poly]


def inside(pt, ring):
    x, y, hit = pt[0], pt[1], False
    for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            hit = not hit
    return hit


def edge_distance(pt, ring):
    best = float("inf")
    for (x1, y1), (x2, y2) in zip(ring, ring[1:]):
        dx, dy = x2 - x1, y2 - y1
        t = max(0, min(1, ((pt[0] - x1) * dx + (pt[1] - y1) * dy) / (dx * dx + dy * dy))) if dx or dy else 0
        best = min(best, math.hypot(pt[0] - x1 - t * dx, pt[1] - y1 - t * dy))
    return best


class Place:
    def __init__(self, kind, name, geometry):
        self.kind, self.name, self.rings = kind, name, rings(geometry)
        xs = [p[0] for r in self.rings for p in r]
        ys = [p[1] for r in self.rings for p in r]
        self.box = (min(xs) - NEAR, min(ys) - NEAR, max(xs) + NEAR, max(ys) + NEAR)
        self.stops, self.routes = [], set()

    def near(self, pt):
        b = self.box
        if not (b[0] <= pt[0] <= b[2] and b[1] <= pt[1] <= b[3]):
            return False
        inn = sum(inside(pt, r) for r in self.rings) % 2 == 1           # holes cancel
        return inn or min(edge_distance(pt, r) for r in self.rings) <= NEAR


# ---------------------------------------------------------------------- build --
def places(layer, kind, data, meta, checked, misses):
    """The city's polygons as Places, each with its facts and shape (written later, once stops are known)."""
    out = []
    for f in json.loads(data)["features"]:
        p = f["properties"]
        raw = (p.get("PARKNAME") or p.get("NA_NAME") or "").strip()
        if not raw or not f.get("geometry"):
            continue
        name = titled(raw)
        place = Place(kind, name, f["geometry"])
        where = PAGES + ("Parks/" if kind == "park" else "Natural-Areas/")
        page = next((where + n for n in page_names(name) if page_answers(where + n, checked)), None)
        if not page:
            misses.append("%s: %s" % (kind, name))
        if kind == "park":
            addr = " ".join(str(p.get(k) or "").strip() for k in ("NUMBER_", "FDPRE", "PRE_TYPE", "FENAME", "FTYPE", "FDSUF"))
            facts = {"name": name, "kind": "park", "type": titled(p.get("PARKTYPE") or "").lower() or None,
                     "city page": page or "none found", "address": titled(" ".join(addr.split())) or None,
                     "acres": round(float(p["ACRESTTL"]), 2) if p.get("ACRESTTL") else None,
                     "opened": int(p["YEAR"]) if p.get("YEAR") else None,
                     "parking": ("%s off the street, %s on it" % (p.get("PRKNGOFFST") or 0, p.get("PRKNGONST") or 0))
                                if (p.get("PRKNGOFFST") or p.get("PRKNGONST")) else None}
        else:
            facts = {"name": name, "kind": "natural area", "city page": page or "none found",
                     "managed by": titled(p.get("MANAGER1") or "") or None,
                     "acres": round(float(p["ACRES"]), 2) if p.get("ACRES") else None,
                     "old site": ("fcgov.com/naturalareas/%s (moved)" % p["WEBSITE"]) if p.get("WEBSITE") else None}
        facts["source"] = "City of Fort Collins open data, %s layer, OBJECTID %s, as of %s" % (
            layer.replace("_", " "), p.get("OBJECTID"), meta.get("modified") or "unknown")
        place.facts, place.feature = facts, f
        out.append(place)
    return out


def transit(data):
    z = zipfile.ZipFile(io.BytesIO(data))

    def rows(name):
        with z.open(name) as fh:
            yield from csv.DictReader(io.TextIOWrapper(fh, encoding="utf-8-sig"))
    routes = {r["route_id"]: r for r in rows("routes.txt")}
    stops = {s["stop_id"]: s for s in rows("stops.txt") if s.get("location_type", "0") in ("", "0")}
    trip_route, route_shapes = {}, {}
    for t in rows("trips.txt"):
        trip_route[t["trip_id"]] = t["route_id"]
        if t.get("shape_id"):
            route_shapes.setdefault(t["route_id"], set()).add(t["shape_id"])
    stop_routes = {}
    for st in rows("stop_times.txt"):
        r = trip_route.get(st["trip_id"])
        if r and st["stop_id"] in stops:
            stop_routes.setdefault(st["stop_id"], set()).add(r)
    shapes = {}
    for s in rows("shapes.txt"):
        shapes.setdefault(s["shape_id"], []).append((int(s["shape_pt_sequence"]), float(s["shape_pt_lon"]), float(s["shape_pt_lat"])))
    info = next(rows("feed_info.txt"), {})
    return routes, stops, stop_routes, route_shapes, shapes, info


def route_label(r):
    s = r["route_short_name"]
    return "Route %s" % s if s.isdigit() else titled(r["route_long_name"] or s)


def stop_label(s):
    return "%s %s" % (s.get("stop_code") or s["stop_id"], titled(s["stop_name"]))


def build(out, catalog=False):
    checked_file = CACHE / "pages.json"
    CACHE.mkdir(parents=True, exist_ok=True)
    checked = json.loads(checked_file.read_text()) if checked_file.exists() else {}
    misses, as_of = [], {}
    parks_raw, parks_meta = fetch("parks.geojson", HUB % "Parks")
    nas_raw, nas_meta = fetch("natural-areas.geojson", HUB % "Natural_Areas")
    gtfs_raw, gtfs_meta = fetch("transfort_gtfs.zip", GTFS)
    as_of.update(parks=parks_meta.get("modified"), nas=nas_meta.get("modified"), gtfs=gtfs_meta.get("modified"))
    every = places("Parks", "park", parks_raw, parks_meta, checked, misses) + \
        places("Natural_Areas", "natural area", nas_raw, nas_meta, checked, misses)
    checked_file.write_text(json.dumps(checked, indent=1, sort_keys=True))
    routes, stops, stop_routes, route_shapes, shapes, info = transit(gtfs_raw)

    stop_near = {}
    for sid, s in stops.items():
        pt = xy(float(s["stop_lon"]), float(s["stop_lat"]))
        for place in every:
            if place.near(pt):
                place.stops.append(sid)
                place.routes |= stop_routes.get(sid, set())
                stop_near.setdefault(sid, []).append(place)

    for sub in ("parks", "natural-areas", "transit"):
        shutil.rmtree(out / sub, ignore_errors=True)
    seen = {}
    for place in every:
        folder = "parks" if place.kind == "park" else "natural-areas"
        key = slug(place.name)
        seen[(folder, key)] = seen.get((folder, key), 0) + 1
        if seen[(folder, key)] > 1:
            key = "%s-%d" % (key, seen[(folder, key)])
        f = dict(place.facts)
        src = f.pop("source")
        f["routes near"] = [route_label(routes[r]) for r in sorted(place.routes, key=sort_route) if r in routes]
        f["stops near"] = sorted(stop_label(stops[s]) for s in place.stops)
        f["source"] = src
        write(out / folder / key / "facts.yml", yml(f))
        write(out / folder / key / "shape.geojson", feature_json({"name": place.name}, place.feature["geometry"]))

    window = "%s to %s" % (fmt_day(info.get("feed_start_date")), fmt_day(info.get("feed_end_date")))
    for rid, r in routes.items():
        mine = [s for s, rs in stop_routes.items() if rid in rs]
        reach = sorted({p.name for s in mine for p in stop_near.get(s, []) if p.kind == "park"})
        reach_na = sorted({p.name for s in mine for p in stop_near.get(s, []) if p.kind != "park"})
        f = {"name": route_label(r), "kind": "bus route", "route": r["route_short_name"],
             "page": r.get("route_url") or None, "colour": ("#" + r["route_color"]) if r.get("route_color") else None,
             "parks near": reach, "natural areas near": reach_na,
             "stops": sorted(stop_label(stops[s]) for s in mine),
             "schedule": window,
             "source": "Transfort GTFS %s, as of %s; redistributed under Transfort's terms (%s); unofficial, not "
                       "endorsed by Transfort" % (info.get("feed_version", ""), gtfs_meta.get("modified") or "unknown", GTFS_TERMS)}
        key = slug(r["route_short_name"])
        write(out / "transit" / "routes" / key / "facts.yml", yml(f))
        lines, seen_lines = [], set()
        for sh in sorted(route_shapes.get(rid, ())):
            pts = [[round(lon, 6), round(lat, 6)] for _, lon, lat in sorted(shapes.get(sh, []))]
            if len(pts) > 1 and json.dumps(pts) not in seen_lines:
                seen_lines.add(json.dumps(pts))
                lines.append(pts)
        if lines:
            write(out / "transit" / "routes" / key / "shape.geojson",
                  feature_json({"name": route_label(r), "colour": f["colour"]}, {"type": "MultiLineString", "coordinates": lines}))
    for sid, s in stops.items():
        near = stop_near.get(sid, [])
        f = {"name": titled(s["stop_name"]), "kind": "bus stop", "code": s.get("stop_code") or None,
             "routes": [route_label(routes[r]) for r in sorted(stop_routes.get(sid, ()), key=sort_route) if r in routes],
             "parks near": sorted(p.name for p in near if p.kind == "park"),
             "natural areas near": sorted(p.name for p in near if p.kind != "park"),
             "at": "%s, %s" % (s["stop_lat"], s["stop_lon"]),
             "source": "Transfort GTFS %s; unofficial, not endorsed by Transfort" % info.get("feed_version", "")}
        write(out / "transit" / "stops" / ("%s.yml" % slug(s.get("stop_code") or s["stop_id"])), yml(f))

    if catalog:
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run([sys.executable, str(pathlib.Path(__file__).with_name("city-catalog.py")), "--out", tmp],
                           check=True, stdout=subprocess.DEVNULL)
            text = (pathlib.Path(tmp) / "catalog.md").read_text(encoding="utf-8")
            write(out / "catalog.md", re.sub(r"^Pulled \S+ by", "Pulled by", text, flags=re.M))

    n_parks = sum(p.kind == "park" for p in every)
    write(out / "README.md", README.format(
        parks=n_parks, nas=len(every) - n_parks, routes=len(routes), stops=len(stops), near=NEAR,
        parks_as_of=as_of["parks"] or "unknown", nas_as_of=as_of["nas"] or "unknown", gtfs_as_of=as_of["gtfs"] or "unknown",
        window=window, terms=GTFS_TERMS, pages=PAGES, hub=HUB.split("/%s")[0], gtfs=GTFS,
        found=len(every) - len(misses), places=len(every),
        misses="\n".join("- %s" % m for m in sorted(misses)) or "- none"))
    say("wrote     %d parks, %d natural areas, %d routes, %d stops; %d of %d places have a city page"
        % (n_parks, len(every) - n_parks, len(routes), len(stops), len(every) - len(misses), len(every)))


def sort_route(rid):
    return (0, int(rid), "") if rid.isdigit() else (1, 0, rid)


def fmt_day(d):
    return "%s-%s-%s" % (d[:4], d[4:6], d[6:]) if d and len(d) == 8 else "unknown"


README = """# The city's shapes

Fort Collins' parks, natural areas and Transfort's bus routes and stops, as facts we can search. A folder
or file each. Every place names the city's own page for it first, then the stops and routes near it
(a stop within {near} m of its edge, a five-minute walk). Written by `bin/city-shapes.py` from what the city publishes;
asked once a day whether anything changed. We are not the authority on any of it.

| what | count | from | as of |
|---|---|---|---|
| parks/ | {parks} | the city's Parks layer ({hub}/Parks) | {parks_as_of} |
| natural-areas/ | {nas} | the city's Natural Areas layer ({hub}/Natural_Areas) | {nas_as_of} |
| transit/routes/ | {routes} | Transfort's GTFS ({gtfs}), schedule {window} | {gtfs_as_of} |
| transit/stops/ | {stops} | the same | |

The bus data is redistributed under Transfort's terms ({terms}): the data only, never Transfort's marks.
This is unofficial and not endorsed by Transfort.

{found} of {places} places have a page at {pages}, matched by name and asked once a week. These have none
found by name yet:

{misses}
"""


def commit(root):
    def git(*a, check=True):
        return subprocess.run(["git", "-C", str(root), *a], capture_output=True, text=True, check=check)
    git("add", "-A", "library/city")
    if git("diff", "--cached", "--quiet", check=False).returncode == 0:
        say("commit    nothing changed")
        return
    stat = git("diff", "--cached", "--shortstat").stdout.strip()
    who = "FCPM library on %s" % socket.gethostname().split(".")[0]
    git("-c", "user.name=" + who, "-c", "user.email=317985568+fcpm-public@users.noreply.github.com",
        "-c", "commit.gpgsign=false", "commit", "-q", "-m", "city: what the city's shapes say now (%s)" % stat)
    say("commit    %s" % git("log", "-1", "--format=%h %s").stdout.strip())
    r = git("push", "-q", "origin", "HEAD", check=False)
    say("push      %s" % ("on origin" if r.returncode == 0 else "waits: " + (r.stderr.strip().splitlines() or ["?"])[-1]))


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("dir", type=pathlib.Path)
    ap.add_argument("--commit", action="store_true")
    ap.add_argument("--catalog", action="store_true")
    a = ap.parse_args(argv)
    root = a.dir.expanduser().resolve()
    if not (root / ".git").exists():
        sys.exit("city-shapes: %s is not a checkout (the library shed's library branch)" % root)
    build(root / "library" / "city", catalog=a.catalog)
    if a.commit:
        commit(root)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
