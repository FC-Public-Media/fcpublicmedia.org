#!/usr/bin/env python3
"""Generate the guest Wi-Fi QR code as an SVG.

    python3 script/make-wifi-qr.py                  # prompts for the password
    FCPM_WIFI_PASSWORD='…' python3 script/make-wifi-qr.py

Run it when the network name or the password changes. Reads the network from
`site/_data/wifi.yml`; the password never appears in that file or in this one.

THE OUTPUT IS GITIGNORED, ON PURPOSE
------------------------------------
`site/assets/img/wifi-qr.svg` is not committed, and this is the one way this script
differs from `make-qr.py` next door — that one commits its output so the build
needs no QR library.

A QR code is not encryption. It is a font. Anyone can point a phone at the
committed SVG and read the password out of a public repository, so committing
it and pasting the password into a data file are the same act with different
numbers of steps. The poster is meant to hang in the lobby, where the audience
is people already in the building; fcpublicmedia.org has a rather larger one.

So: staff runs this, prints the page, tapes it up. Nothing is published. See
the header of `site/_data/wifi.yml` for what it would take to change that, and why
it is FCPM's decision rather than a convenience.
"""

import getpass
import os
import re
import sys

HERE = os.path.dirname(__file__)
OUT = os.path.join(HERE, "..", "site", "assets", "img", "wifi-qr.svg")
CONFIG = os.path.join(HERE, "..", "site", "_data", "wifi.yml")

# In a WIFI: payload these five characters are structure, not text. An SSID of
# `Carnegie;Guest` unescaped produces a working code for a network called
# `Carnegie` — it scans, it joins nothing, and nobody can tell by looking.
#
# The backslash is in the class because it is the escape character itself: a
# password containing one has to arrive as a doubled pair or the reader eats
# it and the next character with it. Leaving it out is the easy version of
# this bug and it only shows up on the one password that has a backslash.
SPECIAL = re.compile(r'([\\;,:"])')

# A value that is entirely hex digits is read as raw bytes rather than as text
# unless it is quoted. Rare, and it fails the same silent way.
HEX_ONLY = re.compile(r"\A[0-9A-Fa-f]+\Z")


def escape(value):
    return SPECIAL.sub(r"\\\1", value)


def field(value):
    """Escape, and quote if the value would otherwise be read as hex."""
    if value and HEX_ONLY.match(value):
        return '"%s"' % escape(value)
    return escape(value)


def read_config():
    try:
        import yaml
    except ImportError:
        raise SystemExit("PyYAML is not installed. Run: pip install pyyaml")
    with open(CONFIG) as handle:
        return yaml.safe_load(handle)


def payload(network, password):
    """Build the WIFI: URI. See https://github.com/zxing/zxing/wiki/Barcode-Contents"""
    security = (network.get("security") or "wpa").lower()
    kind = {"wpa": "WPA", "wep": "WEP", "open": "nopass"}.get(security)
    if kind is None:
        raise SystemExit("Unknown security %r in site/_data/wifi.yml — use wpa, wep, or open" % security)

    parts = ["WIFI:", "T:%s;" % kind, "S:%s;" % field(network["ssid"])]
    if kind != "nopass":
        parts.append("P:%s;" % field(password))
    if network.get("hidden"):
        parts.append("H:true;")
    parts.append(";")
    return "".join(parts), kind


def main():
    try:
        import qrcode
        import qrcode.image.svg
    except ImportError:
        raise SystemExit("qrcode is not installed. Run: pip install qrcode")

    config = read_config()
    network = config["network"]

    if not network.get("confirmed"):
        raise SystemExit(
            "site/_data/wifi.yml says confirmed: false, so the network name is still a\n"
            "guess and this will not generate a poster from it. A printed code with\n"
            "the wrong SSID is worse than no code — it scans, and joins nothing.\n"
            "Confirm the name with FCPM, then set confirmed: true."
        )

    open_network = (network.get("security") or "wpa").lower() == "open"
    password = ""
    if not open_network:
        password = os.environ.get("FCPM_WIFI_PASSWORD") or ""
        if not password:
            # Prompted rather than taken as an argument: an argument lands in
            # shell history and in `ps` output for every user on the machine.
            password = getpass.getpass("Wi-Fi password for %r: " % network["ssid"])
        if not password:
            raise SystemExit("No password given. Set security: open if the network really is open.")

    data, kind = payload(network, password)

    # H tolerates roughly 30% of the code being obscured, which is what you
    # want on something taped to a wall in a studio. Same reasoning as
    # make-qr.py, and the same value.
    code = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=2,
    )
    code.add_data(data)
    code.make(fit=True)

    image = code.make_image(image_factory=qrcode.image.svg.SvgPathImage)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    image.save(OUT)

    # Deliberately does not print the payload: it contains the password, and
    # the terminal it would land in has scrollback.
    print("Wrote %s" % os.path.normpath(OUT))
    print("  network: %s (%s)" % (network["ssid"], kind))
    print("  modules: %dx%d" % (code.modules_count, code.modules_count))
    print("")
    print("  This file is gitignored. Print /wifi/poster/ locally; do not commit it.")


if __name__ == "__main__":
    sys.exit(main())
