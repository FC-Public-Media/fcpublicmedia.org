# The library

What FCPM's library is, where it keeps things, and what it can say about them. Built: `library.yml`, a
machine's binding, and `fcpm library` (status, where, xray, diff, browse), on bay 1's attic and
downloads. The rest is notes: Helm addressing other machines' holdings, the ask, caretaking, and the
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

## X-rays

`fcpm library xray LABEL` takes a picture of a holding's shape. It writes one row per entry: path, kind
(`d` folder, `f` file, `l` link, `?` unreadable), bytes, modified, created, and attributes. The
attributes are `R` read-only, `H` hidden, `S` system, `O` offline, and `P` pinned to the cloud. `O` and
`P` mark a cloud placeholder, where the name is here and the bytes are not. Opening a file is never
part of an x-ray. A link is recorded and not followed.

The x-ray goes inside the holding, at `.library/xray/<when>.tsv`, so it travels with the holding. The
first line gives the coordinates and the totals. `.library/` itself is never x-rayed.

`fcpm library diff LABEL [XRAY]` compares the holding now against its last x-ray, or the one named.
It works like `git status`: `A` came, `D` went, `M` changed size or time. A folder that came or went
whole is shown as one line, with its count and size. An x-ray also prints what changed since the one
before.

That is as much of git as the attic gets. We do not version-track these bytes and will not try to. An
x-ray is a lightweight glimpse of what git would have shown. Because it sits beside the holding, it
stays exactly as private as the holding, and none of it comes into this repository. The repository is
public, and an attic's file names name people.

Later, with `ffprobe` on the bay: a media column (container, duration, streams), still with nothing
decoded.

## Agents work from metadata, never the disk

Agents are layered over the metadata and never given free access to a disk. Each layer builds on the
one below it:

1. **The x-ray**, by `fcpm library xray`: the shape, with no agent involved.
2. **Caretakers** build metadata on top of it (Caretaking, below).
3. **The librarian** browses what is there by leaning on that metadata, as part of an ask. `fcpm
   library browse LABEL [PATH]` is its tool. It lists one level of the last x-ray, with sizes, times
   and counts, and never touches the holding. A file that has gone since still shows until the next
   x-ray, which is the point: the librarian reads what the library knew, not what the disk says now.

A person's reach is unchanged. Whoever can reach a holding reads it (Reading, above). The rule is about
the agents we run: they get the x-ray, the notes and `where`, and never a free walk of the disk.

### Caretaking (notes)

A holding's `.library/` is also where the library leaves notes for caretaking agents. That means a
local model doing annotation that needs no thinking: it reads x-ray rows and writes them back into our
shape, the way a utility script would, without us writing scripts that break. This is FCPM's utility
and lives here, never as an agent skill. Not built. The shape when it is:

- The duty is written down in the holding (`.library/CARETAKING.md`) and points here.
- Annotations sit in the holding, keyed by path and by the x-ray they were made against. What is it
  (a member's project, a board record, media, unknown), and what role expected to reach it. That
  answers who expected access, which is open for the attic.
- A diff shows an annotation whose path has gone.

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
3. Caretaking: `.library/CARETAKING.md` and the annotation shape above, with the local model as the
   caretaker.
4. Upstream: put branches-by-purpose, the attic and the x-ray to the engine as a petition. They are
   vocabulary every library would use, not just ours.
5. The keychain pile, once the keystore holds its first values.
