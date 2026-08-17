#!/usr/bin/env python3
"""The price generator.

Two things are being guarded, and they fail in opposite directions.

The first is drift: a price edited in _data/ that never reaches the broker.
That one is quiet — the page says $70, the card is charged $60, and nobody
finds out until somebody reconciles a bank statement. `--check` in CI is the
guard; the test here is that `--check` actually notices.

The second is a placeholder becoming a charge. Several figures in the data
files are the literal string "TODO" while the board decides. A generator that
coerced those to 0, or to 0 cents, or skipped the check and let `float("TODO")`
raise at some later moment, would either sell something for nothing or take
the site down. They are skipped, deliberately and loudly.
"""

import importlib.util
import pathlib
import subprocess
import sys
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = REPO / "script" / "build-prices.py"

spec = importlib.util.spec_from_file_location("build_prices", SCRIPT)
build_prices = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_prices)


class AmountsAreMoney(unittest.TestCase):
    def test_dollars_become_cents(self):
        self.assertEqual(build_prices.amount(40), 4000)
        self.assertEqual(build_prices.amount(70), 7000)
        self.assertEqual(build_prices.amount(12.5), 1250)

    def test_a_placeholder_is_not_a_price(self):
        # The one that would cost real money. Every one of these has to come
        # back None rather than raising or defaulting.
        for value in ("TODO", "", None, "$40", "forty", [], {}):
            self.assertIsNone(build_prices.amount(value), f"{value!r} was treated as a price")

    def test_a_boolean_is_not_a_price(self):
        # bool is a subclass of int in Python, so `isinstance(True, int)` is
        # True and a stray `price: yes` in YAML would otherwise be one cent.
        self.assertIsNone(build_prices.amount(True))
        self.assertIsNone(build_prices.amount(False))

    def test_nothing_free_or_negative_gets_through(self):
        self.assertIsNone(build_prices.amount(0))
        self.assertIsNone(build_prices.amount(-40))

    def test_a_fraction_of_a_cent_is_refused_rather_than_rounded(self):
        # Rounding somebody's price silently is worse than declining to sell
        # it, because the difference shows up on their statement and not ours.
        self.assertIsNone(build_prices.amount(40.001))


class TheCatalog(unittest.TestCase):
    def test_every_membership_tier_with_a_price_is_for_sale(self):
        catalog, _ = build_prices.build()
        items = catalog["items"]

        for tier in ("sponsor", "student", "creator", "producer"):
            self.assertIn(f"membership:{tier}", items)

    def test_the_unpriced_are_reported_rather_than_dropped_in_silence(self):
        # Skipping quietly is how "why is there no buy button" becomes an
        # afternoon. The script says what it left out and why.
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
        # The same command CI runs. If this fails, run
        # `python3 script/build-prices.py` and commit the result.
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--check"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_check_actually_notices_a_difference(self):
        # A --check that always passed would be worse than none, because it
        # would be believed. Written to a real edit and put back.
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
