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
                 "nonce: 8 to 64 letters, digits, dashes or underscores (the answer is filed under it)": ask(("user", "hi"), nonce="a/b")}
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


NODE = replies.node_exe()
VERIFY = REPO / "machines" / "kiosk" / "verify-bottle.mjs"
COMPOSER = REPO / "site" / "assets" / "js" / "composer"


def read_frames(frames):
    """What the composer makes of frames, as the intake asks it (verify-bottle.mjs)."""
    import subprocess
    out = subprocess.run([NODE, str(VERIFY), str(COMPOSER)], input=json.dumps({"frames": frames, "friends": []}),
                         capture_output=True, text=True, timeout=60)
    return json.loads(out.stdout)


@unittest.skipUnless(NODE, "no node")
class Loop(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        self.saved = replies.STATE
        replies.STATE = self.tmp / "state"

    def tearDown(self):
        replies.STATE = self.saved
        shutil.rmtree(self.tmp)

    def test_each_answer_is_bottled_and_the_index_names_its_bottle(self):
        for n in ("nonce-aaaa", "nonce-bbbb"):
            replies.examine(ask(("user", "question %s?" % n), nonce=n), {"by": "fp-secret", "trust": "signed"})
            asks.answer_one(send=Fake("An answer to %s." % n, "Label %s" % n[-4:]))
        bottles = replies.STATE / "asks" / "bottles"
        index = json.loads((bottles / "index.json").read_text())
        rows = {r["in_reply_to"]: r for r in index["index"]["answers"]}
        self.assertEqual(set(rows), {"nonce-aaaa", "nonce-bbbb"})
        b = json.loads((bottles / "nonce-aaaa.json").read_text())
        self.assertEqual(rows["nonce-aaaa"]["id"], b["id"])
        self.assertTrue(all(f.split("|")[3] == b["id"] for f in b["frames"]))     # every frame names its bottle
        got = read_frames(b["frames"])
        self.assertTrue(got["ok"] and got["unsigned"])
        public = json.loads(got["text"])
        self.assertEqual((public["kind"] if "kind" in public else got["kind"], public["answer"]),
                         ("fcpm.answer", "An answer to nonce-aaaa."))
        self.assertNotIn("by", public)                 # who signed the question is not in the public bottle
        self.assertEqual(json.loads(read_frames(json.loads((bottles / "index.json").read_text())["frames"])["text"])
                         ["schema"], "fcpm.index/v0")

    def test_a_phone_catches_its_own_and_carries_everyone_elses_from_a_mixed_lossy_loop(self):
        for n in ("nonce-mine", "nonce-other1", "nonce-other2"):
            replies.examine(ask(("user", "question %s?" % n), nonce=n), {})
            asks.answer_one(send=Fake("The answer to %s, with some length to it so the bottle has blocks." % n, "L"))
        bottles = replies.STATE / "asks" / "bottles"
        loop = [json.loads((bottles / "index.json").read_text())["frames"]]
        loop += [json.loads((bottles / ("%s.json" % n)).read_text())["frames"] for n in ("nonce-other1", "nonce-mine", "nonce-other2")]
        import subprocess
        script = """
import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";
globalThis.atob ??= (s) => Buffer.from(s, "base64").toString("binary");
const { catcher } = await import(pathToFileURL(process.argv[process.argv.length - 1]).href);
const passes = JSON.parse(readFileSync(0, "utf8"));
let rnd = 7; const keep = () => ((rnd = (rnd * 1103515245 + 12345) % 2147483648) / 2147483648) > 0.3;
const c = catcher((n) => n === "nonce-mine");
let out = { got: null, carried: [], frames: 0 };
for (let pass = 0; pass < 8 && !(out.got && out.carried.length === 2); pass++)   // the loop goes round; a phone
  for (const bottle of (pass ? passes : passes.slice(2)))                            // joins mid-way, loses 30%
    for (const f of bottle) {
      if (!keep()) continue;
      out.frames++;
      const r = await c.feed(f);
      if (r && r.answer && r.mine) out.got = r.answer;
      if (r && r.answer && !r.mine) out.carried.push(r.answer.in_reply_to);
    }
out.index = c.index && c.index.answers.length;
out.bottles = c.bottles.map((b) => ({ label: b.label, mine: b.mine, for: b.for, have: b.have, total: b.total, kind: b.kind }));
process.stdout.write(JSON.stringify(out));
"""
        res = subprocess.run([NODE, "--input-type=module", "-e", script, str(REPO / "site" / "assets" / "js" / "catch.mjs")],
                             input=json.dumps(loop), capture_output=True, text=True, timeout=120)
        out = json.loads(res.stdout or "{}")
        self.assertEqual((out.get("got") or {}).get("in_reply_to"), "nonce-mine", res.stderr[-400:])
        self.assertIn("nonce-mine", out["got"]["answer"])
        rows = out["bottles"]                       # every bottle going by: what it is, how far, whose
        self.assertEqual(sum(1 for b in rows if b["mine"]), 1)
        self.assertEqual([b["label"] for b in rows if b["mine"]], ["L"])       # its own, named once read
        self.assertEqual(sorted(out["carried"]), ["nonce-other1", "nonce-other2"])   # carried for the others
        self.assertTrue(all(b["total"] for b in rows))
        self.assertTrue(all(0 <= b["have"] <= (b["total"] or 0) for b in rows if b["total"]))

    def test_console_frames_fit_qr_locals_screen_and_the_inbox_reads_back(self):
        replies.examine(ask(("user", "what airs tonight?"), nonce="nonce-qrlo"), {})
        asks.answer_one(send=Fake("Tonight: the council meeting, then the jukebox.", "Tonight's lineup"))
        b = json.loads((replies.STATE / "asks" / "bottles" / "nonce-qrlo.json").read_text())
        con = b["console"]
        self.assertEqual(len(con["frames"]), len(con["modules"]))
        self.assertTrue(all(len(m) == 41 and all(len(r) == 41 for r in m) for m in con["modules"]))   # version 6
        self.assertTrue(all(f.split("|")[3] == b["id"] for f in con["frames"]))     # the same bottle, smaller frames
        self.assertTrue(read_frames(con["frames"])["ok"])
        rows = replies.inbox()
        self.assertEqual((rows[0]["state"], rows[0]["what"], rows[0]["nonce"]), ("answered", "Tonight's lineup", "nonce-qrlo"))
        replies.examine(ask(("user", "and tomorrow?"), nonce="nonce-qrl2"), {})
        self.assertEqual(replies.inbox()[0]["state"], "queued")

    def test_the_answerer_says_how_it_is_only_when_that_changes(self):
        asks.say(up=False, working=None, trouble=None)
        first = replies.asks_state()
        self.assertEqual((first["shape"], first["by"], first["up"]), ("model+ask", "bay 1", False))
        asks.say(up=False, working=None, trouble=None)
        self.assertEqual(replies.asks_state()["at"], first["at"])
        asks.say(up=True, working="nonce-x", trouble=None)
        self.assertEqual((replies.asks_state()["up"], replies.asks_state()["working"]), (True, "nonce-x"))

    def test_answers_fall_off_the_loop_after_ten_minutes_and_a_recall_brings_one_back(self):
        import datetime, os
        for n in ("nonce-old1", "nonce-new1", "nonce-old2"):
            replies.examine(ask(("user", "question %s?" % n), nonce=n), {})
            asks.answer_one(send=Fake("Answer to %s." % n, "L " + n[-4:]))
        folder = replies.STATE / "asks" / "answers"
        long_ago = (replies.now() - datetime.timedelta(minutes=30)).isoformat(timespec="seconds")
        for n in ("nonce-old1", "nonce-old2"):                       # answered half an hour ago
            a = json.loads((folder / ("%s.json" % n)).read_text()); a["answered"] = long_ago
            (folder / ("%s.json" % n)).write_text(json.dumps(a))
        self.assertEqual(asks.on_air(), (["nonce-new1"], None))      # on hand, but off the air
        self.assertEqual([r["in_reply_to"] for r in asks.reindex()["answers"]], ["nonce-new1"])
        recall = {"schema": "fcpm.reply/v0", "wizard": "wizard:loop+recall", "at": "test", "nonce": "recall-0001",
                  "issued": replies.now().isoformat(timespec="seconds"), "nonces": ["nonce-old1"]}
        self.assertEqual(replies.examine(recall, {}), (None, "1 answer back in the loop (takeover)"))
        nonces, now = asks.on_air()
        self.assertEqual((sorted(nonces), now["nonces"]), (["nonce-new1", "nonce-old1"], ["nonce-old1"]))
        index = asks.reindex()
        self.assertEqual(index["now"]["nonces"], ["nonce-old1"])     # the screens show it at once
        inject = dict(recall, nonce="recall-0002", nonces=["nonce-old2", "nonce-gone"])
        self.assertEqual(replies.examine(inject, {}), (None, "1 answer back in the loop (inject)"))
        self.assertIn("nonce-old2", asks.on_air()[0])
        self.assertEqual(asks.on_air()[1]["nonces"], ["nonce-old1"])  # an inject takes nothing over
        nothing = dict(recall, nonce="recall-0003", nonces=["nonce-gone"])
        self.assertEqual(replies.examine(nothing, {}), "no answer on hand for …e-gone")

    def test_reindex_bottles_an_answer_that_lacks_one(self):
        replies.examine(ask(("user", "late?"), nonce="nonce-cccc"), {})
        asks.answer_one(send=Fake("Yes.", "Lateness"))
        (replies.STATE / "asks" / "bottles" / "nonce-cccc.json").unlink()
        self.assertEqual([r["in_reply_to"] for r in asks.reindex()["answers"]], ["nonce-cccc"])
        self.assertTrue((replies.STATE / "asks" / "bottles" / "nonce-cccc.json").is_file())


if __name__ == "__main__":
    unittest.main()
