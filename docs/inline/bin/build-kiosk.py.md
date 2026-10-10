# `bin/build-kiosk.py`

Moved out of the file. Unreviewed.

## 1

Above `import argparse`

Build the kiosk artifact from what this repository already knows.

    python3 bin/build-kiosk.py            write kiosk/welcome.yml and welcome.js
    python3 bin/build-kiosk.py --check    fail if either committed file is stale
    python3 bin/build-kiosk.py --print    write nothing, show both

`kiosk/content.yml` is the editorial half — the greeting, the room, the panel
wording. The facts come from `site/_data/`. This script joins them and writes
`kiosk/welcome.yml`, which is committed and canonical, plus `kiosk/welcome.js`
which carries the same content for a panel that cannot read the YAML — see
`JS_HEADER` below for the measurement that forced it.

WHY GENERATED AND NOT HAND-WRITTEN
----------------------------------
Because the alternative is typing the SSID twice.

`site/_data/wifi.yml` owns the network name. It carries a `confirmed:` gate and
a long note recording that this network has, at least once, simply not been
there. A hand-written kiosk file would hold a second copy of that name with
none of that context attached, and the two would agree right up until somebody
changed one of them.

A kiosk is the worst possible place for that drift, which is the argument for
the generator rather than a style preference. A stale poster is read by somebody
who can walk away and ask. A stale kiosk is a screen at the desk confidently
naming a network to a guest who is standing in front of it, and they cannot
tell "the screen is wrong" from "the Wi-Fi is broken" — so they conclude the
second one. Same failure the poster page warns about, one step closer to the
guest.

So the generator also inherits the gate: an unconfirmed SSID refuses to build,
exactly as `site/bin/make-wifi-qr.py` refuses to print one.

WHAT THE ARTIFACT DELIBERATELY DOES NOT CONTAIN
-----------------------------------------------
**The Wi-Fi password, or any QR encoding it.** This repository is public. A
Wi-Fi QR is not encryption — it is a font — so a committed one publishes the
password to everyone rather than to the people in the room. `wifi-qr.svg` is
gitignored for that reason and `check()` below refuses to reference it.

**A hostname, a port, or an address for itself.** Those belong to whatever is
serving the artifact, not to the artifact. Today that is station-node on the
LAN; eventually it is an FCPM machine. The point of leaving them out is that
when that changes, *this file does not* — only who renders it.

`encodes:` is the one URL here, and it is content rather than configuration:
it is where the QR points, and the printed poster shows it as human-readable
fallback for a camera that will not cooperate. Not the kiosk's own address.

**A timestamp.** A generated file that stamps itself churns on every run, and
then nobody can tell whether what is on disk is current or merely recent.
`--check` answers that question properly, by rebuilding and comparing.

WHAT IT DOES CONTAIN, SO A SCREEN CAN NOTICE AN UPDATE
-----------------------------------------------------
`revision:` — a short digest of the content, and the thing a kiosk polls so
that an update can bounce it without anybody pressing refresh. It changes when
the content changes and not otherwise, which is the property a timestamp does
not have. See `revision()`.

## 2

Above `GLOBAL = "FCPM_KIOSK"`

The global the JS transport assigns. Named rather than anonymous so a panel
can check whether it loaded at all.

## 3

Above `CHECKIN_QR = "site/assets/img/check-in-qr.svg"`

The committed check-in QR. A plain https URL and nothing else, which is why
this one is allowed to travel and the Wi-Fi one is not.

## 4

Above `if not network.get("confirmed"):`

The same gate make-wifi-qr.py enforces, for the same reason: a confident
wrong network name is worse than an absent one.

## 5

Above `if panel.get("note"):`

The note is taken from content.yml ONLY, and does not fall back to
`poster.note` even though that field is right there and says almost the
right thing.

It says "point your camera at the code and tap the notification", which
is true of the POSTER, because the poster has a code on it. The kiosk
does not and cannot — the Wi-Fi QR encodes the password and is
gitignored. Inheriting that sentence puts a screen in the lobby telling a
guest to scan something that is not on it, which reads as a broken kiosk
rather than as a missing feature, and the guest has no way to know the
difference. Caught by generating the file and reading it, 2026-09-23.

## 6

Above `"say": url.split("://", 1)[-1],`

Shown as readable text beside the code, the way the printed poster
does it — a camera that will not focus still leaves somebody
something to type.
Scheme stripped and the trailing slash KEPT, so this string is
character-for-character what the printed poster shows
(`{{ ci.url | remove: 'https://' }}`). Two surfaces in one building
disagreeing about a URL is how somebody decides one of them is stale.

## 7

Above `if hasattr(value, "isoformat"):`

An ISO 8601 time that says which zone it is in, or a refusal.

YAML reads `2026-08-11T18:00:00-06:00` as a datetime and JSON leaves it a
string; both come out the same. A time with no offset is read by a browser
as the viewer's own zone, which on a studio screen is merely wrong, and
silently (site/_data/classes.yml says the same about the website).

## 8

Above `calendar = src.get("calendar") or {}`

The class on now, or next. The schedule, never the verdict.

WHICH CLASS IS ON IS DECIDED BY THE SCREEN'S CLOCK, NOT HERE
------------------------------------------------------------
This carries the schedule and the two windows; the renderer asks
`pickSession` in site/assets/js/classes.js, which is what the homepage and
the check-in page ask, so a screen and the website can never disagree about
whether a class is on. `classes` below is exactly the config that function
takes. Deciding "now" here would stamp the artifact with the time it was
built, and it would churn every minute (see `revision()`).

The schedule comes from where the site takes it, in the same order
(site/_includes/class-config.html): calendar.json when it has sessions,
which the media node is to keep current (docs/KIOSK.md), and
classes.yml when it does not. A change there changes `revision`, and a
screen reloads.

ONLY WHAT A STRANGER MAY READ. Title, room, times and summary: the fields
the public website already shows. Nothing else in a session is copied,
whatever the calendar grows, because this repository is public.

## 9

Above `out_sessions.sort(`

By the instant, not the string: calendar.json is in UTC and classes.yml
in local time, whose offset moves at daylight saving.

## 10

Above `"takeover": bool(panel.get("takeover", True)),`

While a class is soon or on, this panel is the screen: the main area
on the rolling TV, the top of the welcome desk. Otherwise it is one
line, the next class. Autumn, 2026-09-26.

## 11

Above `return hashlib.sha256(body.encode("utf-8")).hexdigest()[:12]`

A short digest of the content, for a kiosk to poll.

THIS IS THE ONE THING THAT LETS AN UPDATE BOUNCE A SCREEN
--------------------------------------------------------
Her ask, 2026-09-23: *"I want it to be able to be live... at minimum that
an update can bounce it."* A renderer that live-reads the file already
shows an edit to anybody who presses refresh — but a kiosk on a wall has
nobody to press refresh, so the page has to be able to notice by itself.

It needs something to compare, and the obvious candidate is the wrong one.
**A timestamp cannot do this job**: it changes on every regeneration
whether or not anything was said differently, so a screen watching it
reloads on noise and nobody can tell current from merely recent. That is
why there isn't one — see the module header.

A digest of the content changes **when, and only when, the content
changes.** So a kiosk can poll this field, compare it to the one it
rendered with, and reload when they differ. Same shape as an ETag, and for
the same reason.

Short on purpose: twelve hex characters is plenty to notice a change, and
somebody reading the file over somebody's shoulder can compare it by eye.

## 12

Above `width=4096,`

One line per value, never folded. A folded string reflows its
continuation lines when any word earlier in it changes, so a
one-word edit shows up as a four-line diff and reviewing this file
stops being cheap. Long lines are the better trade for a generated
artifact that gets read in a diff more often than in an editor.

## 13

Above `return HEADER + "\n" + "revision: %s\n" % revision(body) + body`

Computed over the body and then written above it, so the digest covers
exactly the content and never itself. First field in the file because a
poller wants it without parsing the rest.

## 14

Above `data = {"revision": rev}`

The same content as an assignment a `file://` script tag can carry.

`rev` is PASSED IN rather than recomputed, so the two artifacts cannot
disagree about which revision they are. The YAML body is the thing the
digest is taken over; this file quotes the answer.

## 15

Above `if FORBIDDEN_ASSET in text:`

Refuse to emit anything that leaks the guest password.

Two separate guards, because they fail differently. The asset check is
structural and always runs. The password check only fires when the
generator happens to have been handed one — which is exactly the case
where a future edit could start interpolating it without anybody noticing.

## 16

Above `key = line.strip().lower().lstrip('"\'').replace('"', "").replace("'", "")`

Strip a leading quote so a JSON key ("password": …) is caught too, not
just a YAML one. The JS transport carries the same content and needs
the same guard.

## 17

Above `password = os.environ.get("FCPM_WIFI_PASSWORD")`

Both get the guard. The JS carries the same content, so a leak would
leak twice, and the guard that only covers the canonical file is the
guard that misses the one a browser actually loads.

## 18

Above `path.write_text(body, encoding="utf-8", newline="\n")`

UTF-8 and LF on every platform. Left to the default, Windows writes
its code page and CRLF, and the em dashes arrive as mojibake.
