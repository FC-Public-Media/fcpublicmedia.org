#!/usr/bin/env python3
"""Moving existing subscribers onto the current price.

Stripe is faked here, because the decisions worth testing are made before any
request goes out: which subscriptions need moving, which are already right,
and which cannot be placed at all. Those are the ones that would cost somebody
money if they were wrong, and none of them need a network.

The one thing a fake cannot check is whether Stripe accepts the parameters,
which is why `--apply` prints what it did and why the first live run should be
against a Stripe sandbox with a test clock rather than the real membership.
"""

import importlib.util
import pathlib
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = REPO / "script" / "reprice-subscriptions.py"

spec = importlib.util.spec_from_file_location("reprice", SCRIPT)
reprice = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reprice)

ITEMS = {
    "membership:creator": {"amount": 7000, "interval": "year", "name": "Creator membership"},
    "membership:sponsor": {"amount": 4000, "interval": "year", "name": "Sponsor membership"},
}


def subscription(sub_id, sku, amount, item_id="si_1"):
    """A subscription as Stripe returns it, trimmed to what is read."""
    return {
        "id": sub_id,
        "metadata": {"sku": sku} if sku else {},
        "items": {"data": [{"id": item_id, "price": {"unit_amount": amount}}]},
    }


class WhoMoves(unittest.TestCase):
    def test_somebody_on_last_years_price_is_moved(self):
        move, steady, _ = reprice.plan([subscription("sub_1", "membership:creator", 6000)], ITEMS)

        self.assertEqual(len(move), 1)
        self.assertEqual(steady, [])
        self.assertEqual(move[0]["from"], 6000)
        self.assertEqual(move[0]["to"], 7000)

    def test_somebody_already_on_the_current_price_is_left_alone(self):
        # Not merely a no-op worth having: updating a subscription that does
        # not need it resets the quantity and can generate an invoice, so
        # "change nothing" has to actually mean no request.
        move, steady, _ = reprice.plan([subscription("sub_1", "membership:creator", 7000)], ITEMS)

        self.assertEqual(move, [])
        self.assertEqual(len(steady), 1)

    def test_a_price_that_went_down_is_moved_too(self):
        # Not an upgrade path. If the board lowers a price, everybody gets it —
        # that is what having no grandfathered plans means in both directions,
        # and it is the direction people notice if you get it wrong.
        move, _, _ = reprice.plan([subscription("sub_1", "membership:sponsor", 5000)], ITEMS)

        self.assertEqual(len(move), 1)
        self.assertEqual(move[0]["to"], 4000)


class WhoCannotBePlaced(unittest.TestCase):
    def test_a_subscription_with_no_sku_is_reported_not_guessed(self):
        # Predates the metadata, or was made by hand in the dashboard. Its
        # amount might match a tier exactly and still be a different thing, so
        # it goes in front of a person.
        move, steady, unplaceable = reprice.plan([subscription("sub_1", None, 7000)], ITEMS)

        self.assertEqual(move, [])
        self.assertEqual(steady, [])
        self.assertEqual(len(unplaceable), 1)
        self.assertIn("no sku", unplaceable[0]["why"])

    def test_a_sku_we_no_longer_sell_is_reported(self):
        # A retired tier. Repricing it to something is a decision about what
        # those members become, which is a board question and not a script's.
        _, _, unplaceable = reprice.plan([subscription("sub_1", "membership:legacy", 3000)], ITEMS)

        self.assertEqual(len(unplaceable), 1)
        self.assertIn("not for sale", unplaceable[0]["why"])

    def test_a_subscription_with_no_items_does_not_crash_the_run(self):
        empty = {"id": "sub_1", "metadata": {"sku": "membership:creator"}, "items": {"data": []}}
        _, _, unplaceable = reprice.plan([empty], ITEMS)

        self.assertEqual(len(unplaceable), 1)


class WhatIsSentToStripe(unittest.TestCase):
    def setUp(self):
        self.calls = []

    def fake(self, path, params=None, method="GET", key=None):
        self.calls.append({"path": path, "params": params or {}, "method": method})
        if path == "/prices" and method == "GET":
            return {"data": []}
        if path == "/prices":
            return {"id": "price_new"}
        return {"id": "sub_1"}

    def test_nobody_is_prorated(self):
        # The assertion this file exists for. Proration would take money from
        # people between announcements — mid-term, for a change they were told
        # about but have not reached yet.
        move, _, _ = reprice.plan([subscription("sub_1", "membership:creator", 6000)], ITEMS)
        reprice.apply(move, ITEMS, "usd", "rk_test", fetch=self.fake)

        update = [call for call in self.calls if call["path"].startswith("/subscriptions/")][0]
        self.assertEqual(update["params"]["proration_behavior"], "none")

    def test_the_existing_item_is_replaced_rather_than_a_second_one_added(self):
        # Stripe ADDS a price if you do not name the item to replace, leaving
        # the member subscribed to both and billed for both. The docs warn
        # about it twice, which is usually a sign people get it wrong.
        move, _, _ = reprice.plan([subscription("sub_1", "membership:creator", 6000, "si_abc")], ITEMS)
        reprice.apply(move, ITEMS, "usd", "rk_test", fetch=self.fake)

        update = [call for call in self.calls if call["path"].startswith("/subscriptions/")][0]
        self.assertEqual(update["params"]["items[0][id]"], "si_abc")
        self.assertEqual(update["params"]["items[0][price]"], "price_new")

    def test_the_quantity_is_restated(self):
        # Updating a subscription price silently resets quantity to 1. It is
        # already 1 for every membership, so this changes nothing today and
        # stops being free the day somebody sells a two-seat anything.
        move, _, _ = reprice.plan([subscription("sub_1", "membership:creator", 6000)], ITEMS)
        reprice.apply(move, ITEMS, "usd", "rk_test", fetch=self.fake)

        update = [call for call in self.calls if call["path"].startswith("/subscriptions/")][0]
        self.assertEqual(update["params"]["items[0][quantity]"], 1)

    def test_a_price_is_reused_rather_than_recreated_every_run(self):
        def existing(path, params=None, method="GET", key=None):
            self.calls.append({"path": path, "params": params or {}, "method": method})
            if path == "/prices" and method == "GET":
                return {"data": [{"id": "price_already"}]}
            return {"id": "sub_1"}

        move, _, _ = reprice.plan([subscription("sub_1", "membership:creator", 6000)], ITEMS)
        reprice.apply(move, ITEMS, "usd", "rk_test", fetch=existing)

        self.assertEqual([call for call in self.calls if call["method"] == "POST" and call["path"] == "/prices"], [])
        update = [call for call in self.calls if call["path"].startswith("/subscriptions/")][0]
        self.assertEqual(update["params"]["items[0][price]"], "price_already")

    def test_one_failure_does_not_stop_the_rest(self):
        def flaky(path, params=None, method="GET", key=None):
            if path == "/subscriptions/sub_bad":
                raise SystemExit("card expired")
            if path == "/prices" and method == "GET":
                return {"data": [{"id": "price_x"}]}
            return {"id": "ok"}

        move, _, _ = reprice.plan(
            [
                subscription("sub_bad", "membership:creator", 6000),
                subscription("sub_good", "membership:creator", 6000),
            ],
            ITEMS,
        )
        done, failed = reprice.apply(move, ITEMS, "usd", "rk_test", fetch=flaky)

        self.assertEqual(len(done), 1)
        self.assertEqual(len(failed), 1)
        self.assertEqual(done[0]["id"], "sub_good")


class TheCatalogItReadsFrom(unittest.TestCase):
    def test_it_parses_the_generated_module(self):
        # The file is JavaScript with a banner comment, so this is a small
        # piece of parsing that would fail silently if the generator's shape
        # changed. It reads what the broker actually charges from.
        prices = reprice.catalog()

        self.assertEqual(prices["currency"], "usd")
        self.assertIn("membership:creator", prices["items"])
        self.assertEqual(prices["items"]["membership:creator"]["amount"], 7000)


class Pagination(unittest.TestCase):
    def test_it_does_not_stop_at_the_first_hundred(self):
        # The default page size is what a small organization never hits and
        # then hits once. Members 101 onwards staying on an old price, with a
        # report saying everything is fine, is the failure this prevents.
        pages = [
            {"data": [subscription(f"sub_{n}", "membership:creator", 6000) for n in range(100)], "has_more": True},
            {"data": [subscription("sub_100", "membership:creator", 6000)], "has_more": False},
        ]
        seen = []

        def fake(path, params=None, method="GET", key=None):
            seen.append(params)
            return pages[len(seen) - 1]

        out = reprice.active_subscriptions("rk_test", fetch=fake)

        self.assertEqual(len(out), 101)
        self.assertIn("starting_after", seen[1])

    def test_only_active_subscriptions_are_asked_for(self):
        def fake(path, params=None, method="GET", key=None):
            self.assertEqual(params["status"], "active")
            return {"data": [], "has_more": False}

        reprice.active_subscriptions("rk_test", fetch=fake)


if __name__ == "__main__":
    unittest.main()
