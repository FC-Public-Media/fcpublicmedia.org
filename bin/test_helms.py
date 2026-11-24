#!/usr/bin/env python3
"""Helm to helm (machines/helms.yml, replies.py route): a reply whose wizard another job's helm holds is
passed there as it came, or waits for it; the holding helm applies wizard:model+up by model.ps1 pick, and
wizard:site+deploy by bin/deploy-site, on our origin's main only.

    python3 bin/test_helms.py
"""
import datetime
import json
import os
import pathlib
import re
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
         "host": "BAY2", "key": key, "issued": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
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
        self.saved = replies.STATE, replies.route, dict(os.environ), replies.origin_main
        replies.STATE = self.tmp / "state"
        replies._waiting.clear()
        os.environ["FCPM_WEARS"] = "digitization"

    def tearDown(self):
        replies.STATE, replies.route = self.saved[:2]
        replies.origin_main = self.saved[3]
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
        bay2 = replies.helms()["editing-bay-2"]["at"]
        self.assertEqual(replies.holder("wizard:model+up", "editing-bay-2"), ("editing-bay-2", bay2))
        self.assertEqual(replies.holder("wizard:model+up", "nonesuch"), ("production", "http://10.209.1.20:8080"))
        sent = []
        replies.route = lambda path, at: sent.append(at) or "far-name"
        os.environ["FCPM_WEARS"] = "production"              # bay 1 passes bay 2's on
        replies.drop(up("qwen3.5-2b", job="editing-bay-2"))
        self.assertEqual([v for _, v, _ in replies.take()], ["routed"])
        os.environ["FCPM_WEARS"] = "digitization"
        replies.drop(up("qwen3.5-9b"))                        # no job: bay 1's, as before
        self.assertEqual([v for _, v, _ in replies.take()], ["routed"])
        self.assertEqual(sent, [bay2, "http://10.209.1.20:8080"])

    def test_a_helm_without_an_address_is_waited_for(self):
        saved = replies.route, replies.HELMS
        replies.route = self.saved[1]                         # the real one: it refuses an empty address
        replies.HELMS = self.tmp / "helms.yml"                # bay 2 as it was before it had one
        replies.HELMS.write_text(re.sub(r"(  editing-bay-2:\n(?:    .*\n)*?    at: ).*", r'\1""', saved[1].read_text()))
        try:
            name = replies.drop(up("qwen3.5-2b", job="editing-bay-2"))
            [(_, verdict, why)] = replies.take()
            self.assertEqual(verdict, "waiting")
            self.assertIn("no address", why)
            self.assertEqual(replies.where(name)["state"], "inbox")
        finally:
            replies.route, replies.HELMS = saved

    def test_a_reply_any_helm_applies_is_never_routed(self):
        def never(path, at):
            raise AssertionError("routed")
        replies.route = never
        replies.drop(json.dumps({"schema": "fcpm.reply/v0", "wizard": "wizard:nonesuch", "issued": "x", "nonce": "n"}))
        [(_, verdict, _)] = replies.take()
        self.assertEqual(verdict, "held")

    def test_an_intake_hands_on_what_no_helm_holds_and_what_one_does(self):
        self.assertEqual(replies.intakes()["qr"]["hands_to"], "digitization")
        sent = []
        replies.route = lambda path, at: sent.append((json.loads(path.read_bytes())["wizard"], at)) or "far-name"
        os.environ["FCPM_WEARS"] = "qr,bounce"
        self.assertEqual(replies.handed_to(), ("digitization", "http://digitization.local"))
        replies.drop(json.dumps({"schema": "fcpm.reply/v0", "wizard": "wizard:nonesuch", "issued": "x", "nonce": "n"}))
        replies.drop(up("qwen3.5-9b"))
        self.assertEqual([v for _, v, _ in replies.take()], ["routed", "routed"])
        self.assertEqual(sent, [("wizard:nonesuch", "http://digitization.local"),
                                ("wizard:model+up", "http://10.209.1.20:8080")])
        replies.route = lambda path, at: sent.append((path.read_bytes(), at)) or "far-name"
        replies.drop("not a bottle at all")
        self.assertEqual([v for _, v, _ in replies.take()], ["routed"])         # nor one it cannot read
        self.assertEqual(sent[-1], (b"not a bottle at all", "http://digitization.local"))
        self.assertFalse((replies.STATE / "nonces.json").exists())

    def test_an_intake_that_also_wears_a_helm_reads_for_itself(self):
        os.environ["FCPM_WEARS"] = "qr,digitization"
        self.assertIsNone(replies.handed_to())
        os.environ["FCPM_WEARS"] = "digitization"
        self.assertIsNone(replies.handed_to())

    def test_an_intake_waits_while_its_helm_is_away(self):
        def away(path, at):
            raise urllib.error.URLError("refused")
        replies.route = away
        os.environ["FCPM_WEARS"] = "qr"
        name = replies.drop(json.dumps({"schema": "fcpm.reply/v0", "wizard": "wizard:kiosk+host", "issued": "x",
                                        "nonce": "n"}))
        [(_, verdict, why)] = replies.take()
        self.assertEqual(verdict, "waiting")
        self.assertIn("digitization", why)
        self.assertEqual(replies.where(name)["state"], "inbox")

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

    def test_the_holding_helm_deploys_only_our_origins_main_and_one_at_a_time(self):
        mark = self.tmp / "deployed"
        os.environ["FCPM_DEPLOY"] = json.dumps([sys.executable, "-c",
                                                "import os, time; open(%r, 'w').write(os.environ['FCPM_DEPLOY_REV']); "
                                                "time.sleep(1)" % str(mark)])
        full = replies.head()[0]
        elsewhere = "f" * 40 if full != "f" * 40 else "e" * 40
        verdicts = []
        for main, rev in ((full, "abc1234"), (full, "not a commit"), (None, full), (elsewhere, full),
                          (full, full[:7]), (full, full)):
            replies.origin_main = lambda main=main: main
            replies.drop(deploy(rev))              # one at a time: Windows' clock can give two drops the same microsecond
            verdicts += [(v, w) for _, v, w in replies.take()]
        self.assertEqual(verdicts[0], ("held", "rev abc1234: this helm's checkout is at %s" % full[:7]))
        self.assertEqual(verdicts[1], ("held", "rev: the commit to deploy"))
        self.assertEqual(verdicts[2], ("held", "our origin is not answering, so nothing says which commit its main is; "
                                               "nothing deployed"))
        self.assertEqual(verdicts[3], ("held", "rev %s: our origin's main is %s now; nothing deployed"
                                       % (full[:7], elsewhere[:7])))
        self.assertEqual(verdicts[4], ("applied", "deploy of %s started (deploy.log)" % full[:7]))
        self.assertEqual(verdicts[5], ("held", "a deploy is already running (deploy.log)"))
        replies._deploy.wait()
        self.assertEqual(mark.read_text(), full)                          # that commit, by name, not whatever HEAD is
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
