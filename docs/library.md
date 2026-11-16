# The library

What FCPM's library is, where it keeps things, and what it can say about them. Built: `library.yml`, a
machine's binding, `~/code/library` with its `retain/` record, and `fcpm library` (status, where,
xray, diff, log, browse), on bay 1's attic and downloads; the `librarians` branch is seeded. The rest
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
| `library` | holdings in git: the tenant list, `city/`, `voices/` ([members.md](members.md#library-and-wizards)) | a skeleton |
| `origin` | working state: the map of the origin our computers fast-forward from | not made |
| `archives` | what we keep after we stop working on it | not made; not assigned yet |
| `lobby` | the way in: compiled from what is publishable, only directions to the rest | not made |
| `librarians` | what librarian agents answer to: the constitution, each place's decorum | seeded |
| `retain/<machine>` | a machine's own record: x-rays, and later notes, summaries, errors. Never pushed | bay 1 |

Working state and publishing are kept apart this way. The library had begun to gather working
state, and the origin's map was part of it.

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
| `retain/` | `retain/<machine>` | nowhere: it stays here, on the media node's LAN |
| `librarians/` | `librarians` | to GitHub. Instructions, never data |
| `lobby/` | `lobby` | to GitHub. Compiled from what is publishable: directions to the rest, and nothing else |

**`retain` is a marker.** A branch named `retain/…` is never pushed to GitHub and never published. The
library's repository has no GitHub remote, and its pre-push hook refuses `retain/` anywhere. If we ever
move a retained branch, to the LAN's origin say, that is a change we all notice together, made at the
hook and nowhere else. Retained branches are our own operational history: we are chronicling it,
privately.

**The lobby** is the way in. It is a thin branch compiled from what is publishable, holding only
directions to the rest: what holdings there are, what each exposes, and how to ask. Not made yet.

**One `retain` branch, or one per machine?** Open; Autumn is deciding. Today each machine has its own
`retain/<machine>`. The leaning is one `retain` branch we all work on, with a folder per machine. That
way the record is canonical, and the hub's library knows everything when it needs to, because each
machine knows what it holds and when that is out of date. A thing moved to another machine could be
noticed by the machine it arrived on, which updates its own folder without touching anyone else's.
Seeing it all aligned in one place is easier than finding pieces apart.

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

## The keychain wing, and data piles (notes)

Not built. Kept so that the shape is here when it is wanted. A data pile
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
7. The keychain pile, once the keystore holds its first values.
