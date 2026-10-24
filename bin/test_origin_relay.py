#!/usr/bin/env python3
"""The origin's relay (machines/origin/intake, carry), end to end: a keyholder pushes through the door
(machines/origin/door, as test_origin_door.py drives it), and carry takes it out to a scratch "GitHub"
(a bare repository on disk): what was pushed since the last pass, fast-forward only, never main, never
a repository that began here, never what was already sitting at the origin.

    python3 bin/test_origin_relay.py
"""
import importlib.machinery
import importlib.util
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOOR = ROOT / "machines/origin/door"
INTAKE = ROOT / "machines/origin/intake"


class Relay(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        self.origin = self.tmp / "origin"
        self.github = self.tmp / "github"
        self.env = dict(os.environ, FCPM_ORIGIN=str(self.origin), GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
                        GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
        for full in ("FC-Public-Media/hub", "FC-Public-Media/lan"):
            self.git("init", "-q", "--bare", "-b", "main", str(self.origin / full))
        self.git("init", "-q", "--bare", "-b", "main", str(self.github / "hub"))
        hub = self.origin / "FC-Public-Media/hub"
        self.git("-C", str(hub), "config", "remote.github.url", str(self.github / "hub"))
        # GitHub's main, and the origin's copy of it, as intake would have it.
        seed = self.tmp / "seed"
        self.git("init", "-q", "-b", "main", str(seed))
        self.commit(seed, "a")
        self.git("-C", str(seed), "push", "-q", str(self.github / "hub"), "main")
        self.git("-C", str(seed), "push", "-q", str(hub), "main", "main:refs/heads/github/main")
        self.git("-C", str(seed), "push", "-q", str(hub), "main:refs/heads/old")   # here before relay
        ssh = self.tmp / "ssh"
        ssh.write_text(
            "#!/bin/sh\n"
            'for a in "$@"; do [ "$a" = -G ] && exit 0; done\n'
            'while [ "${1#-}" != "$1" ]; do case "$1" in -o|-p|-i) shift 2;; *) shift;; esac; done\n'
            f'shift; SSH_ORIGINAL_COMMAND="$*" exec {sys.executable} -I {DOOR} serve workstation tester\n')
        ssh.chmod(0o755)
        self.env["GIT_SSH_COMMAND"] = str(ssh)
        os.environ["FCPM_ORIGIN"] = str(self.origin)
        loader = importlib.machinery.SourceFileLoader("intake_under_test", str(INTAKE))
        self.intake = importlib.util.module_from_spec(importlib.util.spec_from_loader(loader.name, loader))
        loader.exec_module(self.intake)
        self.door("relay", "on")                # relay switched on: carrying counts from here

    def door(self, *words):
        return subprocess.run([self.env["GIT_SSH_COMMAND"], "door", *words], env=self.env, capture_output=True, text=True)

    def test_a_push_before_the_first_pass_still_goes_out(self):
        w = self.work()
        self.git("checkout", "-qb", "early", cwd=w)
        self.commit(w, "f")
        self.git("push", "-q", "origin", "early", cwd=w)       # after `relay on`, before any pass
        self.assertEqual([r["state"] for r in self.intake.carry()], ["carried"])

    def git(self, *args, cwd=None, check=True):
        return subprocess.run(["git", *args], cwd=cwd, env=self.env, capture_output=True, text=True, check=check)

    def commit(self, work, name):
        (work / name).write_text(name)
        self.git("add", name, cwd=work)
        self.git("commit", "-qm", name, cwd=work)

    def work(self, full="FC-Public-Media/hub"):
        w = self.tmp / ("w-" + full.replace("/", "-"))
        if not w.exists():
            self.git("clone", "-q", f"door:{full}", str(w))
        return w

    def on_github(self, ref):
        return self.git("-C", str(self.github / "hub"), "rev-parse", "-q", "--verify", ref, check=False).stdout.strip()

    def test_a_branch_pushed_here_goes_out_on_the_next_pass(self):
        w = self.work()
        self.git("checkout", "-qb", "feature", cwd=w)
        self.commit(w, "b")
        self.git("push", "-q", "origin", "feature", cwd=w)
        self.assertEqual(self.on_github("refs/heads/feature"), "")
        rows = self.intake.carry()
        self.assertEqual([r["state"] for r in rows], ["carried"])
        self.assertEqual(self.on_github("refs/heads/feature"), self.git("rev-parse", "HEAD", cwd=w).stdout.strip())
        self.assertEqual(self.intake.carry(), [], "a pass with nothing new pushed carries nothing")

    def test_what_was_here_before_relay_stays_here(self):
        self.assertEqual(self.intake.carry(), [])
        self.assertEqual(self.on_github("refs/heads/old"), "")

    def test_a_rebase_github_will_not_fast_forward_is_left_for_a_person(self):
        w = self.work()
        self.git("checkout", "-qb", "topic", cwd=w)
        self.commit(w, "c")
        self.git("push", "-q", str(self.github / "hub"), "topic", cwd=w)   # GitHub has its own topic
        self.git("reset", "-q", "--hard", "HEAD~1", cwd=w)
        self.commit(w, "d")
        self.git("push", "-q", "origin", "topic", cwd=w)                   # ours, not a descendant of theirs
        github_topic = self.on_github("refs/heads/topic")
        rows = self.intake.carry()
        self.assertEqual([r["state"] for r in rows], ["diverged"])
        self.assertEqual(self.on_github("refs/heads/topic"), github_topic, "GitHub's topic is never overwritten")

    def test_a_refusal_is_tried_again_not_left_for_a_person(self):
        hook = self.github / "hub/hooks/pre-receive"
        hook.write_text("#!/bin/sh\necho 'refusing to allow an OAuth App to create or update workflow "
                        "`.github/workflows/x.yml` without `workflow` scope' >&2\nexit 1\n")
        hook.chmod(0o755)
        w = self.work()
        self.git("checkout", "-qb", "ci", cwd=w)
        self.commit(w, "g")
        self.git("push", "-q", "origin", "ci", cwd=w)
        self.assertEqual([r["state"] for r in self.intake.carry()], ["error"])
        hook.unlink()                           # the scope granted
        self.assertEqual([r["state"] for r in self.intake.carry()], ["carried"])
        self.assertEqual(self.on_github("refs/heads/ci"), self.git("rev-parse", "HEAD", cwd=w).stdout.strip())

    def test_a_repository_that_began_here_is_never_carried(self):
        w = self.tmp / "lanwork"
        self.git("init", "-q", "-b", "main", str(w))
        self.commit(w, "x")
        self.git("push", "-q", "door:FC-Public-Media/lan", "main", cwd=w)
        self.assertEqual(self.intake.carry(), [])

    def test_main_is_never_carried(self):
        w = self.work()
        self.commit(w, "e")
        self.assertNotEqual(self.git("push", "-q", "origin", "main", cwd=w, check=False).returncode, 0)
        self.assertEqual(self.intake.carry(), [])


if __name__ == "__main__":
    unittest.main()
