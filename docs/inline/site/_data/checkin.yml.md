# `site/_data/checkin.yml`

Moved out of the file. Unreviewed.

## 1

Above `# The URL the QR code points at. Regenerate the code after changing it:`

Check-in configuration.

The check-in page records visits in the browser's own storage. There is no
server, no account on our side, and nothing is transmitted anywhere.

READ THIS BEFORE RETIRING THE PAPER LOG
---------------------------------------
Device-local history serves the visitor, not the organization. FCPM receives
nothing from a log that lives on someone's phone, and browsers delete this
storage — see README, "Check-in", for both limits and for what a server-side
copy would take.

## 2

Above `url: https://new.fcpublicmedia.org/check-in/`

The URL the QR code points at. Regenerate the code after changing it:
  python3 site/bin/make-qr.py

## 3

Above `location:`

Checking in requires being at the studio. The page asks for location once,
and if the visitor is not there yet it holds the check-in as pending and
finishes it by itself when they arrive.

## 4

Above `latitude: 40.5849119`

Geocoded from the address via OpenStreetMap Nominatim. Worth confirming by
standing at the front door with a phone before this goes live — a few
metres out is fine, a few hundred is not.

## 5

Above `radius_m: 200`

How close counts as "here". 200m covers the building, the parking, and the
street outside without reaching the next block.

## 6

Above `accuracy_slack_m: 100`

Phone fixes are imprecise, especially indoors. A reading is accepted when
distance - accuracy is inside the radius, but only up to this much slack,
so a fix reporting ±3km cannot wave someone through from home.

## 7

Above `recheck_seconds: 300`

How often to re-check while the page is open and visible. Five minutes is
frequent enough to notice an arrival and slow enough not to matter to a
battery. Checks stop entirely when the tab is hidden.

## 8

Above `reasons:`

The paper log asks why someone is here. These prime the same question, and
can be preselected from the URL: /check-in/?reason=Class

## 9

Above `mode: none`

none    — check-ins are recorded without an identity. Works today.
access  — Cloudflare Access protects /check-in/sign-in/ and the page reads
          the verified identity from /cdn-cgi/access/get-identity.

See README, "Check-in / Identity". Note the free Zero Trust plan covers 50
seats, which may be fewer than FCPM has members.
