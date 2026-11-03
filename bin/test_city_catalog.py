#!/usr/bin/env python3
"""Tests for the city catalog: no network, a fake fetch answers from canned replies.

    python3 bin/test_city_catalog.py
"""

import importlib.util
import pathlib
import unittest


def load():
    spec = importlib.util.spec_from_file_location("city_catalog", pathlib.Path(__file__).parent / "city-catalog.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


cc = load()

ITEM = "f8822d882efa40b0a312bab0152817f6"
SERVICE = "https://services1.arcgis.com/x/arcgis/rest/services/OpenBook/FeatureServer/0"

SOCRATA_PAGE = {"resultSetSize": 2, "results": [
    {"resource": {"id": "6eq5-g3gk", "name": "Fort Collins OpenBook Vendors", "type": "dataset",
                  "updatedAt": "2026-06-23T13:38:38.000Z", "createdAt": "2017-03-20T14:55:48.000Z",
                  "description": "Full vendor list from <b>OpenBook</b>.",
                  "columns_name": ["meta_row_index", "Amount", "Vendor/Payee"],
                  "columns_field_name": ["meta_row_index", "amount", "vendor_payee"],
                  "columns_datatype": ["Number", "Number", "Text"],
                  "columns_description": ["sort order", "", ""],
                  "page_views": {"page_views_total": 2281}, "download_count": 13386},
     "classification": {"domain_category": "Economic Health", "domain_tags": ["openbook"]}},
    {"resource": {"id": "b3xw-43sf", "name": "BikeFacilities", "type": "map", "updatedAt": "2026-11-03T00:00:00Z"},
     "classification": {}},
]}

FEED = {"dataset": [
    {"identifier": "https://www.arcgis.com/home/item.html?id=%s&sublayer=0" % ITEM,
     "title": "Fort Collins OpenBook Vendors DEPR", "description": "{{description}}",
     "keyword": ["openbook"], "modified": "2026-07-29T15:10:34.479Z", "issued": "2026-06-23T16:59:13.000Z",
     "landingPage": "https://open-data-fcgov.hub.arcgis.com/datasets/fcgov::openbook",
     "distribution": [{"format": "ArcGIS GeoServices REST API", "accessURL": SERVICE}]},
    {"identifier": "https://www.arcgis.com/home/item.html?id=%s" % ("0" * 32), "title": "Zoning",
     "description": "<p>Zoning districts &amp; overlays.</p>", "modified": "2026-11-02", "distribution": []},
]}


def fake(url):
    if url.startswith(cc.CATALOG):
        return SOCRATA_PAGE
    if url.endswith("/resource/6eq5-g3gk.json?$select=count(*)%20as%20n"):
        return [{"n": "310000"}]
    if url == cc.HUB + "/api/feed/dcat-us/1.1.json":
        return FEED
    if url == cc.ITEM + ITEM + "?f=json":
        return {"description": None, "snippet": "Dataset backend for OpenBook expenses."}
    if url == SERVICE + "?f=json":
        return {"type": "Table", "fields": [{"name": "ObjectId"}, {"name": "Vendor_Name", "alias": "Vendor Name",
                                                                   "type": "esriFieldTypeString"}]}
    if url.startswith(SERVICE + "/query"):
        return {"count": 110512}
    raise AssertionError("unexpected fetch: " + url)


class Catalog(unittest.TestCase):
    def test_plain_drops_markup_and_unfilled_templates(self):
        self.assertEqual(cc.plain("<p>Zoning &amp; overlays.</p>"), "Zoning & overlays.")
        self.assertEqual(cc.plain("{{description}}"), "")

    def test_key_matches_the_hubs_renames(self):
        self.assertEqual(cc.key("BikeFacilities"), cc.key("Bike Facilities"))
        self.assertEqual(cc.key("Fort Collins Floodwarning Rain Gage Data (30-day rolling)"),
                         cc.key("Fort Collins Floodwarning Rain Gage Data"))
        self.assertEqual(cc.key("Current Building Permits"), cc.key("Building Permits"))
        self.assertEqual(cc.key("Stage & Flow Data"), cc.key("Stage and Flow Data"))
        self.assertNotEqual(cc.key("Fort Collins Detailed OpenBook Vendors"), cc.key("Fort Collins OpenBook Vendors"))

    def test_socrata_links_on_the_live_host_and_counts_rows(self):
        soc = cc.socrata(get=fake)
        vendors = soc[0]
        self.assertEqual(vendors["link"], "https://fortcollins.data.socrata.com/d/6eq5-g3gk")
        self.assertEqual(vendors["rows"], 310000)
        self.assertEqual([c["field"] for c in vendors["columns"]], ["amount", "vendor_payee"])
        self.assertEqual(vendors["description"], "Full vendor list from OpenBook.")
        self.assertNotIn("api", soc[1])          # a map has no rows of its own

    def test_hub_reads_the_item_when_the_feed_left_a_template(self):
        hb = cc.hub(get=fake)
        self.assertEqual(hb[0]["description"], "Dataset backend for OpenBook expenses.")
        self.assertEqual(hb[0]["description_from"], "item")
        self.assertEqual(hb[0]["kind"], "table")
        self.assertEqual([c["field"] for c in hb[0]["columns"]], ["Vendor_Name"])
        self.assertEqual(hb[0]["rows"], 110512)
        self.assertEqual(hb[1]["description"], "Zoning districts & overlays.")

    def test_join_says_where_each_lives_and_the_table_reads(self):
        cat = {"pulled": "2026-11-03T00:00:00-07:00", "entries": cc.join(cc.socrata(get=fake), cc.hub(get=fake))}
        where = {e["title"]: e["where"] for e in cat["entries"]}
        self.assertEqual(where, {"Fort Collins OpenBook Vendors": "both", "BikeFacilities": "socrata", "Zoning": "hub"})
        md = cc.markdown(cat)
        self.assertIn("1 on both portals, 1 on Socrata only, 1 on the Hub only", md)
        self.assertIn("| both | [Fort Collins OpenBook Vendors](https://fortcollins.data.socrata.com/d/6eq5-g3gk) "
                      "| 2026-07-29 | 110,512 | 2 |", md)


if __name__ == "__main__":
    unittest.main()
