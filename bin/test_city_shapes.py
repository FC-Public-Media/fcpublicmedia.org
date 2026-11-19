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

    def test_yml_quotes_only_what_yaml_needs(self):
        out = cs.yml({"name": "Spring Park", "colour": "#a4c639", "kind": "yes", "acres": 16.99, "none": None,
                      "stops": ["121 Harmony & Hinsdale"], "empty": []})
        self.assertEqual(out, 'name: Spring Park\ncolour: "#a4c639"\nkind: "yes"\nacres: 16.99\n'
                              'stops:\n  - 121 Harmony & Hinsdale\n')

    def test_near_is_inside_or_within_reach_of_the_edge(self):
        p = cs.Place("park", "Square", SQUARE)
        self.assertTrue(p.near(cs.xy(-105.075, 40.565)))           # inside
        self.assertTrue(p.near(cs.xy(-105.0665, 40.565)))          # about 300 m east of the edge
        self.assertFalse(p.near(cs.xy(-105.06, 40.565)))           # about 850 m


class Build(unittest.TestCase):
    def test_a_build_from_the_same_sources_writes_the_same_bytes(self):
        parks = json.dumps({"features": [{"properties": {"PARKNAME": "SPRING PARK", "PARKTYPE": "NEIGHBORHOOD PARK",
                                                          "OBJECTID": 11, "ACRESTTL": 17, "YEAR": 1965},
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
                    cs.build(out)
                    second = {p: p.read_bytes() for p in out.rglob("*") if p.is_file()}
            finally:
                cs.fetch, cs.page_answers, cs.CACHE = was
            self.assertEqual(first, second)
            park = (out / "parks" / "spring-park" / "facts.yml").read_text()
            self.assertIn("city page: https://www.fortcollins.gov/Parks-and-Natural-Areas-Directory/Parks/Spring-Park", park)
            self.assertIn("routes near:\n  - Route 14\n", park)
            self.assertIn("stops near:\n  - 121 Harmony & Hinsdale\n", park)
            stop = (out / "transit" / "stops" / "999.yml").read_text()
            self.assertNotIn("parks near", stop)
            route = (out / "transit" / "routes" / "14" / "facts.yml").read_text()
            self.assertIn("parks near:\n  - Spring Park\n", route)
            self.assertIn("schedule: 2026-08-17 to 2027-01-16", route)
            self.assertIn("unofficial, not endorsed by Transfort", route)


if __name__ == "__main__":
    unittest.main(verbosity=2)
