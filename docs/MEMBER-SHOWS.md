# Member shows: the plan

Written 2026-09-24 from Autumn's description, laid over what the repositories
already define. **This is a plan, and nothing in it is built as described.**
Every stage says what already exists, what it needs, and **the test that
proves it**, because Autumn's condition is that this is working and tested
before anything is left to run in the background.

Read [`member-sites.md`](member-sites.md), [`INTERMEDIATES.md`](INTERMEDIATES.md),
[`identity.md`](identity.md) and [`RESERVE-DESIGN.md`](RESERVE-DESIGN.md) first.
This plan joins them; it doesn't replace them.

## The shape in one paragraph

A member gets a passkey on `you.fcpublicmedia.org`, which is the member area.
Each **show** gets a sub-subdomain, `<show>.you.fcpublicmedia.org`, and a
**control branch** we provision at sign-up. The member's phone carries the
show as a scratch space and clones the control branch with git-enough. The
kiosk hands the phone a **bottle** to bring it in. Every step a member takes
toward us is a commit to a **wizard**, and every change arrives as a **pull
request** that our own hooks replay and accept or refuse. What they publish
lands in the **trade** area of FCPM's library, and station-node builds and
deploys it. Recordings made at the studio travel the enhance round trip and
come back as a link that only their passkey opens, with a notification to
their phone.

> Offline, every path is theirs. Online, we're canonical: the paths we
> provide on `<show>.you…` are wizard requests to the real host.

## The words, and where each is defined

| Term | Meaning here | Defined in |
|---|---|---|
| **you** | the passkey origin (the RP ID) and index of channels, served from a mounted `.you-engine` | station-node `you.yml`, `README.md` l.79; anecdote.channel `docs/decisions.md` D8, D12 |
| **member area** | `you.fcpublicmedia.org`: visible to anyone, useful to whoever has a passkey | Autumn, 2026-09-24 |
| **show space** | `<show>.you.fcpublicmedia.org`, one per show, not per member; published as a folder named for it on `you.` | Autumn, 2026-09-24. Matches the `<label>.<storage>.<apex>` topology, anecdote.channel D4 |
| **control branch** | the branch a work order starts from, carrying the node's own signed commits, force-pushed clean | station-node `docs/the-work-order.md` l.15, 103, 170 |
| **wizard** | a declaration inside a residency; it "invites a commit and never compels one" | station-node `bin/wizards`, `docs/the-work-order.md` |
| **bottle** | bytes for transit (bag, bottled or canonical), rendered as a QR sequence; a repo plus its hooks in a bottle states the base to commit against | bottles.anecdote.channel `README.md`, `ONBOARDING.md` |
| **git-enough** | the browser and phone git: commit, clone, send-pack | anecdote.channel `docs/git-enough.md`, `git-enough/` |
| **probe** | a private `MessageChannel` port handed to a powerless iframe; holding the port is the capability, and closing it revokes it | anecdote.channel `docs/probe-line.md` |
| **trade** | the record of a site we deploy for somebody; a PR carrying a static site "*is* the consent" | station-node `library/trade/README.md`; `TENANCY.md` "Which categories things land in" |
| **intermediate** | anything from raw source to built HTML, each file marked with its degree | `INTERMEDIATES.md`, `member-sites.md` |

## Decide once, before anything else

1. **The passkey origin is `you.fcpublicmedia.org`.** An RP ID can't be moved
   later without re-enrolling everyone. station-node's `you.yml` uses
   `you.discoverywritten.com`, and FCPM needs its own.
2. **Shows, not members, get subdomains.** `deploying.md` l.361 maps
   `<member>.fcpublicmedia.org` onto `site/member-sites/<member>/`. This
   plan replaces that with `<show>.you.fcpublicmedia.org`, published as
   `you/<show>/`. Members with several shows are "their thing, later".
   `TENANCY.md` l.331 ("Every show gets a site, and most of them are
   virtual") already points this way.
3. **Where trade lives for FCPM:** `trade/<show>/` on the **`library`
   branch**, the way station-node keeps `library/trade/<label>/`. It
   follows station-node's rule of statics only, no workers.
4. **Who provisions a control branch.** `the-work-order.md` builds it
   "locally in `.you-engine/bin/control`; nothing pushes it yet". The
   provisioning step of sign-up needs an owner.
5. **What "pristine bottle" means.** Two meanings are diverging: a transport
   mode with no self-healing budget, and "the canonical compacted bytes" whose
   digest is their identity (station-node petition
   `the-share-wing-and-what-the-library-stops-carrying.md` l.27-47). This
   plan needs the second: the empty show template, compacted, identified by
   its digest.

## Stages

Each stage ends when its test passes. Tests run from the media node on a
schedule, beside the door (see *Who runs the tests*).

### 1. A passkey on `you.`

- **Exists:** the `worker/` broker (`/challenge`, `/verify`, `/bind`, and the
  rest; `identity.md`), `.auth/devices.json` per member repo, `may_publish`
  off by default. The `.you-engine` mount (`INTERMEDIATES.md` l.37,
  "later").
- **Needs:** `.you-engine` mounted, and `you.fcpublicmedia.org` served.
  "A passkey cannot be created on page load" (`RESERVE-DESIGN.md`), so a local
  ID is primed first.
- **Test:** a scripted WebAuthn virtual authenticator (headless Chromium)
  enrols, gets a challenge, signs it, and is verified. A replayed challenge
  is refused.

### 2. Membership sign-up writes a bottle

- **Exists:** `site/membership.md` and the tiers; Stripe via the broker
  (`worker/src/checkout.js` posts only a SKU). `payments.yml` is not live yet.
  `payments.md` still lists membership under Wix in one table and under
  Stripe in another; **reconcile that first.**
- **Needs:** the public sign-up stays a plain web page. Its membership
  controls are an iframe to `you.…/membership`, a **probe**: no UI, just
  messages over the port. The form fill becomes the same kind of bottle a
  phone would send, and goes through the same hooks.
- **Test:** a fake sign-up (a Stripe test key) produces a bottle. The hooks
  accept a well-formed one and refuse one with an extra field. The probe
  iframe refuses a parent not listed in its `frame-ancestors`.

### 3. Provision the show

- **Exists:** `site-template/` (two YAML files), `member-site-core/`, and
  `sites.yml` roles (`tenant` failures are reported, not fatal).
- **Needs:** at sign-up, provision a control branch holding the pristine
  bottle of the **empty show template**: a scratch space that "builds" by
  default, where building can mean pushing it raw, without Jekyll. The show
  needs no name until the member publishes. A placeholder label stands in,
  and it's renamed at the publish wizard.
- **Test:** provisioning twice yields byte-identical control branches, and
  the pristine bottle's digest is stable. The empty show's raw push is
  accepted by trade.

### 4. The kiosk hands over a bottle

- **Exists:** the kiosk's door and screens (`machines/kiosk-1/`). Bottle
  renderings (stored, projected, enchanted), envelope, frames and fountain
  (anecdote.channel `composer/transfer.mjs`, `carrier.mjs`, `fountain.mjs`).
  A git-bundle workspace kind. A measured work order: a 2,103-byte tar.gz
  comes to 13 frames.
- **Needs:** a door page that projects a member's bottle, which is **the
  seam**: the member decodes that artifact on the phone, and it straps them
  into the show's control branch and the wizard. Onboarding by control code
  is "an assertion, not a permission check": authority is exercised when the
  code is minted, never at run time (`ONBOARDING.md`). The passkey is what
  proves who they are.
- **Test:** a phone-sized headless browser films the projected frames (the
  frames fed as images) and reassembles the bytes. The digest matches. A
  dropped frame is healed by the fountain.

### 5. Wizard steps as pull requests

- **Exists:** `the-work-order.md` (draft): the bubble, `forms/`, git hooks,
  and **this node replays the client's log through its own canonical hooks
  and never runs incoming ones**. git-enough's send-pack. `identity.md`
  prefers a Worker holding a GitHub App key over a per-member credential
  ("whoever can unwrap it can dispatch"). That retires the older idea of a
  PIN-unwrapped key.
- **Needs:** each wizard path on `<show>.you…` is a canonical request. The
  published site is a static rendering of the control branch. A PR's author
  is known through the passkey identity. Commits outside the wizard's shape
  are refused, and members can't change the checks. The change has to come
  from our ref.
- **Test:** a scripted member clones, commits one wizard step and opens a
  PR. The hooks accept it. Variants that must be refused: an edit to a hook,
  a path outside the form, a commit not based on our ref, and an unsigned
  commit.

### 6. Publishing to trade

- **Exists:** `deliver: source|intermediate` (`sites.yml`); trade's
  `source: given`, where the PR is the consent and the intake record;
  station-node's `bin/trade ready|build|deploy` with a byte-compare of what
  the edge serves.
- **Needs:** a show publishes into `trade/<show>/` by PR, as raw source, an
  intermediate, or a fully built site. It stays **tolerant**: a member who
  takes their repository elsewhere can still publish to us by PR, and we
  keep them up as long as they stay controllable. We ask them to publish
  with us by courtesy and convention; they're free to publish anywhere.
  **The media node commits; station-node builds and deploys.**
- **Test:** three PRs (raw, intermediate, built) each land in trade and
  serve at `<show>.you…`, checked by the byte-compare. A delisted show is
  taken down. The graceful-degradation promise holds: raw Liquid is shown
  as raw, never as though it were rendered.

### 7. Booking carries the member's nonce

- **Exists:** `RESERVE-DESIGN.md` (host-first, availability baked in, writes
  go to email and then the calendar). The Microsoft 365 app, which signs in
  from the media node with a non-exportable certificate
  (`machines/kiosk-1/m365-token.ps1`). Calendars are readable. The Bookings
  service refuses the app so far.
- **Needs:** the member's app makes a nonce offline. **The booking carries
  its hash** (a Bookings custom-question answer, filled in by our page on
  `you.`). **The member's PR reveals the nonce.** The node reads the Bookings
  calendar, which is read-only by Autumn's rule, and matches the two. Hash
  first and reveal second, because a PR is public the moment it opens.
- **Test:** a test booking made through our page shows up on the Bookings
  calendar with the hash. A PR with the right nonce is matched to it. A
  wrong nonce, and a nonce reused on a second booking, are refused.

### 8. The recording comes home at dinner

- **Exists:** capture (RØDECaster and Audio Hijack, silence-gated), the
  depot hand-off (in at `TO ENHANCE`, out at `PODCAST`), holding on the media
  node with receipt checked against `SHA256SUMS`, and the `enhance` engine
  (`.enhance-engine`, `docs/CAPTURE.md`, `bin/activity.py`).
- **Needs:** capture armed by the booking window, not by sound. Enhance or
  stem, per the member's stated preference. The result goes to SharePoint.
  The member's show space issues a **self-expiring download link** (Graph's
  pre-authenticated `downloadUrl`, about an hour) only after their passkey
  is checked. Then a notification reaches their phone.
- **Test:** a 10-second fixture recording goes all the way through. The link
  works with the passkey and has expired an hour later. The notification
  arrives. Every hand-off is logged with its digest.

## Who runs the tests

**Tests, not advocates.** An advocate "speaks, permanently, for one
constituency" on what would make us stop, decides nothing, and is explicitly
not for build or code correctness: "tests own that" (advocate.anecdote.channel
`README.md`). So:

- **The tests** run on the media node on a schedule, from a job of its own
  beside the door. They report to a page the door serves and to the TV
  wall. A red stage stops the stages after it.
- **Advocates** get seats that watch this system's constituencies: members
  (custody: "we hold it, they own it"), payments (a seat already exists),
  privacy (no names in public commits, no Wi-Fi codes on shares), and
  accessibility at the kiosk. They argue from the test results. They don't
  replace them.

## Open

- Several shows per member: later, by Autumn's word.
- Where the membership record lives: `identity.md` intends a SharePoint list.
  The app can't see sites yet; that waits on consent.
- The empty show's format: "I don't care" is the answer until a member needs
  more. Members keep blobs at any path.
- Notifications: web push from `you.`, or email. Neither is chosen.
