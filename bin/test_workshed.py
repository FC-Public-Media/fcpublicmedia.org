#!/usr/bin/env python3
"""fcpm workshed (machines/workshed.py): a worktree is made in ~/code/workshed/<shed>/<repo>@<branch> from
refs/<repo>, cut from origin/main or following origin's branch; each gets the lowest free port and keeps it;
a short name finds it when only one worktree has it; a changed page is named by its URL; remove never takes
a worktree with changes, and gives its port back. Building and serving need a Node and jekyll-enough, which
`fcpm workshed check` reports; this test does not need them.

    python3 bin/test_workshed.py
"""
import contextlib
import io
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True                    # machines/ holds only profiles and their tools (test_binding)
sys.path.insert(0, str(REPO / "machines"))
import workshed  # noqa: E402


def git(*args, cwd):
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", *args],
                   cwd=cwd, check=True, capture_output=True)


class Workshed(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = pathlib.Path(self.tmp.name)
        # An origin with main and one branch of its own, and refs/demo cloned from it, as fcpm pull keeps it.
        seed = root / "seed"
        (seed / "site").mkdir(parents=True)
        (seed / "site" / "_config.yml").write_text("title: t\n")
        (seed / "site" / "meet.md").write_text("---\ntitle: Meet\n---\nhi\n")
        git("init", "-q", "-b", "main", cwd=seed)
        git("add", ".", cwd=seed)
        git("commit", "-q", "-m", "seed", cwd=seed)
        git("branch", "christmas", cwd=seed)
        git("clone", "-q", "--bare", str(seed), str(root / "origin.git"), cwd=root)
        code = root / "code"
        (code / "refs").mkdir(parents=True)
        git("clone", "-q", str(root / "origin.git"), str(code / "refs" / "demo"), cwd=root)
        self.saved = {k: getattr(workshed, k) for k in ("CODE", "SHED", "LOG", "PORTS", "STATE")}
        workshed.CODE, workshed.SHED = code, code / "workshed"
        workshed.LOG, workshed.PORTS = code / "workshed" / "workshed.log", code / "workshed" / "ports.json"
        workshed.STATE = root / "state"

    def tearDown(self):
        # The test's own worktrees, while workshed still points at the test's code root, and only inside it: a
        # person's real ~/code/workshed is never touched (Windows cannot remove a directory git still lists).
        tmp = pathlib.Path(self.tmp.name).resolve()
        for w in workshed.worktrees():
            if tmp in pathlib.Path(w["path"]).resolve().parents:
                subprocess.run(["git", "worktree", "remove", "--force", str(w["path"])],
                               cwd=workshed.CODE / "refs" / w["repo"], capture_output=True)
        for k, v in self.saved.items():
            setattr(workshed, k, v)
        self.tmp.cleanup()

    def new(self, branch, **kw):
        with contextlib.redirect_stdout(io.StringIO()):
            return workshed.new(branch, repo="demo", **kw)

    def test_new_is_a_worktree_in_its_shed_with_a_port(self):
        name = self.new("meet-photos")
        self.assertEqual(name, "dev/demo@meet-photos")
        path = workshed.SHED / "dev" / "demo@meet-photos"
        self.assertTrue((path / "site" / "meet.md").is_file())
        self.assertEqual(workshed.port_of(name), workshed.FIRST_PORT)
        self.assertEqual(self.new("other", shed="seasons"), "seasons/demo@other")
        self.assertEqual(workshed.port_of("seasons/demo@other"), workshed.FIRST_PORT + 1)
        self.assertIn("dev/demo@meet-photos: made (new, from origin/main), port %d" % workshed.FIRST_PORT,
                      workshed.LOG.read_text())

    def test_a_branch_on_the_origin_is_followed(self):
        self.new("christmas")
        out = subprocess.run(["git", "rev-parse", "--abbrev-ref", "christmas@{upstream}"], capture_output=True, text=True,
                             cwd=workshed.SHED / "dev" / "demo@christmas").stdout.strip()
        self.assertEqual(out, "origin/christmas")

    def test_names_find_one_or_say_which(self):
        self.new("meet-photos")
        with self.assertRaises(workshed.Wrong) as said:     # one branch is checked out in one place only
            self.new("meet-photos", shed="seasons")
        self.assertIn("already used by worktree", str(said.exception))
        git("clone", "-q", str(pathlib.Path(self.tmp.name) / "origin.git"), str(workshed.CODE / "refs" / "demo2"),
            cwd=self.tmp.name)
        with contextlib.redirect_stdout(io.StringIO()):
            workshed.new("meet-photos", shed="seasons", repo="demo2")
        self.assertEqual(workshed.find("dev/demo@meet-photos")["shed"], "dev")
        self.assertEqual(workshed.find("demo2@meet-photos")["shed"], "seasons")
        with self.assertRaises(workshed.Wrong) as said:
            workshed.find("meet-photos")
        self.assertIn("say which", str(said.exception))
        with self.assertRaises(workshed.Wrong):
            workshed.find("nothing-like-it")

    def test_a_name_git_refuses_is_refused(self):
        with self.assertRaises(workshed.Wrong):
            self.new("two words")
        with self.assertRaises(workshed.Wrong):
            self.new("meet-photos", shed="a/b")

    def test_a_changed_page_is_named_by_its_url(self):
        name = self.new("meet-photos")
        state = workshed.state_dir(name)
        state.mkdir(parents=True)                     # what the server writes after a build
        (state / "pages.json").write_text(json.dumps([{"url": "/meet/", "title": "Meet", "source": "meet.md"}]))
        path = workshed.SHED / "dev" / "demo@meet-photos"
        (path / "site" / "meet.md").write_text("---\ntitle: Meet\n---\nhello\n")
        (path / "site" / "photo.jpg").write_bytes(b"\xff\xd8")
        d = workshed.describe(workshed.find("meet-photos"))
        self.assertEqual(d["changed_pages"], ["/meet/"])
        self.assertEqual(d["changed_other"], ["site/photo.jpg"])
        self.assertTrue(d["dirty"])
        self.assertFalse(d["running"])

    def test_remove_never_takes_changes_and_gives_the_port_back(self):
        name = self.new("meet-photos")
        path = workshed.SHED / "dev" / "demo@meet-photos"
        (path / "site" / "meet.md").write_text("changed\n")
        with self.assertRaises(workshed.Wrong):
            workshed.remove("meet-photos")
        self.assertTrue(path.is_dir())
        git("checkout", "--", ".", cwd=path)
        with contextlib.redirect_stdout(io.StringIO()):
            workshed.remove("meet-photos")
        self.assertFalse(path.exists())
        self.assertIsNone(workshed.port_of(name))
        branches = subprocess.run(["git", "branch", "--list", "meet-photos"], capture_output=True, text=True,
                                  cwd=workshed.CODE / "refs" / "demo").stdout
        self.assertIn("meet-photos", branches)        # the branch is kept

    def test_a_site_is_found_in_site_or_at_the_top(self):
        root = pathlib.Path(self.tmp.name) / "plain"
        root.mkdir()
        self.assertIsNone(workshed.build_root(root))
        (root / "_config.yml").write_text("")
        self.assertEqual(workshed.build_root(root), root)
        (root / "site").mkdir()
        (root / "site" / "_config.yml").write_text("")
        self.assertEqual(workshed.build_root(root), root / "site")

    def test_engines_are_looked_for_from_the_code_root(self):
        os.environ.pop("FCPM_JEKYLL_ENOUGH", None)
        self.assertEqual(workshed.engines(), [workshed.CODE / "origin" / "FCCN-ANTIBODY" / "jekyll-enough",
                                              workshed.CODE / "refs" / "jekyll-enough"])
        self.assertIsNone(workshed.engine())


if __name__ == "__main__":
    unittest.main(verbosity=2)
