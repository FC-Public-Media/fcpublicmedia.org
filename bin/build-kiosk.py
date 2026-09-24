#!/usr/bin/env python3
"""Build the kiosk artifact from what this repository already knows.

    python3 bin/build-kiosk.py            write kiosk/welcome.yml and welcome.js
    python3 bin/build-kiosk.py --check    fail if either committed file is stale
    python3 bin/build-kiosk.py --print    write nothing, show both

`kiosk/content.yml` is the editorial half — the greeting, the room, the panel
wording. The facts come from `site/_data/`. This script joins them and writes
`kiosk/welcome.yml`, which is committed and canonical, plus `kiosk/welcome.js`
which carries the same content for a panel that cannot read the YAML — see
`JS_HEADER` below for the measurement that forced it.

WHY GENERATED AND NOT HAND-WRITTEN
----------------------------------
Because the alternative is typing the SSID twice.

`site/_data/wifi.yml` owns the network name. It carries a `confirmed:` gate and
a long note recording that this network has, at least once, simply not been
there. A hand-written kiosk file would hold a second copy of that name with
none of that context attached, and the two would agree right up until somebody
changed one of them.

A kiosk is the worst possible place for that drift, which is the argument for
the generator rather than a style preference. A stale poster is read by somebody
who can walk away and ask. A stale kiosk is a screen at the desk confidently
naming a network to a guest who is standing in front of it, and they cannot
tell "the screen is wrong" from "the Wi-Fi is broken" — so they conclude the
second one. Same failure the poster page warns about, one step closer to the
guest.

So the generator also inherits the gate: an unconfirmed SSID refuses to build,
exactly as `site/bin/make-wifi-qr.py` refuses to print one.

WHAT THE ARTIFACT DELIBERATELY DOES NOT CONTAIN
-----------------------------------------------
**The Wi-Fi password, or any QR encoding it.** This repository is public. A
Wi-Fi QR is not encryption — it is a font — so a committed one publishes the
password to everyone rather than to the people in the room. `wifi-qr.svg` is
gitignored for that reason and `check()` below refuses to reference it.

**A hostname, a port, or an address for itself.** Those belong to whatever is
serving the artifact, not to the artifact. Today that is station-node on the
LAN; eventually it is an FCPM machine. The point of leaving them out is that
when that changes, *this file does not* — only who renders it.

`encodes:` is the one URL here, and it is content rather than configuration:
it is where the QR points, and the printed poster shows it as human-readable
fallback for a camera that will not cooperate. Not the kiosk's own address.

**A timestamp.** A generated file that stamps itself churns on every run, and
then nobody can tell whether what is on disk is current or merely recent.
`--check` answers that question properly, by rebuilding and comparing.

WHAT IT DOES CONTAIN, SO A SCREEN CAN NOTICE AN UPDATE
-----------------------------------------------------
`revision:` — a short digest of the content, and the thing a kiosk polls so
that an update can bounce it without anybody pressing refresh. It changes when
the content changes and not otherwise, which is the property a timestamp does
not have. See `revision()`.
"""

import argparse
import hashlib
import json
import os
import pathlib
import subprocess
import sys

try:
    import yaml
except ImportError:  # pragma: no cover - environment problem, not logic
    print(
        "error: PyYAML is needed to read the data files.\n"
        "       pip install pyyaml",
        file=sys.stderr,
    )
    raise SystemExit(1)

REPO = pathlib.Path(__file__).resolve().parent.parent
CONTENT = REPO / "kiosk" / "content.yml"
ARTIFACT = REPO / "kiosk" / "welcome.yml"
ARTIFACT_JS = REPO / "kiosk" / "welcome.js"

# The global the JS transport assigns. Named rather than anonymous so a panel
# can check whether it loaded at all.
GLOBAL = "FCPM_KIOSK"
DATA = REPO / "site" / "_data"

# The committed check-in QR. A plain https URL and nothing else, which is why
# this one is allowed to travel and the Wi-Fi one is not.
CHECKIN_QR = "site/assets/img/check-in-qr.svg"

# Gitignored, and must never be named by the artifact. See the module header.
FORBIDDEN_ASSET = "wifi-qr.svg"

HEADER = """\
# GENERATED FILE — do not edit.
#
#   python3 bin/build-kiosk.py
#
# Edit `kiosk/content.yml` for the wording, or `site/_data/` for the facts,
# then regenerate. `bin/build-kiosk.py --check` fails if this file is stale.
#
# This is the whole contract between FCPM and whatever renders a kiosk. It is
# inert: no template syntax, no includes, nothing to resolve. It names no host,
# no port and no address, so the machine serving it can change without this
# file changing. See docs/KIOSK.md.
"""

JS_HEADER = """\
// GENERATED FILE — do not edit. The YAML beside it is canonical.
//
//   python3 bin/build-kiosk.py
//
// WHY THIS FILE EXISTS, AND IT IS NOT A PREFERENCE
// -----------------------------------------------
// The panel opens `brand/idle/index.html` as a local file, from a clone, with
// no server behind it. Measured in Chrome 2026-09-24:
//
//   file:// + fetch('welcome.yml')        -> TypeError: Failed to fetch
//   file:// + <script src="welcome.js">   -> works, repeatedly, with a
//                                           cache-buster on the src
//
// A `file://` page has an opaque origin, so fetch and XHR are both refused
// and no header can permit it. That makes the YAML unreadable by the one
// consumer this artifact has — which is why the same content is emitted a
// second time as an assignment a script tag can carry.
//
// This is TRANSPORT, not a second source of truth. It is generated from the
// same `kiosk/content.yml` in the same run and carries the SAME `revision`,
// copied rather than recomputed, so the two cannot disagree about what they
// describe. Read `welcome.yml` if you have a choice; read this if you are a
// browser looking at a file path.
//
// One assignment and nothing else. No logic, no fetch, no side effects.
"""


def load(path):
    text = path.read_text()
    return yaml.safe_load(text) or {}


def read_sources():
    missing = [p.name for p in (CONTENT,) if not p.exists()]
    if missing:
        raise SystemExit("error: %s is missing" % ", ".join(missing))
    return {
        "content": load(CONTENT),
        "org": load(DATA / "org.yml"),
        "wifi": load(DATA / "wifi.yml"),
        "checkin": load(DATA / "checkin.yml"),
    }


def panel_from_wifi(src, panel):
    """The Wi-Fi panel. SSID from wifi.yml, never retyped, never unconfirmed."""
    network = src["wifi"].get("network") or {}
    ssid = network.get("ssid")
    if not ssid:
        raise SystemExit("error: site/_data/wifi.yml has no network.ssid")

    # The same gate make-wifi-qr.py enforces, for the same reason: a confident
    # wrong network name is worse than an absent one.
    if not network.get("confirmed"):
        raise SystemExit(
            "error: site/_data/wifi.yml says confirmed: false, so the network name is\n"
            "       still a guess. The kiosk will not name a guessed network to a\n"
            "       guest standing in front of it. Confirm the name with FCPM and set\n"
            "       confirmed: true."
        )

    out = {"panel": panel["panel"], "say": ssid}

    # The note is taken from content.yml ONLY, and does not fall back to
    # `poster.note` even though that field is right there and says almost the
    # right thing.
    #
    # It says "point your camera at the code and tap the notification", which
    # is true of the POSTER, because the poster has a code on it. The kiosk
    # does not and cannot — the Wi-Fi QR encodes the password and is
    # gitignored. Inheriting that sentence puts a screen in the lobby telling a
    # guest to scan something that is not on it, which reads as a broken kiosk
    # rather than as a missing feature, and the guest has no way to know the
    # difference. Caught by generating the file and reading it, 2026-09-23.
    if panel.get("note"):
        out["note"] = " ".join(panel["note"].split())
    return out


def panel_from_checkin(src, panel):
    """The check-in panel, carrying the committed QR."""
    checkin = src["checkin"]
    url = checkin.get("url")
    if not url:
        raise SystemExit("error: site/_data/checkin.yml has no url")

    if not (REPO / CHECKIN_QR).exists():
        raise SystemExit(
            "error: %s is missing.\n"
            "       A kiosk panel that promises a code and renders a broken image is\n"
            "       worse than one that does not mention it. Regenerate it with:\n"
            "           python3 site/bin/make-qr.py" % CHECKIN_QR
        )

    out = {
        "panel": panel["panel"],
        # Shown as readable text beside the code, the way the printed poster
        # does it — a camera that will not focus still leaves somebody
        # something to type.
        # Scheme stripped and the trailing slash KEPT, so this string is
        # character-for-character what the printed poster shows
        # (`{{ ci.url | remove: 'https://' }}`). Two surfaces in one building
        # disagreeing about a URL is how somebody decides one of them is stale.
        "say": url.split("://", 1)[-1],
        "qr": {
            "image": CHECKIN_QR,
            "encodes": url,
            "alt": "QR code linking to the check-in page",
        },
    }
    if panel.get("note"):
        out["note"] = " ".join(panel["note"].split())
    return out


SOURCES = {"wifi": panel_from_wifi, "checkin": panel_from_checkin}


def build_panel(src, panel):
    if not panel.get("panel"):
        raise SystemExit("error: every panel needs a `panel:` heading")
    name = panel.get("from")
    if name is None:
        # A literal panel. Written in content.yml, sourced nowhere.
        if not panel.get("say"):
            raise SystemExit(
                "error: panel %r has neither `from:` nor `say:`, so it says nothing"
                % panel.get("panel")
            )
        out = {"panel": panel["panel"], "say": " ".join(panel["say"].split())}
        if panel.get("note"):
            out["note"] = " ".join(panel["note"].split())
        return out

    if name not in SOURCES:
        raise SystemExit(
            "error: panel %r wants `from: %s`, which is not a source.\n"
            "       Known sources: %s"
            % (panel.get("panel"), name, ", ".join(sorted(SOURCES)))
        )
    return SOURCES[name](src, panel)


def build(src):
    content = src["content"]
    org = src["org"]

    panels = content.get("panels") or []
    if not panels:
        raise SystemExit("error: kiosk/content.yml lists no panels")

    artifact = {
        "place": org.get("name"),
        "room": content.get("room"),
        "greeting": " ".join((content.get("greeting") or "").split()),
        "panels": [build_panel(src, p) for p in panels],
    }
    if not artifact["place"]:
        raise SystemExit("error: site/_data/org.yml has no name")
    return artifact


def revision(body):
    """A short digest of the content, for a kiosk to poll.

    THIS IS THE ONE THING THAT LETS AN UPDATE BOUNCE A SCREEN
    --------------------------------------------------------
    Her ask, 2026-09-23: *"I want it to be able to be live... at minimum that
    an update can bounce it."* A renderer that live-reads the file already
    shows an edit to anybody who presses refresh — but a kiosk on a wall has
    nobody to press refresh, so the page has to be able to notice by itself.

    It needs something to compare, and the obvious candidate is the wrong one.
    **A timestamp cannot do this job**: it changes on every regeneration
    whether or not anything was said differently, so a screen watching it
    reloads on noise and nobody can tell current from merely recent. That is
    why there isn't one — see the module header.

    A digest of the content changes **when, and only when, the content
    changes.** So a kiosk can poll this field, compare it to the one it
    rendered with, and reload when they differ. Same shape as an ETag, and for
    the same reason.

    Short on purpose: twelve hex characters is plenty to notice a change, and
    somebody reading the file over somebody's shoulder can compare it by eye.
    """
    return hashlib.sha256(body.encode("utf-8")).hexdigest()[:12]


def render(artifact):
    body = yaml.safe_dump(
        artifact,
        sort_keys=False,
        default_flow_style=False,
        allow_unicode=True,
        # One line per value, never folded. A folded string reflows its
        # continuation lines when any word earlier in it changes, so a
        # one-word edit shows up as a four-line diff and reviewing this file
        # stops being cheap. Long lines are the better trade for a generated
        # artifact that gets read in a diff more often than in an editor.
        width=4096,
    )
    # Computed over the body and then written above it, so the digest covers
    # exactly the content and never itself. First field in the file because a
    # poller wants it without parsing the rest.
    return HEADER + "\n" + "revision: %s\n" % revision(body) + body


def render_js(artifact, rev):
    """The same content as an assignment a `file://` script tag can carry.

    `rev` is PASSED IN rather than recomputed, so the two artifacts cannot
    disagree about which revision they are. The YAML body is the thing the
    digest is taken over; this file quotes the answer.
    """
    data = {"revision": rev}
    data.update(artifact)
    body = json.dumps(data, indent=2, ensure_ascii=False, sort_keys=False)
    return JS_HEADER + "window.%s = %s;\n" % (GLOBAL, body)


def outputs(artifact):
    """Both artifacts, from one build, sharing one revision."""
    body = yaml.safe_dump(
        artifact,
        sort_keys=False,
        default_flow_style=False,
        allow_unicode=True,
        width=4096,
    )
    rev = revision(body)
    return HEADER + "\n" + "revision: %s\n" % rev + body, render_js(artifact, rev)


def check_no_secrets(text, password=None):
    """Refuse to emit anything that leaks the guest password.

    Two separate guards, because they fail differently. The asset check is
    structural and always runs. The password check only fires when the
    generator happens to have been handed one — which is exactly the case
    where a future edit could start interpolating it without anybody noticing.
    """
    if FORBIDDEN_ASSET in text:
        raise SystemExit(
            "error: the artifact references %s, which is gitignored because it\n"
            "       encodes the guest password in decodable form. A kiosk cannot\n"
            "       carry it. The printed poster at /wifi/poster/ is how the\n"
            "       password reaches a guest." % FORBIDDEN_ASSET
        )
    if password and password in text:
        raise SystemExit(
            "error: the Wi-Fi password appears in the artifact. It must not: this\n"
            "       repository is public. Nothing should be reading\n"
            "       FCPM_WIFI_PASSWORD here."
        )
    for line in text.splitlines():
        # Strip a leading quote so a JSON key ("password": …) is caught too, not
        # just a YAML one. The JS transport carries the same content and needs
        # the same guard.
        key = line.strip().lower().lstrip('"\'').replace('"', "").replace("'", "")
        if key.startswith(("password:", "passphrase:", "secret:", "psk:")):
            raise SystemExit("error: the artifact carries a secret-looking key: %r" % line.strip())


def committed(path):
    """True if git tracks this path. A consumer needs it committed to read it."""
    try:
        out = subprocess.run(
            ["git", "ls-files", "--error-unmatch", str(path.relative_to(REPO))],
            cwd=REPO,
            capture_output=True,
            text=True,
        )
        return out.returncode == 0
    except OSError:  # pragma: no cover - no git, not this script's problem
        return True


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build the kiosk artifact.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="write nothing; exit non-zero if the committed artifact is stale",
    )
    parser.add_argument(
        "--print", dest="show", action="store_true", help="write nothing; print it"
    )
    args = parser.parse_args(argv)

    artifact = build(read_sources())
    text, js = outputs(artifact)

    # Both get the guard. The JS carries the same content, so a leak would
    # leak twice, and the guard that only covers the canonical file is the
    # guard that misses the one a browser actually loads.
    password = os.environ.get("FCPM_WIFI_PASSWORD")
    check_no_secrets(text, password)
    check_no_secrets(js, password)

    wanted = ((ARTIFACT, text), (ARTIFACT_JS, js))

    if args.show:
        for path, body in wanted:
            sys.stdout.write("==> %s\n" % path.relative_to(REPO))
            sys.stdout.write(body)
            sys.stdout.write("\n")
        return 0

    if args.check:
        stale = []
        for path, body in wanted:
            if not path.exists():
                stale.append("%s does not exist" % path.relative_to(REPO))
            elif path.read_text() != body:
                stale.append("%s is stale" % path.relative_to(REPO))
        if stale:
            print(
                "error: %s.\n"
                "       Its sources have changed since it was generated.\n"
                "       Run: python3 bin/build-kiosk.py" % "; ".join(stale),
                file=sys.stderr,
            )
            return 1
        print(
            "%s and %s are current"
            % (ARTIFACT.relative_to(REPO), ARTIFACT_JS.relative_to(REPO))
        )
        return 0

    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    for path, body in wanted:
        path.write_text(body)
        print("Wrote %s" % path.relative_to(REPO))
        if not committed(path):
            print("  NOT YET COMMITTED. A kiosk reads it off disk, so commit it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
