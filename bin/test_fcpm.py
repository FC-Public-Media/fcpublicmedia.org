#!/usr/bin/env python3
"""fcpm and machines/fcpm.yml name the same verbs; a verb this platform lacks says what stands in and exits 3;
bin/refs keeps the mirrors under FCPM_CODE, in refs/ or the kiosk's ref/.

    python3 bin/test_fcpm.py
"""
import os
import pathlib
import re
import subprocess
import tempfile
import unittest

import yaml

REPO = pathlib.Path(__file__).resolve().parents[1]
FCPM = REPO / "machines" / "fcpm"
VERBS = yaml.safe_load((REPO / "machines" / "fcpm.yml").read_text(encoding="utf-8"))["verbs"]


def arms():
    text = FCPM.read_text(encoding="utf-8")
    body = text[text.index('case "$cmd" in'):]
    names = set()
    for m in re.finditer(r"^  ([a-z0-9|*-]+)\)", body, re.M):
        names.update(m.group(1).split("|"))
    return names - {"*", "-h", "--help"}


def git(*args, cwd):
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", *args],
                   cwd=cwd, check=True, capture_output=True)


class Table(unittest.TestCase):
    def test_same_verbs(self):
        self.assertEqual({v["verb"] for v in VERBS}, arms())

    def test_every_verb_says_both_platforms(self):
        for v in VERBS:
            for plat in ("windows", "linux"):
                self.assertIn(plat, v, v["verb"])
                how = str(v[plat])
                self.assertFalse(how.startswith("not ") and not how.startswith("not:"), f"{v['verb']} {plat}: {how}")


class Run(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = pathlib.Path(self.tmp.name)
        self.env = {**os.environ, "HOME": str(self.home), "FCPM_CODE": str(self.home / "code")}

    def tearDown(self):
        self.tmp.cleanup()

    def run_(self, *args):
        return subprocess.run(list(args), env=self.env, capture_output=True, text=True, timeout=60)

    def test_not_here_exits_3_with_the_stand_in(self):
        r = self.run_("sh", str(FCPM), "camera", "console")
        self.assertEqual(r.returncode, 3, r.stderr)
        self.assertIn("speaks Windows COM", r.stderr)

    def test_pull_without_a_mirror_is_not_here(self):
        r = self.run_("sh", str(FCPM), "pull")
        self.assertEqual(r.returncode, 3, r.stderr)
        self.assertIn("no mirror", r.stderr)

    def test_help_lists_what_stands_in(self):
        r = self.run_("sh", str(FCPM), "help")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("fcpm pull", r.stdout.split("Not on linux")[0])
        self.assertIn("fcpm camera", r.stdout.split("Not on linux")[1])

    def test_refs_in_the_kiosks_ref(self):
        up = self.home / "up"
        up.mkdir()
        git("init", "-q", "-b", "main", ".", cwd=up)
        (up / "a").write_text("a\n")
        git("add", "-A", cwd=up)
        git("commit", "-q", "-m", "a", cwd=up)
        ref = self.home / "code" / "ref"
        ref.mkdir(parents=True)
        git("clone", "-q", str(up), "demo", cwd=ref)
        refs = str(REPO / "bin" / "refs")

        r = self.run_("bash", refs, "status")
        self.assertRegex(r.stdout, r"demo\s+main\s+behind=0")
        (up / "a").write_text("b\n")
        git("commit", "-qam", "b", cwd=up)
        r = self.run_("bash", refs, "pull", "demo")
        self.assertIn("UPDATED", r.stdout, r.stderr)

        r = self.run_("bash", refs, "work", "demo", "x/y")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue((self.home / "code" / "work" / "demo@x-y" / "a").exists())
        r = self.run_("bash", refs, "done", "demo", "x/y")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse((self.home / "code" / "work" / "demo@x-y").exists())


if __name__ == "__main__":
    unittest.main()
