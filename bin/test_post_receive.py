#!/usr/bin/env python3
"""Post delivery (troves/post deliver → machines/digitization/post-receive), end to end on scratch roots.

post.py reaches the receiver through a stand-in for ssh that does what sshd does with a forced
command: it puts the remote command in SSH_ORIGINAL_COMMAND and runs post-receive. The bay's side
needs the post trove checked out (troves/post, or POST_PY); without it those tests are skipped.
"""
import io
import json
import os
import pathlib
import subprocess
import sys
import tarfile
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
RECEIVE = ROOT / "machines/digitization/post-receive"
POST = pathlib.Path(os.environ.get("POST_PY") or ROOT / "troves/post/post.py")


class Receive(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        self.landing = self.tmp / "landing"
        self.bay = self.tmp / "bay"
        (self.bay / "rec").mkdir(parents=True)
        (self.bay / "rec" / "a take.wav").write_bytes(b"RIFF" + os.urandom(4096))
        ssh = self.tmp / "ssh"
        ssh.write_text(
            "#!/bin/sh\n"
            "# skip ssh's options and the destination; what is left is the remote command\n"
            'while [ $# -gt 0 ]; do case "$1" in -o|-i|-p) shift 2;; -*) shift;; *) break;; esac; done\n'
            'shift\n'
            f'SSH_ORIGINAL_COMMAND="$*" FCPM_POST_ROOT="{self.landing}" exec {sys.executable} "{RECEIVE}"\n')
        ssh.chmod(0o755)
        self.env = dict(os.environ, PATH=f"{self.tmp}:{os.environ['PATH']}", POST_CONFIG=str(self.bay / "post.yml"))
        (self.bay / "key").write_text("stand-in: the stand-in ssh never reads it\n")
        (self.bay / "post.yml").write_text(json.dumps({
            "root": str(self.bay / "POST"), "doors": str(self.bay / "DOORS"), "crews": [],
            "steps": {"enhance": {"door": True},
                      "copy": {"run": [sys.executable, "-c",
                                       "import shutil,sys,glob;[shutil.copy(f,sys.argv[2]) for f in glob.glob(sys.argv[1]+'/*')]",
                                       "{in}", "{out}"]}},
            "deliver": {"to": "user@digitization.local", "key": str(self.bay / "key")}}))

    def post(self, *args, ok=True):
        r = subprocess.run([sys.executable, str(POST), *args], env=self.env, capture_output=True, text=True)
        if ok:
            self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout

    def receive(self, take, item, tar_bytes):
        r = subprocess.run([sys.executable, str(RECEIVE), "receive", take, item], input=tar_bytes, capture_output=True,
                           env=dict(os.environ, FCPM_POST_ROOT=str(self.landing)))
        return r.returncode, (r.stdout + r.stderr).decode()

    def tar_of(self, base, item):
        b = io.BytesIO()
        with tarfile.open(fileobj=b, mode="w") as t:
            t.add(base / item, arcname=item)
        return b.getvalue()

    def admit(self, steps):
        (self.bay / "release.yml").write_text(json.dumps({"out": "t", "pipeline": {"steps": steps},
                                                          "clips": [{"path": str(self.bay / "rec" / "a take.wav")}]}))
        out = self.post("admit", str(self.bay / "release.yml"))
        return pathlib.Path(out.split(": ", 1)[1].strip())

    @unittest.skipUnless(POST.is_file(), "the post trove is not checked out")
    def test_a_take_arrives_step_by_step_and_is_fulfilled(self):
        take = self.admit(["enhance", "copy", {"copy": {"from": "enhance"}}])
        self.post("run")                                     # the door opens; route and source go
        kept = self.landing / take.name
        self.assertTrue((kept / "route.json").is_file())
        self.assertTrue((kept / "0-source" / "SHA256SUMS").is_file())
        self.assertFalse((kept / "1-enhance").exists())
        for f in (self.bay / "DOORS" / "enhance" / "out").iterdir():
            (self.bay / "DOORS" / "enhance" / "back" / f.name).write_bytes(f.read_bytes() + b"enhanced")
        said = self.post("run")
        self.assertIn("3-copy delivered: kept", said)
        self.assertEqual(sorted(p.name for p in kept.iterdir()), ["0-source", "1-enhance", "2-copy", "3-copy", "route.json"])
        self.assertIn("fulfilled", self.post("status"))
        self.assertEqual(self.post("deliver").strip(), "nothing to deliver")
        self.env["POST_CONFIG"] = str(self.tmp / "landing.yml")
        (self.tmp / "landing.yml").write_text(json.dumps({"root": str(self.landing), "crews": []}))
        self.assertIn("fulfilled", self.post("status"))

    @unittest.skipUnless(POST.is_file(), "the post trove is not checked out")
    def test_no_key_yet_sends_nothing(self):
        (self.bay / "key").unlink()
        self.admit(["copy"])
        self.assertIn("no key at", self.post("run"))
        self.assertFalse(self.landing.exists())

    @unittest.skipUnless(POST.is_file(), "the post trove is not checked out")
    def test_refusals(self):
        take = self.admit(["copy"])
        self.post("run")
        name = take.name
        self.assertEqual(self.receive(name, "1-copy", self.tar_of(take, "1-copy"))[0], 0)       # again: already
        bad = self.tmp / "bad"
        (bad / "1-copy").mkdir(parents=True)
        for f in (take / "1-copy").iterdir():
            (bad / "1-copy" / f.name).write_bytes(f.read_bytes())
        (bad / "1-copy" / "a take.wav").write_bytes(b"not what was sealed")
        code, said = self.receive(name, "1-copy", self.tar_of(bad, "1-copy"))
        self.assertEqual(code, 1)
        self.assertIn("not the file that was sealed", said)
        b = io.BytesIO()
        with tarfile.open(fileobj=b, mode="w") as t:
            i = tarfile.TarInfo("1-copy/../../escape")
            i.size = 2
            t.addfile(i, io.BytesIO(b"hi"))
        self.assertIn("outside", self.receive(name, "1-copy", b.getvalue())[1])
        (bad / "1-copy").rename(bad / "2-upload")
        self.assertIn("not a step", self.receive(name, "2-upload", self.tar_of(bad, "2-upload"))[1])
        self.assertIn("route.json first", self.receive("other.0123abcd", "1-copy", self.tar_of(take, "1-copy"))[1])
        route = json.loads((take / "route.json").read_text())
        route["steps"].append({"step": "extra"})
        (bad / "route.json").write_text(json.dumps(route))
        self.assertIn("does not hash", self.receive(name, "route.json", self.tar_of(bad, "route.json"))[1])
        self.assertFalse((self.tmp / "escape").exists() or (self.landing / "escape").exists())
        self.assertEqual([p.name for p in self.landing.iterdir() if ".incoming" in p.name], [])

    def test_a_key_may_only_receive(self):
        r = subprocess.run([sys.executable, str(RECEIVE)], env=dict(os.environ, SSH_ORIGINAL_COMMAND="sh -c id",
                                                                     FCPM_POST_ROOT=str(self.landing)), capture_output=True)
        self.assertEqual(r.returncode, 2)

    def test_senders_keep_authorized_keys_to_the_list(self):
        home = self.tmp / "home"
        (home / ".ssh").mkdir(parents=True)
        ak = home / ".ssh" / "authorized_keys"
        other = "restrict,command=\"something else\" ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOtherkeyotherkeyotherkeyotherkeyotherkey qr eyes"
        ak.write_text(other + "\nssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIGonekeygonekeygonekeygonekeygonekeygonek post-deliver:gone\n")
        run = lambda: subprocess.run([sys.executable, str(RECEIVE), "senders"], env=dict(os.environ, HOME=str(home)),
                                     capture_output=True, text=True)
        self.assertEqual(run().returncode, 0)
        lines = ak.read_text().splitlines()
        self.assertEqual(lines[0], other)                                   # every other line untouched
        self.assertFalse(any(l.endswith("post-deliver:gone") for l in lines))   # off the list: shut out
        mine = [l for l in lines if l.endswith("post-deliver:production")]
        self.assertEqual(len(mine), 1)
        self.assertTrue(mine[0].startswith('restrict,from="10.209.1.0/24,'))
        self.assertIn(f'command="FCPM_POST_KEY=production /usr/bin/python3 {RECEIVE.resolve()}"', mine[0])
        self.assertEqual(oct(ak.stat().st_mode & 0o777), "0o600")
        before = ak.read_text()
        self.assertEqual(run().stdout, "")                                  # already right: nothing written
        self.assertEqual(ak.read_text(), before)

    def test_not_mounted_keeps_nothing(self):
        r = subprocess.run([sys.executable, str(RECEIVE), "receive", "t.0123abcd", "route.json"], input=b"",
                           env=dict(os.environ, FCPM_POST_ROOT=str(self.landing), FCPM_POST_MOUNT=str(self.tmp / "nowhere")),
                           capture_output=True)
        self.assertEqual(r.returncode, 1)
        self.assertIn(b"not mounted", r.stderr)


if __name__ == "__main__":
    unittest.main()
