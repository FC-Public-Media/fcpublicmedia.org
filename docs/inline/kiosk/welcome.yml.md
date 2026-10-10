# `kiosk/welcome.yml`

Moved out of the file. Unreviewed.

## 1

Above `revision: aea0eb7325bd`

GENERATED FILE — do not edit.

  python3 bin/build-kiosk.py

Edit `kiosk/content.yml` for the wording, or `site/_data/` for the facts,
then regenerate. `bin/build-kiosk.py --check` fails if this file is stale.

This is the whole contract between FCPM and whatever renders a kiosk. It is
inert: no template syntax, no includes, nothing to resolve. It names no host,
no port and no address, so the machine serving it can change without this
file changing. See docs/KIOSK.md.
