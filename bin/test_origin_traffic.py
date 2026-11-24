#!/usr/bin/env python3
"""The origin's listing and traffic orders (machines/origin/traffic.py), through its door and intake's beat, on
the scratch origin test_origin_relay.py builds: `look` reads everything in one answer, `land` orders a branch as
it was seen, and the next beat lands the orders in turn, by main's own attributes, then lets the branch go.

    python3 bin/test_origin_traffic.py
"""
import json
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import test_origin_relay as relay  # noqa: E402
HUB = relay.HUB


class Traffic(relay.Beat):
    def setUp(self):
        super().setUp()
        self.intake.github_mains = lambda names: {HUB: self.on_github("refs/heads/main")}

    def branch(self, name, files, base="main"):
        """A branch pushed here with one commit writing FILES ({path: text}); returns its tip."""
        w = self.work()
        self.git("checkout", "-q", "-B", name, base, cwd=w)
        for path, text in files.items():
            (w / path).write_text(text)
        self.git("add", "-A", cwd=w)
        self.git("commit", "-qm", "on " + name, cwd=w)
        self.git("push", "-q", "origin", name, cwd=w)
        self.git("checkout", "-q", "main", cwd=w)
        return self.here("refs/heads/" + name)

    def main_with(self, files):
        w = self.work()
        self.git("checkout", "-q", "main", cwd=w)
        self.git("pull", "-q", "--ff-only", "origin", "main", cwd=w)
        for path, text in files.items():
            (w / path).write_text(text)
        self.git("add", "-A", cwd=w)
        self.git("commit", "-qm", "main", cwd=w)
        self.git("push", "-q", "origin", "main", cwd=w)

    def look(self):
        r = self.door("look")
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)

    def hub_of(self, d):
        return next(x for x in d["repos"] if x["repo"] == HUB)

    def beat(self):
        state = self.origin / ".intake/state.json"
        if state.exists():
            state.write_text(json.dumps(dict(json.loads(state.read_text()), beat="2026-01-01T00:00:00+00:00")))
        self.assertEqual(self.intake.main(), 0)
        return [json.loads(l) for l in (self.origin / ".intake/orders.ndjson").read_text().splitlines()]

    def test_the_beat_points_head_at_main(self):
        hub = self.origin / HUB
        self.git("symbolic-ref", "HEAD", "refs/heads/master", cwd=hub)
        self.assertEqual(self.intake.main(), 0)
        self.assertEqual(self.git("symbolic-ref", "HEAD", cwd=hub).stdout.strip(), "refs/heads/main")

    def test_look_reads_every_branch_and_the_tape(self):
        self.main_with({".gitattributes": "/.issues merge=union\n", ".issues": "a the first\n"})
        self.branch("feature", {".issues": "a the first\nb a second, said on the branch\n"})
        self.branch("retain/notes", {"n": "n"})
        hub = self.hub_of(self.look())
        self.assertEqual(hub["tape"], [["a", "the first"]])
        b = {x["name"]: x for x in hub["branches"]}
        self.assertEqual((b["feature"]["lands"], b["feature"]["ahead"], b["feature"]["behind"], b["feature"]["issues"]),
                         ("clean", 1, 0, ["b a second, said on the branch"]))
        self.assertTrue(b["retain/notes"]["library"])
        self.assertNotIn("lands", b["retain/notes"], "the library's branches never land")
        self.assertEqual(b["old"]["lands"], "held", "main holds all of it")
        self.assertTrue((self.origin / ".intake/look.json").exists(), "what a merge would do is kept")

    def test_an_order_lands_on_the_next_beat_and_the_branch_is_let_go(self):
        tip = self.branch("feature", {"f": "f"})
        r = self.door("land", HUB, "feature", tip)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("feature lands in %s's main on the beat of" % HUB, r.stdout)
        self.assertEqual([o["branch"] for o in self.look()["waiting"]], ["feature"])
        tape = self.beat()
        self.assertEqual((tape[-1]["done"], tape[-1]["tip"]), ("landed", tip))
        main = self.here("refs/heads/main")
        self.assertEqual(main, tape[-1]["main"])
        said = self.git("-C", str(self.hub), "log", "-1", "--format=%P%n%B", main).stdout
        self.assertIn(tip, said.split("\n", 1)[0])
        self.assertIn("Land feature\n\nOrdered by tester (workstation)", said)
        self.assertEqual(self.here("refs/heads/feature"), "", "landed and let go on the same beat")
        self.assertEqual(self.look()["waiting"], [])
        self.assertEqual(self.on_github("refs/heads/main"), main, "and carried out")

    def test_orders_land_in_turn_each_on_the_main_the_last_left(self):
        self.main_with({".gitattributes": "/.issues merge=union\n", ".issues": "a the first\n"})
        one = self.branch("one", {".issues": "a the first\na from one\n"})
        two = self.branch("two", {".issues": "a the first\na from two\n"})
        self.door("land", HUB, "two", two)
        self.door("land", HUB, "one", one)
        tape = self.beat()
        self.assertEqual([(t["branch"], t["done"]) for t in tape if "done" in t], [("two", "landed"), ("one", "landed")])
        lines = self.git("-C", str(self.hub), "show", "main:.issues").stdout.splitlines()
        self.assertEqual(sorted(lines), ["a from one", "a from two", "a the first"])

    def test_a_branch_that_moved_after_its_order_is_not_landed(self):
        tip = self.branch("feature", {"f": "f"})
        self.door("land", HUB, "feature", tip)
        self.branch("feature", {"g": "g"}, base="feature")
        main = self.here("refs/heads/main")
        tape = self.beat()
        self.assertEqual(tape[-1]["done"], "moved")
        self.assertEqual(self.here("refs/heads/main"), main)

    def test_a_collision_leaves_main_alone_and_says_where(self):
        tip = self.branch("feature", {"a": "the branch's"})
        self.main_with({"a": "main's"})
        main = self.here("refs/heads/main")
        self.assertEqual(self.hub_of(self.look())["branches"][0]["lands"], "collides")
        self.door("land", HUB, "feature", tip)
        tape = self.beat()
        self.assertEqual((tape[-1]["done"], tape[-1]["conflicts"]), ("collides", ["a"]))
        self.assertEqual(self.here("refs/heads/main"), main)
        self.assertTrue(self.here("refs/heads/feature"), "left for a person")

    def test_hold_takes_an_order_back(self):
        tip = self.branch("feature", {"f": "f"})
        self.door("land", HUB, "feature", tip)
        self.assertEqual(self.door("hold", HUB, "feature").returncode, 0)
        main = self.here("refs/heads/main")
        self.beat()
        self.assertEqual(self.here("refs/heads/main"), main)
        self.assertNotEqual(self.door("hold", HUB, "feature").returncode, 0, "nothing waiting now")

    def test_the_door_refuses_what_never_lands(self):
        tip = self.branch("feature", {"f": "f"})
        lib = self.branch("retain/notes", {"n": "n"})
        for words, why in (((HUB, "main", tip), "not a branch that lands"),
                           ((HUB, "retain/notes", lib), "not a branch that lands"),
                           ((HUB, "feature", lib), "has moved since it was looked at"),
                           ((HUB, "nothing", tip), "there is no branch nothing"),
                           (("FC-Public-Media/none", "feature", tip), "there is no FC-Public-Media/none here"),
                           ((HUB, "old", self.here("refs/heads/old")), "main already holds old")):
            r = self.door("land", *words)
            self.assertNotEqual(r.returncode, 0, words)
            self.assertIn(why, r.stderr, words)
        self.assertEqual(self.look()["waiting"], [])


if __name__ == "__main__":
    unittest.main()
