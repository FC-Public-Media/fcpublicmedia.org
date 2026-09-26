# The library on main, and the wizards it keeps

`status: plan`, 2026-09-26. Written from Autumn's brief the same day, so that
the next session, on any machine, starts from what was decided rather than from
a conversation that may not survive. Nothing below is built unless it says so.

> I need FCPM to start growing its own library instead of this refs folder.
> Because that's going to be the way it behaves.

## What was decided, 2026-09-26

1. **FCPM grows its own library, as a folder on `main`.** Not the `library`
   branch this repository made on 2026-09-24 (`.gitmodules`, the
   `.library-engine` comment). *"I don't want stuff to hide from non-technical
   people."* This reverses that choice for FCPM only: station-node is moving its
   own library the other way (`docs/the-library-as-a-branch.md` there), and
   library.anecdote.channel's `GRANTS.md` prefers a branch. FCPM's reason is its
   board: what the organisation keeps has to be visible where they look.
2. **Branches are still allowed, on purpose.** An engine's residency wing may be
   a branch when it is heavy or needs isolation, and services we support may
   branch out (control branches and the like). *"I don't want to pollute the
   space, but it's not like we're going to be pristine."* Every branch says what
   it is for; none is a default hiding place.
3. **`refs/` is the proto-origin, and stays.** It looks like GitHub: org labels
   people would recognise. The library organises however it likes, and its
   organisation is expected to be found by trying. An `origin/` comes later
   (station-node's reserve: `docs/the-reserve.md` there).
4. **Mount `.you-engine`,** and it keeps its things **on `main`, in a folder**,
   not on its `you` branch. Same reason as 1.
5. **Wizards are curated and kept here.** A wizard is referenced as
   `<engine> + <label>` and resolves to that engine's current head (library
   engine, `wizards/residency-declares-them`). We maintain them at minimum.
6. **A wizard is shown, not linked.** On a studio screen it plays as a bottle:
   frames of QR, from a compressed payload, played by JavaScript. Someone's
   phone camera catches it, decodes the bytes, works the wizard, and sends the
   result back, usually as a pull request. *"It's not taking you to a URL. I'm
   emphatic about this."* A separate still control QR that gets a phone to the
   right page on our site is allowed for now. Served straight from our site,
   no camera is needed; on a screen it is.
7. **Reading a moving QR is a common workflow here,** so the tool that does it
   is part of the kit, not a demo.

## Who does which side, and what never becomes public

Autumn, 2026-09-26: the session **bubbles** (private-repository powers, the
stronger design backing) takes the **camera side**: catching a moving QR and
decoding the bubble. FCPM takes the **screen side**: the first purely optical
transmission, a studio screen playing a bubble with nothing but light between
it and the phone.

**A payload is never public here.** This repository and the site are public;
a teacher's materials carried as a wizard are not. So:

- the kiosk artifact and a screen's show config name a bottle **by reference
  only** (a wizard label, a digest), never by content;
- the door serves the frames at play time from a private source (a private
  repository held on the bubbles side, or the depot), and nothing it plays is
  written into this tree or built into the site;
- the player never fetches a payload from a public URL.

Open with bubbles: the frame format (anecdote.channel's carrier, fountain-coded,
or the you engine's stored GIF), whether a payload is encrypted to recipients or
meant for whoever is in the room, and where the private source lives.

## The wizards we already know we want

| wizard | tier | returns | notes |
|---|---|---|---|
| check-in | anyone | a visit | becomes a wizard, **on the you side**. Today it is `site/check-in.md` + `checkin.js`: local-only, geofenced, makes no network request |
| class registration | anyone / member | a registration, a passkey signature, a Stripe payment | membership status is known from when the passkey was accepted; recovery is out of band |
| start a show | member | a control branch, a starter workspace | `docs/MEMBER-SHOWS.md` stage 3; "still needs an owner on our side" |
| a guest's own form | anyone | whatever shape the form declares | somebody brings a document or a sign-up list; we show it as a wizard and not everyone has to fill it in |
| `you + greet` | anyone | a bound key | built, in you.anecdote.channel |

Most returns carry a field for the passkey signature. Where something came from
is carried by the optical path itself.

**Return channels,** in the order they are likely to exist:

1. the person's own phone, catching the screen;
2. **a site phone** passed around the room, for people who would rather not use
   their own. A member can scan their own QR on it to act as themselves:
   delegated work over QR;
3. a studio webcam reading a phone held up to it. Not set up; it needs thought.

## What exists, and where

| piece | where | state |
|---|---|---|
| library engine | `.library-engine` here (mounted 2026-09-24) | mounted; its `wants:` (stacks, catalogue, intake, seats, petitions) unanswered |
| FCPM's library | `library` branch: `library/{city,trade,voices}/.gitkeep`, a README, a site stub | skeleton only. To be moved to `main` |
| you engine | you.anecdote.channel; **not mounted here** | the control point: passkey `prf` → age identity; wing `you`, `root: branch` |
| bottle codec | you.anecdote.channel `bottle/` | built: bytes → GIF of QR frames and back; `bin/publish` refuses unless it round-trips |
| moving-QR reader | anecdote.channel `composer/carrier-catch-demo.html`, `qr-decode.mjs`, `fountain.mjs` | works as a demo: camera, fountain-coded frames, a decoder that does not need iOS's missing BarcodeDetector |
| screen sender | anecdote.channel `composer/carrier-loop-demo.html`, `press/broadcast.mjs` | demo: still / collage / stream, nine tiles |
| wizard declaration | library engine branch `wizards/residency-declares-them` | unmerged: `wizards:` in residency, two-tier grants |
| wizard listing | station-node `bin/wizards` → `library/share/wizards/` | built there |
| a wizard's envelope | `docs/HOLDING-A-BUBBLE.md` | written: six must-says, "nothing in a bubble runs" |
| the signed return | you.anecdote.channel "What is not" | **not built** |
| the kiosk screens | `kiosk/`, `instruments/`, the door | built; no module plays a bottle |

## The gaps, in the order they can close

1. **Put the library on `main`.** A `library/` folder at the root, with the
   branch's category folders, a README written for the board, and the six
   paths station-node keeps wired on main where they apply. Retire the
   `library` branch after its content is moved, and correct the `.gitmodules`
   comment, `docs/STATION.md` ("mounted as a branch, on purpose") and
   `docs/MEMBER-SHOWS.md` (trade "on the `library` branch"). Answer the library
   engine's `wants:` with paths under `library/`. **Autumn reviews the README's
   wording; the board reads it.**
2. **Mount `.you-engine`, with its things in a folder on `main`.** Its
   residency asks for `root: branch`, so either FCPM's `you.yml` binds the wing
   to a folder (if the engine allows a host to choose), or the engine grows
   that choice. This needs the you engine's owner, which is Autumn in another
   repository. `you.yml`'s `url` is the passkey origin and is decide-once:
   `you.fcpublicmedia.org` (`MEMBER-SHOWS.md` decided it).
3. **Decide where FCPM's own wizards live.** A wizard lives in the engine that
   declares it. FCPM's wizards (check-in, class registration, start a show) need
   a declaring residency. Recommended: a `wizards/<label>/` folder on `main`,
   declared by a `residency.yml` at the root, so this repository is a resident
   of itself for this purpose and everything stays where the board can see it.
   The other option is to put them in `.you-engine`, which makes them
   Autumn's-engine code rather than FCPM's.
4. **A listing,** as station-node's `bin/wizards` does: every wizard every mount
   declares, written to `library/share/wizards/`, checkable, served.
5. **A screen that plays a bottle** (FCPM's side). A kiosk module the door renders: given a
   wizard, it plays its bottle (projected frames; the nine-tile collage on a
   big screen). This answers bottles' own open question "who owns the player?"
   for FCPM: the renderer plays, and the bottles engine owns the format.
6. **A catcher people can open** (bubbles' side). The carrier-catch reader, lifted out of the
   demo into a page on `you.` (or the site) that any phone opens from the still
   control QR, catches the moving one, and opens the wizard it decoded.
7. **The signed return.** A one-commit return, signed by the passkey, arriving
   as a pull request our hooks replay (and never run). Not built anywhere; it is
   the you engine's next form.
8. **Check-in as a wizard.** Its current promise, that checking in makes no
   network request and visits stay on the phone, has to be kept or deliberately
   changed. As a wizard it returns something by definition.
9. **The site phone,** then the webcam.

## Open, for Autumn

- **Library organisation.** The branch has `city/`, `trade/`, `voices/`.
  station-node groups by moniker as well as by type. FCPM's first shelves?
- **Private things.** With the library on `main` and the repository public,
  anything private goes to a wing on a branch, encrypted to its readers (the
  library engine's "the branch is the isolation, the encryption is the
  privilege"). Which, if any, exist yet?
- **Wizard home:** item 3's recommendation, or `.you-engine`.
- **Check-in:** keep "no network request", or trade it for a return.
- **The press demo.** Autumn remembers one; no file here or in the anecdote
  repositories uses that name. The nearest is anecdote.channel's `press/`
  ("go / write / read").
