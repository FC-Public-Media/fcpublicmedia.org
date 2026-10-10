#!/usr/bin/env python3
"""see docs/inline/site/bin/test_build_prices.py.md#1"""

import importlib.util
import pathlib
import subprocess
import sys
import unittest

# see docs/inline/site/bin/test_build_prices.py.md#2
HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent
SCRIPT = HERE / "build-prices.py"

spec = importlib.util.spec_from_file_location("build_prices", SCRIPT)
build_prices = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_prices)


class AmountsAreMoney(unittest.TestCase):
    def test_dollars_become_cents(self):
        self.assertEqual(build_prices.amount(40), 4000)
        self.assertEqual(build_prices.amount(70), 7000)
        self.assertEqual(build_prices.amount(12.5), 1250)

    def test_a_placeholder_is_not_a_price(self):
        # see docs/inline/site/bin/test_build_prices.py.md#3
        for value in ("TODO", "", None, "$40", "forty", [], {}):
            self.assertIsNone(build_prices.amount(value), f"{value!r} was treated as a price")

    def test_a_boolean_is_not_a_price(self):
        # see docs/inline/site/bin/test_build_prices.py.md#4
        self.assertIsNone(build_prices.amount(True))
        self.assertIsNone(build_prices.amount(False))

    def test_nothing_free_or_negative_gets_through(self):
        self.assertIsNone(build_prices.amount(0))
        self.assertIsNone(build_prices.amount(-40))

    def test_a_fraction_of_a_cent_is_refused_rather_than_rounded(self):
        # see docs/inline/site/bin/test_build_prices.py.md#5
        self.assertIsNone(build_prices.amount(40.001))


class TheCatalog(unittest.TestCase):
    def test_every_membership_tier_with_a_price_is_for_sale(self):
        catalog, _ = build_prices.build()
        items = catalog["items"]

        for tier in ("sponsor", "student", "creator", "producer"):
            self.assertIn(f"membership:{tier}", items)

    def test_the_unpriced_are_reported_rather_than_dropped_in_silence(self):
        # see docs/inline/site/bin/test_build_prices.py.md#6
        _, skipped = build_prices.build()
        self.assertTrue(any("class-dropin" in note for note in skipped))

    def test_every_amount_is_a_whole_number_of_cents(self):
        catalog, _ = build_prices.build()
        for sku, item in catalog["items"].items():
            self.assertIsInstance(item["amount"], int, sku)
            self.assertGreater(item["amount"], 0, sku)

    def test_memberships_carry_a_year_so_the_recurring_option_can_exist(self):
        catalog, _ = build_prices.build()
        for sku, item in catalog["items"].items():
            if item["kind"] == "membership":
                self.assertEqual(item["interval"], "year", sku)


class TheCommittedCopy(unittest.TestCase):
    def test_it_is_up_to_date(self):
        # see docs/inline/site/bin/test_build_prices.py.md#7
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--check"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_check_actually_notices_a_difference(self):
        # see docs/inline/site/bin/test_build_prices.py.md#8
        target = REPO / "worker" / "src" / "prices.js"
        original = target.read_text(encoding="utf-8")
        try:
            target.write_text(original.replace("7000", "1"), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--check"],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("out of date", result.stderr)
        finally:
            target.write_text(original, encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
