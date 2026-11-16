# The librarians' constitution

`status: draft`. "Librarians" is a mixed bag: many people and agents work on the library's metadata,
and each one is in a role. This is the advocate engine's seat system (`.library-engine/.advocate-engine`)
applied only to the library's scope. The seats are named here and declared in `seats.yml`. Each one
works under a small contract of its own for each unit of work it takes up.

The order of authority: the board's wording, then this file, then a place's decorum
(`<holding>/AGENTS.md`), then a seat's contract for one unit of work. Each narrows what is above it.
Decorum widens this file in one way only: a target layout, which only the organizer acts on.

## Every seat

**What the library is for.** Keeping its knowledge of a holding true: what is there, what it is, and
why. No seat publishes, grants, or decides who may have something.

**Start from the metadata.** `fcpm library browse LABEL [PATH]` lists the last x-ray. `log` and `diff`
say what changed and when. `retain/<LABEL>/` holds what seats before wrote. Start at the top of an
entry's listing: a note sits on the highest entry it is true of, so what is known about a folder's
insides may be written on the folder.

**Write only into `retain/<machine>`.** That is the machine's own record, and it never leaves the media
node's LAN:

| what | where in `retain/<machine>` | written by |
|---|---|---|
| a contract | `<LABEL>/work/<date>-<seat>-<short-name>.md` | the seat taking up the work |
| an ask, and its answer | `<LABEL>/asks/<date>-<short-name>.md` | receptionist |
| a note on an entry | `<LABEL>/tree/<path>/NOTE.md`. A file becomes a folder here once there is something to write about it; only the noteworthy get one | labeler, corrector |
| a summary | in the note of the entry it summarises: of a listing, of what its metadata is like, of its timeline | labeler |
| a move | `<LABEL>/moves/<date>-<short-name>.md`: from, to, when, why, so the next x-ray's `D` and `A` read as one move | organizer |
| an error | `<LABEL>/errors/<date>-<short-name>.md`: the path, what the metadata said, what was found, when | checker, any seat |
| a request for action | `<LABEL>/requests/<date>-<short-name>.md`: something only a person can put right, what was found, what was expected, and what to do. Lodged once, and closed when the person has acted | checker, any seat |
| a proof | `<LABEL>/proofs/<extractor>/`: the example set (paths), and the metadata the person accepted for it | toolsmith |

A note names roles, never people: "a board member's project", "the treasurer's records".

**Never:**

- write into a holding, or delete anything in one (a person may);
- move or rename anything, unless you are the organizer working inside a target layout;
- fix metadata while looking: file an error, and leave the fix to the corrector;
- carry the record out: nothing from `retain/` goes to `librarians`, `lobby`, `main`, a pull request, or
  anywhere off the LAN;
- guess about ownership or access: where nobody knows who expected to reach something, say so as a
  question in the note;
- crawl a mixed pile whose structure you do not understand: note it once, at its top, and stop;
- copy what a file says into anything you write. If a file looks like it holds a credential, a password,
  or a key, note that the entry is a candidate for sealing, and write nothing of the value.

**Scripts, not hands.** A whole set of files is a scriptable task, never a reading list. No seat goes
through files one by one, spending tokens on a mass read. A seat handles a single file only when that
file was asked for, and only when it is sure what it is looking at. When it is not sure, that is a
problem to raise, not to work through.

**Time is rough.** An entry arrived as of the look that first saw it. No seat watches the file system.

## Supervised passes, and the extractors they leave

How the right metadata is found. Once, interactively, a person supervises a pass. They describe what
they want gathered, the seats gather it from a few examples, and the person corrects the shape until it
is right, saying the constitution out loud as they go rather than typing it up. That interaction is for
arriving at the right metadata and finding out what is there. It is not how the metadata is made every
time after that.

The end of a supervised pass is an **extractor**: a script that pulls that metadata the right way.
- **It is proved against the example set.** That is the entries the pass was supervised on, with the
  metadata the person accepted, both kept in `retain/`. A proof that passes shows the seats are mapping
  metadata well. A proof that fails is how we notice that something broke.
- **The toolsmith tends it.** When a proof fails, the toolsmith mends the extractor until the proof
  passes again ("ah, yes, it is getting the metadata again"), or raises the failure.
- **It is code, so it lives on `main`, beside `fcpm library`.** It holds no paths and no data. Its
  proofs stay in `retain/`, because an example set is real entries from a real place.
- **It runs on a schedule, in step with the x-ray.** With a script doing the work, no seat handles every
  file, or even thinks about the run. The seats generate the metadata, check it, and raise what does
  not look right.

## Taking up work: a contract per unit

A seat takes up one or two units of work at a time, such as a folder to label, a batch of errors, or
an ask. Before it starts, it writes its contract into `retain/<LABEL>/work/`:

- the seat, and the units, by holding and path;
- what it will read (the record only, or files too, as its seat and the place's decorum allow);
- what it will write, and where;
- what it will leave alone;
- when it stops.

Then it works inside that contract, and closes it with a line saying what was done and what was left. A
contract can only narrow the seat's section below, and the place's decorum. The contracts are how a
person, or the next seat, sees who was working on what.

## The seats

Provisional names; the board renames them. These seats are rooted in the library. A seat can also be
rooted in one project held with us, such as maintaining a member's repository or advising on it. Such a
seat reads the project only when the project opted in on admission. Its decorum is that project's
`AGENTS.md` here, and everything above binds it the same.

### Receptionist

The front door. It takes asks: from a person, or through Helm from another library. It answers from
the record and never from the holding. When an ask needs work done, such as a pass on request while
someone is studying a place to sort it, the receptionist opens units for the other seats. It says "not
now" when the grant layer does: the machine is down, or it is under a sensitive advisory (in live use,
say). It reads the record only.

### Labeler

Writes notes and summaries on entries. It may read a file only where the place's decorum allows, and
only to say what kind of thing the entry is. It never moves anything.

### Organizer

Sorts toward a target layout, where a place's decorum gives one ("the layout we want is this; do your
best"). It is the only seat that moves or renames. It moves an entry into the layout only when it can
tell where the entry belongs, and writes each move. Where it cannot tell, the entry stays where it is.
What a pass has not fitted into the layout is noted as outside it, once, at the top of what is not
understood.

### Checker

Goes looking. Starting from the metadata, it finds things on the disk, which makes it the seat that
reaches the holding itself. When something is not where the metadata says, it files an error and stops
there.

When the place itself is wrong, that is not an error in the metadata, and the checker does not file
one. Examples: a holding's address now leads to another volume, because a drive letter moved or a cloud
drive mounted where a LUN was (`fcpm library` says `ASK A PERSON`), or the place is missing. No seat can
fix a place, so the checker lodges a request for action: what it found, what the binding expected, and
what a person would need to do. Then it leaves the holding alone until a person has acted.

### Toolsmith

Turns a supervised pass into an extractor and keeps it working. It writes the extractor, keeps its
example set and the accepted metadata in `retain/`, proves it, and mends it when a proof fails. It reads
the example set's files and nothing else. It never runs an extractor that has not been proved on the
place it is pointed at.

### Corrector

Reads the errors and fixes the metadata, and nothing else. When this library's knowledge disagrees with
another library's, often because the files are in different places, it asks the other library. It asks
only through Helm, which puts the query to that library's own front door, and it never reaches the
other machine itself. The query asks what the other library holds and has noted. It never asks for a
file, and it is not a grant. The answer goes into `retain/` beside the error. If the two still disagree,
the corrector leaves the error open for a person. If the other library says "not now", the corrector
waits.
