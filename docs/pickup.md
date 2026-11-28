# The pickup

How things travel in and out of FC Public Media without anyone being logged in to anything: the QR pickup
station, the iced bottle that is the wire format, the outbox, and the cloud box. Built: the station's intake
(`qr.local/drop`, `replies.py`), the loop for `model+ask` answers (`machines/digitization/asks`), the
library's inbox ([library.md](library.md#the-receptionists-inbox)), the iced bottle's codec (`.you-engine`,
`you.anecdote.channel/bottle/`), and the library's outbox of iced answers. The rest is the design, in the
order it is built (Steps, at the end).

## The pickup station

The QR pickup station is the `qr` job ([machines/qr](../machines/qr/PROFILE.md)), worn by the bounce Pi,
joined, at `qr.local`: it keeps what it catches and hands every reply to Helm. It is what makes anything available on the LAN at all:

- **In.** A camera catches a code, or a bay sets a bottle down at `qr.local/drop`. Helm passes each reply
  to the helm that holds its wizard ([kiosk.md](kiosk.md#helms)).
- **Out.** The loop. Every answer due to someone is played as a fountain of QR frames on a screen, keyed
  by the number of the ask it answers, so the asker's phone catches its own.

Anything the library does for reception joins the station this way. An ask of the library comes in like
`model+ask` does: Helm passes it to production's helm, where the library sets it down in its inbox and a
seat answers it, with the model when one is up. The answer then goes into the library's **outbox**. For
the library it is an outbox. For everyone outside, it is the station's loop playing everything that is
going out. Nothing has to be serialised to QR by hand along the way, because the bottle already is that
form.

## The iced bottle

The wire format is not a JSON message. Passing our wizards' JSON shapes around as raw messages
communicates the wrong thing: anyone can retype one, change its timestamps, or paste a signature into it.
The unit that travels is the **iced bottle**: the smallest, pristine form of what the station would play.

- One QR module to one pixel, no quiet zone, every frame in one zero-delay GIF: "a QR for ants".
- Blocks, not fountain droplets, and the lowest error correction. It has no healing built in, because the
  reader is a program holding the file, not a camera at a distance. It reads perfectly in one pass. When a
  screen has to play it to a camera, it is scaled up and poured again from the same bytes.
- Inside is a signed transfer (`anecdote.transfer/v1`) of the payload. It says what it is (`kind`), where
  it came from (its signer), and what it carries (its hash). It is the same bytes a phone's camera would
  have assembled.

The codec is `you.anecdote.channel/bottle/bottle.mjs` (`bottle(bytes, identity)` to the GIF, and
`unbottle(gif)` back, verified), with a sealed variant for named recipients (`sealed.test.mjs`). FCPM mounts
it as `.you-engine`. An answer of 87 bytes is a 3-frame GIF of 73-pixel codes, 2.6 KB.

### Why iced: a reply that speaks for itself

The person keeps the iced bottle they received, exactly as it came. When they send it back, as a
reference or as the start of a reply, they send those same bytes. They do not send a re-serialisation,
and they do not send just an address in some public context. They send the whole thing, as it was.

Then we can tell a reply from hearsay. We signed that bottle and we kept a record of what we issued, so
the bottle that comes back proves itself: we made this, and here it is, unchanged. The conversation can be
slow and stateful without either side holding a session open, because the context travels with it. A
fat contextual reference, clean-room. A wire format that keeps more about itself than it appears to.

Encryption comes later, by the data pile and the sealed bottle. Today everything is in the unverified
stage: there are no passkeys on the LAN yet, and nothing is sealed. The library learns to build the right
kind of artifact first. Opening a sealed one with the keys we gave you is then much like opening a page
that targets what you came to the library to see.

## The cloud box

The station is a LAN proof of what we can then do in the cloud for free. Off our network, someone's own
page cannot reach `qr.local`, so it puts the same iced bottle it would have shown the camera into the
**cloud box** instead. That is a worker of its own, apart from the site-worker, so its use of the budget
stays visible and it can be run only when wanted.

- **In, as iced bottles only.** The page stores exactly what it would have broadcast. The worker holds it
  and reads nothing in it, as the tanks do for forms.
- **Orders, never iced.** Revoking a bottle that is still waiting, or asking where it is, is a command sent
  apart from the bottles. That is how an order is told from a message: messages are iced, orders are not.
- **The outbox view.** To the person, what they have put up feels like an outbox. Its routing history is
  visible: waiting, then gone (picked up, so being processed), then answered. Some of that is reported,
  and some is plain to see because it moved.
- **The station pulls.** The cloud box never pushes into the building. The station drains it the way
  `machines/drain` empties the site-worker's tanks: one crew line on one machine, with the keychain's
  Cloudflare key. How often is a switch on `fcpm` (as development has its switch), and a staff wizard can
  say "check the cloud intake now".
- **Out, both ways.** An answer is delivered to the station's loop, for whoever is in the room, and up to
  the cloud box, for the person who asked from away. Their page checks the box and pulls in what is theirs.
  That gives a little reactive real-time from the worker, carefully, within the budget.
- **Publishing is a deployed set.** "Up to the cloud" can be a set of iced bottles we consider deployed,
  kept with its history the way git keeps one. It does not need a site of its own.

The worker serves no front end and should not. Serving the wizards is the site's job, and Helm's. Where a
wizard sends to depends on where the person is. On our Wi-Fi it is set down directly. Anywhere else it is
the cloud box, unless they show the code to a camera.

## Steps

1. **Mount `.you-engine`** in this repository, so the codec is ours to call (bay 1). Built: pinned as a
   submodule, and `fcpm install` hydrates public submodules, with theirs inside.
2. **The library's outbox.** `fcpm library inbox answer` also writes the answer as an iced bottle of kind
   `fcpm.answer`, keyed by the ask's nonce, into `~/code/library/outbox/`. It records the transfer's id in
   `retain/`, so that a bottle which comes back can be proved ours (bay 1). Built: `machines/library-bottle.mjs`,
   signed by the keychain's `library` group (`fcpm library signer mint`, once).
3. **The station accepts an answer from a peer helm.** `replies.py` takes a bottle of kind `fcpm.answer` at
   `/drop`, verifies it, and puts it where `asks` keeps answers, so `asks reindex` plays it in the loop
   (digitization: `asks` and the intake are its).
4. **The outbox delivers** to `qr.local/drop` through Helm, and empties behind itself. Then the board
   meeting's demonstration works end to end ([library.md](library.md#next)) (bay 1).
5. **The cloud box:** a worker of its own. Iced bottles in, orders apart, routing history, and the
   station's drain line with its `fcpm` switch and the staff wizard (digitization and the site-worker).
6. **Answers up to the cloud box** for people who asked from away, and their page's pull (the site).
7. **Sealed bottles**, once passkeys work on the LAN: the data pile, and a reader's keys (with the
   keystore).
