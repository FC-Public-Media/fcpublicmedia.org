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

    def lines(self, who, *args, door=None, env=None):
        home = self.tmp / who
        env = dict(os.environ, FCPM_LINES_ME=who, FCPM_LINES_KEY=str(home / "key"), FCPM_LINES_HOME=str(home / "lines"),
                   FCPM_ORIGIN_URL=str(self.tmp / "origin"), FCPM_DOOR_HOLDER=door or who,
                   FCPM_PILE_ENGINE=str(ROOT / ".pile-engine"), **(env or {}))
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

        read = self.lines("production", "run")
        self.assertEqual(read.returncode, 0, read.stderr)
        self.assertIn("read now", read.stdout)
        self.assertNotIn("read now", self.lines("production", "run").stdout)       # a second pass: nothing new
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

    def told_once(self):
        for who in ("digitization", "production"):
            self.lines(who, "reader")
        self.lines("digitization", "tell", "production", "keychain", self.note("a", "first"))
        self.lines("production", "hear", "digitization", "keychain")
        told = self.lines("digitization", "tell", "production", "keychain", self.note("c", "your identity"))
        self.assertEqual(told.returncode, 0, told.stderr)

    def test_a_neighbor_serves_the_lines_with_the_origin_away(self):
        self.told_once()
        served = self.tmp / "served"
        done = self.lines("digitization", "serve", env={"FCPM_LINES_SERVE": str(served), "FCPM_LINES_URL": str(served)})
        self.assertEqual(done.returncode, 0, done.stderr)
        self.lines("production")                                         # production learns where digitization serves
        (self.tmp / "origin").rename(self.tmp / "away")
        read = self.lines("production", "read", "digitization")
        self.assertEqual(read.returncode, 0, read.stderr)
        self.assertIn("the pin waits for the origin", read.stdout)
        got = [p.read_text() for p in (self.tmp / "production/lines/workshed/digitization").iterdir()]
        self.assertEqual(got, ["your identity"])

    def test_a_forged_pile_is_refused_wherever_it_came_from(self):
        self.told_once()
        evil = self.tmp / "evil"
        subprocess.run(["git", "clone", "-q", "--mirror", str(self.tmp / "origin/FC-Public-Media/fcpublicmedia.org"), str(evil)], check=True)
        pile = "refs/heads/retain/pile/digitization.production"
        tip = subprocess.run(["git", "-C", str(evil), "rev-parse", pile], capture_output=True, text=True).stdout.strip()
        blob = subprocess.run(["git", "-C", str(evil), "hash-object", "-w", "--stdin"], input="gossip\n", capture_output=True, text=True).stdout.strip()
        env = dict(os.environ, GIT_INDEX_FILE=str(self.tmp / "evil.index"), GIT_DIR=str(evil))
        subprocess.run(["git", "read-tree", tip], env=env, check=True)
        subprocess.run(["git", "update-index", "--cacheinfo", f"100644,{blob},shape/hears"], env=env, check=True)
        tree = subprocess.run(["git", "write-tree"], env=env, capture_output=True, text=True).stdout.strip()
        forged = subprocess.run(["git", "-c", "user.name=production", "-c", "user.email=production@lines.fcpublicmedia.local",
                                 "commit-tree", tree, "-p", tip, "-m", "shape: hears gossip"], env=env, capture_output=True, text=True).stdout.strip()
        check = subprocess.run([sys.executable, str(ROOT / "machines/origin/door-hooks/lines-gate"), "--check", "0" * 40, forged, pile],
                               capture_output=True, text=True, env=dict(os.environ, GIT_DIR=str(evil), FCPM_PILE_ENGINE=str(ROOT / ".pile-engine")))
        self.assertEqual(check.returncode, 1)
        self.assertIn("not signed by a key this pile names", check.stdout)


if __name__ == "__main__":
    unittest.main()
