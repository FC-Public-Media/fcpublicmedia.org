#!/usr/bin/env python3
"""machines/kiosk/replies.py, fed real bottles: AC1 fountain frames made by the site's own composer
(site/assets/js/composer, under Node), signed and unsigned, as the eyes hand them over. Each test has its
own state and archive. Skips without Node.

    python3 bin/test_replies.py
"""
import datetime
import json
import os
import pathlib
import random
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = pathlib.Path(__file__).resolve().parents[1]
COMPOSER = REPO / "site" / "assets" / "js" / "composer"
sys.path.insert(0, str(REPO / "machines" / "kiosk"))
import replies  # noqa: E402

# Frames for one reply: signed with a fresh key, or the bare envelope (a phone without Ed25519).
POUR = """
import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";
const dir = pathToFileURL(process.argv[2] + "/").href;
const { packTransfer, TRANSFER } = await import(dir + "transfer.mjs");
const { generateIdentity } = await import(dir + "sign.mjs");
const { fountainTransfer } = await import(dir + "carrier.mjs");
const { defaultHash } = await import(dir + "anecdote.mjs");
const { text, signed, tamper } = JSON.parse(readFileSync(0, "utf8"));
const bytes = new TextEncoder().encode(text);
const env = signed ? await packTransfer("fcpm.reply", bytes, await generateIdentity())
  : { schema: TRANSFER, kind: "fcpm.reply", size: bytes.length, hash: await defaultHash(bytes),
      bytes: Buffer.from(bytes).toString("base64") };
if (tamper) env.hash = "sha256:" + "0".repeat(64);
const ft = await fountainTransfer(env, { blockSize: 48 });
process.stdout.write(JSON.stringify(ft.frames(Math.max(40, ft.K * 4))));
"""

NODE = replies.node_exe()


def iso(delta=datetime.timedelta()):
    return (datetime.datetime.now().astimezone() + delta).isoformat(timespec="seconds")


def reply(wizard, **fields):
    r = {"schema": "fcpm.reply/v0", "wizard": wizard, "at": "test"}
    r.update(fields)
    r.setdefault("issued", iso())
    r.setdefault("nonce", os.urandom(8).hex())
    r["sig"] = None
    return r


@unittest.skipUnless(NODE, "no node")
class Replies(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        self.saved = replies.STATE, replies.ANSWERS, replies.COMPOSER
        replies.STATE, replies.ANSWERS, replies.COMPOSER = self.tmp / "state", self.tmp / "answers", COMPOSER

    def tearDown(self):
        replies.STATE, replies.ANSWERS, replies.COMPOSER = self.saved
        shutil.rmtree(self.tmp)

    def frames(self, r, signed=True, tamper=False):
        script = self.tmp / "pour.mjs"
        script.write_text(POUR)
        out = subprocess.run([NODE, str(script), str(COMPOSER)], input=json.dumps(
            {"text": json.dumps(r), "signed": signed, "tamper": tamper}), capture_output=True, text=True, check=True)
        return json.loads(out.stdout)

    def show(self, r, **kw):
        """Shown to the camera: most of the frames, out of order, then the door's pass."""
        frames = self.frames(r, **kw)
        replies.drop_frames(random.Random(3).sample(frames, len(frames) - 4), "test")
        [(_, verdict, why)] = replies.take()
        return verdict, why

    def visits(self):
        return [json.loads(line) for line in (replies.STATE / "visits.ndjson").read_text().splitlines()]

    def archive(self, tank):
        return [json.loads(p.read_text()) for p in sorted((replies.ANSWERS / tank).glob("*.json"))]

    # ---- the check-in

    def test_a_signed_check_in_is_one_visit(self):
        verdict, why = self.show(reply("wizard:kiosk+checkin", name="Sam", email=None, reason="Class"))
        self.assertEqual((verdict, why), ("applied", "Sam checked in (Class)"))
        [visit] = self.visits()
        self.assertEqual(visit["trust"], "signed")
        self.assertTrue(visit["by"].startswith("key:sha256:"))

    def test_the_same_check_in_shown_twice_is_held(self):
        r = reply("wizard:kiosk+checkin", name="Sam", email=None, reason=None)
        self.show(r)
        verdict, why = self.show(r)
        self.assertEqual(verdict, "held")
        self.assertIn("nonce", why)
        self.assertEqual(len(self.visits()), 1)

    def test_an_unsigned_check_in_applies_as_unsigned(self):
        verdict, _ = self.show(reply("wizard:kiosk+checkin", name="Old iPhone", email=None, reason=None), signed=False)
        self.assertEqual(verdict, "applied")
        self.assertEqual(self.visits()[0]["trust"], "unsigned")
        self.assertIsNone(self.visits()[0]["by"])

    def test_an_unsigned_bottle_whose_bytes_do_not_match_is_held(self):
        verdict, _ = self.show(reply("wizard:kiosk+checkin", name="X", email=None, reason=None), signed=False, tamper=True)
        self.assertEqual(verdict, "held")

    def test_a_check_in_older_than_a_day_is_held(self):
        verdict, why = self.show(reply("wizard:kiosk+checkin", name="Sam", email=None, reason=None,
                                       issued=iso(-datetime.timedelta(days=3))))
        self.assertEqual(verdict, "held")
        self.assertIn("too far", why)

    # ---- a form's answers

    def program(self, **kw):
        return reply("wizard:site+answers", tank="program", reference="68ea9429-6dad-4f73-b9fa-a49459ae952d",
                     answers={"first_name": "Ada", "email": "ada@example.org", "copyright": True}, **kw)

    def test_a_form_reply_joins_its_tanks_archive(self):
        verdict, why = self.show(self.program())
        self.assertEqual(verdict, "applied")
        [row] = self.archive("program")
        self.assertEqual({k: row[k] for k in ("form", "reference", "origin", "sku", "answers")}, {
            "form": "program", "reference": "68ea9429-6dad-4f73-b9fa-a49459ae952d", "origin": "camera", "sku": None,
            "answers": {"first_name": "Ada", "email": "ada@example.org", "copyright": True}})
        self.assertTrue(row["received"].endswith("Z"))
        name = next((replies.ANSWERS / "program").glob("*.json")).name
        self.assertTrue(name.endswith("--68ea9429-6dad-4f73-b9fa-a49459ae952d.json"))
        self.assertEqual(oct((replies.ANSWERS / "program" / name).stat().st_mode & 0o777), "0o600")

    def test_a_membership_reply_carries_its_tier_as_the_sku(self):
        self.show(reply("wizard:site+answers", tank="membership", reference="0f0e0d0c-aaaa-bbbb-cccc-000000000001",
                        answers={"email": "a@b.org", "sku": "member-annual"}))
        [row] = self.archive("membership")
        self.assertEqual(row["sku"], "member-annual")
        self.assertNotIn("sku", row["answers"])

    def test_a_reply_the_tank_already_brought_is_not_written_twice(self):
        folder = replies.ANSWERS / "program"
        folder.mkdir(parents=True)
        (folder / "2026-10-27T23-14-21.460Z--68ea9429-6dad-4f73-b9fa-a49459ae952d.json").write_text("{}")
        verdict, why = self.show(self.program())
        self.assertEqual(verdict, "applied")
        self.assertIn("already", why)
        self.assertEqual(len(list(folder.glob("*.json"))), 1)

    def test_a_form_reply_kept_for_a_week_is_still_good(self):
        verdict, _ = self.show(self.program(issued=iso(-datetime.timedelta(days=7))))
        self.assertEqual(verdict, "applied")

    def test_a_form_reply_from_the_future_is_held(self):
        verdict, _ = self.show(self.program(issued=iso(datetime.timedelta(days=3))))
        self.assertEqual(verdict, "held")

    def test_a_form_reply_with_no_proper_tank_is_held(self):
        r = self.program()
        r["tank"] = "../etc"
        verdict, why = self.show(r)
        self.assertEqual((verdict, why), ("held", "tank: a tank's name"))


if __name__ == "__main__":
    unittest.main()
