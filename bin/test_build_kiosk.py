#!/usr/bin/env python3
"""Tests for the kiosk artifact builder.

    python3 bin/test_build_kiosk.py

The assertions worth having here are about the two things that make this
artifact safe to hand to a machine nobody in this repository controls:

**It carries no secret.** The guest Wi-Fi password must not reach a committed
file in a public repository, and the gitignored QR that encodes it must not be
referenced either. Both are checked against a hostile case — the password
present in the sources *and* in the environment — because the guard that only
runs on the happy path is the guard that is not there.

**It stays inert and portable.** No template syntax, no address for itself, no
timestamp. Those are what let station-node render it today and an FCPM machine
render it later with the file unchanged. Each is cheap to break by accident and
silent when broken, which is exactly what a test is for.

Plus a regression test for a bug that shipped in the first draft and was caught
only by generating the file and reading it: the Wi-Fi panel inheriting the
printed poster's "point your camera at the code" wording onto a screen that has
no code on it.
"""

import importlib.util
import json
import pathlib
import re
import subprocess
import unittest
import unittest.mock

import yaml


def load():
    spec = importlib.util.spec_from_file_location(
        "build_kiosk", pathlib.Path(__file__).parent / "build-kiosk.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


bk = load()

# A password that could not occur by coincidence, so a hit is always a leak.
FAKE_PASSWORD = "zz-not-the-real-guest-password-4417"


def sources(**overrides):
    """Minimal but realistic sources, with the password present in the input.

    The Wi-Fi password is deliberately threaded into the source dict even
    though no real data file holds one. If a future edit starts copying
    unknown keys through into the artifact, these tests are what notices.
    """
    src = {
        "content": {
            "room": "the welcome desk",
            "greeting": "Welcome in.",
            "panels": [
                {"panel": "Checking in", "from": "checkin", "note": "Scan it."},
                {"panel": "Guest Wi-Fi", "from": "wifi", "note": "Pick this network."},
                {"panel": "Need a hand?", "say": "Ask at the desk."},
            ],
        },
        "org": {"name": "Fort Collins Public Media"},
        "wifi": {
            "network": {"ssid": "FC Public Media Guest", "confirmed": True},
            "poster": {"note": "Point your camera at the code and tap it."},
            "password": FAKE_PASSWORD,
        },
        "checkin": {"url": "https://www.fcpublicmedia.org/check-in/"},
    }
    src.update(overrides)
    return src


class TestSecrets(unittest.TestCase):
    def test_password_never_reaches_the_artifact(self):
        text = bk.render(bk.build(sources()))
        self.assertNotIn(FAKE_PASSWORD, text)

    def test_the_password_guard_actually_fires(self):
        """The guard must reject a leak rather than merely not causing one."""
        with self.assertRaises(SystemExit) as caught:
            bk.check_no_secrets("greeting: join with %s\n" % FAKE_PASSWORD, FAKE_PASSWORD)
        self.assertIn("must not", str(caught.exception))

    def test_the_gitignored_wifi_qr_is_refused(self):
        with self.assertRaises(SystemExit) as caught:
            bk.check_no_secrets("qr:\n  image: site/assets/img/wifi-qr.svg\n")
        self.assertIn("gitignored", str(caught.exception))

    def test_secret_looking_keys_are_refused(self):
        for key in ("password", "passphrase", "secret", "psk"):
            with self.subTest(key=key):
                with self.assertRaises(SystemExit):
                    bk.check_no_secrets("panels:\n  %s: hunter2\n" % key)

    def test_the_real_artifact_passes_its_own_guard(self):
        """Belt and braces: the committed file, checked as a string."""
        text = bk.ARTIFACT.read_text()
        bk.check_no_secrets(text, FAKE_PASSWORD)
        self.assertNotIn(bk.FORBIDDEN_ASSET, text)


class TestInertAndPortable(unittest.TestCase):
    def setUp(self):
        self.text = bk.ARTIFACT.read_text()

    def test_no_template_syntax(self):
        """A consumer resolves nothing. Liquid, Jinja and ERB all stay out."""
        for token in ("{{", "{%", "<%", "${"):
            with self.subTest(token=token):
                self.assertNotIn(token, self.text)

    def test_names_no_host_port_or_local_address(self):
        """The serving address belongs to whoever serves it, not to the file.

        This is the property that makes the eventual handover free: when FCPM
        stands up its own node, the artifact does not change — only the
        renderer. A hostname baked in here is what would break that.
        """
        body = "\n".join(
            line for line in self.text.splitlines() if not line.startswith("#")
        )
        for pattern in (r"localhost", r"\.local\b", r":\d{4}\b", r"127\.0\.0\.1"):
            with self.subTest(pattern=pattern):
                self.assertIsNone(
                    re.search(pattern, body),
                    "the artifact names an address for itself: %s" % pattern,
                )

    def test_the_only_url_is_the_qr_destination(self):
        """`encodes:` is content. Anything else with a scheme is configuration."""
        body = [
            line for line in self.text.splitlines() if not line.strip().startswith("#")
        ]
        urls = [line for line in body if "://" in line]
        self.assertEqual(len(urls), 1, "unexpected URLs: %r" % urls)
        self.assertIn("encodes:", urls[0])

    def test_no_timestamp(self):
        """A self-stamping file churns every run and stops meaning anything."""
        for pattern in (r"\d{4}-\d{2}-\d{2}", r"generated_at", r"\btimestamp\b"):
            with self.subTest(pattern=pattern):
                self.assertIsNone(re.search(pattern, self.text))

    def test_deterministic(self):
        """Same sources, same bytes — otherwise --check is noise."""
        first = bk.render(bk.build(sources()))
        second = bk.render(bk.build(sources()))
        self.assertEqual(first, second)


class TestRevision(unittest.TestCase):
    """The field that lets an update bounce a screen.

    A kiosk on a wall has nobody to press refresh, so the page polls this and
    reloads when it differs from what it rendered with. That only works if the
    field has both halves of the property: it must change when the content
    changes, and it must NOT change when it hasn't. A timestamp has the first
    and not the second, which is why this is a digest.
    """

    def test_present_and_looks_like_a_digest(self):
        artifact = yaml.safe_load(bk.ARTIFACT.read_text())
        self.assertRegex(artifact["revision"], r"\A[0-9a-f]{12}\Z")

    def test_stable_across_rebuilds(self):
        """Regenerating without editing anything must not move it."""
        self.assertEqual(
            bk.render(bk.build(sources())), bk.render(bk.build(sources()))
        )

    def test_changes_when_the_content_changes(self):
        before = yaml.safe_load(bk.render(bk.build(sources())))["revision"]
        src = sources()
        src["content"]["greeting"] = "Something else entirely."
        after = yaml.safe_load(bk.render(bk.build(src)))["revision"]
        self.assertNotEqual(before, after)

    def test_changes_when_a_fact_changes(self):
        """A new SSID is exactly the case a screen must not miss."""
        before = yaml.safe_load(bk.render(bk.build(sources())))["revision"]
        src = sources()
        src["wifi"]["network"]["ssid"] = "FC Public Media Guest 5G"
        after = yaml.safe_load(bk.render(bk.build(src)))["revision"]
        self.assertNotEqual(before, after)

    def test_does_not_cover_itself(self):
        """The digest is over the body, so it is checkable by hand."""
        text = bk.render(bk.build(sources()))
        lines = [l for l in text.splitlines() if not l.startswith("#")]
        body = "\n".join(l for l in lines if not l.startswith("revision:"))
        # Strip the blank separator line the header leaves behind.
        body = body.lstrip("\n") + "\n"
        self.assertEqual(yaml.safe_load(text)["revision"], bk.revision(body))


class TestTheJsTransport(unittest.TestCase):
    """The second artifact, and why it is transport rather than a second truth.

    The panel opens `brand/idle/index.html` from a clone as a local file.
    Measured in Chrome 2026-09-24: a `file://` page cannot `fetch` a sibling —
    opaque origin, `TypeError: Failed to fetch`, and no header can permit it —
    but a `<script src>` with a cache-buster works and works repeatedly. So the
    YAML is unreadable by the one consumer this artifact has.

    The risk that comes with a second copy is that the two disagree. These
    tests are what makes that not happen.
    """

    def setUp(self):
        self.artifact = bk.build(sources())
        self.yaml_text, self.js_text = bk.outputs(self.artifact)

    def payload(self, js_text=None):
        """Parse the assignment back out, without executing anything."""
        text = js_text if js_text is not None else self.js_text
        body = text[text.index("window.%s = " % bk.GLOBAL) :]
        body = body[body.index("{") : body.rindex("}") + 1]
        return json.loads(body)

    def test_is_one_assignment_and_nothing_else(self):
        """No logic, no fetch, no side effects — it is data in a JS wrapper."""
        code = "\n".join(
            l for l in self.js_text.splitlines() if not l.strip().startswith("//")
        ).strip()
        self.assertTrue(code.startswith("window.%s = {" % bk.GLOBAL))
        self.assertTrue(code.endswith("};"))
        for forbidden in ("fetch(", "XMLHttpRequest", "eval(", "function", "=>", "import "):
            with self.subTest(token=forbidden):
                self.assertNotIn(forbidden, code)

    def test_revision_is_identical_to_the_yaml(self):
        """Copied, not recomputed. Two digests could disagree; one cannot."""
        self.assertEqual(
            self.payload()["revision"], yaml.safe_load(self.yaml_text)["revision"]
        )

    def test_content_is_identical_to_the_yaml(self):
        """Same content, two encodings. Any drift here is the whole risk."""
        from_yaml = yaml.safe_load(self.yaml_text)
        from_js = self.payload()
        self.assertEqual(from_js, from_yaml)

    def test_committed_pair_agrees(self):
        """The real files on disk, not just freshly rendered ones."""
        on_disk_yaml = yaml.safe_load(bk.ARTIFACT.read_text())
        on_disk_js = self.payload(bk.ARTIFACT_JS.read_text())
        self.assertEqual(on_disk_js, on_disk_yaml)

    def test_carries_no_secret_either(self):
        """The guard must cover the file a browser actually loads."""
        bk.check_no_secrets(self.js_text, FAKE_PASSWORD)
        self.assertNotIn(FAKE_PASSWORD, self.js_text)
        self.assertNotIn(bk.FORBIDDEN_ASSET, self.js_text)

    def test_json_style_secret_keys_are_refused(self):
        """A YAML-only key check would miss the JSON encoding entirely."""
        for key in ("password", "passphrase", "secret", "psk"):
            with self.subTest(key=key):
                with self.assertRaises(SystemExit):
                    bk.check_no_secrets('{\n  "%s": "hunter2"\n}\n' % key)

    def test_check_mode_covers_both_files(self):
        """A stale JS with a current YAML must still fail."""
        original = bk.ARTIFACT_JS.read_text()
        try:
            bk.ARTIFACT_JS.write_text(original.replace("window.", "window.X", 1))
            self.assertEqual(bk.main(["--check"]), 1)
        finally:
            bk.ARTIFACT_JS.write_text(original)
        self.assertEqual(bk.main(["--check"]), 0)


class TestTheWifiPanel(unittest.TestCase):
    def test_unconfirmed_ssid_refuses_to_build(self):
        """The same gate make-wifi-qr.py enforces before printing a poster."""
        src = sources()
        src["wifi"]["network"]["confirmed"] = False
        with self.assertRaises(SystemExit) as caught:
            bk.build(src)
        self.assertIn("confirmed: true", str(caught.exception))

    def test_ssid_is_not_retyped_anywhere(self):
        """It comes from wifi.yml, which is the file that owns it."""
        src = sources()
        src["wifi"]["network"]["ssid"] = "Something Else Entirely"
        panels = bk.build(src)["panels"]
        wifi = next(p for p in panels if p["panel"] == "Guest Wi-Fi")
        self.assertEqual(wifi["say"], "Something Else Entirely")

    def test_does_not_inherit_the_posters_scan_wording(self):
        """Regression: the poster has a code on it and the kiosk does not.

        `wifi.poster.note` says "point your camera at the code". On a screen
        with no code that reads as a broken kiosk, and the guest cannot tell
        that from a missing feature. Shipped in the first draft; caught by
        generating the file and reading it.
        """
        src = sources()
        src["content"]["panels"][1].pop("note")
        panels = bk.build(src)["panels"]
        wifi = next(p for p in panels if p["panel"] == "Guest Wi-Fi")
        self.assertNotIn("note", wifi)

        # And the real content file must not have left it to chance either.
        real = next(
            p for p in bk.load(bk.CONTENT)["panels"] if p.get("from") == "wifi"
        )
        self.assertTrue(real.get("note"), "the Wi-Fi panel needs its own wording")
        self.assertNotIn("scan", real["note"].lower())

    def test_carries_no_qr(self):
        panels = bk.build(sources())["panels"]
        wifi = next(p for p in panels if p["panel"] == "Guest Wi-Fi")
        self.assertNotIn("qr", wifi)


class TestTheCheckinPanel(unittest.TestCase):
    def test_qr_is_committed_and_present(self):
        """A consumer reads it off disk with no build step, so it must be there."""
        path = bk.REPO / bk.CHECKIN_QR
        self.assertTrue(path.exists(), "%s is missing" % bk.CHECKIN_QR)
        tracked = subprocess.run(
            ["git", "ls-files", "--error-unmatch", bk.CHECKIN_QR],
            cwd=bk.REPO,
            capture_output=True,
        )
        self.assertEqual(tracked.returncode, 0, "%s is not committed" % bk.CHECKIN_QR)

    def test_say_matches_the_printed_poster(self):
        """Two surfaces in one building must not disagree about a URL."""
        panels = bk.build(sources())["panels"]
        checkin = next(p for p in panels if p["panel"] == "Checking in")
        self.assertEqual(checkin["say"], "www.fcpublicmedia.org/check-in/")
        self.assertEqual(
            checkin["qr"]["encodes"], "https://www.fcpublicmedia.org/check-in/"
        )

    def test_missing_qr_is_fatal_rather_than_a_broken_image(self):
        src = sources()
        with unittest.mock.patch.object(bk, "CHECKIN_QR", "site/assets/img/nope.svg"):
            with self.assertRaises(SystemExit) as caught:
                bk.build(src)
        self.assertIn("make-qr.py", str(caught.exception))


class TestMalformedContent(unittest.TestCase):
    def test_unknown_source_is_named_rather_than_ignored(self):
        src = sources()
        src["content"]["panels"] = [{"panel": "Bookings", "from": "bookings"}]
        with self.assertRaises(SystemExit) as caught:
            bk.build(src)
        self.assertIn("not a source", str(caught.exception))

    def test_a_panel_that_says_nothing_is_refused(self):
        src = sources()
        src["content"]["panels"] = [{"panel": "Empty"}]
        with self.assertRaises(SystemExit):
            bk.build(src)

    def test_no_panels_is_refused(self):
        src = sources()
        src["content"]["panels"] = []
        with self.assertRaises(SystemExit):
            bk.build(src)


class TestTheCommittedArtifactIsCurrent(unittest.TestCase):
    """The drift guard. This is the test that earns the generator its keep.

    `kiosk/welcome.yml` is committed so a consumer needs no build step, which
    means it can be stale, which means something has to say so. A stale kiosk
    names a network to a guest standing in front of it.
    """

    def test_check_mode_passes_against_the_tree(self):
        self.assertEqual(bk.main(["--check"]), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
