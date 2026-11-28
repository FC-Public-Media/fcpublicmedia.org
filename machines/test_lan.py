#!/usr/bin/env python3
"""On the LAN, as this machine: its key at the origin, pull, the library, names, Helm. Writes go to scratch only."""
import importlib.util
import json
import os
import pathlib
import shutil
import socket
import subprocess
import sys
import tempfile
import unittest
import urllib.request

REPO = pathlib.Path(__file__).resolve().parents[1]
ORIGIN = os.environ.get("FCPM_ORIGIN_URL", "fcpm-origin:/srv/origin")
HOST = ORIGIN.split(":", 1)[0]
OURS = "FC-Public-Media/fcpublicmedia.org"
HELM = os.environ.get("FCPM_HELM", "http://helm.fcpublicmedia.local")


def git(*args, cwd=None):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True,
                          env=dict(os.environ, GIT_TERMINAL_PROMPT="0")).stdout.strip()


class Lan(unittest.TestCase):
    def setUp(self):
        base = os.environ.get("FCPM_LAN_SCRATCH")
        self.tmp = tempfile.TemporaryDirectory(dir=base or None)
        self.at = pathlib.Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def main_on_the_origin(self):
        return git("ls-remote", "%s/%s" % (ORIGIN, OURS), "refs/heads/main").split()[0]

    def clone(self, depth):
        here = self.at / "fcpublicmedia.org"
        git("clone", "-q", "--depth", str(depth), "-b", "main", "%s/%s" % (ORIGIN, OURS), str(here))
        return here

    def test_the_origin_answers_this_machines_key(self):
        r = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", HOST, "look", OURS],
                           capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr)
        repo = next(x for x in json.loads(r.stdout)["repos"] if x["repo"] == OURS)
        self.assertEqual(repo["main"], self.main_on_the_origin())

    def test_pull_brings_a_checkout_from_the_origin(self):
        here = self.clone(3)
        git("reset", "-q", "--hard", "HEAD~1", cwd=here)
        git("remote", "set-url", "origin", "https://github.com/%s.git" % OURS, cwd=here)
        # This tree's pull, run as the checkout's own: beside it, kept out of its status.
        tools = here / ".lan-tools"
        tools.mkdir()
        shutil.copy(REPO / "machines" / "pull", tools / "pull")
        with open(here / ".git" / "info" / "exclude", "a") as f:
            f.write("/.lan-tools/\n")
        r = subprocess.run(["sh", str(tools / "pull")], capture_output=True, text=True, timeout=1800)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(git("remote", "get-url", "origin", cwd=here), "%s/%s" % (ORIGIN, OURS))
        self.assertEqual(git("rev-parse", "HEAD", cwd=here), self.main_on_the_origin())
        self.assertTrue((here / "troves" / "scanner" / ".git").exists(), r.stdout)

    def test_the_library_takes_up_a_machines_retained_branch(self):
        here = self.clone(1)
        os.environ["FCPM_LIBRARY"] = str(self.at / "library")
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location("library_on_the_lan", REPO / "machines" / "library.py")
        library = importlib.util.module_from_spec(spec)
        sys.path.insert(0, str(REPO / "machines"))
        spec.loader.exec_module(library)
        library.REPO = here
        wt = library.retain("production", make=True)
        self.assertTrue((wt / "CONTEXT.md").is_file(), "retain/production's CONTEXT.md came from the origin")
        self.assertEqual(git("branch", "--show-current", cwd=wt), "retain/production")

    def test_the_lans_names_resolve(self):
        for name in ("origin.local", HELM.split("//")[-1].split("/")[0]):
            self.assertTrue(socket.getaddrinfo(name, 80, socket.AF_INET), name)

    def test_helms_board_answers(self):
        with urllib.request.urlopen(HELM + "/board/now", timeout=15) as r:
            board = json.load(r)
        self.assertIn("deploy", board)


if __name__ == "__main__":
    unittest.main()
