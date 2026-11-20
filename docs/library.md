# The library

What FCPM's library is, where it keeps things, and what it can say about them. Built: `library.yml`, a
machine's binding, `~/code/library` with its `retain/` record, and `fcpm library` (status, where,
xray, diff, summary, log, browse), on bay 1's attic and downloads; the `librarians` branch is seeded. The rest
is notes: the lobby, Helm addressing other machines' holdings, the ask, the librarians' passes, and the
keychain wing as a data pile. The engine is
`.library-engine` ([library.anecdote.channel](https://github.com/FCCN-ANTIBODY/library.anecdote.channel)).

## What it is for

A library routes to what is there. Not everything in it is publishable, but the library has to know
what it holds, where, and since when. It runs the way Helm does: on every machine where a crew runs
our code, each with its own holdings. This bay is a big Helm and the outposts are little ones, so any
outpost's library can be read from here.

Three files say it:

| file | says |
|---|---|
| [`../library.yml`](../library.yml) | who our library is: its branches by purpose, its holdings by label. No paths |
| `../machines/<job>/library.yml` | where that machine keeps each holding it has. Bay 1: [`production`](../machines/production/library.yml) |
| [`../machines/library.py`](../machines/library.py) | `fcpm library`: reads both, and x-rays a holding |

### Branches, by purpose

A library has more than one branch from the start, and each says what it is for. Only `main` is merged
into. The others are separate concerns: kept beside main, never merged into it.

| branch | for | state |
|---|---|---|
| `main` | what we publish and what we run | |
| `library` | holdings in git: the tenant list, `city/`, `voices/` ([members.md](members.md#library-and-wizards)) | `city/` on origin.local; the LAN's |
| `origin` | the actual origin: canonical submodule references to what we work on; our computers fast-forward from it | not made |
| `archives` | what we keep after we stop working on it | not made; not assigned yet |
| `lobby` | first contact and orientation: takes people to things on other branches | not made |
| `retain/studies` | studies, a folder each: what we are working out, in our own words. Where we keep them; the cloud line's are taken in as they came. The LAN's | on origin.local |
| `studies` | the cloud line for studies: a cloud session commits a study here, and we take it into `retain/studies` | begun |
| `librarians` | what librarian agents answer to: the constitution, each place's decorum | seeded; the LAN's |
| `retain/<machine>` | a machine's own record: x-rays, and later notes, summaries, errors. The LAN's | bay 1 |

Working state and publishing are kept apart this way. The library had begun to gather working
state, and the origin's map was part of it.

**The library is where things go by default** (Autumn, 2026-11-17). Most of what we do is stored here,
not in a folder on whichever computer did it. A session's context stays on its machine, and sessions
often can't see each other, so work kept loose ties people to the one computer that holds it. In the
library, any machine on the LAN reads it from the origin. Then what we did is summarized into released
branches, because the reason to do it at all is to publish it: we heal local access, and we show the
work in the open so others can see how. Released branches have no names yet.

### `refs/` stays; the origin is a branch of the library

Every bay keeps `~/code/refs/`, a tidy set of read-only mirrors, each a live line to its cloud source
(GitHub). `refs/` does not move into the library, and the library does not replace it. It stands as a
machine's nomination of its own concern: what it wants to hear from the cloud version. Station-node had
nothing like it, only a project folder holding the history of everything, and that was its mistake.

The **origin** is a branch of the library: the actual origin, holding canonical submodule references to
what we consider worth working on. FCPM's computers fast-forward from it. So there are two lists, and
they are allowed to differ: `refs/` is what a machine watches, and the `origin` branch is what we keep.
Who carries changes between GitHub and the origin is open. A crew might take over the merge relay
(`fcpm relay`).

## Who can see

Treat every library as publicly viewable. That is not because we publish it. It is because we cannot
prove it private. Our computers stay signed in so people can get work done, and a browser profile is
often signed in for them, so whoever sits at the keyboard is authenticated without our knowing who
they are. A keychain on such a computer is visible to that person too.

So there are three kinds of place, and they are told apart by how hard each is to reach, never by a
promise of privacy:

- **Open.** In the library, readable by whoever is here. Every holding today. Its `disposition`
  ([residency](https://github.com/FCCN-ANTIBODY/library.anecdote.channel/blob/main/RESIDENCY.md)) says
  who has been promised a read. It never says the place is secret.
- **Vault.** Hard to get to. That is the whole principle: once you are in, you can see it.
- **Sealed.** Out in the open, perhaps, but encrypted. Readable only by whoever holds a key we granted.
  That grant is the keychain wing, below.

### Reading is not the library's to offer

The library has no machinery for reading a file. A file is readable because the library exists and
holds it where it can be reached, whether it ought to be protected or is public. The library routes to
what is there and does not stand between a reader and a plain file. Whoever reaches it reads it with
whatever they already have.

So the library has exactly one API for reading, and it is for sealed things only: **ask for a grant of
a core**. A core opens a range, and the grantee decrypts that range themselves. The library hands over
the means to read and never a value it has read. `fcpm library` follows the same rule. It reports where
a holding is and what shape it has, and it never opens a file.

Moving the board's documents off a shared cloud drive is the first job here. Members reached them too
easily. Nothing has gone wrong, but nothing stopped it either.

## Where things are

The library does not read things, but it has no trouble saying where they are. How to address a
holding is not the secret part, so the library resolves it for whoever asks: `fcpm library where LABEL
[PATH]` gives the store and the address.

A machine's binding is the address. A bare path is the filesystem's. Any other store is a mapping
that names its store, and what the address means follows from the store. For example, an IPFS holding
is addressed by its content, with no path at all (the engine's `store:`).

**An address that carries credentials is part of a grant.** Some places cannot be reached at all
without credentials up front, such as a share whose connection string has to log in. For those, the
address itself is the sensitive thing. The binding says `needs: grant` and holds no address, and
`where` says to ask. We can extract all of it for the asker, because asking is already the front
door: the address comes with the grant, the same way a core does.

**A place can move out from under its address.** Drive letters are handed out when volumes mount, and
the order can change. On 2026-11-16, Google Drive mounted at `E:` while the Drobo was detached, and the
Drobo came back as `H:`. A binding can say which volume it expects (`{at: "E:/", label: "TO ENHANCE"}`),
and every x-ray records the volume it saw. When the volume at an address is not the expected one,
`fcpm library`, its console, and `xray` say `ASK A PERSON`. `xray` then refuses, so that nothing is
recorded under another place's name. The library changes no binding and no letter. Putting it right is
a person's job. Noticing it, and lodging it as a request for action, is a librarian's
([constitution](https://github.com/FC-Public-Media/fcpublicmedia.org/blob/librarians/CONSTITUTION.md)).

**On another host, Helm asks.** A holding on another machine is addressed through that machine's helm
(`../machines/helms.yml`): the job and the label, such as `production:attic`. Asking is the library's
business, but only Helm works out how to reach another machine and get a grant. The grant layer can also
say not now: the machine is down, or it is under a sensitive advisory (in live use for something else,
say, so nothing should talk to it for a while). Either way, any one of our checkouts shows whether what
you want is here or there. Not built.

**Libraries can ask each other.** When librarians disagree about something, the files may be in
different places, and reaching a consensus means asking the other library. A librarian can do that by
asking Helm to put a query to the other library's own front door: what does it hold, and what has it
noted, about this? That is its own kind of information access. It is not reading a file (Reading,
above), and it is not a grant of a core. It is one library answering another about its own record. The
answer goes into the asker's `retain/`, alongside the disagreement it was asked to settle. Not built.

## Holdings, and the attic

A holding is a place with things in it. Its label is ours. `is:` gives the engine's word for the same
thing: the engine's `wants:` labels are stacks, catalogue, intake, seats and petitions.

The first holding is the **attic**: what came down from the organization's Google Drive and has not
been placed. It holds heavy video and audio from members' projects, and the board's older documents,
the ones last changed in 2025 or before. Those are evicted from the Drive. We are not sure how all of it
got up there. It is `is: intake` (unfiled, inert, not yet placed) and `disposition: private`. On bay 1
it is `D:/fcpm-audit`.

The attic is addressable before anything has been written about it. `fcpm library` gives what a disk
knows by itself: the machine, the path, the volume's serial and label, and whether the folder is there.
That is the attic's coordinates.

**Downloads** is the second holding, and follows the same plan with fewer expectations. It is whatever a
browser on the computer was asked to fetch: installers, exports, and members' files passing through.
It is `is: intake` and `disposition: private` too, but `expects: ordinary`, where the attic `expects:
sensitive`. If this system ever needs to understand downloads, the library is how it addresses them.
On bay 1 it is `~/Downloads`.

**Drive** is the organization's Google Drive, mounted on bay 1 as a drive (streamed, not mirrored down
into a folder). It is the cloud slice people drop files into to reach another of our computers, the
cloud version of a shared drive on the LAN, beside OneDrive and Dropbox when those get their slices. It
also holds the board's documents that are still there while they are moved off. It is a live line to a
cloud source, as `refs/` is to GitHub. It is `is: intake` and `expects: sensitive`, and it is bound by its
volume's label and the folder inside it (`{label: "Google Drive", in: "My Drive"}`), so it is found on
whatever letter Google gives it (it moved from `E:` to `Z:`). An x-ray of a streamed drive reads only what the
drive reports about each file, and downloads nothing.

### Members' projects

Board members run projects for the members, and those projects need somewhere to be staged. On the
organization's Google account, anything uploaded from our computers counts against that account's space,
whoever's folder it goes in. The only way around that would be to sign in someone else, so we don't.

Instead, we stage the projects ourselves: they can keep uploading, and we manage the space. A
project's files come off the Drive into the attic, and the x-ray of their arrival is our record of what
the project was. We study each one as a file format, as something someone did, and not for its
content. Production's pipeline should understand a project shaped like that.

## The library here: a folder per branch

On each machine, the library is `~/code/library`. It holds one folder per branch the machine keeps,
each a worktree of the library's repository (`~/code/library/.git`). Everything is in folders, and
past the top level a folder name says which branch you are on. That is why each concern gets a
branch and not a nesting inside another.

| folder | branch | goes |
|---|---|---|
| `retain/` | `retain/<machine>` | to origin.local, after each commit, and never past it |
| `studies/` | `retain/studies` | to origin.local, like `retain/`, and never past it |
| `librarians/` | `librarians` | to origin.local, and never past it. Instructions, never data |
| `lobby/` | `lobby` | to GitHub. First contact and orientation: directions to things on other branches, and nothing else |

**`retain` is the LAN's earmark, not this machine's.** A branch named `retain/…` goes to the LAN's
origin (origin.local), eagerly: `fcpm library` pushes it after each commit, when the library has a
remote there, and otherwise it waits here for the next one. It never goes past the origin: not to
GitHub, never published. That is what makes it a directory: anyone on the LAN reads the record from
the origin, without asking an agent or opening a session on the machine that wrote it (Autumn,
2026-11-16). Two gates hold it there:

- **The machine's pre-push hook** lets `retain/`, `refs/grants/` and `refs/jobs/` go to origin.local and
  refuses every other remote. The library's repository has no GitHub remote either.
- **The origin's relay** never carries the library's branches to GitHub (`LAN_ONLY` in
  [`intake`](../machines/origin/intake): `retain/*`, `library`, `librarians`), in any repository,
  whatever relay says. Library content leaves GitHub outright, and the origin is the gate that knows
  it. A branch pushed there is recorded as `lan only` and stays.

Retained branches are our own operational history, chronicled on the LAN.

**Studies** are a folder each on `retain/studies`, flat: the study in our own words, confusion included, and
every file tree made during it, written out. That is where we keep what we do. A cloud session can't reach
the LAN, so its studies come in on the cloud line: the `studies` branch on GitHub, or a pull request. We take
that payload as it came, its folder byte for byte, and note in `retain/studies`' README where it came from
(the branch or pull request, its commit, the session). It may not be how we would have written it, but it was
shared that way, so it is valid: it is our job to learn from outside study too, where our rules don't matter
at the point of their authorship. What settles is summarized into a released branch.

**The lobby** is first contact. It orients people and takes them to things on other branches, the
released ones first: what is here, where it is, what each place exposes, and how to ask. It holds
directions, never the things themselves. Not made yet.

**One `retain` branch, or one per machine?** Open; Autumn is deciding. Today each machine has its own
`retain/<machine>`. The leaning is one `retain` branch we all work on, with a folder per machine. That
way the record is canonical, and the hub's library knows everything when it needs to, because each
machine knows what it holds and when that is out of date. A thing moved to another machine could be
noticed by the machine it arrived on, which updates its own folder without touching anyone else's.
Seeing it all aligned in one place is easier than finding pieces apart.

### The city

`library/city/` on the `library` branch is Fort Collins as the city and Transfort publish it, as things we
can search ([workshed.md, Scopes](workshed.md#scopes)): `parks/`, `natural-areas/`, `transit/routes/` and
`transit/stops/`, a folder each holding `shape.geojson` and `city.scopes`, its lines
(`park.spring-park.near.route.14`), all wearing `city.fort-collins`; and `catalog.md`, both open-data portals
as one list. Every place
names the city's own page for it first, then the stops within a five-minute walk (400 m of its edge) and their
routes, and every stop and route names the places near it, so any one of them leads to the others. The city
holds the shapes and the pages; nothing in the open data links one to the other, so the join is ours, by name,
asked of the city's site once a week, and the places it could not find are listed in `city/README.md`.

`bin/city-shapes.py` writes it, the digitization crew's `city` line, once a day, into the library shed's
checkout of the branch, and pushes it to origin.local. Each source is asked whether it changed (ETag,
Last-Modified), so a quiet day costs the city a 304 and writes the same bytes. We follow; we are never the
authority, and never instant. Transfort's data is redistributed under its own terms: the data, never its
marks, and said to be unofficial. The study behind it is `open-data/` on `retain/studies`.

**Layers.** `bin/city-layers.py` adds readers on top, each writing its own `.scopes` beside `city.scopes` and
folders of its own things, the crew's `layers` line, after the city's: `districts` (the council district,
precinct, and state senate and house districts a place or stop is in; `districts/<n>/` with its member),
`trails` (the named trails within 50 m of a place; `trails/<name>/`: surface, dogs, bikes, its segment count and
length total), and `osm` (what OpenStreetMap maps inside a park or natural area, in its own tags:
`leisure.playground`, `amenity.toilets`, `leisure.pitch.sport.tennis`; Overpass asked at most weekly, ©
OpenStreetMap contributors, ODbL). Together they answer `playground route max` or `pitch tennis district 6`.
`city/layers.md` says when each last read.

**As is.** Every value is the source's own, as it sent it: a name in the city's capitals, acres to the city's eight
places, OpenStreetMap's own tags, Transfort's dates and colours as its feed writes them. Nothing is rounded,
recased or renamed on the way in, so there is no invisible transformation between a source and what we hold; the
extraction is the truth. What is ours is said as ours: which thing a line is about, what is near or inside what,
the city page we found for it, and a sum we made. A normalized value (acres to two places, a name as people
write it) is a reader of its own whose lines say what it did, and it never replaces the source's line.

## X-rays

`fcpm library xray LABEL` takes a picture of a holding's shape. It writes one row per entry: path, kind
(`d` folder, `f` file, `l` link, `?` unreadable), bytes, modified, created, and attributes. The
attributes are `R` read-only, `H` hidden, `S` system, `O` offline, and `P` pinned to the cloud. `O` and
`P` mark a cloud placeholder, where the name is here and the bytes are not. Opening a file is never
part of an x-ray. A link is recorded and not followed.

The x-ray goes to `retain/<LABEL>/xray.tsv`, and each look is a commit on `retain/<machine>`. So the
metadata is version-tracked, even though the bytes are not and never will be. Nothing is written into a
holding. A sidecar beside every download would confuse whoever uses the folder, and would go when they
delete. Turning Downloads into a git repository is out of the question. The first line of an x-ray gives
the coordinates and the totals.

- `fcpm library diff LABEL [REV]` compares the holding now against its last x-ray, or the one at
  `REV`. It works like `git status`: `A` came, `D` went, `M` changed size or time. A folder that came or
  went whole is one line, with its count and size. An x-ray also prints what changed since the one
  before.
- `fcpm library log LABEL` lists the looks, one line each.

We know roughly when something arrived, as of the look that first saw it. We are not hooking the file
system. This is about what sits at rest. Something in flight may have no metadata yet, and waits until a
look, or an agent, notices it.

None of it comes into this repository. The repository is public, and an attic's file names name people.
Even the shape is not for just anyone to x-ray that deeply: we do not know for sure what is in there.

Later, with `ffprobe` on the bay: a media column (container, duration, streams), still with nothing
decoded.

## Old data compacts to summaries

Things in a library move off the shelf before they go anywhere else:

1. **On the shelf.** In use, and put in front of people.
2. **Off the shelf.** Still there, and reachable by anyone who goes in, but no longer put on anyone's
   monitor. Most of our old machines are here: nobody has plugged them in, so nobody is missing them.
3. **Summary.** The x-ray and what it comes to, kept in `retain/`, and nothing more. This is where
   most old data should sit until someone makes a judgment call.
4. **Judged.** Salvage something, keep the whole thing, or let it go. Wiping a machine for another use
   waits for this step, and the summary is what the call is made on.

`fcpm library summary LABEL [REV]` is the step from 2 to 3. Every x-ray writes one beside itself
(`retain/<LABEL>/summary.txt`, in the same commit), worked out from the x-ray alone. It gives:

- the totals and the dates;
- the kinds of file, by weight;
- the parts every Windows install has (`Windows`, `Program Files`, `ProgramData`, the page file, each
  home's `AppData`, and so on), folded into one line;
- what stands out, heaviest first. That is a line per top folder, or per folder inside a home
  (`Users/<someone>/Videos`), with its dates and its main kinds of file. Loose files are one line per
  level.

That is the question to answer for an old machine, without reading a file: is there a file structure
here that stands out from normal Windows, and is it worth diving in to salvage something? What we find
in the Google Drive is mostly what succeeded these machines, and that helps the comparison.

### The inventory wing

A lot of this is our own inventorying. It is not necessarily private data, but it needs somewhere to be
kept. The machines waiting for a judgment call (two old desktops, a laptop, the one meant for music,
perhaps called "dj", and the kiosk, which is barely holding together) each become a holding once a copy
of their disk is taken, or the disk is attached to a bay. Each is x-rayed, summarized and judged. A
machine judged worth keeping may be rebuilt on something predictable (Alpine, say), with drivers looked
into only where they matter.

### The barn: big drives, kept unplugged

Some old machines had big drives, bigger than the Drobo can take. Their dumps may live on one large
drive that stays unplugged, a barn. Then "the whole dump is over there" is something the library can
say. The Buffalo DriveStation is a candidate barn, once what it holds now is known.

A barn drive is bound by its **label alone** (`buffalo: {label: "RAID Backup"}`). Plugged in, it is
found on whatever letter it was given. Unplugged, `fcpm library` says "not plugged in" and shows its
last x-ray, and the console lists it as unplugged. That is its ordinary state, not an alarm. This is
the opposite of a binding that names a letter and a label (`{at: "E:/", label: ...}`): for that one, a
wrong volume is a person's to put right.

The Buffalo is the first target. Its RAID Backup volume (NTFS, about 19 TB used) holds the old Mac
backup that once ran this place. We do not care about it as such. We need to know whether it is safe to
cut loose. It is RAID 6 with one drive down ([troves/buffalo-drivestation](https://github.com/FC-Public-Media/buffalo-drivestation)),
so the order is: x-ray it first, which reads only names, and let its summary say whether anything is
worth the one heavy read a copy would be. It is bound on the kiosk, where it was measured, and on bay 1,
whichever it is plugged into.

### `retain` is our half

What sits in `retain/` is our half of things. Being here, at a machine on the media node's LAN, is a
better sign that someone may look than any git account could be. That is why a retained branch never
goes to GitHub, and why its summaries can say more than anything we publish.

## Librarians

The library's code does not read files. Librarian agents will have to, because they are the caretakers.
So they answer to a constitution, on the `librarians` branch, and to each place's decorum: why things
are there at all, and what they are for. Decorum is written per place, never per item. It is an
`AGENTS.md` in that place's own folder shape on the `librarians` branch: `attic/AGENTS.md`, and
`attic/<folder>/AGENTS.md` only where a folder needs its own. That slice of the structure is what gets
committed. It holds the instructions, kept apart from the data.

"Librarians" is a mixed bag: many people and agents work the metadata, each in a role. It is the
advocate engine's seat system, scoped to the library. The seats are named on the `librarians` branch
(`seats.yml`, provisional names): a receptionist at the front door, a labeler, an organizer (the only
seat that moves anything), a checker (the one that reaches the disk), a toolsmith, and a corrector. Each seat takes
up a unit or two of work at a time. Before it starts, it writes a contract for that work into
`retain/`: what it will read and write, what it will leave alone, and when it stops. A contract only
narrows what the constitution and the place's decorum already allow.

**Scripts, not hands.** A whole set of files is a scriptable task. Seats never read through a set file
by file, burning tokens. They handle a single file only when it was asked for, and only when they are
sure what it is. The right metadata is found once, in a pass a person supervises live: they describe
what to gather and correct its shape until it is right, laying down the constitution as they talk
instead of typing it up. That pass ends in an **extractor**, a script on `main` holding no paths and no
data. The extractor is proved against the example set the pass used, and that set and the accepted
metadata are kept in `retain/`. A passing proof shows the mapping is good; a failing one is how we
notice it broke, and the toolsmith seat mends it. Proved extractors run on a schedule, in step with the
x-ray, so no seat thinks about the run, and the seats check what comes out and raise what looks wrong.

The passes are kept separate, and each builds on the one before:

1. **The x-ray**, by `fcpm library xray`. No agent is involved.
2. **Caretakers** write metadata into `retain/`. A file becomes a folder in the metadata tree once
   there is something to write about it. Only the noteworthy get one. Summaries can be prepared ahead:
   of a listing, of what its metadata is like, of its timeline.
3. **Librarians** look for things starting from the metadata. `fcpm library browse LABEL [PATH]` lists
   one level of the last x-ray and never touches the holding. Where a librarian goes on to the disk, and
   finds something is not where the metadata says it should be, it files an error in `retain/` and
   stops there.
4. **Correction** is a pass of its own: it reads the errors and fixes the metadata.

**Start at the top of an entry's listing.** A note sits on the highest entry it is true of. A project
with a `build/` folder needs no note on `build/` for us to know it is there: the project's note can say
so, and an agent that starts at the beginning of that entry's listing finds it.

**A pass on request, toward a target layout.** A person studying a holding, say to categorize it and
move it, can ask for a metadata pass instead of waiting for the next one. A place's decorum may give a
target layout ("the layout we want is this; do your best"), and librarians sort toward it. Whatever a
pass has not fitted into the layout is noted as outside it, at the top of what is not understood. Then
the pass stops there: no librarian crawls a mixed pile whose structure it does not understand.
`fcpm library xray` is the mechanical part of a pass; asking for the librarians' part is not built.

A person's reach is unchanged. Whoever can reach a holding reads it (Reading, above).

## Seats rooted in a project (notes)

Some seats will be especially active in maintaining one project held with us: someone's documents, or
someone's git repository that they keep here so that, for example, its dependencies are kept up. That
is just another seat, but its root is the project and not the core of the library. It is also a way a
member can use our hardware: if they are willing to be a member, we can offer that kind of compute.

The same seats can study projects to give advice. For example: "you're having a lot of trouble
expressing this idea on this framework; a lot of other people are having more success here, and it
would look like this stub." That is an advocate report, from the reconnaissance the engine already
describes ([`SEATS.md`](https://github.com/FCCN-ANTIBODY/library.anecdote.channel/blob/main/SEATS.md)).
Its finding is about the tool, not about them, and it is visible only from where the seat sits, across
holdings.

Two things carry over unchanged:

- **Reading a project is a term of admission.** The engine's rule is that held content is inert, and
  that a seat handed nothing reads nothing. A project opts into maintenance or advice when it comes in,
  visibly, and can decline. Where that term is written (the bottle's manifest, most likely) is the
  engine's open question, and is not improvised here.
- **A project seat answers to the same constitution.** Its decorum is the project's own `AGENTS.md` on
  the `librarians` branch, its contracts go into `retain/`, and it works with scripts, not hands.

This is the larger reason to address things through the library. We point agents at parts of the
library, by holding and path, rather than at spots on a local disk. A spot on a disk means nothing to an
agent. A holding comes with its decorum, its record, and its terms.

## The grant book

Built (stage 1): `fcpm library grant SEAT UNIT WORDS`, `release GRANT`, `grants`, and the console,
below. The first caller-in is digitization's `seats` (advocate seats called in by hand; machines/digitization/PROFILE.md,
Seats), which holds both grants for a call as itself. A grant's holder is found by walking up from `fcpm` past shells and interpreters, so it is the
agent that asked (on bay 1, `claude.exe`) or a person's terminal. The workshed is the second: a worktree made is
a grant spent at once, and a served one is held by its server ([workshed.md](workshed.md)). Helm serves the
console ([consoles.md](consoles.md)). Not yet: jobs (`ask`, `wait`), votes, and signing.

A grant here is the engine's ordinary sense of the word: a delegation of capability, common, cheap, and
boring ([`GRANTS.md`](https://github.com/FCCN-ANTIBODY/library.anecdote.channel/blob/main/GRANTS.md)).
It is not a permission token, and for now it stops nothing. What it is for today is body language: who
is at work, on what, and how often. Ten grants in an hour against one is worth seeing. (The crew's
`GRANTS` file, which lists what a crew may run, and the keystore's grant of a key are the same mood,
with different jobs.)

Our first attempt designed the grant book before the library existed, on one computer, and the book
never got to sit in plain view. This time the book is part of the library every machine already has,
and no service runs it.

### Two grants for one agent

1. **Calling in.** The process that calls an agent in (the crew's supervisor, a scheduled task, a remote
   control server) holds a grant to make that agent's worktree. It fabricates the worktree with `git
   worktree add`; nothing is cloned. Once the worktree exists, the grant is spent and is not issued
   again.
2. **Work.** The agent that wakes, in its seat, holds a grant for its unit of work: the seat, the holding
   and path, and a short description in its own words. There is no vocabulary of permissions to choose
   from, because these are intelligent agents and the words are the grant. "Run the metadata pass for
   the attic's projects" is granted behavior, and so is the preparation the job needs. The agent releases
   the grant when it is done, or the grant lapses when its process ends.

### Where the book is

In the library's own repository, `~/code/library/.git`, as refs:

- `refs/grants/live/<id>` is the grants in use right now. `git for-each-ref refs/grants/live` is who is at
  work.
- `refs/grants/book` is an append-only chain of commits: issued, released, lapsed, voted. `git log
  refs/grants/book --since=1.hour` is how much.
- Each entry is a commit. Its subject is the description. Its trailers are `Seat:`, `Unit:`, `Holder:`
  (process id and start time), `Called-in-by:` (the parent grant), and `Job:`.

Refs under `refs/grants/` are not a branch. A clone does not fetch them by default and `git branch` does
not list them. They are in plain view to anyone who looks, but are not dumped on anyone. That is
obscurity and not confidentiality, which is fine, because a grant is not a secret. The pre-push hook
treats `refs/grants/` as it treats `retain/`: origin.local takes it, and nothing else does.

Later, a grant's commit can be signed with the machine's own key from its birth ([keystore.md](keystore.md);
on Windows, the ssh agent holds it). That gives claims bound to an ID, with nothing new in the
cryptography. Credential Manager is not the place for grants: it holds secrets, and a grant is not one.
It holds what a grant may later open, such as a core or a sealed address.

### Liveness comes from the operating system

A grant names its holder: the process id and the start time of the process that holds it. The
operating system already knows whether that process is still running (`GetProcessTimes` on Windows,
`/proc` on Linux), so we use what the environment gives us. A grant whose process ended without
releasing it is lapsed, and whoever reads the book next records that. Nothing depends on an agent's
manners. Later, the caller can follow the whole process tree it started: a Windows job object, or a
systemd scope.

### Asking, not doing: jobs are shared promises

A seat can ask for work to be performed instead of running the scripts itself: a metadata pass, or an
extractor's run. It asks, waits, is told it is done, lets go, and moves on. The job is named by what it
is for, so identical asks share a name: `xray/attic`, or `extract/<extractor>/attic@<x-ray commit>`.

The first asker creates `refs/jobs/<key>`. Git creates a ref only if it is absent, and does so
atomically, so exactly one asker makes the job and every other finds it already there and waits on the
same one. When the job is done, its ref points at the result, and the waiters see that and go. Ten
seats noticing the same thing at once make one job: no congestion, no live pipes between agents, and no
daemon. Waiting means reading a ref. A Windows named event could wake the waiters instead, later.

Proved on bay 1 (2026-11-16): a second create-only `git update-ref` on the same job fails with exit 128,
so its asker knows to wait; and any process's start time can be read through `GetProcessTimes`.

### Votes

When a seat closes a contract, it votes in the book: what it thinks is needed next. That might be a seat
to come up ("an organizer for attic/Google Drive") or "next round, no problems", with a line saying why.
The votes are the bucket that scheduling reads. Many votes for one seat means it should be scheduled. A
cluster of the same unexpected complaint means something is wrong, perhaps a merge conflict that keeps
work from landing. Seats collaborate through their branches, not through live connections, and a vote
is how one asks for another to come up.

### Up to the council

An advocate seat reads the book the way it reads anything else: issuance rates, lapsed grants, clusters
of votes. When every agent is being warned that the cloud drive is full and nothing works, that is not a
fire. It is a finding for the council's report (the `council` branch), with the options attached when
there are any, so it reaches the next board meeting as a problem brought, and maybe with its solutions.
The advocates are not in charge of fixing it. Their job is to say that something needs to happen.

### The console

The console is what Helm will show: who is at work, the jobs, the last hour's grants, and the last
x-rays, flat, at a glance. It is a buffer, `~/code/library/console.txt`, written out whole. It is not
a tailed log. The only thing it guarantees is when it was written: its first line says when, and until
when it is fresh.

- **Reading it never runs the query.** `fcpm library console` shows the buffer. If the buffer is older
  than a minute, it is rewritten first, but only by the one reader that takes the lock; everyone else
  is shown what is there. So it is impossible, by construction, to ask too often: a hundred readers in
  a minute cause one rewrite, and nobody hammers the grant book to find out what is going on.
- **`fcpm library console --beat`** rewrites it every minute, for a crew line or Helm to keep it warm.
  Production's helm keeps it warm, as its `library` console ([consoles.md](consoles.md)).
- **Helm serves the file as it is, and runs none of the code.** A librarian on bay 2 asks bay 1's Helm
  for the console and can see whether an agent is already working on something, ask for one, watch it
  start working, and watch it stop, all on its own. Bay 1 can do the same with digitization. The
  console is not published on the network. Helm holds it up as a proof, so that people can answer
  their own questions, and when they can't, they know what to ask for. That is stage 2.

### The receptionist's inbox

An ask of the library comes in like any other wizard's reply: someone forms it on `/library/ask/`, shows it
to a camera wherever one is (digitization's, today), and Helm passes it to the helm that holds the library
(production's, in `helms.yml`). That helm sets it down in the library's own inbox,
`~/code/library/inbox/<lane>/`, one file per ask. It does not need a live agent. The ask waits there until a
seat picks it up.

**A lane is a wizard, chosen by whoever asks.** No dispatcher reads a request and decides what it wants,
because a dispatcher would get that wrong. When a different behaviour is needed, it is written down as a
lane in `library.yml`, with its own wizard, so that we can pull that string on purpose:

| lane | wizard | budget per round |
|---|---|---|
| `urgent` | `wizard:library+urgent` | all of them, before any other lane |
| `ask` | `wizard:library+ask` | 2, oldest first; the rest wait for the next round |

- `fcpm library inbox` lists what is waiting, lane by lane.
- `fcpm library inbox round` is what a seat runs. It takes this round's asks, lanes in order and each within
  its budget, moves them to `inbox/taken/`, and prints one JSON line per ask. Moving a file is the claim, so
  two rounds at once never take the same ask.
- `fcpm library inbox answer NONCE WORDS` files the answer in `inbox/answered/`, and bottles it for the
  outbox: an iced bottle of kind `fcpm.answer`, keyed by the ask's nonce and signed by the library's own key,
  at `~/code/library/outbox/<nonce>.gif` ([pickup.md](pickup.md#the-iced-bottle)). Its transfer id is
  recorded in `retain/` (`outbox/issued.tsv`), so a bottle that comes back can be proved ours.
  `fcpm library outbox` lists the outbox, and `outbox make` bottles anything answered but not bottled yet.
  Delivering it to the station's loop is the next step ([pickup.md](pickup.md#steps), 3 and 4).
- `fcpm library signer` shows the library's bottling identity by its fingerprint, never its value.
  `signer mint` makes it once, on purpose, into this machine's keychain (the `library` group in its
  `keys.yml`); it refuses if one is held, because a new identity makes every reader that trusted the old one
  see a stranger. Without one, an answer is still filed, and simply waits to be bottled.

The console shows the inbox as counts only. An ask's words are for the library, not for its peers. A
priority call made on demand, such as calling a seat up at once for an urgent ask, would be another string
of its own, written as one.

## The keychain wing, and data piles (notes)

Not built. Kept so that the shape is here when it is wanted ([pile-lines.md](pile-lines.md) designs the lines beside each entry). A data pile
([data-pile](https://github.com/FCCN-ANTIBODY/data-pile)) holds the shape of what it is looking for,
and that shape can change. What arrives either matches it or doesn't get in. The pile assembles
disparate data under one idea. Because the reader fetches the pile and measures it themselves, the
reader resolves any ambiguity.

For the library, that means:

- **A pile per idea, entries in time order.** For example, a keychain for the old Google era: a single
  pile, not split any further, with each item entered as it comes. Entries are age-encrypted. Each one
  carries the date it entered the pile, beyond whatever metadata it brought, and nothing can hide inside
  it. It is observable by construction, with no clever machinery.
- **A trunk that has been opened.** An x-ray of a folder can go into a pile apart from its payloads.
  Then the pile can be read at whim by anyone intending to look. No redaction is applied, except where a
  value is entered and decrypted in advance to prove what it was.
- **Cores, by range.** Protected values are read through a granted core, a private key that opens a
  range of the pile. This grant is the library's only reading API (see Reading, above). The grantee
  reads the data themselves, and we never hand a value over. Ranges
  are measured in characters, the unit a value is read at. So a secrets pile is one flat buffer,
  something like an environment map with secrets marked plainly, and each entry's character positions
  are recorded as it goes in.
- **Truncation is rotation.** Appending keeps old ranges good, up to a limit, but reading means
  reading the whole pile, as with migrations. Eventually the pile is squashed: the content is truncated
  and the entries are put back in. That invalidates every core that ever worked, even where the values
  are unchanged. This is token rotation, under our control. A holder whose grant is gone asks again,
  through Helm, and Helm knows the way.
- **Two piles, if any.** A real one kept in version control, which cannot reveal anything that way. A
  published one, flushed from it as a flat buffer whenever needed, which records an update at every
  position as long as it is read whole. Keep the moving parts few.

The reason not to hand secrets over at a keyboard: a secret is something someone holds, not something
fetched every time. CI calls a fetched value a secret, but that is a different thing. There are real
reasons someone may need one before any of our infrastructure is running, like building an SD card to
recover a machine. Helm can ask even then. Having a keyboard and a monitor in front of you is not a
reason to have the value. The keystore ([keystore.md](keystore.md)) is where sealed values go today.
The pile is how a sealed value could sit in the open and still be granted by range.

## Next

1. Bind holdings on the other machines (`machines/<job>/library.yml`), and have Helm address them, so
   a big Helm knows which holdings a little one keeps and where. Helm addresses and does not serve:
   reading what is there means reaching it, the same as anywhere else (Reading, above).
2. The ask: one front door for a grant, which hands over a core or a sealed address, and may seat the
   librarian to browse for the asker.
3. The librarians' constitution and the attic's and downloads' decorum, on the `librarians` branch,
   and the shape of a note, a summary and an error in `retain/`. Then a local model as the first
   caretaker.
4. A pass on request, and target layouts in decorum. A supervised pass ends in an extractor, with
   `fcpm library` running it, proving it against its example set, and scheduling it with the x-ray.
   The first candidate is the members' projects in the attic.
5. The lobby: compiled by `fcpm library`, from `library.yml` and what each holding exposes.
6. Upstream: put branches-by-purpose, the attic and the x-ray to the engine as a petition. They are
   vocabulary every library would use, not just ours.
   Later, and not yet: staged summary applied to our own code, to make a guide to it that can be tested.
   That is the approachable way into this repository, rather than agent instructions written for other
   agents about how to caretake it.
7. Seats rooted in a project: maintenance and advice as a member's term of admission, once the engine
   says where the term is written.
8. The receptionist's inbox, stage 2: answers back to the asker through the loop; a seat that runs
   `inbox round` on a schedule, within budget, under a grant; a priority call that brings one up at once.
   **The board meeting's demonstration** is the measure. Someone shows a `/library/ask/` code to the camera,
   asking a free-form question. The answer comes back to a monitor on the Raspberry Pi, and is clear and
   coherent. It is fast, because it is a crawl of the metadata (summaries, x-rays, the console) and not of
   anyone's files, so the only real wait is the model's thinking. Any agent may serve it, a small and cheap
   one included: the point is that a new kind of developer can pick this up and know what is going on.
   After that, members do it from their own phones, onboarded with a passkey (signed bottles on the LAN
   first).
9. The grant book, stage 2: Helm serves the console (bay 1 reads digitization's, and the other way
   round), a crew line keeps it beating, and `ask`/`wait` on `refs/jobs/`. Then votes at a contract's
   close, signed entries, and an advocate seat that reads the book.
10. The keychain pile, once the keystore holds its first values.
