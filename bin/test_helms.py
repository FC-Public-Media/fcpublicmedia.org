#!/usr/bin/env python3
"""Helm to helm (machines/helms.yml, replies.py route): a reply whose wizard another job's helm holds is
passed there as it came, or waits for it; the holding helm applies wizard:model+up by model.ps1 pick, and
wizard:site+deploy by bin/deploy-site.

    python3 bin/test_helms.py
"""
import datetime
import json
import os
import pathlib
import shutil
import sys
import tempfile
import time
import unittest
import urllib.error

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "machines" / "kiosk"))
import replies  # noqa: E402


def deploy(rev):
    return json.dumps({"schema": "fcpm.reply/v0", "wizard": "wizard:site+deploy", "at": "test",
                       "issued": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
                       "nonce": os.urandom(8).hex(), "rev": rev})


def birth(key, **fields):
    r = {"schema": "fcpm.reply/v0", "wizard": "wizard:keys+birth", "at": "test", "job": "editing-bay-2",
         "host": "FCPMEDIT2", "key": key, "issued": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
         "nonce": os.urandom(8).hex(), "sig": None}
    r.update(fields)
    return json.dumps(r)


def up(*names, **fields):
    r = {"schema": "fcpm.reply/v0", "wizard": "wizard:model+up", "at": "test",
         "issued": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
         "nonce": os.urandom(8).hex(), "up": list(names)}
    r.update(fields)
    return json.dumps(r)


class Helms(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        self.saved = replies.STATE, replies.route, dict(os.environ)
        replies.STATE = self.tmp / "state"
        replies._waiting.clear()
        os.environ["FCPM_WEARS"] = "digitization"

    def tearDown(self):
        replies.STATE, replies.route = self.saved[:2]
        if replies._deploy is not None:
            replies._deploy.wait()
            replies._deploy = None
        os.environ.clear()
        os.environ.update(self.saved[2])
        shutil.rmtree(self.tmp)

    def test_the_helms_map_names_the_one_that_holds_the_models(self):
        self.assertEqual(replies.holder("wizard:model+up"), ("production", "http://10.209.1.20:8080"))
        self.assertIsNone(replies.holder("wizard:model+ask"))           # any helm applies it

    def test_a_reply_another_helm_holds_waits_for_it_then_goes_as_it_came(self):
        sent = []
        def away(path, at):
            raise urllib.error.URLError("refused")
        replies.route = away
        name = replies.drop(up("qwen3.5-9b"), "test")
        self.assertEqual([v for _, v, _ in replies.take()], ["waiting"])
        self.assertEqual(replies.take(), [])                             # said once, still waiting
        self.assertEqual(replies.where(name)["state"], "inbox")
        def there(path, at):
            sent.append((path.read_bytes(), at))
            return "far-name"
        replies.route = there
        [(_, verdict, why)] = replies.take()
        self.assertEqual((verdict, why), ("routed", "to production's helm, kept there as far-name"))
        self.assertEqual(sent[0][1], "http://10.209.1.20:8080")
        self.assertEqual(json.loads(sent[0][0])["up"], ["qwen3.5-9b"])  # byte for byte
        self.assertEqual(replies.where(name)["state"], "routed")
        self.assertFalse((replies.STATE / "nonces.json").exists())       # the holder spends the nonce, not us

    def test_two_bays_hold_the_models_and_the_reply_names_which(self):
        self.assertEqual(replies.holder("wizard:model+up", "editing-bay-2"), ("editing-bay-2", ""))
        self.assertEqual(replies.holder("wizard:model+up", "nonesuch"), ("production", "http://10.209.1.20:8080"))
        sent = []
        replies.route = lambda path, at: sent.append(at) or "far-name"
        os.environ["FCPM_WEARS"] = "production"              # bay 1 passes bay 2's on
        replies.drop(up("qwen3.5-2b", job="editing-bay-2"))
        self.assertEqual([v for _, v, _ in replies.take()], ["routed"])
        os.environ["FCPM_WEARS"] = "digitization"
        replies.drop(up("qwen3.5-9b"))                        # no job: bay 1's, as before
        self.assertEqual([v for _, v, _ in replies.take()], ["routed"])
        self.assertEqual(sent, ["", "http://10.209.1.20:8080"])

    def test_a_helm_without_an_address_is_waited_for(self):
        saved = replies.route
        replies.route = self.saved[1]                         # the real one: it refuses an empty address
        try:
            name = replies.drop(up("qwen3.5-2b", job="editing-bay-2"))
            [(_, verdict, why)] = replies.take()
            self.assertEqual(verdict, "waiting")
            self.assertIn("no address", why)
            self.assertEqual(replies.where(name)["state"], "inbox")
        finally:
            replies.route = saved

    def test_a_reply_any_helm_applies_is_never_routed(self):
        def never(path, at):
            raise AssertionError("routed")
        replies.route = never
        replies.drop(json.dumps({"schema": "fcpm.reply/v0", "wizard": "wizard:nonesuch", "issued": "x", "nonce": "n"}))
        [(_, verdict, _)] = replies.take()
        self.assertEqual(verdict, "held")

    def test_the_holding_helm_runs_the_pick_with_the_line_up(self):
        os.environ["FCPM_WEARS"] = "production"
        log = self.tmp / "picked"
        os.environ["FCPM_MODEL_PICK"] = json.dumps([sys.executable, "-c",
                                                    "import sys; open(%r, 'w').write(sys.argv[1])" % str(log)])
        replies.drop(up("qwen3.5-9b", "gpt-oss-20b"), "a peer")
        [(_, verdict, why)] = replies.take()
        self.assertEqual(verdict, "applied", why)
        for _ in range(50):
            if log.exists():
                break
            time.sleep(0.1)
        self.assertEqual(log.read_text(), "qwen3.5-9b,gpt-oss-20b")
        self.assertIn("by unsigned", (replies.STATE / replies.PICK_LOG).read_text())

    def test_the_default_can_be_down_and_none_up_is_said_as_none(self):
        os.environ["FCPM_WEARS"] = "production"
        log = self.tmp / "picked"
        os.environ["FCPM_MODEL_PICK"] = json.dumps([sys.executable, "-c",
                                                    "import sys; open(%r, 'w').write(sys.argv[1])" % str(log)])
        replies.drop(up())
        [(_, verdict, why)] = replies.take()
        self.assertEqual((verdict, why), ("applied", "up: none; model.ps1 pick started (model-pick.log)"))
        for _ in range(50):
            if log.exists():
                break
            time.sleep(0.1)
        self.assertEqual(log.read_text(), "none")

    def test_the_holding_helm_holds_what_it_cannot_pick(self):
        os.environ["FCPM_WEARS"] = "production"
        os.environ["FCPM_MODEL_PICK"] = json.dumps(["true"])
        replies.drop(up("qwen3.5-9b", "made-up-model"))
        replies.drop(up(up="all"))
        verdicts = replies.take()
        self.assertEqual([(v, w) for _, v, w in verdicts], [("held", "not in the spread: made-up-model"),
                                                             ("held", "up: a list of model names")])
        os.environ.pop("FCPM_MODEL_PICK")
        if os.name != "nt":
            replies.drop(up("qwen3.5-9b"))
            [(_, verdict, why)] = replies.take()
            self.assertEqual((verdict, why), ("held", "this helm cannot run model.ps1 (not Windows)"))

    def test_the_deploy_is_held_by_digitizations_helm_and_passed_there_from_a_bay(self):
        self.assertEqual(replies.holder("wizard:site+deploy"), ("digitization", "http://digitization.local"))
        os.environ["FCPM_WEARS"] = "production"
        sent = []
        replies.route = lambda path, at: sent.append(at) or "far-name"
        replies.drop(deploy(replies.head()[0]))
        [(_, verdict, _)] = replies.take()
        self.assertEqual((verdict, sent), ("routed", ["http://digitization.local"]))

    def test_the_holding_helm_deploys_only_the_commit_it_has_and_one_at_a_time(self):
        mark = self.tmp / "deployed"
        os.environ["FCPM_DEPLOY"] = json.dumps([sys.executable, "-c",
                                                "import sys, time; open(%r, 'w').write('x'); time.sleep(1)" % str(mark)])
        full = replies.head()[0]
        replies.drop(deploy("abc1234"))
        replies.drop(deploy("not a commit"))
        replies.drop(deploy(full[:7]))
        replies.drop(deploy(full))
        verdicts = [(v, w) for _, v, w in replies.take()]
        self.assertEqual(verdicts[0], ("held", "rev abc1234: this helm's checkout is at %s" % full[:7]))
        self.assertEqual(verdicts[1], ("held", "rev: the commit to deploy"))
        self.assertEqual(verdicts[2], ("applied", "deploy of %s started (deploy.log)" % full[:7]))
        self.assertEqual(verdicts[3], ("held", "a deploy is already running (deploy.log)"))
        replies._deploy.wait()
        self.assertTrue(mark.exists())
        self.assertIn("by unsigned", (replies.STATE / replies.DEPLOY_LOG).read_text())

    def test_a_birth_goes_to_the_keystores_helm_and_is_lodged_never_granted(self):
        self.assertEqual(replies.holder("wizard:keys+birth"), ("digitization", "http://digitization.local"))
        key = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFH+qRqGtHSJs4bTDOHkA6z2nu2XC9PFFSYrOhwqbvME fcpm editing-bay-2 X"
        os.environ["FCPM_WEARS"] = "editing-bay-2"
        sent = []
        replies.route = lambda path, at: sent.append(at) or "far-name"
        replies.drop(birth(key))
        [(_, verdict, _)] = replies.take()
        self.assertEqual((verdict, sent), ("routed", ["http://digitization.local"]))
        os.environ["FCPM_WEARS"] = "digitization"
        verdicts = []
        for r in (birth(key, nonce="n1"), birth("ssh-rsa AAAAB3Nza not ours"), birth(key, job="nonesuch")):
            replies.drop(r)                   # one at a time: Windows' clock can give two drops the same microsecond
            verdicts += [(v, w) for _, v, w in replies.take()]
        self.assertEqual(verdicts[0][0], "applied")
        self.assertIn("lodged for the keystore: editing-bay-2's key", verdicts[0][1])
        self.assertEqual(verdicts[1], ("held", "key: one public key line (ssh-ed25519)"))
        self.assertEqual(verdicts[2], ("held", "job: 'nonesuch' is no profile in machines/"))
        petition = json.loads((replies.STATE / "petitions" / "n1.json").read_text())
        self.assertEqual((petition["job"], petition["key"], petition["trust"]), ("editing-bay-2", key, "unsigned"))


if __name__ == "__main__":
    unittest.main()
