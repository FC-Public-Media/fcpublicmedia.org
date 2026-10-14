#!/usr/bin/env python3
"""Generate the guest Wi-Fi QR code as an SVG.

    python3 site/bin/make-wifi-qr.py                  # prompts for the password
    FCPM_WIFI_PASSWORD='…' python3 site/bin/make-wifi-qr.py

Reads the network from site/_data/wifi.yml. The output carries the password and is gitignored.
See docs/site.md#never-published.
"""

import getpass
import os
import re
import sys

HERE = os.path.dirname(__file__)
OUT = os.path.join(HERE, "..", "assets", "img", "wifi-qr.svg")
CONFIG = os.path.join(HERE, "..", "_data", "wifi.yml")

# Structure characters in a WIFI: payload, backslash included; unescaped, the code joins nothing.
SPECIAL = re.compile(r'([\\;,:"])')

# An all-hex value is read as raw bytes unless quoted.
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
            # Not an argument: that would land in shell history and `ps`.
            password = getpass.getpass("Wi-Fi password for %r: " % network["ssid"])
        if not password:
            raise SystemExit("No password given. Set security: open if the network really is open.")

    data, kind = payload(network, password)

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

    # The payload holds the password, so it is never printed.
    print("Wrote %s" % os.path.normpath(OUT))
    print("  network: %s (%s)" % (network["ssid"], kind))
    print("  modules: %dx%d" % (code.modules_count, code.modules_count))
    print("")
    print("  This file is gitignored. Print /wifi/poster/ locally; do not commit it.")


if __name__ == "__main__":
    sys.exit(main())
