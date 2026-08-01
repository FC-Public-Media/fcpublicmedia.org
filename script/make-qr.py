#!/usr/bin/env python3
"""Generate the check-in QR code as an SVG.

Run this only when the check-in URL changes:

    pip install qrcode
    python3 script/make-qr.py

The output is committed, so building the site needs no QR library and no
network. This is the one script here that is not standard-library-only, which
is why it runs by hand rather than in CI.

SVG rather than PNG on purpose: the poster gets printed and taped to a wall,
and a vector code stays sharp at whatever size it ends up.
"""

import os
import re
import sys

OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "img", "check-in-qr.svg")
CONFIG = os.path.join(os.path.dirname(__file__), "..", "_data", "checkin.yml")


def read_url():
    """Pull `url:` out of _data/checkin.yml without needing a YAML parser."""
    with open(CONFIG) as f:
        for line in f:
            match = re.match(r"^url:\s*(\S+)", line)
            if match:
                return match.group(1)
    raise SystemExit("No `url:` found in _data/checkin.yml")


def main():
    try:
        import qrcode
        import qrcode.image.svg
    except ImportError:
        raise SystemExit("qrcode is not installed. Run: pip install qrcode")

    url = read_url()

    # Error correction H tolerates roughly 30% of the code being obscured,
    # which is what you want on something taped to a wall in a studio.
    code = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=2,
    )
    code.add_data(url)
    code.make(fit=True)

    image = code.make_image(image_factory=qrcode.image.svg.SvgPathImage)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    image.save(OUT)

    print("Wrote %s" % os.path.normpath(OUT))
    print("  encodes: %s" % url)
    print("  modules: %dx%d" % (code.modules_count, code.modules_count))


if __name__ == "__main__":
    sys.exit(main())
