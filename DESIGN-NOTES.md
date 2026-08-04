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

**Shows and schedule items are separate resources.** A show can exist with no
schedule item attached, and TRMS's own `new-show.mjs` example creates the show
first and schedules it as a second call. So **an upload does not have to be
slated against a draft schedule.** A member could upload, the show record would
exist, and it would air nowhere until somebody scheduled it.

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

2. **Ask TRMS whether a draft or pending run status exists.** If it does, the
   whole idea works with Cablecast as the source of truth and nothing stored
   here — which is the version worth wanting. One support email answers it.

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

- Does a draft or pending `runStatus` exist? (support@cablecast — one email)
- Does the first-party tool staff use today create shows, schedule items, or
  both? Watching Nate answers this and question one at the same time.
- Are the gaps in a typical week big enough to be worth picking from, or is
  the schedule effectively full and the real scarce resource something else?

---

## Other threads not yet written up

Recorded so they are not lost, in rough order of how ready they are:

- **The broker.** One Cloudflare Worker serving several jobs — device
  binding, settings editing, and eventually this. See README, "Identity", and
  `_data/authorize.yml`. Deliberately unbuilt until something needs it enough
  to justify operating it.
- **The site factory.** `site-template/` is scaffolded; creation, hosting and
  fast-forwarding are not. See `site-template/README.md`.
- **Microsoft Graph.** Whether a nonce survives a published ICS decides
  whether Graph is needed at all. Ten minutes with one published calendar
  settles it. See README, "Calendar".
