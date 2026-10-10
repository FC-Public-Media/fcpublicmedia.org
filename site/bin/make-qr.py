#!/usr/bin/env python3
"""Write site/assets/img/check-in-qr.svg (committed) from `url:` in site/_data/checkin.yml.

Run by hand when that URL changes: pip install qrcode && python3 site/bin/make-qr.py
"""

import os
import re
import sys

OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "img", "check-in-qr.svg")
CONFIG = os.path.join(os.path.dirname(__file__), "..", "_data", "checkin.yml")


def read_url():
    """Pull `url:` out of site/_data/checkin.yml without needing a YAML parser."""
    with open(CONFIG) as f:
        for line in f:
            match = re.match(r"^url:\s*(\S+)", line)
            if match:
                return match.group(1)
    raise SystemExit("No `url:` found in site/_data/checkin.yml")


def main():
    try:
        import qrcode
        import qrcode.image.svg
    except ImportError:
        raise SystemExit("qrcode is not installed. Run: pip install qrcode")

    url = read_url()

    # Level H survives ~30% obscured, which leaves room for the clock hands drawn over it.
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
