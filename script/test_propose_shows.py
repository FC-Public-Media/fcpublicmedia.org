#!/usr/bin/env python3
"""Tests for the show proposer.

The failures worth catching are the ones that produced a plausible-looking
wrong answer: a show split into three because its episodes have different
second words, or two shows merged because one name is a prefix of another.
Both look fine in a list and are wrong in the archive.

Fixtures are shaped like the real catalog, including the specific messes it
contains — Paltrocast's varying second word, Parker St.'s inconsistent full
stop, Stages numbering its own episodes.
"""

import importlib.util
import pathlib
import sys
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("propose_shows", HERE / "propose-shows.py")
ps = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ps)


def item(title, producer="", local=True, date="2026-01-01"):
    return {"title": title, "producer": producer, "local": local, "date": date}


class Clustering(unittest.TestCase):
    def test_a_varying_second_word_does_not_split_a_show(self):
        # The real failure: grouping on two words made Paltrocast into
        # "paltrocast cast", "paltrocast stars" and "paltrocast the".
        catalog = [
            item("Paltrocast - Cast of Swagger"),
            item("Paltrocast - Stars of FROM"),
            item("Paltrocast - The Yellowjackets Composers"),
            item("Paltrocast - Butterfly Black"),
        ]
        proposals = ps.propose(catalog, [])

        self.assertEqual(len(proposals), 1)
        self.assertEqual(proposals[0]["slug"], "paltrocast")
        self.assertEqual(proposals[0]["episodes"], 4)

    def test_punctuation_does_not_split_a_show(self):
        # "Parker St." and "Parker St" were two groups in the archive, which is
        # the kind of wrong nobody reports and everybody notices.
        catalog = [
            item("Parker St. Session One"),
            item("Parker St Session Two"),
            item("PARKER ST. SESSION THREE"),
        ]
        proposals = ps.propose(catalog, [])

        self.assertEqual(len(proposals), 1)
        self.assertEqual(proposals[0]["episodes"], 3)

    def test_a_show_that_numbers_itself_is_not_named_after_its_numbering(self):
        catalog = [item(f"Stages Ep. {n}") for n in range(1, 5)]
        proposals = ps.propose(catalog, [])

        self.assertEqual(proposals[0]["name"], "Stages")
        self.assertEqual(proposals[0]["slug"], "stages")

    def test_the_match_is_the_whole_common_prefix_not_the_first_word(self):
        # "under" would claim anything starting with it. A greedy match rule
        # silently swallows somebody else's show; a narrow one just shows up as
        # a missing episode, which somebody notices and reports.
        catalog = [item(f"Under the Marquee - {n}") for n in "ABCD"]
        proposals = ps.propose(catalog, [])

        self.assertEqual(proposals[0]["prefix"], "under the marquee")

    def test_a_shared_first_word_that_means_nothing_is_not_a_show(self):
        catalog = [
            item("The Mayor Speaks"),
            item("The River Project"),
            item("The Last Word"),
            item("A Night Out"),
        ]
        self.assertEqual(ps.propose(catalog, []), [])

    def test_one_offs_are_left_alone(self):
        catalog = [item("A Documentary"), item("Another Thing"), item("Third")]
        self.assertEqual(ps.propose(catalog, []), [])

    def test_titles_that_never_vary_still_group(self):
        # Democracy Now is 249 episodes sharing one title exactly.
        catalog = [item("Democracy Now", date=f"2026-01-{n:02d}") for n in range(1, 6)]
        proposals = ps.propose(catalog, [])

        self.assertEqual(proposals[0]["name"], "Democracy Now")
        self.assertEqual(proposals[0]["episodes"], 5)

    def test_the_biggest_cluster_comes_first(self):
        catalog = [item(f"Small Thing {n}") for n in range(3)]
        catalog += [item(f"Large Thing {n}") for n in range(9)]
        proposals = ps.propose(catalog, [])

        self.assertEqual([p["episodes"] for p in proposals], [9, 3])


class AlreadyConfigured(unittest.TestCase):
    def test_a_configured_show_is_not_proposed_again(self):
        catalog = [item(f"Brick Wall {n}") for n in range(5)]
        known = [{"slug": "brick-wall", "prefixes": ["brick wall"], "producers": []}]

        self.assertEqual(ps.propose(catalog, known), [])

    def test_a_producer_rule_claims_episodes_a_prefix_would_miss(self):
        # Some series were listed under several unrelated titles. The producer
        # is the only thing they have in common.
        catalog = [
            item("Something Entirely Different", producer="In the Shed Media"),
            item("Another Unrelated Name", producer="In the Shed Media"),
            item("A Third", producer="In the Shed Media"),
        ]
        known = [{"slug": "shed", "prefixes": [], "producers": ["In the Shed Media"]}]

        self.assertEqual(ps.propose(catalog, known), [])

    def test_what_is_left_over_is_still_proposed(self):
        catalog = [item(f"Brick Wall {n}") for n in range(4)]
        catalog += [item(f"Radiovision {n}") for n in range(4)]
        known = [{"slug": "brick-wall", "prefixes": ["brick wall"], "producers": []}]

        proposals = ps.propose(catalog, known)
        self.assertEqual([p["slug"] for p in proposals], ["radiovision"])


class RoundTrip(unittest.TestCase):
    def test_a_written_stub_claims_the_episodes_it_was_proposed_for(self):
        # The one that matters: a proposal is only useful if merging it
        # actually gathers the episodes it was made from. A mismatch between
        # what the proposer clusters and what the config matches would leave a
        # show page empty and nobody would know why.
        catalog = [item(f"Under the Marquee - {n}") for n in "ABCDEF"]
        catalog += [item("Underground Sound"), item("Under Pressure Rehearsal")]

        proposals = ps.propose(catalog, [])
        self.assertEqual(proposals[0]["episodes"], 6)

        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / f"{proposals[0]['slug']}.md"
            path.write_text(ps.stub(proposals[0]), encoding="utf-8")

            known = ps.load_known(directory)
            self.assertEqual(known[0]["prefixes"], ["under the marquee"])

            claimed = [i for i in catalog if ps.claimed_by(i, known)]
            self.assertEqual(len(claimed), 6, "the config does not match its own cluster")

            # And nothing else got swept in by a too-greedy prefix.
            self.assertNotIn("Underground Sound", [i["title"] for i in claimed])

    def test_a_written_stub_stops_the_show_being_proposed_again(self):
        catalog = [item(f"Radiovision {n}") for n in range(5)]
        proposals = ps.propose(catalog, [])

        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / f"{proposals[0]['slug']}.md"
            path.write_text(ps.stub(proposals[0]), encoding="utf-8")

            self.assertEqual(ps.propose(catalog, ps.load_known(directory)), [])


class TheRealCatalog(unittest.TestCase):
    def test_it_survives_what_cablecast_actually_contains(self):
        # Not an assertion about any particular show — those change. This is
        # here so a change to the clustering that blows up on real titles fails
        # in CI rather than in a workflow run at three in the morning.
        import json

        catalog_path = HERE.parent / "_data" / "cablecast.json"
        if not catalog_path.exists():
            self.skipTest("no catalog checked out")

        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))["shows"]
        proposals = ps.propose(catalog, [])

        self.assertGreater(len(proposals), 5)
        for proposal in proposals:
            self.assertTrue(proposal["slug"], "a proposal with no slug")
            self.assertTrue(proposal["name"], "a proposal with no name")
            self.assertGreaterEqual(proposal["episodes"], 3)
            # The stub has to be writable for every one of them.
            self.assertIn(proposal["slug"], ps.stub(proposal))
            self.assertIn(proposal["name"], ps.body(proposal))


if __name__ == "__main__":
    unittest.main(verbosity=2 if "-v" in sys.argv else 1)
