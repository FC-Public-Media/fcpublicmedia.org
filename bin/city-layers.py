#!/usr/bin/env python3
"""Readers that add their own lines to the city's things, each in a file of its own beside city-shapes' lines.

    python3 bin/city-layers.py DIR [LAYER ...] [--commit]

DIR is the library branch's checkout that bin/city-shapes.py wrote. Each LAYER (all of them unless named) reads the
things there by their shape.geojson and writes LAYER.scopes into their folders, and folders of its own things:

    districts  the council district, precinct and state senate and house districts each place and stop is in;
               districts/<n>/ (the city's DistrictPrecinct layer)
    trails     the named trails, what they are, and the places they pass; trails/<name>/ (the city's Trails layer)
    osm        what OpenStreetMap maps inside each park and natural area, in its own tags: leisure.playground,
               amenity.toilets, leisure.pitch.sport.tennis (Overpass, at most once a week; © OpenStreetMap contributors, ODbL)

Every value is the source's own, as it sent it: nothing is rounded, recased or renamed. What is ours is said as
ours: which thing a line is about, what is near or inside what, and a trail's segment count and length total.

A layer removes only its own files and starts again, so dropping one and reading it again is ordinary. It never
writes another reader's lines: where two disagree, both stand. layers.md says where each came from. Doc:
docs/library.md, The city.
"""
import argparse
import datetime
import importlib.util
import json
import pathlib
import sys
import urllib.parse
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("city_shapes", HERE / "city-shapes.py")
cs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cs)
scopes = cs.scopes

OVERPASS = "https://overpass-api.de/api/interpreter"
OSM_AGE = 7                                     # days before Overpass is asked again
TRAIL_REACH = 50                                # metres from a place's edge that a trail counts as passing it
OSM_REACH = 15                                  # metres: a mapped thing just over a park's line is still in it

# The OpenStreetMap tags asked for; each is written as OpenStreetMap wrote it (has.leisure.playground), with its sport.
OSM_TAGS = (("leisure", "playground"), ("leisure", "dog_park"), ("leisure", "pitch"), ("leisure", "fitness_station"),
            ("leisure", "picnic_table"), ("tourism", "picnic_site"), ("leisure", "skatepark"), ("leisure", "swimming_pool"),
            ("leisure", "disc_golf_course"), ("leisure", "water_park"), ("leisure", "track"), ("amenity", "toilets"),
            ("amenity", "drinking_water"), ("amenity", "shelter"), ("amenity", "bbq"), ("leisure", "garden"),
            ("leisure", "bandstand"))


def things(city):
    """Every thing city-shapes wrote, by kind: (root, Place or point) from its folder's shape."""
    out = {"places": [], "stops": []}
    for folder, kind in (("parks", "park"), ("natural-areas", "natural-area")):
        for shape in sorted((city / folder).glob("*/shape.geojson")):
            g = json.loads(shape.read_text())["geometry"]
            place = cs.Place(kind, shape.parent.name, g)
            place.root, place.dir = (kind, shape.parent.name), shape.parent
            out["places"].append(place)
    for shape in sorted((city / "transit" / "stops").glob("*/shape.geojson")):
        lon, lat = json.loads(shape.read_text())["geometry"]["coordinates"][:2]
        out["stops"].append((("stop", shape.parent.name), shape.parent, cs.xy(lon, lat)))
    return out


def centre(place):
    ring = max(place.rings, key=len)
    return sum(p[0] for p in ring) / len(ring), sum(p[1] for p in ring) / len(ring)


def clear(city, layer):
    for f in city.rglob(layer + ".scopes"):
        f.unlink()
    for d in sorted((x for x in city.rglob("*") if x.is_dir()), key=lambda x: -len(x.parts)):
        if not any(d.iterdir()):
            d.rmdir()


def districts(city, t):
    data, meta = cs.fetch("districts.geojson", cs.HUB % "DistrictPrecinct")
    precincts = []
    for f, said in zip(json.loads(data)["features"], json.loads(data, parse_float=str)["features"]):
        p = said["properties"]
        if f.get("geometry") and p.get("DIST"):
            precincts.append((p, cs.Place("precinct", str(p.get("PRECT")), f["geometry"])))
    clear(city, "districts")
    by = {}
    for p, shape in precincts:
        d = by.setdefault(int(p["DIST"]), {"names": set(), "members": set(), "precincts": set(), "senate": set(), "house": set(), "in": set()})
        for k, f in (("names", "DIST_LEGEND"), ("members", "NAME")):
            if cs.as_is(p.get(f)) is not None:
                d[k].add(str(p[f]))
        d["precincts"].add(str(p.get("PRECT")))
        for k, f in (("senate", "SENATE"), ("house", "HOUSE")):
            if p.get(f):
                d[k].add(str(p[f]))

    def where(pt):
        return next(((p, s) for p, s in precincts if s.near(pt, 0)), None)
    for place in t["places"]:
        hit = where(centre(place))
        if hit:
            p, _ = hit
            by[int(p["DIST"])]["in"].add(place.root)
            cs.put(place.dir / "districts.scopes", in_lines(place.root, p))
    for root, folder, pt in t["stops"]:
        hit = where(pt)
        if hit:
            by[int(hit[0]["DIST"])]["in"].add(root)
            cs.put(folder / "districts.scopes", in_lines(root, hit[0]))
    for n, d in sorted(by.items()):
        root = ("district", n)
        rows = [root] + [root + ("name", x) for x in sorted(d["names"])] + [root + ("member", x) for x in sorted(d["members"])]
        rows += [root + ("precinct", x) for x in sorted(d["precincts"], key=int)]
        rows += [root + ("state senate", x) for x in sorted(d["senate"], key=int)]
        rows += [root + ("state house", x) for x in sorted(d["house"], key=int)]
        rows += [root + ("has",) + r for r in sorted(d["in"])]
        rows.append(root + ("source", "districtprecinct layer"))
        cs.put(city / "districts" / str(n) / "districts.scopes", rows)
    return "districts  %d council districts, %d precincts, as of %s" % (len(by), len(precincts), meta.get("modified") or "unknown")


def in_lines(root, p):
    rows = [root + ("in", "district", p["DIST"]), root + ("in", "precinct", p.get("PRECT"))]
    rows += [root + ("in", "state senate", p["SENATE"])] if p.get("SENATE") else []
    rows += [root + ("in", "state house", p["HOUSE"])] if p.get("HOUSE") else []
    return rows


def trails(city, t):
    data, meta = cs.fetch("trails.geojson", cs.HUB % "Trails")
    named = {}
    for f, said in zip(json.loads(data)["features"], json.loads(data, parse_float=str)["features"]):
        p, g = said["properties"], f.get("geometry")
        name = (p.get("TRAILLABEL") or p.get("NAME") or "").strip()
        if not g or not name or name.upper().startswith("NONE"):
            continue
        tr = named.setdefault(cs.slug(name), {"names": set(), "segments": 0, "metres": 0.0, "pts": [], "facts": set()})
        tr["names"].add(name)
        tr["segments"] += 1
        tr["metres"] += float(f["properties"].get("Shape__Length") or 0)
        lines = g["coordinates"] if g["type"] == "MultiLineString" else [g["coordinates"]]
        for ln in lines:
            pts = [cs.xy(*c[:2]) for c in ln]
            for (x1, y1), (x2, y2) in zip(pts, pts[1:]):      # a point every 25 m, so a long straight run is not missed
                n = max(1, int(((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5 // 25))
                tr["pts"] += [(x1 + (x2 - x1) * i / n, y1 + (y2 - y1) * i / n) for i in range(n)]
            tr["pts"] += pts[-1:]
        for key, field in (("surface", "SURFACETYPE"), ("surface kind", "SURFACE"), ("construction", "CONSTRUCTIONTYPE"),
                           ("dogs", "DOGS"), ("bikes", "BIKEUSE"), ("horses", "HORSEUSE"), ("rating", "RATING"),
                           ("wheelchair rating", "WC_RATING"), ("ada", "ADA"), ("managed by", "MANAGER")):
            if cs.as_is(p.get(field)) is not None:
                tr["facts"].add((key, str(p[field])))
    clear(city, "trails")
    passes = {}
    for tid, tr in named.items():
        xs, ys = [p[0] for p in tr["pts"]], [p[1] for p in tr["pts"]]
        for place in t["places"]:
            b = place.box
            if max(xs) < b[0] or min(xs) > b[2] or max(ys) < b[1] or min(ys) > b[3]:
                continue
            if any(place.near(pt, TRAIL_REACH) for pt in tr["pts"]):
                passes.setdefault(place, set()).add(tid)
                tr.setdefault("near", set()).add(place.root)
        root = ("trail", tid)
        rows = [root] + [root + ("name", x) for x in sorted(tr["names"])]
        rows += [root + ("segments", tr["segments"]), root + ("shape length total", repr(tr["metres"]))]
        rows += [root + f for f in sorted(tr["facts"])]
        rows += [root + ("near",) + r for r in sorted(tr.get("near", ()))]
        rows.append(root + ("source", "trails layer"))
        cs.put(city / "trails" / tid / "trails.scopes", rows)
    for place, tids in passes.items():
        cs.put(place.dir / "trails.scopes", [place.root + ("near", "trail", x) for x in sorted(tids)])
    return "trails     %d named trails passing %d places, as of %s" % (len(named), len(passes), meta.get("modified") or "unknown")


def overpass(t):
    """Overpass's answer for the box around every place, kept a week: one question, never a stream of them."""
    cache = cs.CACHE / "osm.json"
    if cache.exists() and (datetime.datetime.now().timestamp() - cache.stat().st_mtime) < OSM_AGE * 86400:
        cs.say("osm.json       kept (asked within %d days)" % OSM_AGE)
        return json.loads(cache.read_text())
    lon = [x for p in t["places"] for r in p.rings for x, _ in r]
    lat = [y for p in t["places"] for r in p.rings for _, y in r]
    k = 111320 * __import__("math").cos(__import__("math").radians(cs.LAT0))
    box = "%f,%f,%f,%f" % (min(lat) / 110540, min(lon) / k, max(lat) / 110540, max(lon) / k)
    sel = "".join('nwr["%s"="%s"](%s);' % (a, b, box) for a, b in OSM_TAGS)
    q = "[out:json][timeout:120];(%s);out center tags;" % sel
    req = urllib.request.Request(OVERPASS, data=urllib.parse.urlencode({"data": q}).encode(), headers={"User-Agent": cs.UA})
    with urllib.request.urlopen(req, timeout=180) as r:
        data = json.loads(r.read())
    cs.CACHE.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(data))
    cs.say("osm.json       asked (%d elements)" % len(data.get("elements", [])))
    return data


def osm(city, t):
    data = overpass(t)
    clear(city, "osm")
    has, n = {}, 0
    for el in data.get("elements", []):
        tags = el.get("tags", {})
        c = el.get("center") or ({"lat": el["lat"], "lon": el["lon"]} if "lat" in el else None)
        tag = next(((a, b) for a, b in OSM_TAGS if tags.get(a) == b), None)
        if not c or not tag:
            continue
        pt = cs.xy(c["lon"], c["lat"])
        for place in t["places"]:
            if place.near(pt, OSM_REACH):
                row = ("has",) + tag + (("sport", tags["sport"]) if tags.get("sport") else ())
                has.setdefault(place, set()).add(row)
                n += 1
    for place, rows in has.items():
        cs.put(place.dir / "osm.scopes", [place.root + r for r in sorted(rows)])
    return "osm        %d mapped things in %d places (© OpenStreetMap contributors, ODbL)" % (n, len(has))


LAYERS = {"districts": districts, "trails": trails, "osm": osm}

NOTES = """# Layers on the city

Readers that add lines to the things in this folder, each in its own file beside `city.scopes`, written by
`bin/city-layers.py`. A layer removes only its own files and reads again; none changes another's lines.

| file | says | from |
|---|---|---|
| `districts.scopes` | the council district, precinct, and state senate and house districts a place (by its middle) or a stop is in; `districts/<n>/` has the city's own legend and member name, and everything in it | the city's DistrictPrecinct layer |
| `trails.scopes` | the named trails a place's edge is within 50 m of; `trails/<name>/` has each name and value the city's segments carry, their count and total length (segments named `NONE-<id>` belong to no trail) | the city's Trails layer |
| `osm.scopes` | what is mapped inside a park or natural area (within 15 m of its edge), in OpenStreetMap's own tags: `leisure.playground`, `amenity.toilets`, `leisure.pitch.sport.tennis` | OpenStreetMap, asked of Overpass at most weekly. © OpenStreetMap contributors, under the Open Database License (ODbL) |

Every value is the source's own, as sent; nothing is rounded, recased or renamed. A normalized value would be a
reader of its own, its lines saying what it did.

Last read:

{said}
"""


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("dir", type=pathlib.Path)
    ap.add_argument("layers", nargs="*", choices=list(LAYERS))
    ap.add_argument("--commit", action="store_true")
    a = ap.parse_args(argv)
    root = a.dir.expanduser().resolve()
    city = root / "library" / "city"
    if not (city / "parks").is_dir():
        sys.exit("city-layers: %s has no city to read (bin/city-shapes.py writes it first)" % city)
    t = things(city)
    said = []
    for name in a.layers or LAYERS:
        try:
            said.append(LAYERS[name](city, t))
        except OSError as exc:                            # its source did not answer: its lines stay as they were
            said.append("%-10s not read now (%s); its lines are as they were" % (name, exc))
        cs.say(said[-1])
    notes = city / "layers.md"
    old = notes.read_text() if notes.exists() else ""
    kept = [ln for ln in old.splitlines() if ln.startswith("    ") and ln.split()[0] not in (a.layers or LAYERS)]
    cs.write(notes, NOTES.format(said="\n".join(sorted(kept + ["    " + s for s in said]))))
    if a.commit:
        cs.commit(root, "the city's layers")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
