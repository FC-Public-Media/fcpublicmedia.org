#!/usr/bin/env python3
"""The city's shapes as lines the library can search: parks, natural areas, Transfort's routes and stops.

    python3 machines/digitization/city-shapes.py DIR [--commit] [--catalog]

DIR is a checkout of the library branch, the one in the library shed. This writes DIR/library/city/: a folder per
thing (parks/, natural-areas/, transit/routes/, transit/stops/), each holding shape.geojson and city.scopes, this
reader's lines about it (machines/scopes.py: park.spring-park.near.route.14), and WORN.scopes, what everything under
city/ wears. With --catalog, catalog.md (machines/digitization/city-catalog.py). It writes and removes only its own files: other
readers' .scopes beside them are theirs (machines/digitization/city-layers.py).

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

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "machines"))
sys.dont_write_bytecode = True
import scopes  # noqa: E402

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


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def feature_json(props, geometry):
    """One feature, its coordinates as the source gave them, keys sorted: the same shape writes the same bytes."""
    g = {"type": geometry["type"], "coordinates": geometry["coordinates"]}
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

    def near(self, pt, reach=NEAR):
        b = self.box
        if not (b[0] <= pt[0] <= b[2] and b[1] <= pt[1] <= b[3]):
            return False
        inn = sum(inside(pt, r) for r in self.rings) % 2 == 1           # holes cancel
        return inn or min(edge_distance(pt, r) for r in self.rings) <= reach


# ---------------------------------------------------------------------- build --
def as_is(v):
    """A source's value as it sent it: its own text for a number (json.loads(parse_float=str)), never rounded or cast."""
    return None if v is None or (isinstance(v, str) and not v.strip()) else v


def places(layer, kind, data, meta, checked, misses):
    """The city's polygons as Places, each with its facts and shape (written later, once stops are known). Every value
    is the layer's own; ours are only the thing's id, its page (asked of the city's site) and what is near it."""
    out = []
    shown = json.loads(data, parse_float=str)["features"]
    for f, said in zip(json.loads(data)["features"], shown):
        p = said["properties"]
        raw = (p.get("PARKNAME") or p.get("NA_NAME") or "").strip()
        if not raw or not f.get("geometry"):
            continue
        place = Place(kind, raw, f["geometry"])
        where = PAGES + ("Parks/" if kind == "park" else "Natural-Areas/")
        page = next((where + n for n in page_names(titled(raw)) if page_answers(where + n, checked)), None)
        if not page:
            misses.append("%s: %s" % (kind, raw))
        pid = slug(raw)
        place.id = pid
        root = ("park", pid) if kind == "park" else ("natural-area", pid)
        facts = [root, root + ("name", raw), root + ("page", page or "none found")]
        fields = ((("type", "PARKTYPE"), ("address", "number", "NUMBER_"), ("address", "prefix", "FDPRE"),
                   ("address", "prefix type", "PRE_TYPE"), ("address", "street", "FENAME"), ("address", "street type", "FTYPE"),
                   ("address", "suffix", "FDSUF"), ("acres", "ACRESTTL"), ("acres", "developed", "ACRESDEV"),
                   ("acres", "undeveloped", "ACRESUNDEV"), ("opened", "YEAR"), ("parking", "off street", "PRKNGOFFST"),
                   ("parking", "on street", "PRKNGONST"))
                  if kind == "park" else (("managed by", "MANAGER1"), ("acres", "ACRES"), ("website", "WEBSITE")))
        facts += [root + tuple(k[:-1]) + (as_is(p.get(k[-1])),) for k in fields if as_is(p.get(k[-1])) is not None]
        facts.append(root + ("source", layer.replace("_", " ").lower() + " layer", "objectid", p.get("OBJECTID")))
        place.root = root
        place.facts, place.feature = [x for x in facts if x], f
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


def route_id(r):
    return slug(r["route_short_name"] or r["route_id"])


def route_name(r):
    return r["route_long_name"] or r["route_short_name"]


def stop_id(s):
    return slug(s.get("stop_code") or s["stop_id"])


def put(path, rows):
    """A reader's lines about one thing, a line each, in the order given, each said once."""
    text = "".join(scopes.line(*r) + "\n" for r in dict.fromkeys(tuple(r) for r in rows if r))
    write(path, text)


def clear(out):
    """This reader's own files under out, and only those (and the nested facts it wrote before scopes)."""
    for name in ("city.scopes", "shape.geojson", "facts.yml"):
        for f in out.rglob(name):
            f.unlink()
    for f in (out / "transit" / "stops").glob("*.yml"):
        f.unlink()
    for d in sorted((x for x in out.rglob("*") if x.is_dir()), key=lambda x: -len(x.parts)):
        if not any(d.iterdir()):
            d.rmdir()


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

    clear(out)
    write(out / scopes.WORN, "city.fort-collins\n")
    seen = {}
    for place in every:
        folder = "parks" if place.kind == "park" else "natural-areas"
        n = seen[(folder, place.id)] = seen.get((folder, place.id), 0) + 1
        if n > 1:
            place.id = "%s-%d" % (place.id, n)
            place.root = (place.root[0], place.id)
            place.facts = [place.root + tuple(x[2:]) for x in place.facts]
    for place in every:
        folder = "parks" if place.kind == "park" else "natural-areas"
        rows = list(place.facts)
        rows += [place.root + ("near", "route", route_id(routes[r])) for r in sorted(place.routes, key=sort_route) if r in routes]
        rows += [place.root + ("near", "stop", stop_id(stops[s])) for s in sorted(place.stops, key=lambda s: stop_id(stops[s]))]
        put(out / folder / place.id / "city.scopes", rows)
        write(out / folder / place.id / "shape.geojson", feature_json({"name": place.name}, place.feature["geometry"]))

    version = info.get("feed_version", "")
    window = "%s to %s" % (info.get("feed_start_date") or "unknown", info.get("feed_end_date") or "unknown")
    for rid, r in sorted(routes.items(), key=lambda x: sort_route(x[0])):
        root = ("route", route_id(r))
        mine = sorted((s for s, rs in stop_routes.items() if rid in rs), key=lambda s: stop_id(stops[s]))
        near = sorted({(p.root[0], p.id) for s in mine for p in stop_near.get(s, [])})
        rows = [root, root + ("name", route_name(r))]
        rows += [root + (k, as_is(r.get(f))) for k, f in (("short name", "route_short_name"), ("long name", "route_long_name"),
                                                            ("page", "route_url"), ("colour", "route_color"),
                                                            ("text colour", "route_text_color"), ("type", "route_type"))
                 if as_is(r.get(f)) is not None]
        rows += [root + ("schedule", k, info[f]) for k, f in (("from", "feed_start_date"), ("to", "feed_end_date")) if info.get(f)]
        rows += [root + ("near",) + k for k in near]
        rows += [root + ("stop", stop_id(stops[s])) for s in mine]
        rows.append(root + ("source", "transfort gtfs", version))
        put(out / "transit" / "routes" / root[1] / "city.scopes", rows)
        lines, seen_lines = [], set()
        for sh in sorted(route_shapes.get(rid, ())):
            pts = [[lon, lat] for _, lon, lat in sorted(shapes.get(sh, []))]
            if len(pts) > 1 and json.dumps(pts) not in seen_lines:
                seen_lines.add(json.dumps(pts))
                lines.append(pts)
        if lines:
            write(out / "transit" / "routes" / root[1] / "shape.geojson",
                  feature_json({"name": route_name(r)}, {"type": "MultiLineString", "coordinates": lines}))
    for sid, s in stops.items():
        root = ("stop", stop_id(s))
        rows = [root, root + ("name", s["stop_name"])]
        rows += [root + (k, as_is(s.get(f))) for k, f in (("code", "stop_code"), ("description", "stop_desc"),
                                                            ("wheelchair boarding", "wheelchair_boarding")) if as_is(s.get(f)) is not None]
        rows += [root + ("route", route_id(routes[r])) for r in sorted(stop_routes.get(sid, ()), key=sort_route) if r in routes]
        rows += [root + ("near",) + k for k in sorted({(p.root[0], p.id) for p in stop_near.get(sid, [])})]
        rows.append(root + ("source", "transfort gtfs", version))
        put(out / "transit" / "stops" / root[1] / "city.scopes", rows)
        write(out / "transit" / "stops" / root[1] / "shape.geojson",
              feature_json({"name": s["stop_name"]}, {"type": "Point", "coordinates": [float(s["stop_lon"]), float(s["stop_lat"])]}))

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


README = """# The city's shapes

Fort Collins' parks, natural areas and Transfort's bus routes and stops, a folder each, as lines we can search:
`park.lee-martinez-community-park.near.route.14`. Everything here wears `city.fort-collins` (WORN.scopes). In each
folder, `city.scopes` is this reader's lines and `shape.geojson` the shape; other readers add their own `.scopes`
beside them and never change these. Every place names the city's own page for it (`page`), then the stops within
{near} m of its edge (a five-minute walk) and their routes, and every stop and route names the places near it.
Every value is the city's or Transfort's own, as sent: nothing is rounded, recased or renamed.
Written by `machines/digitization/city-shapes.py` from what the city publishes, asked once a day whether anything changed. We are not
the authority on any of it.

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


def commit(root, what="the city's shapes"):
    def git(*a, check=True):
        return subprocess.run(["git", "-C", str(root), *a], capture_output=True, text=True, check=check)
    git("add", "-A", "library/city")
    if git("diff", "--cached", "--quiet", check=False).returncode == 0:
        say("commit    nothing changed")
        return
    stat = git("diff", "--cached", "--shortstat").stdout.strip()
    who = "FCPM library on %s" % socket.gethostname().split(".")[0]
    git("-c", "user.name=" + who, "-c", "user.email=317985568+fcpm-public@users.noreply.github.com",
        "-c", "commit.gpgsign=false", "commit", "-q", "-m", "city: what %s say now (%s)" % (what, stat))
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
