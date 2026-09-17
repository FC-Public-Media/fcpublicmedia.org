#!/usr/bin/env python3
"""Tests for the catalog report.

The failure that matters here is not missing something. It is crying wolf: a
report that lists two hundred false positives every month gets ignored, and
then the month it says something true it gets ignored too.

So most of these are about what the report REFUSES to say.
"""

import datetime
import importlib.util
import pathlib
import unittest

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("catalog_report", HERE / "catalog-report.py")
cr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cr)

TODAY = datetime.date(2026, 8, 9)


def item(id, title, producer="Somebody", local=True, watchable=True, seconds=1800, date="2026-08-01"):
    return {
        "id": id,
        "title": title,
        "producer": producer,
        "local": local,
        "watchable": watchable,
        "seconds": seconds,
        "date": date,
        "thumb": "https://example/thumb",
    }


class Typos(unittest.TestCase):
    def test_a_near_miss_of_an_established_title_is_reported(self):
        catalog = [item(n, "Democracy Now") for n in range(10)]
        catalog.append(item(99, "Democrracy Now"))

        found = cr.typos(catalog)
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["id"], 99)
        self.assertEqual(found[0]["looks_like"], "Democracy Now")

    def test_a_missing_space_counts(self):
        # "Brickwall" against twenty-nine "Brick Wall" — found in the real
        # catalog and easy to miss by eye.
        catalog = [item(n, "Brick Wall") for n in range(10)]
        catalog.append(item(99, "Brickwall"))

        self.assertEqual([f["id"] for f in cr.typos(catalog)], [99])

    def test_two_rare_titles_that_look_alike_are_not_a_typo(self):
        # Neither is established, so there is no reason to think one is a
        # mistyping of the other rather than two different programmes.
        catalog = [item(1, "River Walk"), item(2, "River Talk")]
        self.assertEqual(cr.typos(catalog), [])

    def test_genuinely_different_episodes_are_not_typos(self):
        catalog = [item(n, f"Beware Theater Episode {n}") for n in range(10)]
        self.assertEqual(cr.typos(catalog), [])


class Miscredits(unittest.TestCase):
    def test_one_odd_credit_among_many_is_reported(self):
        catalog = [item(n, "Brick Wall", producer="Jorie Kramer") for n in range(28)]
        catalog.append(item(99, "Brick Wall", producer="Free Speech TV"))

        found = cr.miscredits(catalog)
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["id"], 99)
        self.assertEqual(found[0]["expected"], "Jorie Kramer")

    def test_a_series_with_two_real_producers_is_not_a_miscredit(self):
        # A show that genuinely changed hands, or has co-producers. Half and
        # half is not somebody's mistake.
        catalog = [item(n, "Shared Show", producer="One") for n in range(5)]
        catalog += [item(n + 50, "Shared Show", producer="Two") for n in range(5)]

        self.assertEqual(cr.miscredits(catalog), [])

    def test_a_short_run_is_left_alone(self):
        # Three episodes with three credits is not enough to call any of them
        # the odd one out.
        catalog = [item(1, "Thing", producer="A"), item(2, "Thing", producer="B")]
        self.assertEqual(cr.miscredits(catalog), [])


class Duplicates(unittest.TestCase):
    def test_the_same_record_twice_is_reported(self):
        catalog = [item(1, "Fog Island", seconds=5384), item(2, "Fog Island", seconds=5384)]

        found = cr.duplicates(catalog)
        self.assertEqual(len(found), 1)
        self.assertEqual(sorted(found[0]["ids"]), [1, 2])

    def test_a_daily_series_sharing_runtimes_is_not_duplicated(self):
        # THE false positive this check exists to avoid. A hundred and forty
        # episodes of an hour-long news programme are all 3542 seconds, and
        # reporting them would bury everything else.
        catalog = [item(n, "Democracy Now", seconds=3542) for n in range(140)]
        self.assertEqual(cr.duplicates(catalog), [])

    def test_the_same_title_at_different_lengths_is_two_episodes(self):
        catalog = [item(1, "Council Meeting", seconds=3600), item(2, "Council Meeting", seconds=5400)]
        self.assertEqual(cr.duplicates(catalog), [])


class Unwatchable(unittest.TestCase):
    def test_something_recent_of_ours_that_will_not_play_is_reported(self):
        catalog = [item(1, "Last Month's Show", watchable=False, date="2026-07-01")]
        self.assertEqual([f["id"] for f in cr.unwatchable_local(catalog, today=TODAY)], [1])

    def test_the_historical_backlog_is_not_reported_every_month(self):
        # Twenty of ours are unwatchable and none is newer than 2024. Listing
        # them monthly would mean this report was never quiet, which is the
        # one thing it has to be.
        catalog = [item(n, f"Old Thing {n}", watchable=False, date="2023-05-01") for n in range(20)]
        self.assertEqual(cr.unwatchable_local(catalog, today=TODAY), [])
        self.assertEqual(cr.standing(catalog)["ours and not watchable"], 20)

    def test_syndicated_material_is_nobody_here_to_fix(self):
        catalog = [item(1, "Bought In", local=False, watchable=False, date="2026-07-01")]
        self.assertEqual(cr.unwatchable_local(catalog, today=TODAY), [])


class TheReport(unittest.TestCase):
    def test_a_clean_catalog_says_so_and_counts_nothing(self):
        catalog = [item(n, f"Fine Show {n}") for n in range(5)]

        total, report = cr.build(catalog)
        self.assertEqual(total, 0)
        self.assertIn("Nothing looks wrong", report)
        # The workflow keys off this being zero — no issue, no notification.
        self.assertIn("Standing counts", report)

    def test_findings_carry_a_link_to_the_record(self):
        # Whoever reads this has to open it in Cablecast to fix it, and
        # copying an ID out of a code block is a worse morning.
        catalog = [item(n, "Brick Wall", producer="Jorie") for n in range(28)]
        catalog.append(item(99, "Brick Wall", producer="Somebody Else"))

        total, report = cr.build(catalog)
        self.assertEqual(total, 1)
        self.assertIn("internetchannel/show/99", report)

    def test_it_says_the_fix_is_not_here(self):
        catalog = [item(n, "Brick Wall", producer="Jorie") for n in range(28)]
        catalog.append(item(99, "Brick Wall", producer="Somebody Else"))

        self.assertIn("live in Cablecast", cr.build(catalog)[1])


class TheRealCatalog(unittest.TestCase):
    def test_it_runs_on_what_cablecast_actually_contains(self):
        import json

        path = HERE.parent / "_data" / "cablecast.json"
        if not path.exists():
            self.skipTest("no catalog checked out")

        catalog = json.loads(path.read_text(encoding="utf-8"))["shows"]
        total, report = cr.build(catalog)

        # Not an assertion about the count — it should go down as things get
        # fixed, and up when somebody fat-fingers a title. This is here so a
        # change that throws on real data fails in CI rather than in a
        # scheduled run nobody is watching.
        self.assertIsInstance(total, int)
        self.assertIn("Standing counts", report)

        # And the thing this was built to avoid: a report so long nobody reads
        # it. If it ever gets here, a check needs scoping rather than the
        # threshold being raised.
        self.assertLess(total, 60, "the report is too long to be read")


if __name__ == "__main__":
    unittest.main()
