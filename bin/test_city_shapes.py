#!/usr/bin/env python3
"""bin/city-shapes.py without the network: names as people write them, the city page's spellings, plain YAML,
a stop near a place's edge, and a build from fixed sources writing the same bytes twice.

    python3 bin/test_city_shapes.py
"""
import contextlib
import importlib.util
import io
import json
import pathlib
import tempfile
import unittest
import zipfile

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("city_shapes", HERE / "city-shapes.py")
cs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cs)

SQUARE = {"type": "Polygon", "coordinates": [[[-105.08, 40.56], [-105.07, 40.56], [-105.07, 40.57], [-105.08, 40.57], [-105.08, 40.56]]]}


def gtfs():
    files = {
        "routes.txt": "route_id,route_short_name,route_long_name,route_url,route_color\n14,14,ROUTE 14,http://r/14,a4c639\n",
        "stops.txt": "stop_id,stop_code,stop_name,stop_lat,stop_lon,location_type\n1,121,HARMONY & HINSDALE,40.565,-105.075,0\n2,999,FAR AWAY,40.70,-105.30,0\n",
        "trips.txt": "route_id,service_id,trip_id,shape_id\n14,1,t1,s1\n",
        "stop_times.txt": "trip_id,arrival_time,departure_time,stop_id,stop_sequence\nt1,08:00:00,08:00:00,1,1\nt1,08:10:00,08:10:00,2,2\n",
        "shapes.txt": "shape_id,shape_pt_lat,shape_pt_lon,shape_pt_sequence\ns1,40.565,-105.075,1\ns1,40.70,-105.30,2\n",
        "feed_info.txt": "feed_publisher_name,feed_start_date,feed_end_date,feed_version\nTransfort,20260817,20270116,S1\n",
    }
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        for k, v in files.items():
            z.writestr(k, v)
    return b.getvalue()


class Words(unittest.TestCase):
    def test_titled(self):
        self.assertEqual(cs.titled("SPRING PARK"), "Spring Park")
        self.assertEqual(cs.titled("THE COTERIE"), "The Coterie")
        self.assertEqual(cs.titled("MCMURRY NATURAL AREA"), "McMurry Natural Area")
        self.assertEqual(cs.titled("HARMONY & HINSDALE"), "Harmony & Hinsdale")

    def test_page_names(self):
        self.assertEqual(cs.page_names("Mallard's Nest Natural Area")[0], "Mallards-Nest-Natural-Area")
        self.assertIn("Edora-Park", cs.page_names("Edora Community Park"))
        self.assertIn("Oak-Street-Plaza", cs.page_names("Oak St Plaza Park"))

    def test_put_writes_each_line_once_with_its_dots_doubled(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = pathlib.Path(tmp) / "x" / "city.scopes"
            cs.put(f, [("park", "spring-park"), ("park", "spring-park", "acres", 16.99), None, ("park", "spring-park")])
            self.assertEqual(f.read_text(), "park.spring-park\npark.spring-park.acres.16..99\n")

    def test_near_is_inside_or_within_reach_of_the_edge(self):
        p = cs.Place("park", "Square", SQUARE)
        self.assertTrue(p.near(cs.xy(-105.075, 40.565)))           # inside
        self.assertTrue(p.near(cs.xy(-105.0665, 40.565)))          # about 300 m east of the edge
        self.assertFalse(p.near(cs.xy(-105.06, 40.565)))           # about 850 m


class Build(unittest.TestCase):
    def test_a_build_from_the_same_sources_writes_the_same_bytes(self):
        parks = json.dumps({"features": [{"properties": {"PARKNAME": "SPRING PARK", "PARKTYPE": "NEIGHBORHOOD PARK",
                                                          "OBJECTID": 11, "ACRESTTL": 16.98999977, "YEAR": "1965"},
                                           "geometry": SQUARE}]}).encode()
        sources = {"parks.geojson": parks, "natural-areas.geojson": b'{"features": []}', "transfort_gtfs.zip": gtfs()}
        was = cs.fetch, cs.page_answers, cs.CACHE
        with tempfile.TemporaryDirectory() as tmp:
            cs.CACHE = pathlib.Path(tmp) / "cache"
            cs.fetch = lambda name, url: (sources[name], {"modified": "Mon, 16 Nov 2026 08:04:34 GMT"})
            cs.page_answers = lambda url, checked: url.endswith("/Parks/Spring-Park")
            out = pathlib.Path(tmp) / "city"
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    cs.build(out)
                    first = {p: p.read_bytes() for p in out.rglob("*") if p.is_file()}
                    (out / "parks" / "spring-park" / "osm.scopes").write_text("park.spring-park.has.playground\n")
                    cs.build(out)
                    second = {p: p.read_bytes() for p in out.rglob("*") if p.is_file()}
            finally:
                cs.fetch, cs.page_answers, cs.CACHE = was
            self.assertEqual(first, {p: b for p, b in second.items() if p.name != "osm.scopes"})
            self.assertTrue((out / "parks" / "spring-park" / "osm.scopes").exists())     # another reader's: left alone
            self.assertEqual((out / "WORN.scopes").read_text(), "city.fort-collins\n")
            park = (out / "parks" / "spring-park" / "city.scopes").read_text().splitlines()
            self.assertEqual(park[0], "park.spring-park")
            self.assertIn("park.spring-park.page.https://www..fortcollins..gov/Parks-and-Natural-Areas-Directory/Parks/Spring-Park", park)
            self.assertIn("park.spring-park.near.route.14", park)
            self.assertIn("park.spring-park.near.stop.121", park)
            self.assertIn("park.spring-park.type.NEIGHBORHOOD PARK", park)        # every value as the city sent it
            self.assertIn("park.spring-park.name.SPRING PARK", park)
            self.assertIn("park.spring-park.acres.16..98999977", park)
            self.assertIn("park.spring-park.opened.1965", park)
            stop = (out / "transit" / "stops" / "999" / "city.scopes").read_text()
            self.assertNotIn("near", stop)
            route = (out / "transit" / "routes" / "14" / "city.scopes").read_text().splitlines()
            self.assertIn("route.14.near.park.spring-park", route)
            self.assertIn("route.14.schedule.to.20270116", route)
            self.assertIn("route.14.colour.a4c639", route)
            self.assertIn("route.14.name.ROUTE 14", route)
            self.assertIn("route.14.stop.121", route)



lspec = importlib.util.spec_from_file_location("city_layers", HERE / "city-layers.py")
cl = importlib.util.module_from_spec(lspec)
lspec.loader.exec_module(cl)
BIG = {"type": "Polygon", "coordinates": [[[-105.2, 40.4], [-104.9, 40.4], [-104.9, 40.7], [-105.2, 40.7], [-105.2, 40.4]]]}


class Layers(unittest.TestCase):
    def test_each_layer_writes_its_own_lines_and_only_those(self):
        with tempfile.TemporaryDirectory() as tmp:
            city = pathlib.Path(tmp) / "library" / "city"
            park, stop = city / "parks" / "spring-park", city / "transit" / "stops" / "121"
            park.mkdir(parents=True)
            stop.mkdir(parents=True)
            (park / "shape.geojson").write_text(cs.feature_json({}, SQUARE))
            (park / "city.scopes").write_text("park.spring-park\n")
            (stop / "shape.geojson").write_text(cs.feature_json({}, {"type": "Point", "coordinates": [-105.075, 40.565]}))
            sources = {
                "districts.geojson": json.dumps({"features": [{"properties": {"DIST": 3, "PRECT": 318, "NAME": "TRICIA CANONICO",
                                                                             "SENATE": 14, "HOUSE": 53}, "geometry": BIG}]}).encode(),
                "trails.geojson": json.dumps({"features": [{"properties": {"TRAILLABEL": "Spring Creek Trail", "DOGS": "Leash",
                                                                          "SURFACETYPE": "unknown", "Shape__Length": 1500},
                                                           "geometry": {"type": "LineString", "coordinates": [[-105.09, 40.565], [-105.06, 40.565]]}},
                                                          {"properties": {"NAME": "NONE-1"}, "geometry": {"type": "LineString", "coordinates": [[0, 0], [1, 1]]}}]}).encode()}
            was = cl.cs.fetch, cl.overpass
            cl.cs.fetch = lambda name, url: (sources[name], {"modified": "today"})
            cl.overpass = lambda t: {"elements": [{"lat": 40.565, "lon": -105.075, "tags": {"leisure": "pitch", "sport": "soccer"}},
                                                  {"lat": 40.565, "lon": -105.075, "tags": {"leisure": "playground"}},
                                                  {"lat": 40.9, "lon": -105.075, "tags": {"amenity": "toilets"}}]}
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    cl.main([str(pathlib.Path(tmp))])
                    cl.main([str(pathlib.Path(tmp)), "osm"])          # read again: the same lines, not twice
            finally:
                cl.cs.fetch, cl.overpass = was
            self.assertEqual((park / "city.scopes").read_text(), "park.spring-park\n")
            self.assertEqual((park / "districts.scopes").read_text().splitlines()[0], "park.spring-park.in.district.3")
            self.assertIn("stop.121.in.state senate.14", (stop / "districts.scopes").read_text())
            self.assertIn("district.3.member.TRICIA CANONICO", (city / "districts" / "3" / "districts.scopes").read_text())
            self.assertIn("district.3.has.park.spring-park", (city / "districts" / "3" / "districts.scopes").read_text())
            self.assertEqual((park / "trails.scopes").read_text(), "park.spring-park.near.trail.spring-creek-trail\n")
            trail = (city / "trails" / "spring-creek-trail" / "trails.scopes").read_text()
            self.assertIn("trail.spring-creek-trail.name.Spring Creek Trail", trail)
            self.assertIn("trail.spring-creek-trail.dogs.Leash", trail)
            self.assertIn("trail.spring-creek-trail.surface.unknown", trail)            # the city's word, kept
            self.assertIn("trail.spring-creek-trail.segments.1", trail)
            self.assertFalse((city / "trails" / "none-1").exists())
            self.assertEqual((park / "osm.scopes").read_text(),
                             "park.spring-park.has.leisure.pitch.sport.soccer\npark.spring-park.has.leisure.playground\n")
            self.assertIn("ODbL", (city / "layers.md").read_text())


if __name__ == "__main__":
    unittest.main(verbosity=2)
