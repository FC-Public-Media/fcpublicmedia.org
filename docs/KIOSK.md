# The kiosk

Written 2026-09-23, when station-node built a welcome screen for the studio and
the content turned out to belong here.

A kiosk is a screen on a desk in the FCPM studio. This repository owns **what it
says**. Something else owns **showing it**. That split is the whole design, and
everything below is a consequence of it.

Companion documents: [`NODE.md`](NODE.md) for what else is at the root and why,
and [`STATION.md`](STATION.md) for the station posture this sits inside — in
particular *"the website keeps working the entire time"*, which is why a kiosk
is a new artifact rather than a change to the site.

---

## Why the content lives here and the renderer does not

Autumn's call, 2026-09-23. Station-node had a working kiosk reading a
placeholder file it had invented on its own side, and the correction was that
the file was in the wrong repository:

> The problem is I can't tell them all like the specifics about our SSIDs and
> stuff because it just simply belongs here. Like we're the ones who are
> supposed to be generating this content.

That is not a preference about tidiness. **The guest network name is a fact FCPM
owns**, and it already lives in `site/_data/wifi.yml` with the two things that
make it trustworthy attached to it: a `confirmed:` gate, and a long note
recording that this network has at least once simply not been there. A copy of
that name in another repository is a copy with none of that attached.

The other half, from the same conversation:

> They are worrying about strapping us to station node as if we are a static
> site they can deploy. And so our node-like capabilities will grow up, but they
> are being prototyped by our host here, the station node.

So the arrangement is **guest hosting, and it is temporary by design.**
Station-node renders the kiosk because FCPM had no machine of its own when this
was written — and **that stopped being true the next day**, which is worth
knowing before reading the rest as current. `machines/kiosk-1/` is a Windows box,
stood up 2026-09-23, *"the one who grows up thinking of itself as a media node"*;
the `STATION.md` paragraph this sentence used to cite is now amended rather than
true. So the handover below is not hypothetical, and the property that makes it
free is being cashed in sooner than expected. The
artifact is shaped so that when FCPM does have one, **the artifact does not
change** — only who reads it. Her framing of the endpoint, same day:

> Later, fcpublicmedia.org would do this for itself, and you have your own site
> folder, and so you wouldn't need.

### The coupling is sanctioned, and the artifact still earns its place

Worth answering directly, because it is the obvious objection. Station-node
mounts this repository and can read `site/_data/` itself — Autumn's words: *"they
are able to look at us and our data because we are tightly coupled."* So why
generate a file at all, rather than letting the renderer read `wifi.yml`?

Because **reading our data and knowing what to show are different problems, and
only the first one is solved by access.** `wifi.yml` contains the SSID, the
security mode, the `confirmed:` flag, a poster title, two pieces of poster
wording, and four paragraphs of caveats about publishing passwords. A renderer
given that file has to decide which of those a stranger may see, and that
decision is exactly the one she said belongs here.

The artifact is the decision already made. It is also the reason the password
cannot leak by accident: not because the renderer is careful, but because the
only file it reads has never contained one. **Disposition is settled at
generation, not at render** — which is the rule station-node already runs its own
published surfaces on, arrived at from the other side.

That property is what makes the coupling safe to keep rather than something to
unwind. Tight coupling is fine; an unfiltered read would not be.

---

## The three files

| | |
|---|---|
| `kiosk/content.yml` | **hand-written.** The editorial half: the greeting, the room, the panel wording |
| `kiosk/welcome.yml` | **generated, and committed.** The only file a kiosk reads |
| `bin/build-kiosk.py` | joins the first to `site/_data/` and writes the second |

```sh
python3 bin/build-kiosk.py           # write it
python3 bin/build-kiosk.py --check   # fail if it is stale
python3 bin/build-kiosk.py --print   # write nothing, show it
```

Edit `content.yml`, regenerate, commit both. CI runs `--check`, so a forgotten
regeneration fails a pull request rather than reaching a wall.

### Why it is at the root and not in `site/`

Because a kiosk is not a web page. `site/` is what the public gets; the root is
everything else, and the kiosk is everything else — a screen on the LAN, served
by a node. `NODE.md` has the rule and the reason it exists.

The generator reads *down* into `site/_data/`, which is the sanctioned
direction: **the root reaches into `site/` freely, and `site/` never reaches
up.** Nothing in the Jekyll build knows this directory exists, and nothing
should.

### Why generated rather than hand-written

One reason, and it is enough: **the alternative is typing the SSID twice.**

A hand-written kiosk file would hold a second copy of the network name, and the
two would agree right up until somebody changed one of them. A kiosk is the
worst place for that drift — a stale poster is read by somebody who can walk
away and ask, and a stale kiosk is a screen at the desk naming a network to a
guest standing in front of it. They cannot tell "the screen is wrong" from "the
Wi-Fi is down", so they conclude the second one and stop trying.

The generator therefore also inherits the gate: **an unconfirmed SSID refuses to
build**, exactly as `site/bin/make-wifi-qr.py` refuses to print one.

---

## What the artifact deliberately does not contain

**The Wi-Fi password, or any QR encoding it.** This repository is public. A
Wi-Fi QR is not encryption — it is a font — so a committed one publishes the
password to everyone rather than to the people in the room. `wifi-qr.svg` is
gitignored and the generator refuses to reference it. The printed poster at
`/wifi/poster/` is how the password reaches a guest, and the header of
`site/_data/wifi.yml` explains at length why that distinction is real.

This is the public-repository rule from `STATION.md` doing its job rather than a
special case: *"Only the encrypted-by-specification path gets built here."*

**A hostname, a port, or an address for itself.** Those belong to whatever is
serving the artifact. This is the property that makes the eventual handover
free, and it is tested.

`encodes:` is the one URL in the file, and it is content rather than
configuration: it is where the check-in QR points, and it is shown as readable
text so a camera that will not focus still leaves somebody something to type. It
is character-for-character what the printed poster shows, because two surfaces
in one building disagreeing about a URL is how somebody decides one of them is
stale.

**A timestamp.** A file that stamps itself churns on every run, and then nobody
can tell whether what is on disk is current or merely recent. `--check` answers
that question properly.

---

## Being live: `revision`, and what a renderer owes

Her ask, 2026-09-23:

> I want it to be able to be live, and I don't know by what mechanism. If it's
> a naive refresh for a little while, that's okay, but I don't want to like…
> There is nothing to refresh and find. I'm just trying to make sure that like
> when we do an update that at minimum that an update can bounce it.

**A naive poll is fine. What is not fine is a screen with no way to notice.**

Half of this is already true and costs nothing: station-node's renderer reads
the file per request, so an edit is visible to anybody who reloads the page — no
rebuild, no restart. The gap is that **a kiosk on a wall has nobody to reload
it.**

So the artifact carries `revision:` — a twelve-character digest of its own
content, and the first field in the file so a poller does not have to parse the
rest.

```yaml
revision: 9e55079fd1d7
```

The contract is one sentence: **`revision` changes when the content changes, and
never otherwise.** That is the whole reason it is a digest and not a timestamp.
A timestamp has only half the property — it moves on every regeneration whether
or not anything was said differently, so a screen watching it reloads on noise
and *"is this current?"* stops being answerable. There is a test for each half.

**What a renderer does with it:** poll the artifact on some cheap interval,
compare `revision` to the one currently on screen, reload when they differ.
Nothing more. The interval is the renderer's business and is deliberately not
recorded here — it is a property of the machine serving the kiosk, and this file
knows nothing about that machine on purpose.

**What this repository owes in exchange:** regenerate when content changes, and
commit it. `--check` in CI is what makes that a promise rather than a habit — a
forgotten regeneration fails a pull request, so a revision a kiosk polls is
always one somebody meant.

Two honest limits, neither of them ours to fix:

- **`revision` says the content changed. It does not deliver it.** The file
  still has to reach the machine, today by a pull into the station-node mount.
  Nothing here automates that, and until something does, the freshness bound is
  however often somebody pulls.
- **A digest cannot say what changed**, only that something did. That is the
  right trade for a screen, which redraws the whole thing anyway.

---

## The kiosk shows the check-in code. It does not check anybody in.

This is the one hard rule about behaviour rather than content, and it is worth
stating before somebody adds the obvious convenience.

`site/assets/js/checkin.js` keeps the visitor's details in `localStorage`:
`fcpm.profile` holds name, reason, note **and email**, and `fcpm.checkins` holds
up to 200 past visits. On a personal phone that is exactly right, and it is what
the page promises — *"Your visits stay on your own phone."*

**On a shared browser at a desk it inverts that promise.** Every guest's
check-in accumulates in one profile, and the form prefills the previous guest's
name and email for the next person to read.

So the kiosk displays a QR the guest scans with **their own phone**, and a kiosk
browser must never open `/check-in/` itself. The QR is not a convenience here —
it is the mechanism that makes it their device.

**This is true of that page whether or not a kiosk exists.** A staffer pulling
up `/check-in/` on the desk machine to help somebody has the same problem today.
That belongs in `REVIEW-NOTES.md` as its own finding and is not a kiosk
question; it is recorded here only because the kiosk is what surfaced it.

---

## Panels

A panel is read standing up, from across a room, by somebody who has just walked
in. That is the brief, and it is why a panel is three short fields rather than a
document.

```yaml
- panel: Checking in     # the heading
  say: …                 # the short answer
  note: …                # the smaller qualifying line (optional)
  qr:                    # generated, never hand-written
    image: …             # repo-relative path
    encodes: …           # where it points
    alt: …
```

In `content.yml` a panel is one of two things:

- **`from: <source>`** — the facts come from `site/_data/`, so they cannot drift
  from what the website and the posters say. Sources today are `wifi` and
  `checkin`. The wording is still yours: `say` and `note` override.
- **`say:` / `note:`** — a literal panel, written there, sourced nowhere. For
  things no data file knows, like who to ask for help.

An unknown `from:` is an error rather than an empty panel, because a kiosk that
silently drops a panel is a kiosk nobody notices is broken.

### The Wi-Fi panel does not inherit the poster's wording

Worth its own note, because the first draft got it wrong and the bug was only
caught by generating the file and reading it.

`wifi.poster.note` says *"Point your camera at the code and tap the
notification."* That is true **of the poster**, which has a code on it. The
kiosk has none and cannot. Inheriting that sentence puts a screen in the lobby
telling a guest to scan something that is not on it — which reads as a broken
kiosk rather than a missing feature, and the guest has no way to tell.

So the Wi-Fi panel takes its note from `content.yml` only, and there is a
regression test asserting the fallback stays gone.

---

## What the placeholders are

Three, all marked in `content.yml`, and each one is a sentence somebody in the
building should write rather than an agent:

- **the greeting.** Deliberately *not* borrowed from `org.yml`'s mission
  statement: that is the board president's verbatim wording for the homepage,
  and a greeting is a different job. See `CLAUDE.md`, *"Bryan's wording is
  authoritative"* — reusing his sentence on a screen he has not seen is a
  paraphrase with extra steps.
- **where the Wi-Fi card actually hangs.** "By the desk" is a guess.
- **who a guest should ask.** By role, not by name — people leave and a screen
  does not notice.

## What is not here

- **No second monitor.** Specified below, and waiting on a data source that does
  not exist yet. Nothing here feeds it and no artifact for it has been invented.
- **No media-drop kiosk.** A second kiosk on triple portrait monitors has been
  described. `room:` exists so each screen says where it is rather than
  assuming.

  > **Superseded the day after this was written.** That machine exists and is
  > described: [`../machines/kiosk-1/PROFILE.md`](../machines/kiosk-1/PROFILE.md)
  > — *"It is the box with the three portrait panels. Confirmed rather than
  > inferred."* And something does serve it:
  > [`../brand/idle/index.html`](../brand/README.md), which carries a marked
  > empty element and says of it *"The slot in the idle screen is a slot on this
  > box."*
  >
  > **That slot is what this artifact is for**, and neither side arrived at it by
  > agreement — the panel was built with a hole in it and the content was built
  > with no renderer, independently, and they fit. Whoever wires them should have
  > `#slot` read `welcome.yml` and poll `revision`.
  >
  > Not wired here. Three pieces of work by three hands meet at that seam and
  > which of them owns the join is a coordination call, not a technical one.

---

## The second monitor: the day, and not Microsoft Bookings

The welcome desk has a second screen meant to show current bookings and what is
in use. It is not built. What follows is the shape it has to be, recorded
2026-09-23 so that nobody designs the wrong thing and nobody re-derives the
ruling below.

### Microsoft Bookings is ruled out for intake. Hard break.

Autumn, 2026-09-23:

> Microsoft Bookings is not specifically going to do intake. I think I'm going to
> do it, but we are going to log it into like some database API. So, definitely
> hard breaks on Microsoft Bookings specifically.

**This reverses the direction [`RESERVE-DESIGN.md`](RESERVE-DESIGN.md) points
in**, and that document has not been rewritten — only annotated — so read this
before acting on it. Its reasoning was that Bookings is *"the obvious product and
genuinely close to right"*, and that we should own the form while treating
Microsoft as the system of record behind it. The first half survives: **we own
the form.** The second half is withdrawn. Intake is hers, and it lands in a
database API.

What that costs, and it is worth naming because it was Bookings' best property:
an appointment there *was* a real Exchange calendar entry, so a booking became a
calendar event with nothing having to carry it there. Off that path, **something
has to carry it**, and that something is the sync this monitor waits on.

What it saves is larger. No Graph app registration, no tenant admin, no
permission grant, and no dependence on the unverified question of whether Graph
change notifications cover `bookingBusinesses` at all — which `RESERVE-DESIGN.md`
flagged as unconfirmed and which nobody has confirmed since.

### What the screen actually needs

Also hers, and it is a much smaller ask than "a bookings system":

> I may be mirroring stuff that we have processed and I really only need to show
> one day at a time. So I think we have the live slice. And in fact, if someone
> were booking an appointment speculatively and needed our approval, it would be
> okay for it to show up here too.

Four things follow, and each one makes this cheaper than it first looked:

1. **One day, not a calendar.** The artifact is today's slice. No week view, no
   month, no navigation — a screen nobody touches cannot navigate anyway. This is
   the constraint that makes the whole thing small.
2. **A mirror of what has already been processed**, not a live query against
   anything. Same posture as the five existing syncs: something writes a file,
   the file is the record. So this monitor's dependency is a sync, and the sync's
   dependency is the database API.
3. **Pending is a displayable state, not an error.** A speculative booking
   awaiting approval may appear. So an entry carries a **status** — approved or
   awaiting-approval at minimum — and the renderer distinguishes them visibly. A
   screen that shows a pending slot as confirmed is worse than one that omits it,
   because somebody will plan around it.
4. **It is a second artifact, not more panels.** `welcome.yml` is content that
   changes when somebody edits it; a day slice changes on its own schedule and
   goes stale in hours rather than months. Putting a decaying feed inside the
   evergreen file would mean the whole thing churns, and `revision` would stop
   being a useful signal for either.

### What is deliberately not decided here

**The field names.** There is no source yet, and a schema invented against
imagined data is a schema that will be wrong in the one way that matters. When
the database API exists, the sync's output shape is settled by what it actually
returns.

**The freshness mechanism.** `revision` is the right primitive to reuse and the
polling story is identical, but a day slice has a second problem `welcome.yml`
does not: **it can be correct and still be stale**, because the day rolls over
whether or not anything changed. A digest cannot notice midnight. Whatever is
built needs to say which day it is describing, so a renderer can refuse to show
yesterday rather than showing it confidently.
- **No renderer.** On purpose. This repository produces the artifact and stops.
