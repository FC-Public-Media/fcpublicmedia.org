#!/usr/bin/env python3
"""machines/digitization/spread: the same words to every model, kept side by side."""
import importlib.machinery
import importlib.util
import json
import pathlib
import tempfile
import unittest
import urllib.error

REPO = pathlib.Path(__file__).resolve().parents[1]
_load = importlib.machinery.SourceFileLoader("spread", str(REPO / "machines" / "digitization" / "spread"))
spread = importlib.util.module_from_spec(importlib.util.spec_from_loader("spread", _load))
_load.exec_module(spread)


class Spread(unittest.TestCase):
    def test_every_model_gets_the_same_words_and_seed_and_a_sleeper_is_kept_as_its_error(self):
        sent = []
        def send(body):
            sent.append(body)
            if body["model"] == "qwen3.8-27b":
                raise urllib.error.URLError("timed out")
            return {"choices": [{"message": {"content": " City pay "}, "finish_reason": "stop"}],
                    "usage": {"completion_tokens": 3}}
        sh = dict(spread.asks.shape("label"), effort="quick")
        msgs = spread.messages(sh, "Salaries by department")
        ticks = iter(range(100))
        got = spread.ask_all(["qwen3.5-0.8b", "qwen3.8-27b", "gpt-oss-20b"], msgs, sh, 7, send, lambda: next(ticks))
        self.assertEqual([b["messages"] for b in sent], [msgs] * 3)
        self.assertEqual({b["seed"] for b in sent}, {7})
        self.assertEqual(msgs[0]["role"], "system")
        self.assertEqual(sent[2]["chat_template_kwargs"], {"reasoning_effort": "low"})
        self.assertEqual([(a["model"], a["text"]) for a in got], [("qwen3.5-0.8b", "City pay"), ("qwen3.8-27b", ""), ("gpt-oss-20b", "City pay")])
        self.assertIn("timed out", got[1]["error"])
        self.assertEqual(got[0]["model_sha256"], "091d8deba394")
        with tempfile.TemporaryDirectory() as d:
            spread.write({"name": "pay", "at": "2026-11-06T12:00:00-07:00", "shape": "model+label", "effort": "quick",
                          "seed": 7, "input": "Salaries by department", "messages": msgs, "answers": got}, pathlib.Path(d))
            self.assertEqual(len(json.loads((pathlib.Path(d) / "round.json").read_text())["answers"]), 3)
            md = (pathlib.Path(d) / "round.md").read_text()
            self.assertIn("## qwen3.8-27b (Qwen, 27B)", md)
            self.assertIn("timed out", md)

    def test_without_a_shape_the_input_is_asked_as_it_is(self):
        self.assertEqual(spread.messages({}, "hi"), [{"role": "user", "content": "hi"}])


if __name__ == "__main__":
    unittest.main()
