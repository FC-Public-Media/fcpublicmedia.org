#!/usr/bin/env python3
"""machines/scopes.py: a line's parts and its doubled dots, and finding a thing by words in any order, where words
side by side must be side by side in a line and a number never stands alone.

    python3 bin/test_scopes.py
"""
import pathlib
import sys
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "machines"))
import scopes  # noqa: E402

PARK = ["park.lee-martinez", "park.lee-martinez.name.Lee Martinez Community Park", "park.lee-martinez.acres.89..56",
        "park.lee-martinez.near.route.14", "park.lee-martinez.near.stop.1478", "park.lee-martinez.has.field.tennis"]


class Lines(unittest.TestCase):
    def test_a_double_dot_is_a_dot_in_a_part(self):
        self.assertEqual(scopes.parts("park.x.acres.89..56"), ["park", "x", "acres", "89.56"])
        self.assertEqual(scopes.line("park", "x", "page", "www.example.org"), "park.x.page.www..example..org")
        self.assertEqual(scopes.parts(scopes.line("a", "b c.d", "e")), ["a", "b c.d", "e"])
        self.assertEqual(scopes.line("a", None, "", "b"), "a.b")

    def test_title_is_the_name(self):
        self.assertEqual(scopes.title(PARK), "Lee Martinez Community Park")
        self.assertEqual(scopes.title(["stop.1478"]), "1478")


class Find(unittest.TestCase):
    def says(self, *asked):
        return scopes.find(list(asked), PARK)

    def test_words_side_by_side_are_one_line_and_any_order_otherwise(self):
        for asked in (["park route 14"], ["route 14 park"], ["route", "14"], ["lee martinez", "tennis"]):
            self.assertIsNotNone(self.says(*asked), asked)
        used, runs, _ = self.says("park route 14")
        self.assertEqual(runs, 2)
        self.assertIn("park.lee-martinez.near.route.14", used)

    def test_a_number_never_stands_alone_and_is_whole(self):
        self.assertIsNone(self.says("park 14"))
        self.assertIsNone(self.says("route 147"))
        self.assertIsNone(self.says("147"))
        self.assertIsNotNone(self.says("1478"))
        self.assertIsNotNone(self.says("stop 1478"))

    def test_a_word_is_whole(self):
        self.assertIsNone(self.says("parks"))
        self.assertIsNone(self.says("mart"))

    def test_a_dot_asked_is_a_parts_edge_and_two_are_a_literal_dot(self):
        for asked in ("route.14", "near.route.14", ".14", "route.", "89..56", "89 56", ".."):
            self.assertIsNotNone(self.says(asked), asked)
        for asked in ("89.56", "near.14", "route..14", "lee.martinez"):
            self.assertIsNone(self.says(asked), asked)
        self.assertEqual(self.says("park route.14")[1], 2)
        self.assertEqual(self.says("..")[0], ["park.lee-martinez.acres.89..56"])

    def test_the_thing_itself_opens_a_line(self):
        self.assertTrue(scopes.find(["route 14"], ["route.14", "route.14.name.Route 14"])[2])
        self.assertFalse(self.says("route 14")[2])


if __name__ == "__main__":
    unittest.main(verbosity=2)
