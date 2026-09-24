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
32 for the one sampled. That is all-time, whereas `site/_data/airings.json` is a
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

`site/_data/authorize.yml` says forwarding a claim link is allowed on purpose. That
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

## Digitizing somebody's tapes, and giving them more than a thumb drive

From a spoken briefing, 2026-09-17. Quotations are dictated speech, lightly
de-garbled where speech-to-text mangled a proper noun. Nothing here is built.

**The digitization station is the pet use case.** FCPM runs a bay that takes
people's physical media and turns it into files. The question is what we hand
back.

> I want to make a product where we are importing video for people, and we're
> not just capturing it into a capture card and sending them a video on a thumb
> drive. I wanna give them everything they could ask for from us. I wanna give
> them the UI to look at it.
>
> This isn't, like, an HTML file on a thumb drive. We can deliver their results
> privately to them. They can come into the studio to get large files too.

### Contact sheets are the ancestor, not AI-gen proofing

This correction is the most useful thing in the briefing and it is worth
protecting, because the two ideas share a repository and are easy to conflate.

`.proofing-engine` today is about **AI generation** — sweeping what a generator
made and deciding which outputs are any good. FCPM is not doing AI-gen capture.
What FCPM wants is the *other* thing in that repository:

> We were crawling Google Drive videos, and requesting **byte ranges** for them
> in order to generate frames at intervals. And the aspirational notes there
> were: you had a UI for this. You could zoom in. You might wanna see new
> thumbnails — click on a range to see thumbnails there, between here and here.
> Maybe you want it to be every five seconds instead of twenty. We can do that,
> and we can keep the frames.

So the mechanism is: **fetch byte ranges of a remote video, decode frames at an
interval, render a grid, and let the interval be a thing you change by pointing
at part of the timeline.** Not a transcode, not a download.

And the shared ground with proofing is ideological rather than technical:

> I was talking about the proofing repository mostly because that was where I
> imagined different people could look at what they've got and decide what they
> like. That's the part where ideologically proofing and contact sheets share
> some ground. And I think I want proofing to gain what I was talking about in
> the contact sheets thing.

**Proofing already has half of this.** Its sweep view renders `image`, `video`
and `audio` in a grid, and a video tile has no controls because *"the pointer is
the playhead"* — moving across a tile seeks to that fraction of the duration.
What it does not have is interval extraction over byte ranges from a remote
file, a zoomable interval, or kept frames.

**It should gain that in proofing, not in a fork here.**

> The proofing engine might get a new set of faces here. But I don't wanna be
> editing it only for FCPM.

### The pipeline already exists, and it has never been committed

Looked for while writing this note, and found: **`~/Project/contact-sheets` is a
complete, working implementation of most of the above.** It is not a sketch. It
has a cache contract, a disk floor, a resume story, and a list of its own known
failures.

| | |
|---|---|
| `process-all.sh` → `process-clip.sh` → `assemble.sh` | folder, clip, sheet. Extraction is idempotent: a clip gets a `.done` marker and is never re-read |
| `proof.sh`, `proof-all.sh`, `proof-rates.conf` | proofing at configurable rates — *"every five seconds instead of twenty"*, already parameterised |
| `ranges.py` | writes a **ranges document** (CSV + JSON), one row per range, clip-relative *and* wall-clock time |
| `segment.py` | camera settled versus in transit |
| `make-sheet-html.py`, `build-site.py` | the sheet, and a publishable static site assembled from the cache |
| `reconcile.py` | what is on the phone and not on Drive |

It reads Google Drive through the local CloudStorage mount, and its own notes say
streaming *"pulls byte ranges into Drive's local cache as it goes"* — which is
the byte-range behaviour from the briefing, arrived at from the filesystem side
rather than over HTTP.

Two of its documented design positions are worth importing wholesale, because
they are the same instincts this repository already runs on:

> The sheet is how a person finds a moment, this is how a tool finds the same
> moment. Two artifacts, one source of truth each.

> Cutting, if it happens, is a separate step that writes NEW files to a NEW
> folder and reads this document as input.

**It has zero commits.** Not "few" — the repository was `git init`-ed, a
considered `.gitignore` was written, a `CLAUDE.md` was written, and then nothing
was ever committed: 46 untracked entries, no branches, no remote, no reflog. It
also has no address in the node's library, so nothing can petition it, serve it,
or name it.

That is worth saying here rather than anywhere else, because it changes what
"start with a script" means. **The script is written.** What is missing is not
the capability; it is history, an address, and a decision about where it lives.
Three of its known problems are already documented in its own `CLAUDE.md` — most
sharply that `assemble.sh` deletes the previous sheet *before* running montage,
so an interrupted assemble leaves an empty directory rather than a stale sheet.

Placement is Autumn's call and nothing here should assume it. What FCPM needs
from it is the capability, and the note above says that belongs in proofing.

### The permission model is the interesting part

> The Google Drive example is the easiest first case, because anything that we
> do is fantastic. What we don't wanna do is have them give us edit permission
> to their folder sources. So what I think should happen is that they could give
> us a folder with a shortcut to their stuff inside of it in Google Drive itself.
> That way we can read it, but **by construction** we don't have the ability to
> edit it.

This is the good idea to keep. A Drive shortcut inherits the target's
permissions rather than the containing folder's, so a customer can put a
shortcut to their own footage inside a folder shared with us and we get read
access to the bytes without any grant that could destroy the original. **The
safety is structural rather than procedural** — nobody has to remember not to
write, because there is nothing to write with.

It is the same argument the Wix standing order in `AGENTS.md` makes from the
other direction, and the same argument `_config.yml` now makes about internal
documents: an arrangement where the mistake is impossible beats one where it is
merely forbidden.

### Start with a script

> We will be granting an AI worker to even do it. But otherwise, we just need to
> make a script. We don't need an AI worker yet — we can do tooling that does
> this stuff, and it could even write into their own folder for now. We don't
> have to keep these files local per se. They're scratch. They're temp space.

An explicit permission to build the boring version first. The AI worker is a
later shape of the same pipe, not a prerequisite.

`DiscoveryWritten/stagecraft` has already proven the heavy end is available —
*"the stagecraft product has proven that I can use the workstation GPUs
cooperatively to do renders"* — but it is not required for this, and the note is
that we may not need it: *"I don't know if we have to. Maybe the process is just
as well."*

### Tapes arrive from us, and go down the same pipe

> If it's VHS stuff, you have to do it at normal speed. That's not a practical
> way to do it otherwise without inventing some weird physical equipment. So
> we'll have the sources for those in studio, and we're gonna wanna put them
> through the same pipe, but they're gonna arrive from us. And we'll get to
> deliver those however we want. We could do Google Drive again for starters.

Two intakes, one pipe. A customer's Drive link and a tape captured in the studio
differ only in where the file starts life; everything downstream — frames, the
grid, the delivery — should not care which.

Real-time capture is also the sizing constraint nobody can engineer away: an
hour of tape costs an hour of a machine, which is what makes *"our station
getting video constantly spit out of it"* the normal state rather than a burst.

### Where the files live

> We have a few file storage services, but not specifically for something like
> this, so it doesn't really fit yet. We will handle certain of the big file
> delivery, but **the workstation libraries are gonna be where they live even if
> they're not committed.** Large things don't have to be committed, especially
> if they're just transient and don't really matter to the code or the station
> configuration itself.

A library holding does not have to be bytes in git. That is worth stating
plainly here, because it is the first case in this repository where the library
is being asked to know about something it is deliberately not carrying.

**The drive it lands on is being partitioned now**, and the partitions are not
interchangeable:

> Right now I'm partitioning a little network drive. I'm trying to make about
> four gigabytes per box — it's like a thirty-two gig drive, so it's a little
> less than four gigs each. They're gonna have different uses. We're gonna
> coordinate on them. It's gonna be a network drive. If it's plugged into the
> real FCPM station and shared to a network that way, also fine.

Eight partitions, one per box, under four gigabytes each. Small enough that
*where a capture goes* is a real decision rather than a default, which is
probably why the partitioning is happening before the pipe exists.

### The one AI-gen-shaped thing FCPM would want

Not capture — routing:

> If we did have someone using a browser and we had an alternate route
> available — like they could have our own private extension loaded — then when
> they are looking at stock photos and they wanna download a thing, our tool can
> shuttle it to the right place.

A private extension that puts a downloaded asset in the correct partition for
the box you are sitting at. It is proofing's capture idea aimed at stock
footage instead of at generated images, and it is the only part of the AI-gen
posture that transfers.

## Showing what is on the network drive

Written 2026-09-23, from a briefing about the kiosk boxes and the drive they
share. Nothing here is built. It is written up now because the design converged
across two sessions and the reasoning is worth more than the conclusions.

The errand:

> I want it to be possible to use this thing as both an inbox and an outbox.
> I'd like to have a client page here at the kiosk that is able to show what's
> in the queue, so that people don't need to be sitting at a computer to know
> if it made it.

The drive itself is described in [`TENANCY.md`](TENANCY.md), *"The hook is the
product"* — eight partitions of a little under four gigabytes, *"little
mailboxes for files"*, shared over Samba from the router. What follows is only
about **saying what is in them.**

### A browser cannot speak SMB, so the shape is forced

A page gets `fetch` and WebSocket. SMB needs a socket on 445. There is no
client-side trick that reaches it, and a JavaScript SMB implementation would
have to run somewhere with sockets, which is not a kiosk browser.

So: **something that can see the drive walks it periodically and publishes an
index; the page renders the index.** That is not a workaround, it is the split
[`KIOSK.md`](KIOSK.md) already describes — this repository owns what a screen
says, something else owns showing it — arrived at a second time from a
different direction.

### The drive refuses to introduce itself

Checked 2026-09-23, so the next session does not repeat it. The router is at
**10.209.1.1**, a Linksys serving `lighttpd`; SMB is open on both 445 and 139.

**Anonymous and guest sessions are both rejected.** Null, `guest`, `nobody` and
`admin` all return *"server rejected the authentication"*. So share enumeration
is credential-gated at the router. Nothing is misconfigured; that is the
default.

Enumeration itself is one command once a credential exists, so **nobody has to
type out a list of partitions** — but until then the scanner cannot discover
what it is scanning. Two ways out, and the choice is a network decision rather
than a code one:

1. **Connect once in Finder** with *remember this password in my keychain*.
   After that the enumeration runs under a saved credential and no secret has
   to be written down anywhere. Only the username is needed by anyone else, and
   a username is not a secret.
2. **Turn anonymous access on** in the router's external-storage settings. Then
   the scanner carries no credential at all — one less thing to rotate, leak,
   or explain to whoever runs this next — at the cost that anyone on that
   network can read and write the drive.

(2) is defensible precisely because of what the drive is for. It is a transit
box for media in motion, not a store. But it is Autumn's call and it should be
made rather than defaulted into.

### The limits are part of naming the volume

FAT is not an incidental detail here; it decides what the drive can be told to
hold. Each of these changes a design:

- **A file cannot exceed 4 GiB on FAT32, or 2 GiB on FAT16.** Partitions of
  *"a little less than four gigs each"* may be either. **Masters do not fit on
  this drive** — it routes proxies, deliverables and sheets. That has to be
  said at submit time, because the alternative is finding out when a copy fails
  at 4 GB after twenty minutes over SMB.
- **A FAT16 root directory holds about 512 entries**, and a long filename
  consumes several of them. A root full of `Council Meeting 2026-09-14 Full
  Session.mp4` reports the disk as full with gigabytes free. **Nothing should
  ever be written to the root of a partition.** This failure is invisible and
  it will be misread as a broken drive.
- **There are no permissions and no ownership.** Inbox and outbox cannot be
  enforced by the filesystem. They are a directory convention, and the index is
  what makes the convention legible to a person.
- **`mtime` is local time at two-second resolution, with no zone** — stamped by
  whatever machine wrote the file, according to whatever it thought the hour
  was. Do not order a queue by it.
- **`: * ? " < > |` are illegal, as are trailing dots and spaces.** Google
  Drive titles are full of colons. Sanitize on write and keep the original
  title in the index, or the screen shows a mangled name to the person who
  chose it.

These are filed upstream in `tiliv/station-node#160`
(`give-this-node-a-word-for-media.md`), whose argument is that a media entry has
to say what a volume **cannot** take and not only what it is for. That is the
right place for them; they are repeated here because they constrain this
artifact directly.

### Completeness cannot be observed. It has to be declared.

This is the load-bearing correction and it arrived from station-node's side.

The obvious design is: if a file's size is unchanged across two scans, it has
landed. **That is a guess, and it fails exactly when it matters.** A stalled
writer looks identical to a finished small file — a partial file is
indistinguishable from a complete one by inspection. A 3 GB copy that died
halfway is the worst case on this drive, and a size-stable heuristic reports it
as the best case.

The node's standing rule is that *config declares intent and the system
discovers fact*. **Completeness inverts it**, because the reader genuinely
cannot observe the property. It has to come from whoever wrote the bytes.

That is free for writers we control — a job writes under a temporary name and
renames on completion, and **the rename is the declaration**. It is impossible
for a person dragging a file into the share from Finder, which is the majority
path. So the index carries three states and the third one admits what it is:

| state | means |
|---|---|
| `declared` | the writer said so, with a digest. Trustworthy. |
| `arriving` | observed growing between scans. Trustworthy in the negative. |
| `unwitnessed` | present, nobody declared anything, not currently growing. **A guess, and the name says so.** |

`unwitnessed` names the *absence of a declaration* rather than asserting a
condition, which is the job `landed: true` failed to do. Station-node's own
`mounts()` uses `quiet` for the same semantic; it was considered and declined,
because `quiet` reads to a person as idle and idle reads as done.

Two consequences that are easy to get wrong:

- **`arriving` → `unwitnessed` is not progress.** It is the moment we *lost*
  the only signal we had. Across a room it reads as advancement. So **the
  artifact emits a state name and its evidence, never an ordinal** — no stage
  numbers, nothing asserting sequence — which leaves a renderer free to put
  `unwitnessed` off the track rather than at the end of it.
- **A file that finishes between two scans never passes through `arriving`.**
  It appears already static. Nothing may assume `arriving` is a stage every
  upload visits.

The supporting field is **`growth_last_observed`: a frozen instant**, written
once when growth stops and never moved again. Not a duration — a duration is
recomputed every scan and churns the artifact when nothing has happened. A
renderer reading per request subtracts it from now and gets a live duration for
free, at whatever precision the screen wants. *Was growing, hasn't for six
minutes* is a different screen from *hasn't for four seconds*, and the
difference is whether a person waits or fetches somebody.

**Its absence is a third reading**, not a zero and not "long ago": we never
witnessed this file growing at all.

### Identity is declared too, for the same reason

A FAT volume label is a name, not an identity. It is short, anyone who plugs
the drive in can rename it, and **nothing stops all eight partitions being
called `MEDIA`.**

A volume serial number exists underneath and survives a relabel — but this is
seen through Samba, which serves a filesystem rather than a block device.
SMB2 carries a serial in `FileFsVolumeInformation`, and whether the mount or
the scanner surfaces it is a coin toss not worth building on.

So identity is **minted and declared**: each partition carries a marker file at
a known subpath holding an id, written once. Readable over plain SMB with no
special calls, survives relabelling and survives the drive moving to another
box. It does not survive a reformat, which is correct — a reformatted partition
genuinely is a new place, and an identity that outlived it would assert a
continuity that does not exist.

**The trade, which belongs in the marker file's own header:** a marker file is
copyable and a sniffed serial is not. Back the drive up by copying files, or
clone a partition, and two volumes now assert one identity — both telling the
truth as they were written. **A duplicate id means a copy was made, not that a
volume moved.** The failure is silent, and the first person to meet it will
assume the index is broken.

A missing marker makes a volume `unidentified` rather than guessed at — the
same discipline as `unwitnessed`, and it should render the same way: not an
error, not a blank, and not something that reads as fine.

The label is still emitted, as a display name that is **explicitly allowed to
collide**. It is not what identifies a partition on screen either: `wants:`
carries `holds:`, what a label is *for*, and *"proxies for editing"* tells
somebody which partition their file went to where `MEDIA` tells them nothing.
Purpose is the heading; the label is a subtitle for whoever has the drive in
their hand and wants to match what Finder shows.

Note that `wants:` — `label` / `holds` / `lifecycle` / `disposition` — is a
binding **no host implements yet**. Adopting it here is being an early
implementer rather than a consumer, and that sentence belongs in the artifact
itself rather than only in a commit message.

### The one kiosk rule this artifact cannot keep

[`KIOSK.md`](KIOSK.md) already settles the shape: inert, no hostname or port or
address of its own, no timestamp, and a `revision:` digest as the first field so
a poller need not parse the rest. All of that applies here unchanged, and a
queue index should be recognisably the same kind of file.

**Except that it cannot be committed.** The kiosk artifact is generated at build
time and `--check` in CI turns "regenerate when content changes" into a promise
a pull request can fail. A queue index describes a drive that changes every few
seconds. There is no build to attach it to and no commit that could be current.

That is worth naming rather than glossing, because `--check` is what makes the
kiosk's freshness *guaranteed* rather than *likely*, and this artifact has no
equivalent available to it. The honest substitute is that every observation in
it is stamped with a frozen instant of its own, so a renderer can show staleness
directly instead of the repository promising freshness it cannot deliver. **A
screen should say when it last heard anything, and say it even when — especially
when — the answer is a while ago.**

The consequence for a renderer that serves referenced images by membership in
the set the artifact names: **anything to be displayed must be named in the
index**, and anything unnamed is unreachable rather than merely unlinked.

### Contact sheets are downstream of this, and are already written

The jobs that land things on this drive are the subject of *"Digitizing
somebody's tapes"* above, and Autumn has since narrowed which part she wants
first:

> Don't use the proofing project — that's a word for functionality we're not
> going to worry about yet. It's that contact sheet stuff from the Google Drive
> that I'm really interested in, because that's the thing that just makes the
> thumbnails. It doesn't need human operators. Its task is automatic.

So the first job is: take a Drive link, produce thumbnails, write them back.
**No human in the loop, which removes an approval state**, and it makes a sheet
a *derived* artifact — if one is wrong it is deleted and regenerates. Nothing
about a sheet needs to be durable, reviewed, or version-controlled, which is a
different disposition from everything else the index names, and `disposition:`
is where that gets said.

It also means no vocabulary has to be invented for it here. `~/Project/contact-sheets`
already implements the pipeline, per the section above.

### What to find out

- **A credential for 10.209.1.1, or anonymous access turned on.** Everything
  else is designed; this is what the first real listing waits on.
- **Whether the router exposes one share or eight.** It changes the scan root
  and nothing else, but it is worth knowing before writing the walk.
- **Whether a volume serial survives to the scanner** on this particular mount.
  If it does, it is a cheap second opinion alongside the marker file — enough
  to notice a cloned drive, which the marker alone cannot.

---

## Signing in to a workstation with the passkeys we already have

Same briefing. This one is closer to buildable than it looks, because most of
the machinery is already in this repository.

**What the studio does today:**

> We have computers that have a PIN on one account, and you open a browser
> profile, and you can pick any of our profiles to open a browser window for.
> It could be done better, but it's clear that no one has tackled it yet.

One shared OS account, and identity is whichever browser profile you clicked.

**What is wanted**: the passkey system doubling as a way to get into the
machines. And the mechanism comes from a part of `ablative` that is not being
brought over:

> I am conceiving of something in ablative that was called **the shroud**, that
> works like a tool I use to kinda hide the screen. We're not gonna do any of
> that — but it did have a mechanism in it where I could put a QR code on the
> screen, and you could get in with your phone. And we could know exactly who
> you are **without accounts on the device**, on the workstation, because you're
> using your phone to get in.

### Why this is nearer than it sounds

Every piece of it exists here already, built for other reasons:

| piece | where it already is |
|---|---|
| Passkey enrolment and assertion | the broker, `worker/` — `/bind` and `/device` |
| Signed, forwardable claims | `site/bin/mint-claim.py`, `site/_data/identity.yml`, `site/assets/js/claims.js` |
| A QR code standing in for a session | `/check-in/`, `site/bin/make-qr.py`, `site/_data/checkin.yml` |
| Identity policy written down | `site/_data/authorize.yml` |

A workstation sign-in is *check-in with a different consequence*. That is a
strong hint the thing to build is a new consumer of the broker rather than a new
system beside it.

### The constraint that shapes it

> It's not the only way to get in, but I wanted it to be possible. We don't have
> to lock it per se. Not everyone wants to pull their phone out, especially if
> they're old. So there are gonna be multiple ways to do this stuff.

**Phone-as-key is one door, never the only door**, and any design that makes the
QR path load-bearing is wrong on arrival. The failure this prevents is specific
and it is an access failure: an older member standing in front of a machine that
will not let them work until they produce a smartphone.

Note also that this cuts against a claim currently in
`site/_data/authorize.yml` — that forwarding a claim link is deliberate and allowed.
A link that opens a workstation is exactly the case `RESERVE-DESIGN.md` already
flagged as needing one-to-one claims. **The two notes should be read together.**

## Other threads not yet written up

Recorded so they are not lost, in rough order of how ready they are:

- **Reserving studio time** is written up on its own, in `RESERVE-DESIGN.md`.
  It turns `/reserve/` from a list of rooms into a list of hosts, because a
  member cannot use a studio without one — so the thing on offer is a shift,
  not a space. Two things there bear on the notes below: claim links have to
  become one-to-one, which is the *opposite* of the forwarding that
  `site/_data/authorize.yml` currently calls deliberate, and revocation has to stop
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
  fast-forwarding are not. See [`member-sites.md`](member-sites.md).
- **The screens in the building.** `brand/` holds desktop backgrounds for the
  studio's three portrait panels and an idle screen, generated by
  `bin/make-wallpaper.py`. Worth knowing for two reasons. The first is that it
  is where this brand stops being CSS and starts being a file somebody
  downloads once and then looks at for a year, so the two rules that cannot be
  seen to be broken — the mark leans counterclockwise, yellow is a surface and
  never a colour — are enforced by `bin/test_make_wallpaper.py` in CI rather
  than by whoever happened to run the generator. The second is the slot in
  `brand/idle/index.html`: an empty, marked place on a full-screen panel for
  live content — guest network, check-in, what is on air. It ships empty on
  purpose, and it is the seam that work should land in.
- **Microsoft Graph.** Whether a nonce survives a published ICS decides
  whether Graph is needed at all. Ten minutes with one published calendar
  settles it. See README, "Calendar".
