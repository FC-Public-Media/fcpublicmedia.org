#!/usr/bin/env python3
"""What a main here pins, the origin keeps (machines/origin/intake, pinned): a pin by GitHub URL or by a
relative one, and the library's `origin` branch, each made here as a bare repository with GitHub's main."""
import importlib.machinery
import importlib.util
import os
import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
INTAKE = ROOT / "machines/origin/intake"


def git(*args, cwd=None):
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", *args],
                          cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


class Pins(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.origin = pathlib.Path(self.tmp.name) / "origin"
        os.environ["FCPM_ORIGIN"] = str(self.origin)
        loader = importlib.machinery.SourceFileLoader("intake_pins", str(INTAKE))
        self.intake = importlib.util.module_from_spec(importlib.util.spec_from_loader(loader.name, loader))
        loader.exec_module(self.intake)

    def tearDown(self):
        os.environ.pop("FCPM_ORIGIN", None)
        self.tmp.cleanup()

    def repo(self, full, branches):
        bare = self.origin / full
        git("init", "-q", "--bare", "-b", "main", str(bare))
        for branch, gitmodules in branches.items():
            work = pathlib.Path(self.tmp.name) / ("w-" + full.replace("/", "-") + "-" + branch)
            git("init", "-q", "-b", branch, str(work))
            (work / ".gitmodules").write_text(gitmodules)
            git("add", "-A", cwd=work)
            git("commit", "-q", "-m", "pins", cwd=work)
            git("push", "-q", str(bare), "%s:refs/heads/%s" % (branch, branch), cwd=work)

    def test_a_pin_comes_in(self):
        self.repo("FC-Public-Media/fcpublicmedia.org", {
            "main": '[submodule ".you-engine"]\n\tpath = .you-engine\n\turl = https://github.com/FCCN-ANTIBODY/you.anecdote.channel.git\n'
                    '[submodule "troves/pools"]\n\tpath = troves/pools\n\turl = https://fcpm-public@github.com/FC-Public-Media/pools.git\n',
            "origin": '[submodule "x"]\n\tpath = Other/thing\n\turl = ../../Other/thing\n'})
        self.repo("FCCN-ANTIBODY/you.anecdote.channel", {
            "main": '[submodule "anecdote.channel"]\n\tpath = anecdote.channel\n\turl = ../anecdote.channel\n'})
        have = {"FC-Public-Media/fcpublicmedia.org", "FCCN-ANTIBODY/you.anecdote.channel"}
        made = self.intake.pinned(have)
        self.assertEqual(made, ["FC-Public-Media/pools", "FCCN-ANTIBODY/anecdote.channel", "Other/thing"])
        url = git("-C", str(self.origin / "FCCN-ANTIBODY/anecdote.channel"), "config", "remote.github.url")
        self.assertEqual(url, "https://github.com/FCCN-ANTIBODY/anecdote.channel.git")
        self.assertEqual(self.intake.pinned(have | set(made)), [])


if __name__ == "__main__":
    unittest.main()
