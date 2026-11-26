#!/usr/bin/env python3
"""The keychain's door (machines/keychain/door), end to end against a scratch keychain.

Each call is what sshd does with a holder's forced command: SSH_ORIGINAL_COMMAND set, `door serve OFFICE
HOLDER` run. Needs age and age-keygen (the keychain's box has them); without them it skips.
"""
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
DOOR = ROOT / "machines/keychain/door"
PHRASE = "correct horse battery"


@unittest.skipUnless(shutil.which("age") and shutil.which("age-keygen"), "no age here")
class Door(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        repo = self.tmp / "repo"
        (repo / "machines/production").mkdir(parents=True)
        (repo / "machines/production/keys.yml").write_text("dir: x\n\ngroups:\n  cloudflare:\n    what: y\n")
        (repo / "machines/production/keys.projects.yml").write_text("dir: x\n\ngroups:\n  layers:\n    what: y\n")
        for a in (["init", "-q", "-b", "main"], ["add", "."], ["-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "x"]):
            subprocess.run(["git", "-C", str(repo), *a], check=True)
        self.env = dict(os.environ, FCPM_KEYCHAIN=str(self.tmp / "store"), FCPM_KEYCHAIN_OPEN=str(self.tmp / "open"),
                        FCPM_LEDGERS=str(repo), FCPM_SCRATCH=str(self.tmp))

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def door(self, office, holder, command, stdin=""):
        env = dict(self.env, SSH_ORIGINAL_COMMAND=command)
        return subprocess.run([sys.executable, str(DOOR), "serve", office, holder], input=stdin,
                              capture_output=True, text=True, env=env)

    def made(self):
        done = self.door("keeper", "digitization", "init", PHRASE + "\n")
        self.assertEqual(done.returncode, 0, done.stderr)

    def test_put_while_locked_get_once_open(self):
        self.made()
        self.door("keeper", "digitization", "lock")
        self.assertIn("locked", self.door("keeper", "digitization", "status").stdout)
        self.assertEqual(self.door("machine", "production", "put cloudflare TOKEN", "abc123").returncode, 0)
        self.assertIn("locked", self.door("machine", "production", "get cloudflare TOKEN").stderr)
        self.assertEqual(self.door("keeper", "digitization", "unlock", "wrong one!\n").returncode, 1)
        self.assertEqual(self.door("keeper", "digitization", "unlock", PHRASE + "\n").returncode, 0)
        self.assertEqual(self.door("machine", "production", "get cloudflare TOKEN").stdout, "abc123")

    def test_protected_goes_to_its_ledger_and_keepers_only(self):
        self.made()
        self.door("keeper", "digitization", "put cloudflare TOKEN", "abc123")
        self.assertEqual(self.door("machine", "production", "get cloudflare TOKEN").stdout, "abc123")
        self.assertEqual(self.door("keeper", "Autumn", "get cloudflare TOKEN").stdout, "abc123")
        refused = self.door("machine", "editing-bay-2", "get cloudflare TOKEN")
        self.assertEqual(refused.returncode, 1)
        self.assertEqual(refused.stdout, "")

    def test_secret_goes_to_its_holder_alone(self):
        self.made()
        self.door("keeper", "digitization", "put youtube KEY secret production", "s3cret")
        self.assertEqual(self.door("keeper", "digitization", "get youtube KEY").stdout, "")
        self.assertEqual(self.door("machine", "production", "get youtube KEY").stdout, "s3cret")

    def test_the_same_value_is_no_new_version(self):
        self.made()
        self.door("keeper", "digitization", "put cloudflare TOKEN", "abc")
        self.assertIn("held already", self.door("keeper", "digitization", "put cloudflare TOKEN", "abc").stdout)
        self.door("keeper", "digitization", "put cloudflare TOKEN", "abd")
        self.assertIn("v2", self.door("keeper", "digitization", "list").stdout)

    def test_mint_lodges_a_secret_identity(self):
        self.made()
        done = self.door("keeper", "digitization", "mint ssh editing-bay-2")
        self.assertTrue(done.stdout.startswith("ssh-ed25519 "), done.stderr)
        self.assertNotIn("PRIVATE", done.stdout)
        self.assertEqual(self.door("keeper", "digitization", "get identity-editing-bay-2 ssh").stdout, "")
        self.assertIn("PRIVATE KEY", self.door("machine", "editing-bay-2", "get identity-editing-bay-2 ssh").stdout)
        self.assertEqual(self.door("machine", "production", "mint ssh x").returncode, 1)

    def test_a_backup_is_the_store_and_a_keepers(self):
        self.made()
        self.door("keeper", "digitization", "put cloudflare TOKEN", "abc123")
        env = dict(self.env, SSH_ORIGINAL_COMMAND="backup")
        tar = subprocess.run([sys.executable, str(DOOR), "serve", "keeper", "digitization"], capture_output=True, env=env)
        names = subprocess.run(["tar", "-tf", "-"], input=tar.stdout, capture_output=True).stdout.decode().split()
        self.assertIn("identity.age", names)
        self.assertIn("held/cloudflare/TOKEN/meta.json", names)
        self.assertNotIn(b"abc123", tar.stdout)
        self.assertEqual(self.door("machine", "production", "backup").returncode, 1)

    def test_a_secondary_hands_out_by_its_own_ledgers(self):
        self.env["FCPM_KEYCHAIN_NAME"] = "projects"
        self.made()
        self.door("keeper", "digitization", "put layers TOKEN", "abc123")
        self.door("keeper", "digitization", "put cloudflare TOKEN", "abc123")
        self.assertEqual(self.door("machine", "production", "get layers TOKEN").stdout, "abc123")
        self.assertEqual(self.door("machine", "production", "get cloudflare TOKEN").returncode, 1)
        holders = self.tmp / "HOLDERS.projects"
        holders.write_text("keeper digitization ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIDL8JGISv1fAIISOJDQTaV3z/p4ncm1kNuZ/zYecb/fO x\n")
        env = dict(self.env, FCPM_HOLDERS=str(holders), FCPM_AUTHORIZED_KEYS=str(self.tmp / "ak"))
        subprocess.run([sys.executable, str(DOOR), "keys"], env=env, check=True, capture_output=True)
        self.assertIn('command="FCPM_KEYCHAIN_NAME=projects python3', (self.tmp / "ak").read_text())

    def test_nothing_held_is_plain(self):
        self.made()
        self.door("keeper", "digitization", "put cloudflare TOKEN", "plainly-visible-token")
        for path in (self.tmp / "store").rglob("*"):
            if path.is_file():
                self.assertNotIn(b"plainly-visible-token", path.read_bytes(), path)


if __name__ == "__main__":
    unittest.main()
