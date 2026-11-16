#!/usr/bin/env python3
"""wizard:seat+run: replies.py queues the call, machines/digitization/seats grants, admits and runs it by the advocate
engine's run.sh, and files the finished reply as an answer. No API: a fake agent stands behind ADVOCATE_AGENT_CMD and
keeps a response with usage where seat-curl would. Each test has its own state, library and seats' clone.

    python3 bin/test_seats.py
"""
import importlib.machinery
import importlib.util
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import textwrap
import unittest

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "machines" / "kiosk"))
import replies  # noqa: E402

loader = importlib.machinery.SourceFileLoader("seats", str(REPO / "machines" / "digitization" / "seats"))
spec = importlib.util.spec_from_loader("seats", loader)
seats = importlib.util.module_from_spec(spec)
loader.exec_module(seats)

AGENT = textwrap.dedent("""\
    #!/bin/sh
    [ "${1:-}" = --available ] && exit 0
    cat > "$SEAT_SEEN"
    echo '{"model":"claude-opus-5-5","usage":{"input_tokens":1000,"output_tokens":500}}' > "$SEAT_DUMP"
    cat <<'J'
    {"position":"# Position\\n\\nPaid online: unmeasured.\\n","complaints":"","asks":"","session":"Read the range. Said nothing about prices."}
    J
    """)


def call(seat="payments", nonce=None, **extra):
    r = {"schema": "fcpm.reply/v0", "wizard": "wizard:seat+run", "at": "test",
         "issued": replies.now().isoformat(timespec="seconds"), "nonce": nonce or "s-" + os.urandom(6).hex(), "seat": seat}
    r.update(extra)
    return r


@unittest.skipUnless((REPO / ".advocate-engine" / "run.sh").is_file(), "the advocate engine is not checked out")
class Seats(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        self.was = replies.STATE
        replies.STATE = self.tmp / "state"
        cfg = self.tmp / "seats.yml"
        cfg.write_text("repo: %s\nprices:\n  claude-opus-5-5: [4, 20]\nseats:\n  payments:\n    gap: 30m\n"
                       % (self.tmp / "seats" / "fcpublicmedia.org"))
        seats.CONFIG = cfg
        agent = self.tmp / "agent"
        agent.write_text(AGENT)
        agent.chmod(0o755)
        self.env = {"FCPM_LIBRARY": str(self.tmp / "library"), "ADVOCATE_AGENT_CMD": str(agent),
                    "SEAT_SEEN": str(self.tmp / "seen.json")}
        self.kept = {k: os.environ.get(k) for k in self.env}
        os.environ.update(self.env)

    def tearDown(self):
        replies.STATE = self.was
        for k, v in self.kept.items():
            os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)
        subprocess.run(["rm", "-rf", str(self.tmp)])

    def take(self, reply):
        return replies.examine(reply, {"by": "key:sha256:test", "trust": "friend"})

    def test_unknown_seat_is_held_at_the_door(self):
        self.assertIn("no seat", self.take(call("nobody")))

    def test_a_call_runs_and_its_reply_is_an_answer(self):
        r = call(note="before the board meeting",
                 quote=[{"in_reply_to": "earlier-0001", "label": "x", "answer": "Stripe is live."}])
        self.assertIsInstance(self.take(r), tuple)
        self.assertEqual(seats.run_one(), r["nonce"])
        run = json.loads((replies.STATE / "seats" / "runs" / r["nonce"] / "run.json").read_text())
        self.assertIn(run["outcome"], ("seated", "spoke"), run)
        repo = self.tmp / "seats" / "fcpublicmedia.org"
        self.assertEqual(run["commit"], subprocess.run(["git", "-C", str(repo), "rev-parse", "refs/heads/advocate/payments"],
                                                       capture_output=True, text=True).stdout.strip())
        self.assertIn("POSITION.md", run["wrote"])
        self.assertEqual(run["usage"], {"model": "claude-opus-5-5", "input": 1000, "output": 500, "dollars": 0.014})
        seen = json.loads((self.tmp / "seen.json").read_text())        # what the agent was given
        self.assertIn("This session's admission", seen["method"])
        self.assertIn("Stripe is live.", seen["method"])                 # the quoted reply, relayed
        self.assertIn(r["nonce"], seen["method"])
        admission = json.loads((replies.STATE / "seats" / "runs" / r["nonce"] / "admission.json").read_text())
        self.assertEqual(admission["called"]["note"], "before the board meeting")
        self.assertTrue(all(admission["grants"].values()))
        a = json.loads((replies.STATE / "asks" / "answers" / ("%s.json" % r["nonce"])).read_text())
        self.assertEqual((a["in_reply_to"], a["shape"]), (r["nonce"], "seat+run"))
        self.assertIn("advocate/payments@" + run["commit"][:7], a["answer"])
        self.assertIn("about $0.01", a["answer"])
        self.assertIn("Said nothing about prices.", a["answer"])
        book = subprocess.run([sys.executable, str(REPO / "machines" / "library.py"), "--profile", "digitization", "grants"],
                              capture_output=True, text=True).stdout
        self.assertIn("no one", book)                                    # both grants released

    def test_a_second_call_inside_the_gap_is_held_and_answered(self):
        first, second = call(), call()
        self.take(first)
        seats.run_one()
        self.take(second)
        seats.run_one()
        run = json.loads((replies.STATE / "seats" / "runs" / second["nonce"] / "run.json").read_text())
        self.assertEqual(run["outcome"], "held")
        self.assertIn("seats.yml gap", run["why"])
        a = json.loads((replies.STATE / "asks" / "answers" / ("%s.json" % second["nonce"])).read_text())
        self.assertIn("was held", a["answer"])

    def test_a_seat_this_helm_does_not_hold_is_held(self):
        r = call("credentials")
        self.assertIsInstance(self.take(r), tuple)
        seats.run_one()
        run = json.loads((replies.STATE / "seats" / "runs" / r["nonce"] / "run.json").read_text())
        self.assertEqual(run["outcome"], "held")
        self.assertIn("holds no credentials seat", run["why"])


if __name__ == "__main__":
    unittest.main()
