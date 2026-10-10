# `troves/camera/camera.py`

Moved out of the file. Unreviewed.

## 1

Above `import json`

camera.py                        the console, opened in this host's browser
    camera.py console [--port 8790] [--no-open]
    camera.py state                  one reading, as JSON
    camera.py presets                the curated presets (presets.yml)
    camera.py apply <preset>         set a preset, then read every value back

The console shows everything the camera reports over USB and lets you set
everything it lets us set. The operator pages are built on it: /presets is a
page of buttons, each a curated set of settings (presets.yml), pressed and
then checked. Both are served on 127.0.0.1 only; nothing outside this host can
reach them.

One thread owns the camera. It finds it, reads every property about once a
second, and runs one command at a time from a queue, so a camera pulled out
mid-read costs one failed reading and never the web server. When the camera
comes back it is found again.

Needs comtypes and pyyaml:
    uv run --no-project --python 3.12 --with comtypes --with pyyaml camera.py
`fcpm camera` does that.

## 2

Above `PROPS = {`

What each property is, as far as it has been measured (docs/troves/camera/README.md). Units say
how to show and enter it: "x100" is stored times 100, "fixed16" is
Blackmagic's 5.11 fixed point (value times 2048), "1/x" a shutter speed.

## 3

Above `u = PROPS.get(code, {}).get("unit", "raw")`

A value as a person writes it (3200, 1/48 as 48, 24 fps as 24, ND 2)
to what the camera stores.
