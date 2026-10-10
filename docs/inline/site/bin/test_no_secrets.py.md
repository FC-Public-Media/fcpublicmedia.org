# `site/bin/test_no_secrets.py`

Moved out of the file. Unreviewed.

## 1

Above `import pathlib`

Nothing secret-shaped may reach the built site, or the repository.

WHY THIS IS NOT PARANOIA
------------------------
The restricted Stripe key is named PUBLIC_STRIPE_API_KEY, where "public" names
who causes it to be used — /checkout authenticates nobody, so a stranger makes
that key act — and therefore how tightly it is scoped. It is a good name and
it is about blast radius, not visibility.

It is also a name somebody will one day read quickly, take to mean "safe to
expose", and put in a template. That is a reasonable misreading of a name that
is doing something subtler than usual, and no amount of comment prevents it.
So the guarantee is mechanical rather than documentary: whatever anybody
believed, a secret key does not reach the built site.

It is deliberately mechanical and looks at OUTPUT rather than at intent. It
does not care how a key got there: interpolated by Liquid, pasted into a data
file, hardcoded in a script, committed to a config. If a string shaped like a
Stripe secret is in _site or in the tracked source, the build fails.

WHAT COUNTS AS SECRET-SHAPED
----------------------------
    rk_live_…  rk_test_…   restricted
    sk_live_…  sk_test_…   secret
    sk_org_…               organization

`pk_live_` and `pk_test_` are absent from that list on purpose. Publishable
keys are meant to be in the page — refusing them would make this check
something people switch off, and a check people switch off protects nothing.

THE GUEST WI-FI PASSWORD IS THE SAME PROBLEM WEARING A COSTUME
--------------------------------------------------------------
A Wi-Fi QR code encodes the password as plain text. A QR is not encryption,
it is a font — `site/assets/img/wifi-qr.svg` committed here would publish the
guest password to anyone who points a phone at a public repository, and it
would not look like publishing a password while you did it. That is exactly
the misreading this file exists to make impossible, so the same mechanical
treatment applies: the generated code is gitignored, and these tests fail if
it, or a `WIFI:` payload, or a password field in `site/_data/wifi.yml`, is ever
tracked.

The poster is meant for the lobby, where everyone reading it is already in
the building. Publishing it to fcpublicmedia.org is a different decision and
FCPM has not made it. See the header of `site/_data/wifi.yml`.

## 2

Above `SOURCE = pathlib.Path(__file__).resolve().parent.parent`

`site/bin/` is inside the Jekyll source, so a path here is relative to the
site rather than to the repository. SITE is the build root; REPO is the node.

## 3

Above `SECRET = re.compile(r"\b(?:rk|sk)_(?:live|test|org)_[A-Za-z0-9]{8,}")`

The underscore after the prefix matters: it is what separates a real key
from prose about one. This very file says "rk_live_…" with an ellipsis
rather than a plausible suffix so that it does not match itself.

## 4

Above `# A Wi-Fi join payload, but only one carrying a key: P: with something in`

Booqable access tokens and Cloudflare/R2 credentials would be just as bad,
but they have no distinctive prefix to match on. The Stripe shapes are the
ones that can be caught mechanically, and catching those is worth doing
even though it is not everything.

## 5

Above `WIFI_KEY = re.compile(r"WIFI:" + r"[^\n]{0,300}?;" + r"P:[^;\n]+;")`

A Wi-Fi join payload, but only one carrying a key: `P:` with something in
it. `WIFI:T:nopass;S:Guest;;` is an open network and discloses nothing, and
prose about the format — which site/_data/wifi.yml and site/wifi/poster.md are full of
— has no payload in it at all.
Assembled rather than written out for the same reason the shapes above use
an ellipsis: spelled in one piece, the pattern's own source is a payload and
this file fails its own check. test_this_file_does_not_trip_its_own_wifi_check
is what keeps that honest.

## 6

Above `WIFI_QR = "site/assets/img/wifi-qr.svg"`

The generated code. Gitignored; this asserts that the gitignore is doing its
job, because a `git add -f` or a rewritten ignore file is silent otherwise.

## 7

Above `result = subprocess.run(`

What git actually has, rather than what is lying around.

Scanning the working tree would trip over _site, node_modules, and any
key somebody has sensibly kept OUT of version control in a scratch file.
The question is what would be published, and git answers that.

## 8

Above `payments = (SOURCE / "_data" / "payments.yml").read_text(encoding="utf-8")`

The specific mistake the naming invites: someone reads
PUBLIC_STRIPE_API_KEY, believes it, and pastes the restricted key
into the field that gets rendered into every page.

## 9

Above `for shape in (`

A scanner that never matches passes every time and proves nothing.
These are not real keys; they are the shape of one.

## 10

Above `if not SITE.exists():`

Not the same guarantee as the tracked-file check, and this is the
one that catches the realistic accident. CI builds from a clean
checkout and so can never have the code — but README, "Deploying to
Cloudflare", documents `npx wrangler deploy` from a local checkout
as the fallback when Actions is unavailable, and it publishes
whatever `_site` happens to contain. Somebody who generated the
poster an hour earlier would ship the password without touching a
file that git can see.

## 11

Above `config = SOURCE / "_data" / "wifi.yml"`

The specific mistake the file invites: somebody finds a config with
an SSID in it, reasonably expects the password next to it, and adds
the field the generator deliberately does not read.

## 12

Above `scheme = "WIFI:"`

A scanner that never matches passes every time and proves nothing.

The scheme is assembled from a name rather than written out, for the
same reason the Stripe shapes above use an ellipsis: a file that
contains a complete example payload fails its own check, and the
obvious fix for that is to weaken the pattern.

## 13

Above `self.assertIsNone(`

Not redundant with the tracked-file sweep: this file is the one most
likely to acquire a literal payload, and the sweep's failure message
would read as a real leak when it was a test fixture.

## 14

Above `for benign in (`

This file, site/_data/wifi.yml and site/wifi/poster.md all discuss the format
at length, and an open network has nothing to disclose. If any of
those tripped it, the check would be switched off within a week.

## 15

Above `for prose in ("rk_live_…", "use the rk_ key", "sk_live_ keys are dangerous", "pk_live_…"):`

The README and several data files discuss rk_live_ and sk_live_ at
length. If those tripped it, the check would be turned off within a
week, which is the failure mode worth designing against.
