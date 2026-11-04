#!/usr/bin/env python3
"""wizard:model+ask: replies.py queues the question, machines/digitization/asks answers it. No model and no
network: a fake `send` answers in the model's shape. Each test has its own state.

    python3 bin/test_asks.py
"""
import importlib.machinery
import importlib.util
import json
import os
import pathlib
import shutil
import sys
import tempfile
import unittest
import urllib.error

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "machines" / "kiosk"))
import replies  # noqa: E402

loader = importlib.machinery.SourceFileLoader("asks", str(REPO / "machines" / "digitization" / "asks"))
spec = importlib.util.spec_from_loader("asks", loader)
asks = importlib.util.module_from_spec(spec)
loader.exec_module(asks)


def ask(*turns, nonce=None, **extra):
    r = {"schema": "fcpm.reply/v0", "wizard": "wizard:model+ask", "at": "test",
         "issued": replies.now().isoformat(timespec="seconds"), "nonce": nonce or "n-" + os.urandom(6).hex(),
         "messages": [{"role": role, "content": text} for role, text in turns]}
    r.update(extra)
    return r


class Fake:
    """The model: records each request, answers from a list (the last answer repeats)."""
    def __init__(self, *answers):
        self.answers, self.sent = list(answers), []

    def __call__(self, body):
        self.sent.append(body)
        text = self.answers.pop(0) if len(self.answers) > 1 else self.answers[0]
        return {"choices": [{"message": {"content": text}, "finish_reason": "stop"}], "usage": {"completion_tokens": 7}}


class Asks(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        self.saved = replies.STATE
        replies.STATE = self.tmp / "state"

    def tearDown(self):
        replies.STATE = self.saved
        shutil.rmtree(self.tmp)

    def queued(self):
        return sorted((replies.STATE / "asks" / "queue").glob("*.json"))

    def test_a_question_is_queued_whole(self):
        verdict = replies.examine(ask(("system", "be brief"), ("user", "what is PEG?")), {"by": "fp", "trust": "signed"})
        self.assertEqual(verdict[0], None)
        q = json.loads(self.queued()[0].read_text())
        self.assertEqual([m["role"] for m in q["messages"]], ["system", "user"])
        self.assertEqual((q["by"], q["trust"]), ("fp", "signed"))

    def test_what_is_held_and_why(self):
        cases = {"messages: the last is the question (role user)": ask(("user", "hi"), ("assistant", "hello")),
                 "messages: each a role (system, user or assistant) and its text": ask(("tool", "x")),
                 "messages: 1600 characters; model+ask takes 1500": ask(("user", "x" * 1600)),
                 "nonce: 8 to 64 letters, digits or dashes (the answer is filed under it)": ask(("user", "hi"), nonce="a/b")}
        for why, r in cases.items():
            self.assertEqual(replies.examine(r, {}), why)
        self.assertEqual(self.queued(), [])

    def test_answered_labeled_and_filed_under_the_nonce(self):
        replies.examine(ask(("system", "like a librarian"), ("user", "a garden show?"), nonce="nonce-0001"), {})
        fake = Fake("Yes, gladly.", "Garden show idea.")
        self.assertEqual(asks.answer_one(send=fake), "nonce-0001")
        a = json.loads((replies.STATE / "asks" / "answers" / "nonce-0001.json").read_text())
        self.assertEqual((a["in_reply_to"], a["answer"], a["label"], a["effort"]),
                         ("nonce-0001", "Yes, gladly.", "Garden show idea", "quick"))
        system = fake.sent[0]["messages"][0]
        self.assertEqual(system["role"], "system")
        self.assertIn("FC Public Media", system["content"])          # our role first
        self.assertIn("like a librarian", system["content"])         # theirs inside it
        self.assertEqual(fake.sent[0]["chat_template_kwargs"], {"enable_thinking": False})
        self.assertEqual(fake.sent[0]["seed"], asks.seed_of("nonce-0001"))
        self.assertEqual(self.queued(), [])
        self.assertTrue((replies.STATE / "asks" / "done").is_dir())

    def test_considered_that_comes_back_empty_is_asked_again_at_quick(self):
        got = asks.complete({"effort": "considered", "answer": 50}, [], 1,
                            {"considered-thinking": 1024, "quick-thinking": 0}, Fake("", "an answer"))
        self.assertEqual((got["text"], got["effort"]), ("an answer", "quick (considered came back empty)"))

    def test_a_sleeping_model_leaves_the_question_waiting(self):
        replies.examine(ask(("user", "anyone there?")), {})

        def asleep(body):
            raise urllib.error.URLError("connection refused")
        with self.assertRaises(OSError):
            asks.answer_one(send=asleep)
        self.assertEqual(len(self.queued()), 1)

    def test_an_unreadable_question_is_set_aside(self):
        folder = replies.STATE / "asks" / "queue"
        folder.mkdir(parents=True)
        (folder / "2026-01-01T00-00-00--broken.json").write_text("{not json")
        asks.answer_one(send=Fake("never"))
        self.assertEqual(self.queued(), [])
        self.assertTrue((replies.STATE / "asks" / "held" / "2026-01-01T00-00-00--broken.json").exists())


if __name__ == "__main__":
    unittest.main()
