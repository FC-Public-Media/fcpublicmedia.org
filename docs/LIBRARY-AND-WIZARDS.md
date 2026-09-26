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

**Private is never committed; public may be** (Autumn, 2026-09-26: *"we may
never commit things that are private, but anything that is made public might be
good there. We need options mostly."*). This repository and the site are
public, and a teacher's materials usually are not. So a screen names a bottle
**by reference only**, and the reference says where it comes from:

| reference | from | for |
|---|---|---|
| `sha256:<hex>` | the door, by digest: the media node's library wing or cloud wing, never a git tree | anything private. Loopback only: the door answers the kiosk's own screens |
| `wizard:<engine>+<label>` | the door, resolving the label through its grant to a digest | the usual case |
| `public:<repo path>` | a committed bottle, read from the checkout (or `file://` on a screen that cannot reach the door) | a wizard that is public on purpose; the door refuses unless its entry says `payload_public: true` |

The player never fetches a payload from a public URL for a private reference.

**Settled with bubbles, 2026-09-26:**

- **Frames.** anecdote.channel's carrier, cut by `press/broadcast.mjs`
  `planBroadcast`: `stream` on single screens, `collage` with nine tiles on the
  big TV, the `droplets` cut (an LT fountain, so a loop heals), ecLevel M,
  8 fps, 256-byte blocks, the signed layout tile kept in rotation. Drawn with
  anecdote.channel's `qr-encode` and nothing else, so screen and camera cannot
  disagree. Not the you engine's stored GIF: *pristine* is the perfect-read
  form, not for a camera. The contract is the frame strings; the player only
  draws them. It loops forever, and no signal comes back: light is one way, and
  the return is the member's signed PR.
- **Envelope.** Always signed. Sealed to recipients (`composer/age-seal.mjs`)
  or for whoever is in the room is Autumn's call; the player is the same
  either way.
- **The door's endpoint** is bubbles' to build on the media node: refuses a
  non-loopback caller and a reference with no grant.
- **A wizard's delivery, as flat keys** on its residency entry, checked by the
  door: `deliver_optical_only` or `deliver_on_web`, `payload_kept_off_repo`,
  `payload_held_in_library`, `requires_member_passkey`, and `payload_public`
  for the `public:` case.
- **Open:** how the kiosk page gets `broadcast.mjs`, `carrier.mjs` and
  `qr-encode.mjs` byte-identical to the catcher's. Proposed: one anecdote.channel
  commit pinned here, served by the door from its mirror at that commit, and the
  catcher on the same pin.

## `learn.`: the you side, for transient members

Autumn, 2026-09-26: *"a learn subdomain, which can be treated like a you
branch that has new scope applied to transient members."* A class's attendees
are members for the length of a class: they need a teacher's materials and to
send things back, and not the member wizards. `learn.` is where that scope
lives, and it is the natural audience for a teacher's materials: encrypted to
a class's roster, not published.

**One decide-once question comes with it.** `MEMBER-SHOWS.md` fixes the passkey
origin (the WebAuthn RP ID) at `you.fcpublicmedia.org`. A browser accepts a
passkey only on its RP ID or a subdomain of it, so a passkey made on `you.`
does not work on `learn.fcpublicmedia.org` by itself. The ways through, to be
chosen before anybody enrolls:

- **`learn.` names itself as a related origin of `you.`.** WebAuthn's related
  origin requests: `you.` serves `/.well-known/webauthn` listing `learn.`. One
  passkey for both. Browser support is recent and must be measured on the
  phones people actually carry.
- **`learn.` is a label under `you.`** (`learn.you.fcpublicmedia.org`), as a
  show is (`<show>.you.`). Works everywhere, and says outright that `learn.` is
  a scope of the member area.
- **`learn.` keeps its own passkeys.** A transient member enrolls there, and
  becoming a full member is a second enrollment on `you.`.

**Recommended by bubbles: the label, `learn.you.fcpublicmedia.org`.** The RP ID
`you.` already covers every `*.you.` host, so a class attendee makes the
ordinary you passkey and "transient member" is a scope on it (on a roster, no
membership), not a second credential. Related origins need Chromium 128 or
Safari 18, and the kiosk's own Edge is 106. Separate passkeys cost friction
every class, for people who by definition come once. The cost: `learn` becomes
a reserved label that no show may claim. Two consequences:

- sealing to a roster needs each attendee's recipient at minting, so a walk-in
  who enrolls at the door means a re-seal, or a class key the roster check
  hands out; either way the door re-plans, and the player is unchanged;
- any `*.you.` page can ask for assertions against that RP ID, including a
  member-built show site. The trade acceptance check refuses or strips WebAuthn
  in those builds, or show sites get a no-script CSP, or they live under a
  sibling the RP ID does not cover.

## The wizards we already know we want

| wizard | tier | returns | notes |
|---|---|---|---|
| check-in | anyone | a visit | becomes a wizard, **on the you side**. Today it is `site/check-in.md` + `checkin.js`: local-only, geofenced, makes no network request |
| class registration | anyone / member, onto `learn.` | a registration, a passkey signature, a Stripe payment | membership status is known from when the passkey was accepted; recovery is out of band |
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
