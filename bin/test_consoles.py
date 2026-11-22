#!/usr/bin/env python3
"""fcpm consoles (machines/consoles.py) and fcpm places (machines/places.py).

A console is one fixed shape, ROWS lines of at most COLS, whatever its composer says: what does not fit is
counted on its last line, and a composer that fails writes a page saying so. A page is put in place whole and
read without composing, unless it is missing or three beats stale. CONSOLES is Fighter's list.

An origin branch is known by its shape (every submodule at <owner>/<repo>), and lists each repository as its
worktree in the shed named for the branch, its read-only mirror, or offered with what it needs.

    python3 bin/test_consoles.py
"""
import os
import pathlib
import subprocess
import sys
import tempfile
import time
import unittest

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True                    # machines/ holds only profiles and their tools (test_binding)
sys.path.insert(0, str(REPO / "machines"))
import consoles  # noqa: E402
import places  # noqa: E402
import workshed  # noqa: E402


def git(*args, cwd):
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", *args],
                          cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


class Consoles(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.was = (consoles.DIR, dict(consoles.CONSOLES))
        consoles.DIR = pathlib.Path(self.tmp.name) / "consoles"
        self.calls = 0

        def counted():
            self.calls += 1
            return ["line %d" % i for i in range(3)]
        consoles.CONSOLES.clear()
        consoles.CONSOLES.update({"short": (10, counted), "long": (10, lambda: ["x" * 200] + ["row"] * 60),
                                  "broken": (10, lambda: 1 / 0)})

    def tearDown(self):
        consoles.DIR = self.was[0]
        consoles.CONSOLES.clear()
        consoles.CONSOLES.update(self.was[1])
        self.tmp.cleanup()

    def test_every_page_is_the_same_shape(self):
        for name in ("short", "long", "broken"):
            lines = consoles.write(name).split("\n")[:-1]
            self.assertEqual(len(lines), consoles.ROWS, name)
            self.assertTrue(all(len(l) <= consoles.COLS for l in lines), name)
            self.assertTrue(lines[0].startswith(name) and "fresh until" in lines[0], name)

    def test_what_does_not_fit_is_counted(self):
        lines = consoles.write("long").split("\n")
        self.assertTrue(lines[1].endswith("..."))
        self.assertEqual(lines[consoles.ROWS - 1], "... %d more lines" % (61 - (consoles.ROWS - 2)))

    def test_a_composer_that_fails_says_so(self):
        self.assertIn("could not be written: division by zero", consoles.write("broken"))

    def test_reading_never_composes_a_fresh_page(self):
        consoles.read("short")
        consoles.read("short")
        self.assertEqual(self.calls, 1)
        old = time.time() - 31                     # three beats stale: no helm is keeping it
        os.utime(consoles.path("short"), (old, old))
        consoles.read("short")
        self.assertEqual(self.calls, 2)

    def test_the_helm_console_lists_a_joined_intake_after_the_helms(self):
        was = consoles.answers, os.environ.get("FCPM_WEARS")
        consoles.answers = lambda url, timeout=2: "bounce.local" in url
        os.environ["FCPM_WEARS"] = "digitization"
        try:
            rows = consoles.helm()
        finally:
            consoles.answers = was[0]
            if was[1] is None:
                os.environ.pop("FCPM_WEARS")
            else:
                os.environ["FCPM_WEARS"] = was[1]
        self.assertEqual(rows[-1].split(), ["Q", "qr", "answering", "joined", "http://bounce.local"])
        self.assertEqual(rows[-2].split()[:2], ["2", "editing-bay-2"])

    def test_the_list_is_fighters(self):
        consoles.write("short")
        text = (consoles.DIR / "CONSOLES").read_text(encoding="utf-8")
        self.assertEqual(text.splitlines()[0], "# supplier: helm")
        self.assertEqual(text.splitlines()[1].split("\t"), ["short", str(consoles.path("short")), "helm"])
        self.assertIn("long\thttp://bay:8080/consoles/long\thelm", consoles.listing("http://bay:8080"))


class Places(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        code = pathlib.Path(self.tmp.name) / "code"
        home = code / "refs" / places.HOME_REPO
        home.mkdir(parents=True)
        git("init", "-q", "-b", "main", cwd=home)
        (home / "README.md").write_text("x\n")
        git("add", ".", cwd=home)
        git("commit", "-q", "-m", "main", cwd=home)
        self.pin = git("rev-parse", "HEAD", cwd=home)
        # The origin branch: two pinned repositories at <owner>/<repo>, one following a branch.
        git("checkout", "-q", "--orphan", "origin", cwd=home)
        git("rm", "-rq", "--cached", ".", cwd=home)
        (home / ".gitmodules").write_text('[submodule "Owner/demo"]\n\tpath = Owner/demo\n\turl = ../../Owner/demo\n'
                                          '\tbranch = tiliv\n[submodule "Owner/gone"]\n\tpath = Owner/gone\n'
                                          '\turl = ../../Owner/gone\n')
        git("add", ".gitmodules", cwd=home)
        for p in ("Owner/demo", "Owner/gone"):
            git("update-index", "--add", "--cacheinfo", "160000,%s,%s" % (self.pin, p), cwd=home)
        git("commit", "-q", "-m", "origin", cwd=home)
        git("update-ref", "refs/remotes/origin/origin", "HEAD", cwd=home)
        # Ordinary branches named like one: a trove at troves/x looks like <owner>/<repo>, but its folder has a
        # README beside it; an engine at .advocate-engine is not at <owner>/<repo> at all.
        git("checkout", "-q", "-f", "main", cwd=home)
        (home / "troves").mkdir()
        (home / "troves" / "README.md").write_text("troves\n")
        git("add", "troves/README.md", cwd=home)
        git("update-index", "--add", "--cacheinfo", "160000,%s,troves/x" % self.pin, cwd=home)
        git("commit", "-q", "-m", "a trove", cwd=home)
        git("update-ref", "refs/remotes/origin/origin-evidence", "HEAD", cwd=home)
        git("update-index", "--add", "--cacheinfo", "160000,%s,.advocate-engine" % self.pin, cwd=home)
        git("rm", "-q", "--cached", "troves/README.md", cwd=home)
        git("commit", "-q", "-m", "an engine", cwd=home)
        git("update-ref", "refs/remotes/origin/origin-workflow-scope", "HEAD", cwd=home)
        # A mirror of Owner/demo (its origin says so), holding the pin.
        demo = code / "refs" / "demo"
        git("clone", "-q", str(home), str(demo), cwd=self.tmp.name)
        git("remote", "set-url", "origin", "https://github.com/owner/Demo.git", cwd=demo)
        self.code, self.was = code, places.CODE
        places.CODE = code
        # The origin branches' sheds are the workshed's, placed by a binding of the test's own.
        self.shed_was = workshed.CODE, workshed.BINDINGS
        (code / "workshed.yml").write_text("origins: origins\n")
        workshed.CODE, workshed.BINDINGS = code, [code / "workshed.yml"]
        os.environ.pop("FIGHTER_MODE", None)

    def tearDown(self):
        places.CODE = self.was
        workshed.CODE, workshed.BINDINGS = self.shed_was
        self.tmp.cleanup()

    def test_an_origin_is_known_by_its_shape(self):
        self.assertEqual(places.origins(), ["origin"])
        self.assertIsNone(places.pins("origin-evidence"))
        self.assertIsNone(places.pins("origin-workflow-scope"))
        self.assertEqual(places.pins("origin")["Owner/demo"], (self.pin, "tiliv"))

    def test_a_mirror_a_worktree_and_an_offer(self):
        (self.code / "origins" / "origin" / "demo@visit").mkdir(parents=True)
        lines = places.listing().splitlines()
        self.assertEqual(lines[0], "@modes\torigin")
        self.assertEqual(lines[1], "# Owner")
        rows = [l.split("\t") for l in lines[2:]]
        self.assertEqual(rows[0][:2], ["demo@visit", str(self.code / "origins" / "origin" / "demo@visit")])
        self.assertIn("worktree in the origin shed", rows[0][2])
        self.assertEqual(rows[1][:2], ["demo", str(self.code / "refs" / "demo")])
        self.assertEqual(rows[1][2], "pin %s, follows tiliv, mirror (read only)" % self.pin[:7])
        self.assertEqual(rows[2][:2], ["gone", ""])
        self.assertIn("offered, not mirrored here", rows[2][2])

    def test_fighters_mode_picks_the_branch(self):
        os.environ["FIGHTER_MODE"] = "origin-evidence"
        try:
            self.assertIn("not an origin branch", places.listing())
        finally:
            os.environ.pop("FIGHTER_MODE")


if __name__ == "__main__":
    unittest.main(verbosity=2)
