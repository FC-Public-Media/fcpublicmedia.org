# `site/bin/make-qr.py`

Moved out of the file. Unreviewed.

## 1

Above `import os`

Generate the check-in QR code as an SVG.

Run this only when the check-in URL changes:

    pip install qrcode
    python3 site/bin/make-qr.py

The output is committed, so building the site needs no QR library and no
network. This is the one script here that is not standard-library-only, which
is why it runs by hand rather than in CI.

SVG rather than PNG on purpose: the poster gets printed and taped to a wall,
and a vector code stays sharp at whatever size it ends up.

## 2

Above `code = qrcode.QRCode(`

Error correction H tolerates roughly 30% of the code being obscured,
which is what you want on something taped to a wall in a studio.
