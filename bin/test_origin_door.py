#!/usr/bin/env python3
"""The origin's SSH door (machines/digitization/origin-door), end to end against a scratch origin.

git reaches the door through a stand-in for ssh that does what sshd does with a forced command:
it puts what git asked for in SSH_ORIGINAL_COMMAND and runs `origin-door serve OFFICE HOLDER`.
"""
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOOR = ROOT / "machines/digitization/origin-door"
KEY = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOrigindoortestkeyonlynotarealkeyatall000"


class Door(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        self.origin = self.tmp / "origin"
        for full, github in (("FC-Public-Media/lan", None), ("FC-Public-Media/hub", "https://github.com/x/hub.git")):
            repo = self.origin / full
            self.git("init", "-q", "--bare", "-b", "main", str(repo))
            self.git("-C", str(repo), "config", "receive.denyNonFastForwards", "true")
            self.git("-C", str(repo), "config", "receive.denyDeletes", "true")
            if github:
                self.git("-C", str(repo), "config", "remote.github.url", github)
        self.env = dict(os.environ, FCPM_ORIGIN=str(self.origin), GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
                        GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
        self.as_office("technology", "Tester")

    def as_office(self, office, holder):
        ssh = self.tmp / f"ssh-{office}"
        ssh.write_text(
            "#!/bin/sh\n"
            '# git asks `ssh -G` which ssh it has; real ssh answers that without reaching the server\n'
            'for a in "$@"; do [ "$a" = -G ] && exit 0; done\n'
            'while [ "${1#-}" != "$1" ]; do case "$1" in -o|-p|-i) shift 2;; *) shift;; esac; done\n'
            f'shift; SSH_ORIGINAL_COMMAND="$*" exec {sys.executable} -I {DOOR} serve {office} {holder}\n')
        ssh.chmod(0o755)
        self.env["GIT_SSH_COMMAND"] = str(ssh)

    def git(self, *args, cwd=None, check=True):
        return subprocess.run(["git", *args], cwd=cwd, env=getattr(self, "env", None), capture_output=True,
                              text=True, check=check)

    def log(self):
        return [json.loads(line) for line in (self.origin / ".door/actions.ndjson").read_text().splitlines()]

    def clone(self, full):
        work = self.tmp / full.replace("/", "-")
        self.git("clone", "-q", f"door:{full}", str(work))
        return work

    def commit(self, work, name):
        (work / name).write_text(name)
        self.git("add", name, cwd=work)
        self.git("commit", "-qm", name, cwd=work)

    def test_a_keyholder_pushes_to_a_repository_that_began_here(self):
        work = self.clone("FC-Public-Media/lan")
        self.commit(work, "slide.txt")
        self.git("push", "-q", "origin", "HEAD:main", cwd=work)
        head = self.git("-C", str(self.origin / "FC-Public-Media/lan"), "rev-parse", "main").stdout.strip()
        self.assertEqual(head, self.git("rev-parse", "HEAD", cwd=work).stdout.strip())
        push = [r for r in self.log() if r["verb"] == "push"][-1]
        self.assertEqual((push["office"], push["holder"], push["ok"]), ("technology", "Tester", True))
        self.assertEqual(push["moved"]["refs/heads/main"], [None, head])

    def test_main_of_a_repository_on_github_is_intakes(self):
        work = self.clone("FC-Public-Media/hub")
        self.commit(work, "x")
        for ref in ("main", "github/main"):
            run = self.git("push", "-q", "origin", f"HEAD:{ref}", cwd=work, check=False)
            self.assertNotEqual(run.returncode, 0, ref)
            self.assertIn("by intake", run.stderr)
        self.assertEqual(self.git("-C", str(self.origin / "FC-Public-Media/hub"), "for-each-ref").stdout, "")

    def test_a_branch_waits_at_the_origin_for_github(self):
        work = self.clone("FC-Public-Media/hub")
        self.commit(work, "x")
        self.git("push", "-q", "origin", "HEAD:refs/heads/brand-source", cwd=work)
        self.git("update-ref", "refs/tags/snapshot-1", "HEAD", cwd=work)
        self.git("push", "-q", "origin", "snapshot-1", cwd=work)
        held = self.git("-C", str(self.origin / "FC-Public-Media/hub"), "for-each-ref", "--format=%(refname)").stdout.split()
        self.assertEqual(held, ["refs/heads/brand-source", "refs/tags/snapshot-1"])
        push = [r for r in self.log() if r["verb"] == "push"][-1]
        self.assertIn("refs/tags/snapshot-1", push["moved"])

    def test_history_is_never_rewritten(self):
        work = self.clone("FC-Public-Media/lan")
        self.commit(work, "a")
        self.git("push", "-q", "origin", "HEAD:main", cwd=work)
        self.git("commit", "--amend", "-qm", "rewritten", cwd=work)
        run = self.git("push", "-q", "--force", "origin", "HEAD:main", cwd=work, check=False)
        self.assertNotEqual(run.returncode, 0)

    def test_only_the_secretary_makes_a_repository(self):
        run = subprocess.run([self.env["GIT_SSH_COMMAND"], "door", "init", "FC-Public-Media/new"],
                             env=self.env, capture_output=True, text=True)
        self.assertNotEqual(run.returncode, 0)
        self.assertFalse((self.origin / "FC-Public-Media/new").exists())
        self.as_office("secretary", "Autumn")
        run = subprocess.run([self.env["GIT_SSH_COMMAND"], "door", "init", "FC-Public-Media/new"],
                             env=self.env, capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        made = self.origin / "FC-Public-Media/new"
        self.assertEqual(self.git("-C", str(made), "config", "receive.denyDeletes").stdout.strip(), "true")
        self.assertIn("secretary (Autumn)", (made / "description").read_text())

    def test_nothing_outside_the_origin(self):
        for asked in ("git-upload-pack '../../etc'", "git-upload-pack 'a/b/c'", "sh -c id", "git-upload-pack"):
            run = subprocess.run([self.env["GIT_SSH_COMMAND"], "door", asked], env=self.env,
                                 capture_output=True, text=True)
            self.assertNotEqual(run.returncode, 0, asked)
        self.assertTrue(all("refused" in r for r in self.log()))


class Keys(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        self.keyholders = self.tmp / "KEYHOLDERS"
        self.authorized = self.tmp / "authorized_keys"
        self.authorized.write_text('restrict,command="eyes" ssh-ed25519 AAAAeyes eyes\n')
        self.env = dict(os.environ, FCPM_KEYHOLDERS=str(self.keyholders), FCPM_AUTHORIZED_KEYS=str(self.authorized))

    def keys(self, *extra):
        return subprocess.run([sys.executable, "-I", str(DOOR), "keys", *extra], env=self.env,
                              capture_output=True, text=True)

    def test_a_filled_slot_becomes_one_forced_line_and_the_rest_stays(self):
        self.keyholders.write_text(f"secretary Autumn - -\ntechnology Autumn {KEY} 2026-10-21\n")
        self.assertEqual(self.keys().returncode, 0)
        lines = self.authorized.read_text().splitlines()
        self.assertEqual(lines[0], 'restrict,command="eyes" ssh-ed25519 AAAAeyes eyes')
        door = [line for line in lines if line.startswith("restrict,command=") and "origin-door" in line]
        self.assertEqual(len(door), 1)
        self.assertIn("serve technology Autumn", door[0])
        self.assertIn(KEY, door[0])
        self.assertEqual(oct(self.authorized.stat().st_mode & 0o777), "0o600")
        self.assertIn("as KEYHOLDERS says", self.keys().stdout)

    def test_emptying_a_slot_takes_its_key_out(self):
        self.keyholders.write_text(f"technology Autumn {KEY} 2026-10-21\n")
        self.keys()
        self.keyholders.write_text("technology Autumn - -\n")
        self.keys()
        self.assertNotIn(KEY, self.authorized.read_text())
        self.assertIn("eyes", self.authorized.read_text())

    def test_check_changes_nothing(self):
        self.keyholders.write_text(f"technology Autumn {KEY} 2026-10-21\n")
        before = self.authorized.read_text()
        self.assertIn("would change", self.keys("--check").stdout)
        self.assertEqual(self.authorized.read_text(), before)

    def test_a_bad_line_is_loud(self):
        self.keyholders.write_text("technology Autumn rsa-sha1 AAAA 2026\n")
        run = self.keys()
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("KEYHOLDERS:1", run.stderr)


if __name__ == "__main__":
    unittest.main()
