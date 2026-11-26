#!/usr/bin/env python3
"""fcpm and machines/fcpm.yml name the same verbs; a verb this platform lacks says what stands in and exits 3;
machines/pull brings a checkout named at GitHub from the origin instead.

    python3 bin/test_fcpm.py
"""
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import unittest

import yaml

REPO = pathlib.Path(__file__).resolve().parents[1]
FCPM = REPO / "machines" / "fcpm"
VERBS = yaml.safe_load((REPO / "machines" / "fcpm.yml").read_text(encoding="utf-8"))["verbs"]
PLAT = "windows" if sys.platform == "win32" else "linux"
AWAY = next(v for v in VERBS if str(v[PLAT]).startswith("not:")
            and not all(str(v[p]).startswith("not:") for p in ("windows", "linux")))


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
        gone = {v["verb"] for v in VERBS if all(str(v[p]).startswith("not:") for p in ("windows", "linux"))}
        self.assertEqual({v["verb"] for v in VERBS} - gone, arms())
        self.assertFalse(gone & arms(), "a verb no platform has needs no arm")

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
        r = self.run_("sh", str(FCPM), AWAY["verb"])
        self.assertEqual(r.returncode, 3, r.stderr)
        self.assertIn(str(AWAY[PLAT])[4:].strip(), r.stderr)

    def test_pull_points_to_install(self):
        r = self.run_("sh", str(FCPM), "pull")
        self.assertEqual(r.returncode, 3, r.stderr)
        self.assertIn("fcpm install brings in the latest", r.stderr)

    def test_help_lists_what_stands_in(self):
        r = self.run_("sh", str(FCPM), "help")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("fcpm install [JOB]", r.stdout.split("Not on " + PLAT)[0])
        self.assertIn("fcpm " + AWAY["verb"], r.stdout.split("Not on " + PLAT)[1])

    def test_pull_from_the_origin(self):
        origin = self.home / "origin"
        up = origin / "FC-Public-Media" / "fcpublicmedia.org"
        up.mkdir(parents=True)
        git("init", "-q", "-b", "main", ".", cwd=up)
        (up / "machines").mkdir()
        (up / "machines" / "pull").write_bytes((REPO / "machines" / "pull").read_bytes())
        git("add", "-A", cwd=up)
        git("commit", "-q", "-m", "a", cwd=up)
        here = self.home / "code" / "fcpublicmedia.org"
        git("clone", "-q", str(up), str(here), cwd=self.home)
        git("remote", "set-url", "origin", "https://github.com/FC-Public-Media/fcpublicmedia.org.git", cwd=here)
        (up / "b").write_text("b\n")
        git("add", "-A", cwd=up)
        git("commit", "-q", "-m", "b", cwd=up)

        env = dict(os.environ, HOME=str(self.home), FCPM_ORIGIN_URL=str(origin))
        r = subprocess.run(["sh", str(here / "machines" / "pull")], env=env, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        url = subprocess.run(["git", "remote", "get-url", "origin"], cwd=here, capture_output=True, text=True).stdout
        self.assertEqual(url.strip(), str(up))
        self.assertTrue((here / "b").exists(), r.stdout)

if __name__ == "__main__":
    unittest.main()
