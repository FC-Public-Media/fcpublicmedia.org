# `site/bin/sync-nonprofits.py`

Moved out of the file. Unreviewed.

## 1

Above `import argparse`

WHY THIS EXISTS
---------------
Nonprofits pay half. Today there is no way to establish that anybody actually
is one until after they have paid, so the sequence has been: the organization
picks a tier, staff notice, staff correct it, and somebody posts a cheque back.
Worse, a nonprofit that knows about the rate but cannot claim it up front tends
to just wait — which means the discount, which exists to bring them in, is
keeping them out.

The catch is that "prove you are a nonprofit" normally means asking somebody to
find their IRS determination letter. Nobody has that to hand. So instead of
asking them to prove it, this looks them up: the IRS publishes the whole list,
and an organization in Larimer County can pick their own name off it.

That is not a security control and is not meant to be one. It is a way of
answering "which organization?" with an EIN attached, so staff have something
to check rather than a free-text box, and so the right price can be shown
BEFORE anybody pays.

WHAT THE DATA IS
----------------
The Exempt Organizations Business Master File, published by the IRS as four
regional CSVs. Colorado is in region 3, which is around a million rows and
roughly 150 MB, so it is streamed and filtered rather than held in memory.

Filtered to:
  * STATE  == CO and a ZIP in Larimer County
  * SUBSECTION == 03   — 501(c)(3) specifically, not every exempt body
  * STATUS == 01       — unconditional exemption, so revoked ones are gone

That comes to about two thousand organizations and a hundred kilobytes, which
is small enough to hand to a browser.

WHAT IT IS NOT
--------------
Not every nonprofit. An organization can be legitimate and absent — newly
registered, filed under a parent's EIN, a fiscal sponsorship, a chapter of a
national body, or simply outside these ZIP codes. So the page that uses this
must always offer "my organization isn't listed" and route that to a person.
A lookup that becomes a gate would be worse than no lookup at all.

## 2

Above `SOURCE = "https://www.irs.gov/pub/irs-soi/eo3.csv"`

Region 3 of the Business Master File. Colorado lives here; the other three
regions are checked by hand rather than guessed at, and if the IRS
reorganises them this is the line that has to change.

## 3

Above `ZIPS = {`

Larimer County, which is the service area rather than the city limits —
Loveland, Estes Park, Wellington and Berthoud are all people who drive to
Fort Collins to use a studio. Windsor straddles the county line and is
included on the same reasoning.

## 4

Above `request = urllib.request.Request(url, headers={"User-Agent": "fcpm-sync"})`

Stream the CSV rather than reading it whole.

The file is around 150 MB. Holding it in memory works on a laptop and is a
rude thing to do on a small runner, and there is no reason to: every row is
examined once and nearly all of them are discarded.

## 5

Above `last = None`

Download it, and expect the download to fail sometimes.

A hundred and fifty megabytes over one connection drops often enough to
matter — the first run of this script died on an IncompleteRead partway
through. That is not a reason to fail a build, it is a reason to start
again, so each attempt restarts from the top rather than trying to resume.

The rows are collected here rather than yielded, because a generator that
fails halfway has already handed out half a list and there is no taking it
back. Whatever this returns is a whole download or an exception.

## 6

Above `return " ".join(name.split()).strip()`

The master file is upper case throughout. Title case reads better in a
list somebody is scanning, and the EIN is what actually identifies them.

## 7

Above `out.sort(key=lambda entry: (entry[1], entry[0]))`

Sorted by name so the file diffs sanely: without this, an unrelated
reordering upstream would look like every organization changed.

## 8

Above `print("no organizations matched — refusing to overwrite", file=sys.stderr)`

Refusing to write an empty file rather than replacing a good list
with nothing. A layout change upstream would otherwise silently
empty the picker, and the page would look like it worked.
