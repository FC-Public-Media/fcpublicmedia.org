#!/usr/bin/env python3
"""The LAN's lines (machines/lines, machines/origin/door-hooks), end to end: two machines and a scratch
origin whose pushes run the door's pre-receive as the pusher's holder would. Needs age, jq, openssl and
bash (data-pile); without age it skips.
"""
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
LINES = ROOT / "machines/lines"


@unittest.skipUnless(shutil.which("age") and shutil.which("jq"), "no age or jq here")
class Lines(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        origin = self.tmp / "origin/FC-Public-Media/fcpublicmedia.org"
        subprocess.run(["git", "init", "-q", "--bare", str(origin)], check=True)
        for k, v in (("receive.denyNonFastForwards", "true"), ("receive.denyDeletes", "true"),
                     ("core.hooksPath", str(ROOT / "machines/origin/door-hooks"))):
            subprocess.run(["git", "-C", str(origin), "config", k, v], check=True)
        for who in ("digitization", "production"):
            home = self.tmp / who
            home.mkdir()
            subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", who, "-f", str(home / "key")], check=True)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def lines(self, who, *args, door=None):
        home = self.tmp / who
        env = dict(os.environ, FCPM_LINES_ME=who, FCPM_LINES_KEY=str(home / "key"), FCPM_LINES_HOME=str(home / "lines"),
                   FCPM_ORIGIN_URL=str(self.tmp / "origin"), FCPM_DOOR_HOLDER=door or who,
                   FCPM_PILE_ENGINE=str(ROOT / ".pile-engine"))
        return subprocess.run([sys.executable, str(LINES), *args], capture_output=True, text=True, env=env, cwd=self.tmp)

    def note(self, name, text):
        path = self.tmp / name
        path.write_text(text)
        return str(path)

    def test_a_line_hears_nothing_then_one_shape_then_answers(self):
        for who in ("digitization", "production"):
            made = self.lines(who, "reader")
            self.assertEqual(made.returncode, 0, made.stderr)
        first = self.lines("digitization", "tell", "production", "keychain", self.note("a", "first"))
        self.assertEqual(first.returncode, 1)
        self.assertIn("hears nothing", first.stderr)

        self.assertEqual(self.lines("production", "hear", "digitization", "keychain").returncode, 0)
        other = self.lines("digitization", "tell", "production", "gossip", self.note("b", "noise"))
        self.assertIn("hears keychain, not gossip", other.stderr)
        told = self.lines("digitization", "tell", "production", "keychain", self.note("c", "your identity"))
        self.assertEqual(told.returncode, 0, told.stderr)

        read = self.lines("production", "read", "digitization")
        self.assertEqual(read.returncode, 0, read.stderr)
        got = list((self.tmp / "production/lines/workshed/digitization").iterdir())
        self.assertEqual([p.read_text() for p in got], ["your identity"])

        unheard = self.lines("production", "tell", "digitization", "keychain", self.note("d", "got it"))
        self.assertIn("hears nothing", unheard.stderr)                       # its pile is born; nothing heard yet
        self.assertEqual(self.lines("digitization", "hear", "production", "keychain").returncode, 0)
        back = self.lines("production", "tell", "digitization", "keychain", self.note("d", "got it"))
        self.assertEqual(back.returncode, 0, back.stderr)
        self.assertEqual(self.lines("digitization", "read", "production").returncode, 0)
        status = self.lines("digitization").stdout
        self.assertIn("production", status)
        self.assertIn("1 told, 1 read there", status)

    def test_only_the_signer_pushes_and_only_its_own_folder(self):
        stolen = self.lines("digitization", "reader", door="production")
        self.assertEqual(stolen.returncode, 1)
        self.assertIn("production writes only lines/production/", stolen.stderr)
        for who in ("digitization", "production"):
            self.lines(who, "reader")
        self.lines("production", "hear", "digitization", "keychain")                 # no pile yet: refused
        pushed_as = self.lines("digitization", "tell", "production", "keychain", self.note("e", "x"), door="production")
        self.assertEqual(pushed_as.returncode, 1)
        self.assertIn("bears its own pile", pushed_as.stderr)


if __name__ == "__main__":
    unittest.main()
