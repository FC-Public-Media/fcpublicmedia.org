# Reserving studio time

What `/reserve/` becomes, and the posture we need for it. Written from the
board president's email and the decisions taken off the back of it.

Nothing here is built. This is the plan, and the point of writing it down is
that most of it is settled — the parts that are not are marked as questions at
the end rather than guessed at in the middle.

## The page is a list of us, not a list of rooms

Today the page lists five spaces. That is the wrong noun. Board members are
each hosting a minimum of two hours a week, a member cannot use a studio
without a host present, and so **the thing being offered is a host's shift**.
The room comes with it.

So the page is a list of people. Each host is one row:

- their photo
- their name and a short self-introduction, in their own words
- the hours they are on
- the **activities** they can support, as structured data rather than prose

The member reads down the list, finds someone whose activities match what they
came to do, and books a day that person is on. That is the whole interaction.

### It is not a week grid, and that is deliberate

The obvious design is seven columns. It is wrong here for a specific reason:
there are likely to be **more board members than there are days in the week**,
so a day-first layout makes the same person appear on Monday, Wednesday and
Friday, and the page becomes a rundown you scroll past rather than a set of
people you choose between.

Host-first means the plentiful case — seven of us, all listed — reads as
*welcoming*, because more hosts means more of the page is opportunity. Day-first
means the plentiful case reads as noise.

Days appear **inside** a host's row, as the days that host is on. Nothing
worships the Monday-to-Friday loop.

### Not half-hours either

There are no thirty-minute increments and no duration picker. The host's shift
is the unit: you are booking *that person, that day*. A shift that cannot
accommodate what is being asked — a four-hour podcast shoot against a two-hour
shift — is not solved by a finer grid. It is solved by a person, below.

### How far ahead

Two weeks, and **through the end of the second week rather than exactly
fourteen days**. A hard `+14` boundary produces "you are one day out of range,
come back tomorrow", which is a dead end dressed as a rule.

Further out than that is refused on purpose. Past two weeks the likelier
failure is a member forgetting they booked, not the technology.

Longer sessions and anything outside the shifts go to
`bookings@fcpublicmedia.org` with at least two weeks' notice, and are
accommodated when a host can stay. The page should say that plainly rather than
hiding it — it is the escape hatch that lets the main flow stay simple.

## Two data sources, and keeping them apart is the whole trick

The thing to avoid is re-typing reality into a product's database. Every
scheduling tool wants you to define your availability inside it, by hand, again,
and every change becomes somebody's chore. That person then either becomes a
bottleneck or a hostage. So:

| | Answers | Lives in | Changes |
|---|---|---|---|
| **The calendar** | *When is somebody here* | One shared M365 calendar | Constantly |
| **The host profile** | *Who they are, what they can support* | This repository | Rarely |

The calendar is the only thing that moves week to week, and it is maintained
where it is already maintained. **Nothing about a host's photo, bio or
activities is stored in the calendar**, so a shift moving one night changes the
day and nothing else — all the other configuration rides along from the
profile.

That split is what makes the sync cheap enough to run every fifteen minutes and
boring enough to trust.

### Joining an event to a host

One calendar holds every host's shifts, so each event has to say whose it is.
In preference order:

1. **The host is an attendee**, by their real M365 address. That address is the
   join key. It is also just correct in Outlook — they get the invite.
2. **A category** on the event, if attendees turn out to be inconvenient.
   Graph exposes `categories[]`.

Not the subject line. A naming convention in free text is a convention until
somebody types it wrong, and then it is a silent gap on a public page.

### Host profiles, edited without GitHub

Board members will not be editing YAML in a web UI on GitHub, and should not be
asked to. They do not need to: `/settings/` plus the device-authentication
broker already does exactly this job for member sites — sign in with a passkey,
edit your own record, the Worker opens a pull request with the change.

Pointing that existing machinery at a board profile is close to free, and it
means **no Graph permission, no app registration and no tenant admin is
involved in the part board members touch**. Photos, bios and activities are all
public-facing anyway, so there is no personal data going anywhere sensitive.

## Microsoft Bookings: what it is good for, and the thing it cannot do

Bookings is the obvious product and it is genuinely close to right. It ships
with M365 Business Standard and above, it models Services and Staff, staff
availability can be driven from each person's own Outlook calendar rather than
retyped, and appointments land on a real Exchange mailbox calendar — so a
booking *is* a calendar entry without anything having to carry it there. That
last property answers the "if it is not literally putting it on a calendar I
need a webhook" worry: with Bookings, it is.

Microsoft Graph exposes it under `/solutions/bookingBusinesses`, including
`bookingStaffMembers`, `bookingServices`, `bookingAppointments`, and
`getStaffAvailability`. So it can be read programmatically rather than
duplicated.

**But the embedded booking page cannot be given context.** There is no
supported way to pass our own fields into the standard Bookings iframe and get
them back out on the far side — no prefill, no pass-through, and the submit
button lives inside their frame where we cannot reach it. Which means the one
thing specifically wanted from an embed is the one thing an embed will not do.

So: **do not use the Bookings iframe as the interface.** Use our own UI, and
treat Microsoft as the system of record behind it. That is the same conclusion
already reached for `/book/` and `/register/` — we own the form, we submit the
data, and the vendor's UI stays out of it.

Whether Bookings is used at all, or just a plain shared calendar, becomes an
implementation detail we can defer. The page does not care.

> **Verify before relying on it:** Graph change notifications (webhooks) are
> well supported for calendar events on a mailbox, and I am *not* confident
> they cover `bookingBusinesses` resources. If a push signal is wanted, the
> safer subscription is the Bookings mailbox's calendar, which is an ordinary
> Exchange calendar. Treat this as unverified.

## Reading the calendar: one path, two triggers

The site is static and has to work with JavaScript off, which settles the
question that looks like a choice. Availability **cannot** be fetched in the
browser: no-JS visitors would see nothing, and every visitor would be asking
Microsoft the same question. So availability is baked in at build time, and the
freshness bound is however often we build.

`script/sync-calendar.py` already exists for this and already documents both
ways in — a published ICS link needing no admin at all, or Graph with workload
identity federation from Actions so there is no stored secret to rotate. It
also already records the sharp edge: `Calendars.Read` as an *application*
permission grants every mailbox in the tenant, and wants an Application Access
Policy scoping it to the calendars in question.

**One mechanism, two ways to fire it:**

- a scheduled Action every fifteen minutes, which is the floor
- `repository_dispatch`, so a webhook can trigger the *same* job immediately if
  and when one exists

That is deliberately not two systems. The webhook becomes a faster trigger for
a path that already works without it, so if the webhook silently dies the site
degrades to fifteen minutes late rather than to wrong. Diagnosing it is then one
question — "did the scheduled run pass?" — rather than a hunt through two
pipelines.

**Staleness must be visible.** If the sync has not succeeded recently the page
should say when it last updated rather than presenting old availability as
current. A schedule that is quietly twelve hours stale is worse than one that
admits it.

## Writing a booking

The member submits; the **booker** — the board president today — confirms. The
host being booked does not need to be notified by the system.

Staged, because the first stage needs nothing from Microsoft:

1. **Email.** Our form posts to the Worker, which sends a structured message to
   `bookings@fcpublicmedia.org`: who, which host, which day, which activity,
   which equipment, and their contact details. The booker works from that. This
   needs no app registration, no consent and no Graph write permission, and it
   is how the page can ship before any integration exists.
2. **Tentative calendar entry.** The Worker writes the appointment directly.
   Same form, same UI, one changed destination.

Nothing about the interface changes between the two, which is the point of
doing them in that order.

## Activities are a shared vocabulary

Each host declares which activities they can support. Two rules:

- **The list is shared, not per-person.** If two hosts can both support
  podcasting, it says the same words on both. Their *introductions* should
  differ; their capabilities should not, or the page turns into a reading
  comprehension test.
- **Declaring an activity is opt-in and low-stakes.** A host who is not
  confident with the video kit simply does not list it. That is the correct
  internal signal — it means that person wants training — and it is much better
  than a page implying a floor of service nobody agreed to.

Each activity carries a colour. Because the layout is host-first rather than
day-first, a row can carry several activities without anything needing to be
striped or split — which was the problem that made a calendar grid unworkable.

**Colour is never the only signal.** Each activity is a labelled control with
its own text. Somebody who cannot distinguish the colours loses a convenience,
not a capability. Clicking an activity is how you book that day for that
purpose.

### Activities are also how we describe the space

Losing the list of rooms cost us the description of the rooms, and that should
come back attached to the activities rather than as a separate inventory. An
activity should carry what it gets you: the room, the lighting, the software on
the edit bay, the equipment available for it.

That also does something the old page failed at — it makes vividly clear that
**equipment used in the studio comes with membership, and renting is for taking
gear out into the community.** Somebody who cannot afford the rental should be
able to see, on this page, that joining and coming in is the cheaper answer.

Equipment is already inventoried in Booqable and curated by the board
president, so categorising it by activity is a tagging exercise there rather
than a second inventory here.

## One card, two pages

The host card appears on `/meet/` under the board, and on `/reserve/` for
whoever is on. Same person, same photo, same bio, mostly the same fields.

So it is **one include taking a host and a flag for which fields to show** —
not two templates that will drift. On `/meet/` it can carry a link straight
into booking that person's slot.

## Device accounts, and one thing that will not work as described

The intent: provision a member's device account at first contact, from any
entry point, so that by the time they need it they have one. Empty name and
empty email are fine. One primed state that everything later builds on.

That is right, with one correction:

> **A passkey cannot be created on page load.** `navigator.credentials.create()`
> requires a user gesture; browsers refuse it otherwise, and there is no way
> around that. "Provision on landing" therefore cannot mean "make a passkey on
> landing."

What it can mean, and should:

- **On landing:** mint a local identifier and an empty profile in local
  storage. No gesture, no prompt, no network. This is the primed state.
- **On first gesture that wants it:** upgrade to a real passkey. Booking is a
  natural moment; so is class registration.

The two-step is invisible to the member and it is the only shape the browser
allows.

### Single-use links, and what has to change

`_data/authorize.yml` currently documents forwarding as *deliberate* — a claim
link is a capability, and a co-producer forwarding it to bind their own phone
is a wanted behaviour. The new requirement is the opposite: **one link, one
device, and paying it forward means minting another.**

That is a real change, not a setting. Claims are stateless signed tokens today,
which is exactly why they are forwardable. Making them one-to-one requires the
Worker to remember which claims have been spent — a small amount of state in
KV or D1, checked and written inside the same request that binds.

### Revocation must not depend on who issued the link

Required, and correctly so: if the person who issued a link is gone, the
organisation must still be able to revoke what it authorised. Nothing may be
contingent on an individual.

The existing model already mostly does this. `/device` flips `may_publish` or
revokes, and authority comes from being a listed, allowed device on **the
organisation's** list — not from having issued anything. The rule that the last
publishing device cannot be revoked prevents locking everyone out.

What that leaves is a policy rather than code: **the board's list must always
have at least two devices that can publish**, so no single person's absence
strands it. Worth writing into the board's own procedures rather than trusting
to luck.

## Graceful degradation, with no scolding

The floor is set deliberately low, because the person browsing with JavaScript
and local storage off is not going to be talked out of it and should not be
asked.

**The no-JS path is the primary path, not a fallback.** The reserve form is an
ordinary `<form method="post">` pointing at the Worker, which replies with a
real page — a redirect to a confirmation URL. It works with scripting disabled,
storage disabled and cookies refused. Identity in that case is simply the email
address they typed, which is all the booker needs anyway.

Everything above that floor is enhancement:

| Available | What they get |
|---|---|
| Nothing | The form works. Booking completes. Nothing is remembered. |
| Local storage | Name and email remembered. A device account exists. |
| Storage + passkey | The account is provable, and can carry authority. |

**No banner ever asks anyone to enable anything.** A visitor with scripting off
sees a page that works, not a page complaining.

`/settings/` is the litmus test. With JavaScript off it must render a plain
form that posts and returns a page — not a blank screen and not an apology. If
that view degrades cleanly, everything else on the site does.

## What could ship for the board meeting

The page does not need Microsoft to exist to be worth approving. In order:

1. The host card include, and the host profile data shape.
2. `/reserve/` rebuilt as the host list, with activities, colours, and the
   two-week horizon — reading availability from a **hand-maintained data file**.
3. The form posting to the Worker, emailing the booker.
4. Swap the hand-maintained file for the calendar sync. **No interface change.**

Steps 1–3 are ours end to end. Step 4 is the only one that waits on anything,
and building 1–3 first means the calendar arrives into a page that already
works rather than being the thing the page is blocked on.

## Open questions

For the board president rather than for us:

- **How are hosts identified on the shared calendar** — attendee, or category?
  This is the only thing the sync genuinely cannot guess.
- **What is the activity vocabulary?** The list needs to be short, shared, and
  agreed, because hosts pick from it rather than writing their own.
- **How does equipment map onto activities?** A tagging pass in Booqable.
- **Who holds the second publishing device**, so revocation never depends on
  one person.

Unverified on our side, flagged above: whether Graph change notifications cover
Bookings resources directly, or whether a push signal has to subscribe to the
Bookings mailbox calendar instead.

## A follow-up worth doing properly

Navigating this page with a screen reader is its own exercise, not a checklist
item at the end. The interaction — choose a person, choose a day, choose a
purpose — is bespoke enough that it deserves being *used* rather than audited.
There is prior art in the `discovery-written` media showcases, where the
switching panels and the player were built by living with a screen reader for
months rather than by testing against one.
