#!/usr/bin/env python3
"""The keychain (machines/keys): each machine holds the ledger of the jobs it wears, and `run` hands a group
to one command with the job's own gear (a bay's Node) first on its PATH. No value is ever printed.

    python3 bin/test_keys.py
"""
import http.server
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import textwrap
import threading
import unittest

REPO = pathlib.Path(__file__).resolve().parents[1]
KEYS = REPO / "machines" / "keys"


def keys(*args, **env):
    return subprocess.run([sys.executable, "-I", str(KEYS), *args], capture_output=True, text=True,
                          env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1", **env))


class Keys(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        self.ledger = self.tmp / "keys.yml"
        self.ledger.write_text(textwrap.dedent(f"""\
            dir: {self.tmp}/held
            groups:
              cloudflare:
                what: a test group
                form: env
                keys:
                  CLOUDFLARE_API_TOKEN: {{may: deploy, from: a test}}
                  CLOUDFLARE_ACCOUNT_ID: {{shape: hex32, may: names it, from: a test}}
            """))

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_each_job_has_its_own_ledger(self):
        out = keys(FCPM_WEARS="production", HOME=str(self.tmp)).stdout
        self.assertIn("WANTED  key cloudflare CLOUDFLARE_API_TOKEN", out)
        self.assertNotIn("stripe", out)                               # digitization's groups are not bay 1's
        self.assertIn("stripe-live", keys(FCPM_WEARS="digitization").stdout)
        self.assertIn("holds no keychain", keys(FCPM_WEARS="kiosk").stdout)

    def test_wanted_until_held_and_never_a_value(self):
        out = keys("check", FCPM_KEYS_LEDGER=str(self.ledger))
        self.assertEqual(out.returncode, 1)
        (self.tmp / "held").mkdir(mode=0o700)
        (self.tmp / "held" / "cloudflare.env").write_text("CLOUDFLARE_API_TOKEN=s3cret\nCLOUDFLARE_ACCOUNT_ID=" + "a" * 32 + "\n")
        os.chmod(self.tmp / "held" / "cloudflare.env", 0o600)
        out = keys("check", FCPM_KEYS_LEDGER=str(self.ledger))
        self.assertEqual(out.returncode, 0, out.stdout)
        self.assertNotIn("s3cret", out.stdout)

    def test_run_hands_the_group_to_one_command(self):
        (self.tmp / "held").mkdir(mode=0o700)
        (self.tmp / "held" / "cloudflare.env").write_text("CLOUDFLARE_API_TOKEN=s3cret\nCLOUDFLARE_ACCOUNT_ID=" + "a" * 32 + "\n")
        out = keys("run", "cloudflare", "--", "sh", "-c", 'echo "$CLOUDFLARE_API_TOKEN"', FCPM_KEYS_LEDGER=str(self.ledger))
        self.assertEqual(out.stdout.strip(), "s3cret")
        self.assertIn("lacks CLOUDFLARE_API_TOKEN", keys("run", "cloudflare", "--", "true",
                                                         FCPM_WEARS="production", HOME=str(self.tmp)).stderr)
        self.assertIn("no nonesuch-command", keys("run", "cloudflare", "--", "nonesuch-command",
                                                  FCPM_KEYS_LEDGER=str(self.ledger)).stderr)

    def test_birth_makes_one_key_and_shows_only_its_public_half(self):
        home = dict(HOME=str(self.tmp), USERPROFILE=str(self.tmp), FCPM_BIRTH_FILE="1",
                    FCPM_BIRTH_HELM="http://127.0.0.1:9")                # nothing answers: never this machine's helm
        self.assertIn("wears no job", keys("birth", FCPM_WEARS="", **home).stderr)
        first = keys("birth", FCPM_WEARS="editing-bay-2", **home)
        self.assertEqual(first.returncode, 0, first.stderr)
        pub = (self.tmp / ".ssh" / "fcpm-editing-bay-2.pub").read_text().strip()
        self.assertTrue(pub.startswith("ssh-ed25519 ") and " fcpm editing-bay-2 " in pub, pub)
        self.assertIn(pub, first.stdout)
        self.assertNotIn("PRIVATE KEY", first.stdout)
        again = keys("birth", FCPM_WEARS="editing-bay-2", **home)
        self.assertNotIn("keys: made", again.stdout)                      # once: a second run shows the same key
        self.assertIn(pub, again.stdout)
        self.assertIn("Not lodged yet", again.stdout)
        (self.tmp / ".ssh" / "fcpm-editing-bay-2").unlink()
        self.assertIn("private half is not", keys("birth", FCPM_WEARS="editing-bay-2", **home).stderr)

    def test_birth_lodges_its_petition_at_its_own_helm_once(self):
        kept = []

        class Helm(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                kept.append((self.path, json.loads(self.rfile.read(int(self.headers["Content-Length"])))))
                body = json.dumps({"kept": "20261110-000000.000001"}).encode()
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):
                pass

        helm = http.server.HTTPServer(("127.0.0.1", 0), Helm)
        threading.Thread(target=helm.serve_forever, daemon=True).start()
        self.addCleanup(helm.shutdown)
        home = dict(HOME=str(self.tmp), USERPROFILE=str(self.tmp), FCPM_BIRTH_FILE="1", FCPM_WEARS="editing-bay-2",
                    FCPM_BIRTH_HELM="http://127.0.0.1:%d" % helm.server_port)
        first = keys("birth", **home)
        self.assertIn("Lodged with the keystore", first.stdout, first.stderr)
        [(path, petition)] = kept
        pub = (self.tmp / ".ssh" / "fcpm-editing-bay-2.pub").read_text().strip()
        self.assertEqual(path, "/drop")
        self.assertEqual((petition["schema"], petition["wizard"], petition["job"], petition["key"]),
                         ("fcpm.reply/v0", "wizard:keys+birth", "editing-bay-2", pub))
        self.assertTrue(petition["nonce"] and petition["issued"])
        self.assertIn("already", keys("birth", **home).stdout)
        self.assertEqual(len(kept), 1)                                # once: a second run sets nothing down


if __name__ == "__main__":
    unittest.main()
