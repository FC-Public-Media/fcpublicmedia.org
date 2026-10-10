# `site/bin/make-wifi-qr.py`

Moved out of the file. Unreviewed.

## 1

Above `import getpass`

Generate the guest Wi-Fi QR code as an SVG.

    python3 site/bin/make-wifi-qr.py                  # prompts for the password
    FCPM_WIFI_PASSWORD='…' python3 site/bin/make-wifi-qr.py

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

## 2

Above `SPECIAL = re.compile(r'([\\;,:"])')`

In a WIFI: payload these five characters are structure, not text. An SSID of
`Carnegie;Guest` unescaped produces a working code for a network called
`Carnegie` — it scans, it joins nothing, and nobody can tell by looking.

The backslash is in the class because it is the escape character itself: a
password containing one has to arrive as a doubled pair or the reader eats
it and the next character with it. Leaving it out is the easy version of
this bug and it only shows up on the one password that has a backslash.

## 3

Above `HEX_ONLY = re.compile(r"\A[0-9A-Fa-f]+\Z")`

A value that is entirely hex digits is read as raw bytes rather than as text
unless it is quoted. Rare, and it fails the same silent way.

## 4

Above `password = getpass.getpass("Wi-Fi password for %r: " % network["ssid"])`

Prompted rather than taken as an argument: an argument lands in
shell history and in `ps` output for every user on the machine.

## 5

Above `code = qrcode.QRCode(`

H tolerates roughly 30% of the code being obscured, which is what you
want on something taped to a wall in a studio. Same reasoning as
make-qr.py, and the same value.

## 6

Above `print("Wrote %s" % os.path.normpath(OUT))`

Deliberately does not print the payload: it contains the password, and
the terminal it would land in has scrollback.
