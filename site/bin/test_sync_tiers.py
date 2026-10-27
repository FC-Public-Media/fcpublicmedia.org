#!/usr/bin/env python3
"""Tests for sync-tiers.py's reading of a Stripe /v1/prices response.

    python3 site/bin/test_sync_tiers.py

The prices below are invented to exercise the rules; they are not FCPM's.
"""

import importlib.util
import os
import tempfile
import unittest

# A hyphenated script name cannot be imported, so it is loaded by path.
_spec = importlib.util.spec_from_file_location(
    "sync_tiers", os.path.join(os.path.dirname(__file__), "sync-tiers.py")
)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

tiers, dollars = _module.tiers, _module.dollars


def price(lookup_key, amount, name="A", interval="year", active=True, **extra):
    p = {
        "id": f"price_{lookup_key}",
        "lookup_key": lookup_key,
        "unit_amount": amount,
        "currency": "usd",
        "recurring": {"interval": interval, "interval_count": 1},
        "product": {"id": f"prod_{name}", "name": name, "active": active},
    }
    p.update(extra)
    return p


class TestTiers(unittest.TestCase):
    def test_only_membership_lookup_keys_cheapest_first(self):
        found, skipped = tiers([
            price("membership:creator", 9000, "Creator"),
            price(None, 500, "Something else"),
            price("donation:monthly", 1000, "Monthly gift"),
            price("membership:supporter", 4000, "Supporter"),
        ])
        self.assertEqual([t["name"] for t in found], ["Supporter", "Creator"])
        self.assertEqual(found[0], {"sku": "membership:supporter", "name": "Supporter",
                                    "amount": 4000, "currency": "usd", "price": "40"})
        self.assertEqual(skipped, [])

    def test_monthly_and_archived_are_named_not_shown(self):
        found, skipped = tiers([
            price("membership:student", 300, "Student", interval="month"),
            price("membership:old", 5000, "Old", active=False),
        ])
        self.assertEqual(found, [])
        self.assertEqual(len(skipped), 2)

    def test_an_unexpanded_product_is_refused(self):
        found, skipped = tiers([price("membership:a", 100, product="prod_123")])
        self.assertEqual(found, [])
        self.assertIn("not expanded", skipped[0])

    def test_a_duplicate_lookup_key_is_reported(self):
        _, skipped = tiers([price("membership:a", 100), price("membership:a", 200)])
        self.assertIn("more than one", skipped[0])

    def test_dollars(self):
        self.assertEqual(dollars(4000), "40")
        self.assertEqual(dollars(4050), "40.50")


class TestCatalog(unittest.TestCase):
    def test_the_workers_price_list_names_the_tiers(self):
        source = 'export default {"currency": "usd", "items": {' \
            '"membership:creator": {"amount": 7000, "interval": "year", "name": "Creator membership"},' \
            '"membership:supporter": {"amount": 4000, "interval": "year", "name": "Supporter membership"},' \
            '"class-dropin:public": {"amount": 1500, "interval": null, "name": "Class drop-in"}}};\n'
        found, _ = _module.from_catalog(source)
        self.assertEqual([(t["name"], t["price"], t["sku"]) for t in found],
                         [("Supporter", "40", "membership:supporter"), ("Creator", "70", "membership:creator")])


class TestNothingFound(unittest.TestCase):
    def test_an_empty_account_writes_nothing(self):
        written = []
        real_open = open

        def guard(path, mode="r", *a, **k):
            if "w" in mode:
                written.append(path)
            return real_open(path, mode, *a, **k)

        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
            handle.write('{"data": []}')
        try:
            _module.open = guard
            self.assertEqual(_module.main(["--file", handle.name]), 1)
        finally:
            del _module.open
            os.remove(handle.name)
        self.assertEqual(written, [])


if __name__ == "__main__":
    unittest.main()
