# The camera trove

A camera on a USB cable, as a console that shows and sets everything it reports, and operator pages
built on it, such as one-button presets. Built against the studio's Blackmagic Pocket Cinema Camera
6K Pro (firmware 7.5.1); reading every property and setting ISO are proven on it.

    fcpm camera                        the console, http://127.0.0.1:8790/ (this host only)
    fcpm camera presets                the curated presets; the page is /presets
    fcpm camera apply studio-tungsten  set one, then read every value back
    fcpm camera state                  one reading, as JSON

`ptp.py` sends raw PTP through Windows' own MTP driver (WPD's MTP extension commands): no driver
swap, no Blackmagic software, no administrator; `comtypes` comes through uv. One thread owns the
camera, polls it about once a second (it sends no events), and finds it again after an unplug.
What each property code means, as measured, is `PROPS` in `camera.py`; `D007` to `D00A` are unnamed.

`presets.yml` is one button each, in order: a label, a sentence, and settings as a person says them
(`wb: 3200`, `shutter: 48`, `nd: 2`). Pressing one sets each value, reads all back and says which took.
