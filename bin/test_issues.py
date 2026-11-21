#!/usr/bin/env python3
"""fcpm issues (machines/issues.py): `.issues` is read as committed, a line each; a lowercase label is a draft
and a capital one ready, and any other is shown as written; a line's story is every commit that touched it,
oldest first; a union merge that left two of one line says so on both; and this repository's own `.issues`
is a label and a title on every line.

    python3 bin/test_issues.py
"""
import pathlib
import subprocess
import sys
import tempfile
import unittest

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True                    # machines/ holds only profiles and their tools (test_binding)
sys.path.insert(0, str(REPO / "machines"))
import issues  # noqa: E402


def git(*args, cwd):
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", *args],
                   cwd=cwd, check=True, capture_output=True)


class Issues(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = pathlib.Path(self.tmp.name) / "demo"
        self.repo.mkdir()
        git("init", "-q", "-b", "main", ".", cwd=self.repo)
        (self.repo / ".gitattributes").write_text("/.issues merge=union\n")
        self.say("a the door is open\na the roof leaks\n", "two issues")

    def tearDown(self):
        self.tmp.cleanup()

    def say(self, text, message):
        (self.repo / ".issues").write_text(text)
        git("add", "-A", cwd=self.repo)
        git("commit", "-qm", message, cwd=self.repo)

    def test_a_repository_without_the_file_says_so(self):
        git("rm", "-q", ".issues", cwd=self.repo)
        git("commit", "-qm", "none", cwd=self.repo)
        self.assertIsNone(issues.look(self.repo))
        self.assertIn("keeps no .issues", issues.page(self.repo)[0])

    def test_lowercase_is_a_draft_capital_is_ready_and_any_label_is_shown(self):
        self.assertEqual([issues.kind(l) for l in ("a", "q", "B", "FA", "d2", "?", "")],
                         ["draft", "draft", "ready", "ready", "labelled d2", "labelled ?", "blank"])
        self.say("b the door is open at night\nA the roof leaks\nd2 something else\n", "turned")
        head = issues.page(self.repo)[0]
        self.assertIn("3 lines: 1 draft, 1 ready, 1 labelled another way", head)

    def test_a_lines_story_is_every_commit_that_touched_it(self):
        self.say("b the door is open at night\na the roof leaks\n", "the door: at night")
        self.say("b the door is open at night\na the roof leaks\na the sign is dark\n", "the sign")
        self.say("C the door is open at night, and nobody locks it\na the roof leaks\na the sign is dark\n", "the door: ready")
        rows = issues.look(self.repo)
        self.assertEqual([len(r["story"]) for r in rows], [3, 1, 1])
        self.assertEqual([t["said"] for t in rows[0]["story"]], ["two issues", "the door: at night", "the door: ready"])
        self.assertEqual([t["left"] for t in rows[0]["story"]],
                         [["a the door is open"], ["b the door is open at night"],
                          ["C the door is open at night, and nobody locks it"]])
        out, code = issues.story_page(self.repo, ["locks", "door"])
        self.assertEqual(code, 0)
        self.assertEqual(sum("the door" in l and l.startswith("    ") for l in out), 2)
        self.assertEqual(issues.story_page(self.repo, ["the"])[1], 2, "more than one line says that")
        self.assertEqual(issues.story_page(self.repo, ["3"])[0][0], "line 3 of .issues, demo")

    def test_the_file_is_read_as_committed(self):
        (self.repo / ".issues").write_text("a not committed\n")
        out = issues.page(self.repo)
        self.assertIn("2 lines", out[0])
        self.assertTrue(out[-1].startswith("uncommitted"))

    def test_a_merge_that_left_two_of_one_line_says_so_on_both(self):
        for branch, text in (("one", "b the door is open, by one\na the roof leaks\na from one\n"),
                             ("two", "b the door is open, by two\na the roof leaks\na from two\n")):
            git("checkout", "-q", "-b", branch, "main", cwd=self.repo)
            self.say(text, branch)
        git("checkout", "-q", "main", cwd=self.repo)
        git("merge", "-q", "--no-ff", "-m", "one", "one", cwd=self.repo)
        git("merge", "-q", "--no-ff", "-m", "two", "two", cwd=self.repo)
        rows = issues.look(self.repo)
        lines = [r["line"] for r in rows]
        for kept in ("b the door is open, by one", "b the door is open, by two", "a from one", "a from two"):
            self.assertIn(kept, lines)
        doors = [r for r in rows if "door" in r["line"]]
        self.assertEqual([r["twins"] for r in doors], [[doors[1]["n"]], [doors[0]["n"]]])
        out = issues.page(self.repo)
        self.assertEqual(sum("forked: line" in l for l in out), 2)
        self.assertEqual(sum("said twice: line" in l for l in out), 2 * (lines.count("a the roof leaks") - 1))
        self.assertEqual([r.get("twins") for r in rows if r["line"].startswith("a from")], [[], []])

    def test_how_many_lines_it_held_before(self):
        self.assertEqual(issues.count_at(self.repo, -60), 2)
        self.assertIsNone(issues.count_at(self.repo, 7 * issues.DAY), "no commit that long ago")


class Ours(unittest.TestCase):
    def test_every_line_of_this_repositorys_issues_is_a_label_and_a_title(self):
        lines = (REPO / ".issues").read_text(encoding="utf-8").splitlines()
        self.assertTrue(lines)
        for line in lines:
            label, title = issues.split(line)
            self.assertTrue(label and title and line == line.strip(), line)

    def test_the_file_merges_by_union(self):
        self.assertRegex((REPO / ".gitattributes").read_text(), r"(?m)^/\.issues\s+merge=union$")


if __name__ == "__main__":
    unittest.main()
