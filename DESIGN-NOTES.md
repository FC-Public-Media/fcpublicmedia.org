# Design notes

Open questions worked far enough to be resumed, but deliberately not built.
Each one records what is actually known — from evidence where evidence was
available — so the next session starts from findings rather than from a
transcript.

Nothing here is a commitment. Several of these will turn out to be bad ideas,
and saying so later is cheaper than rediscovering the reasoning.

---

## Members scheduling their own programs

**The question.** Today a member submits a file and staff place it. Could a
member instead pick their own slot — reserving space the way they would book a
studio — with staff approving rather than assembling? Fewer steps, and for
members who do not care where they land, "we'll place it for you" becomes a
feature rather than a limitation.

### What is known

Checked against the live Cablecast API, August 2026.

Cablecast is made by Tightrope Media Systems, who publish API examples at
`github.com/trms`. Where this note says "ask the vendor", it means whoever
FCPM already talks to for Cablecast support.

**Shows and schedule items are separate resources.** A show can exist with no
schedule item attached, and the vendor's own `new-show.mjs` example creates the
show first and schedules it as a second call. So **an upload does not have to
be slated against a draft schedule.** A member could upload, the show record
would exist, and it would air nowhere until somebody scheduled it.

That matters more than it sounds: it means the safe version of this idea is
available without any of the risky parts.

**Gap-finding is computable from public data.** A show carries
`totalRunTime` in seconds and a schedule item carries `runDateTime`, so free
space in a week is start times plus durations. No private API needed to answer
"where could this fit".

**Shows already count their own runs.** `runCount` is on the show record —
32 for the one sampled. That is all-time, whereas `_data/airings.json` is a
365-day window and also carries *last aired*, which `runCount` cannot answer.
Both are worth having; neither replaces the other.

**No draft state is observable.** Across a sampled week, all 455 schedule
items had `runStatus: 1`, `runType: null`, `runLock: false`. There is no
evidence from outside of a pending or draft tier. The field names hint that
one might exist — `runStatus` is plainly an enum — but its values are not
documented publicly.

### What that implies

**This is the crux:** if creating a schedule item puts a program straight onto
the real broadcast schedule, then "members pick a time" means members writing
live schedule that staff then edit. That is a different and much worse
proposition than approving a request.

Three ways out, in order of how much they cost:

1. **Members create the show, not the schedule item.** An unscheduled show is
   inert — it airs nowhere. The "reservation" becomes *your program exists and
   is waiting for a slot*, which is genuinely fewer steps than today and risks
   nothing. **This is the version to build first if this is ever built.**

2. **Ask the vendor whether a draft or pending run status exists.** If it
   does, the whole idea works with Cablecast as the source of truth and
   nothing stored here — which is the version worth wanting, and one support
   question answers it.

3. **Hold the intent outside Cablecast.** Works, but breaks the property that
   makes this attractive: Cablecast stops being the source of truth for what
   is scheduled, and now two systems disagree about the same week.

### The overlap problem is already solved

Two members computing gaps in a browser and picking simultaneously is a race.
This is the same race as the studio reservations, and it has the same answer:
**staff approval dissolves it.** Nobody is holding a lock, because nothing is
committed until a person says yes — and a person is looking at the week anyway.

Do not build locking for this. It would be solving a problem that the approval
step already removes.

### Authorization is already built

A member posting to us needs to prove who they are, and that is
`/authorize/` — the passkey bound to a member site. Same mechanism, different
verb: the credential that authorizes editing a site's settings is the one that
would authorize reserving a slot.

Worth noticing because it means this feature does not need an identity system
of its own. It needs the broker that several other things already need.

### Dropbox

Dropbox stays regardless — it is the right fallback and members are not using
it as working space anyway. But if a member uploads directly, the submission
stops being "a file in a shared folder that someone must find" and becomes a
record that arrived with its own metadata. Two providers rather than one, and
the direct path is better when it works.

### What to find out

- Does a draft or pending `runStatus` exist, and what do its values mean?
  One question to Cablecast support.
- Does the first-party tool staff use today create shows, schedule items, or
  both? Watching Nate answers this and question one at the same time.
- Are the gaps in a typical week big enough to be worth picking from, or is
  the schedule effectively full and the real scarce resource something else?

---

## Removing the weekly approval

**Why this is the point.** Today staff are a courier: a member puts a file on
Dropbox, staff take it off Dropbox and put it on Cablecast. Every week, every
episode, forever.

The passkey work is not about making sign-in nice. It is about moving approval
from **per-submission** to **per-device, once**. Approve someone's phone one
time and they publish to their own channel every week after that without
anybody in the middle. One act ever, instead of one act per episode. That is a
different cost curve, and it is the whole reason any of this is worth
operating.

### Enrollment and authority are two different things

`_data/authorize.yml` says forwarding a claim link is allowed on purpose. That
is right for the case it was written for — a co-producer binding their own
phone — and **wrong** for anything that confers publishing rights. If
forwarding a link grants the power to publish, then the design has an attack
built into it.

They come apart cleanly:

- **Enrollment** — "you may bind a device to this site." Survivable when
  forwarded, because binding on its own does nothing.
- **Authority** — "this device may publish." Never the claim's job. It is a
  property of the device record in `.auth/devices.json`.

The claim gets you listed. Being listed is what gets you trusted. Conflating
the two is what makes forwarding frightening.

### First device free, later devices co-signed

Locking a claim to the owner's address cannot actually be enforced: possession
of the address was proven by receiving the mail, and a forward destroys
precisely that. So instead:

1. **The first device to bind is trusted.** No staff involvement at all — the
   owner opens their link, makes a passkey, and is done.
2. **Every device after that is co-signed by an existing one.** The owner
   approves a co-producer's phone from their own phone.

**Built.** `worker/` — `/bind` enrols, `/device` approves and revokes. One
detail turned out to matter in the writing: "first" is *first that counts*, not
first in the file. A site whose only devices are listed-but-not-allowed has
nobody who could approve anything, so the next to arrive is still the first
that matters. Reading it the other way would have left a site permanently
unable to grant anybody.

A forwarded link is worthless the moment the owner has enrolled, which they
will have, because they are the one who asked for the site. Staff leave the
loop entirely and the two-people case still works.

The residual risk is narrow: somebody intercepts the very first link before
the owner opens it. Short expiry covers most of it, and the owner notices
immediately because their own link no longer works. Mailing the owner when a
device is added turns the rest into something detected rather than prevented,
which is the right trade at this size.

### Scope: this page assumes the notes exist

/upload/ takes a title, a summary and a date rather than reading a release log
that may not have been written yet — a producer often has not filled one in
until the moment they submit. Preparing show notes is a separate act at a
separate time, and folding it in would make one page responsible for two jobs
that fail in different ways.

Keep them apart.

---

## Other threads not yet written up

Recorded so they are not lost, in rough order of how ready they are:

- **Reserving studio time** is written up on its own, in `RESERVE-DESIGN.md`.
  It turns `/reserve/` from a list of rooms into a list of hosts, because a
  member cannot use a studio without one — so the thing on offer is a shift,
  not a space. Two things there bear on the notes below: claim links have to
  become one-to-one, which is the *opposite* of the forwarding that
  `_data/authorize.yml` currently calls deliberate, and revocation has to stop
  being contingent on whoever issued the link.

- **The broker.** One Cloudflare Worker serving several jobs. Built and
  tested: it issues challenges bound to a declared action, verifies the
  assertions made over them, and writes the file. `worker/`. `/settings/` uses
  it when one is configured — signing in stays wayfinding, and saving becomes
  a second prompt bound to those exact bytes. Enrolment and approval are there
  too, as `/bind` and `/device`, and `/upload` signs presigned R2 URLs so a
  finished episode goes from the browser straight to storage. Nothing is
  deployed and `url` is empty, so the site behaves exactly as before. What is
  left is the pages that would use `/bind`, `/device` and `/upload` — and, for
  uploads, a bucket with a size cap and a retention rule, which is a decision
  rather than a value.
- **The site factory.** `site-template/` is scaffolded; creation, hosting and
  fast-forwarding are not. See `site-template/README.md`.
- **Microsoft Graph.** Whether a nonce survives a published ICS decides
  whether Graph is needed at all. Ten minutes with one published calendar
  settles it. See README, "Calendar".
