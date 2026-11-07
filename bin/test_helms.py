#!/usr/bin/env python3
"""Helm to helm (machines/helms.yml, replies.py route): a reply whose wizard another job's helm holds is
passed there as it came, or waits for it; the holding helm applies wizard:model+up by model.ps1 pick.

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


if __name__ == "__main__":
    unittest.main()
