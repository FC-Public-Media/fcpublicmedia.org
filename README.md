# fcpublicmedia.org

A static site for Fort Collins Public Media. Built with Jekyll, deployed to
Azure Static Web Apps.

This is a proposal-stage scaffold. The structure is real and it builds; a lot
of the content is marked `TODO` because it lives inside Wix widgets on the
current site and can't be read from outside. See [CONTENT-TODO.md](CONTENT-TODO.md).

---

## The idea

The current site is on Wix. Almost all of it is static — prose, images, a few
embeds. The parts that genuinely aren't static come down to five transactions:
class tickets, membership dues, donations, studio booking, and program
submissions. None of those require a site builder. They require a payment
processor and a calendar.

So: publish the static part as static files, and treat the five transactions as
explicit, swappable integrations rather than as a reason to rent a platform.

## Running it

```
bundle install
bundle exec jekyll serve
```

Then open <http://localhost:4000>. Edits rebuild automatically. There is no npm,
no bundler, no CSS preprocessor, and no plugins.

## How it's laid out

```
_config.yml              Site settings. ~40 lines, all commented.
_data/                   Content that repeats or changes. Plain YAML.
  org.yml                Address, email, phone, socials.
  nav.yml                Header and footer menus.
  providers.yml          The five transactions. See below.
  membership.yml         Tiers and prices.
  facilities.yml         Bookable spaces.
  equipment.yml          What kinds of gear we have (not an inventory).
  watch.yml              Channels and carriage.
  board.yml              Board and staff roster.
_layouts/                Three of them: default, page, podcast.
_includes/               Four: head, header, footer, transaction.
_podcasts/               One file per show. Shares the podcast layout.
assets/css/site.css      The entire visual design. One file.
assets/js/nav.js         Ten lines. The mobile menu. That's all the JS.
*.md                     One file per page. Filename becomes the URL.
api/                     The small server-side piece. See "Members" below.
worker/                  The broker. Its own Worker. See "Identity" below.
staticwebapp.config.json Routing, redirects, auth rules.
```

That's the whole thing. Nine template files and a stylesheet.

### Adding a page

Create `something.md` in the root:

```markdown
---
title: Something
lede: One sentence under the heading.
---

Write in Markdown.
```

It's live at `/something/`. Add it to `_data/nav.yml` if it belongs in a menu.

### Adding a podcast

Copy any file in `_podcasts/` and edit the front matter. It appears on
`/podcasts/` automatically and gets its own page.

### Why so little Jekyll

Deliberately. Jekyll is here to loop over data files and stamp out a header —
not to be learned. Anyone who can edit YAML and Markdown can maintain this
site, and anyone who can write HTML and CSS can restyle it. If a future need
argues for a plugin, check first whether a `_data` file and a ten-line Liquid
loop would do it. On a site this size, it usually will.

No React. Nothing to compile. Not knowing a framework should never be the
reason someone doesn't contribute.

---

## The five transactions

Everything on this site that isn't a static file goes through
`_data/providers.yml` and `_includes/transaction.html`. That's on purpose:
switching a vendor is a one-line edit, and it's impossible to lose track of how
many paid integrations the organization has.

| Key | What it is | Now |
|---|---|---|
| `tickets` | Class registration | Wix Events |
| `membership` | Dues | Wix Pricing Plans |
| `donate` | Donations | Wix Donations |
| `booking` | Studio and bay reservations | Bookable — staying |
| `submit` | Program submissions | Wix form + Dropbox |

An entry with an empty `url` renders as a visible "not wired up yet" block
rather than a dead button, so nothing ships silently broken.

Booking stays on Bookable. Microsoft 365 calendar integration is being built
separately; when it lands, only the `booking` entry changes.

---

## Members and sign-in

The current site has no real accounts, and it doesn't need them. What it needs
is a way to tell whether the person asking to book a studio has paid.

Azure Static Web Apps does this without a user table:

1. A visitor clicks sign in and authenticates against **Entra ID**. FCPM never
   stores a password and never has one to leak.
2. SWA calls **`api/GetRoles`** once, with the visitor's email.
3. That function looks up whether the email has paid dues and hasn't expired,
   and returns `["member"]` or `[]`.
4. `staticwebapp.config.json` gates `/members/*` on that role.

The membership record itself is the only thing FCPM stores: an email address
and a paid-through date. The natural home is a **SharePoint list in the
existing Microsoft 365 tenant**, read through Microsoft Graph — no new vendor,
no new bill, and board members can see and edit it without touching code.

The write side is the payment redirect: a member pays, the provider sends them
back or fires a webhook, and that records the dues. Signing in by itself never
grants membership.

`api/src/functions/GetRoles.js` is a working stub with the lookup left as a TODO.

## Check-in

`/check-in/` is a QR destination. Someone scans the poster, taps once, and the
visit is recorded — in their own browser's storage, on their own device.

- The device identifier is a random UUID made on first visit. Not derived from
  the device or the person, never transmitted, deleted by "Forget this device".
- History is capped, exportable to a JSON file, and re-importable — importing
  merges rather than replaces, so restoring a backup never drops newer visits.
- A test asserts that checking in makes **no network request**. If a future
  change starts posting somewhere, the suite fails.

Print the poster at `/check-in/poster/`. The QR is a committed SVG; regenerate
it only if the URL changes:

```
pip install qrcode
python3 script/make-qr.py
```

The generated code was decoded back to `https://www.fcpublicmedia.org/check-in/`
to confirm it is correct — a printed poster with a wrong URL is worse than no
poster.

### Location

Checking in requires being at the studio. Coordinates, radius, and re-check
interval are in `_data/checkin.yml`.

- Tap **Check in**. If you are within 200m, done.
- If not, the check-in is held as **pending**: the page shows the distance and
  a directions link, and completes by itself when you arrive. Leave it open,
  walk in, look down.
- Pending survives a reload. Re-checks run every five minutes and **only while
  the tab is visible**, so a page left open in a pocket costs nothing.
- A tap asks for a fresh fix; background polls reuse a cached one. That
  distinction matters — with a cached fix, someone standing in the doorway
  gets told they are still down the street. A test covers it.
- Coordinates are never stored, even locally. The history keeps the distance
  and a `verified` flag, which is the part that means anything later.

Accuracy is handled by accepting a reading when `distance - accuracy` is
inside the radius, capped by `accuracy_slack_m` so a fix reporting ±3km cannot
wave someone through from home.

The venue coordinates were geocoded from the address. Worth confirming by
standing at the front door with a phone before this goes live.

### This does not replace the paper log

Two things follow from there being no server, and neither is a bug in the page:

**FCPM receives nothing.** A log on a visitor's phone cannot be counted,
reported to the City, or put in a grant application. The export button lets a
visitor hand their history over, but that is a favour, not a reporting system.
The stated goal was simplifying check-in *reporting* — device-local storage
serves the visitor, not the organization.

**Browsers delete this.** Safari removes script-writable storage after about
seven days without a visit unless the site is on the Home Screen, and clearing
browsing data clears it. For a log people touch monthly, losing it is the
normal outcome, not an edge case. The page says so plainly rather than
implying a permanence it cannot deliver.

So run it alongside the paper log until check-ins have somewhere to go.

### Storage durability

`navigator.storage.persist()` is requested on load, and the page reports what
the browser said. Persistent mode exempts an origin from routine eviction in
both Chrome and Safari.

The catch is how it is granted. Neither browser prompts — both decide on
heuristics. Chrome uses engagement signals; **WebKit grants it largely when the
site is running as a Home Screen web app**. So on iPhone, the reliable way to
keep a check-in history is Add to Home Screen, not an API call. The page says
so instead of pretending the request is a guarantee.

That is worth knowing before treating any of this as durable: for a visitor
who opens the page once a month in Safari and never installs it, the history
is likely to be gone by their next visit.

### What "somewhere to go" would take

**The short version: a Worker, and it is the low-impact option, not the heavy
one.**

Any design where the browser triggers a GitHub Actions dispatch means the
browser holds a credential that can dispatch it — and a credential in a
browser is a public credential. Wrapping it per member does not change that:
whoever can unwrap it can dispatch, and the thing doing the wrapping is itself
a server you now have to run and rotate. You would have built a key
distribution service to avoid running thirty lines of Worker.

There is also a quieter problem. `repository_dispatch` needs a token with
write access to the repository. Not "can trigger this one workflow" — write.
Anyone holding it can push. Fine-grained PATs narrow it, but the floor is
still higher than "may append a row to a log".

What the Worker actually costs: 100,000 requests a day on the free plan. A
check-in is one request. At FCPM's volume that is not a rounding error, it is
noise.

Two shapes, both small:

1. **Straight through.** The Worker receives the check-in and immediately
   fires `repository_dispatch` with a token held as a Worker secret, never in
   the client. Nothing is stored anywhere. Fastest possible flush, no state to
   jam.
2. **Batched.** The Worker appends to KV; a cron trigger flushes every few
   hours and clears the key. Fewer Actions runs. The batch is the only thing
   ever "held", and a failed flush retries on the next tick rather than
   stalling — a jam self-clears.

Given the stated goal of flushing as fast as possible and holding nothing,
shape 1 is the better fit, and it is the simpler one. Batching is worth it only
if Actions runs turn out to be the annoyance.

Either way the device-local history keeps working as the visitor's own copy —
that part does not change.

#### The token, and not having to manage it

Use a **GitHub App**, not a personal access token. This is the difference
between a credential you maintain and one you set up once.

- A PAT expires. Fine-grained ones must, classic ones can be set not to but
  are broad and are a bearer secret forever. Either way it is a thing in a
  calendar reminder.
- **A GitHub App's private key does not expire.** The Worker signs a short JWT
  with it and exchanges that for an installation access token, which lasts one
  hour and is minted on demand. Nothing to rotate, nothing to remember. The
  key sits as a Worker secret and is never in the client.

Workers can do the RS256 signing with built-in WebCrypto — no library. It is
about forty lines rather than one header, which is the whole cost of never
thinking about it again.

Install the App on this repository only, with the narrowest permission that
lets it fire `repository_dispatch`. Confirm the exact permission when creating
the App; GitHub documents the classic-token requirement as `repo` scope, and
the fine-grained equivalent is narrower but worth checking rather than
assuming.

#### Concurrency

Thirty people arriving for a class would fire thirty dispatches, thirty
workflow runs, and thirty racing commits to the same log file. Runs would
clobber each other or fail on a stale ref.

Add a concurrency group to the workflow:

```yaml
concurrency:
  group: checkin-log
  cancel-in-progress: false
```

Runs then queue instead of racing. `cancel-in-progress: false` matters — the
default would throw away queued check-ins, which is exactly the data you were
trying to keep.

If that queue gets long, batching (shape 2) collapses thirty runs into one and
the problem stops existing. That is the case where batching earns its keep,
rather than the daily-volume case.

Public repositories get unlimited Actions minutes, so the cost of a run is
wall-clock and queue depth, not money.

This is listed rather than built because it turns a static site into one
holding a record of who was in the building and when. Retention, who can read
it, what happens on a subpoena, whether it needs a privacy notice — board
decisions, not technical ones.

### Identity: proving an email address without a server

Nothing on the site proves anything today. The paper log by the door accepts
any name in any handwriting, and the check-in page records whatever it is
given. That is the baseline any of this is measured against — not a secure
system, a clipboard.

Two mechanisms are built, and they answer different questions. A third piece —
the broker — is what makes either of them count for anything beyond the
visitor's own browser.

#### Email claims (built, unconfigured)

A static site has nowhere to check a password and nowhere to remember that
someone answered a one-time code. So this inverts the usual direction: instead
of the visitor proving something to us, **we prove something to them and let
them keep it**.

1. Staff mint a claim for an address and email the link:

   ```
   python3 script/mint-claim.py --new-key claim-key.pem   # once, ever
   python3 script/mint-claim.py --email someone@example.com
   ```

2. Receiving the mail is the proof — only the holder of that mailbox gets it.
3. Opening the link verifies an ECDSA P-256 signature against the public key in
   `_data/identity.yml` and stores the token on that device.

**The token is kept whole, not just the address read out of it.** That is the
part with any value. A page verifying a signature in the visitor's own browser
proves nothing to us — it is their browser, and they can edit it. The check
exists so someone whose link was mangled by an email client finds out
immediately. The security lives in the signature, which anything downstream —
staff, a form, a Worker not yet built — re-verifies for itself rather than
believing a flag some device set.

Consequences worth knowing before turning it on:

- **Every provider at once, or rather none.** No OAuth registration with
  Google, then Microsoft, then Apple. It works for any address that receives
  mail, which is all of them.
- **Multi-device falls out for free.** The same email opened on a phone and a
  laptop verifies independently on each. FCPM never learns how many devices
  anyone uses, because nothing reports back.
- **The link is in the URL fragment**, which browsers do not send to servers.
  It appears in no access log, ours or Cloudflare's.
- **There is no revocation.** With no server there is nowhere to keep a
  revocation list. A claim is good until it expires (`days:` in
  `_data/identity.yml`, default 120) or until its signing key is removed from
  the list, which invalidates every claim that key signed.
- **A claim is not a login.** No session, no sign-out, no password. It says
  "the holder of this device received mail at this address". Do not gate
  anything on it that you would not leave on a clipboard by the door.

**Left unconfigured** (`keys: []`) because minting requires generating a
private key, and where that key lives is a decision with consequences — anyone
holding it can assert any address. The page's default state is the typed-address
field, which is what almost everyone will see and is not treated as a failure:
an address someone typed still lines their visits up with the membership list,
and is recorded as unconfirmed so the record never claims more than it knows.

#### The broker (built, undeployed)

Claims prove an address. Passkeys prove a device. Neither proved anything *to
us* until now, because both checks ran in the visitor's own browser against a
challenge the visitor's own browser generated.

`worker/` is where that changes. It is a Cloudflare Worker with six endpoints
and no user table:

- `POST /challenge` — a page declares what it wants to do; the broker returns a
  challenge bound to that declaration, good for five minutes, good once.
- `POST /verify` — the page sends the assertion; the broker checks the
  signature against the public key recorded in the member's own repository at
  `.auth/devices.json`. Changes nothing, and says so.
- `POST /write` — the same checks, then the file is written.
- `POST /bind` — put a new passkey on a site's list.
- `POST /device` — approve or revoke a listed device.
- `POST /upload` — sign permission to put a file in storage.

Three properties are worth naming, because each of them is a thing that goes
wrong when it is skipped:

- **The challenge is bound to an intent.** A challenge that is only a nonce
  makes a verified assertion a bearer token — good for any action, because the
  signature says nothing about what was agreed to. Here the page declares the
  file, the blob SHA, and a hash of the content *before* the passkey prompt,
  and the finished request has to match. The member's device signed for one
  specific edit.
- **The repository comes from the challenge, never the request.** So a
  signature made for one member site cannot be redirected at another.
- **Listed is not allowed.** A device in `.auth/devices.json` exists; whether
  it may change anything is `may_publish` on the record, absent by default.
  That separation is exactly what makes the forwardable enrollment link in
  `_data/authorize.yml` safe.

**What `/settings/` does with it.** Signing in stays exactly what it was — a
way for the page to learn which site the passkey belongs to, proving nothing to
anybody. Saving becomes a *second* prompt, bound to those exact bytes, that
path and that SHA. The member approves one specific edit at the moment they
make it, rather than having approved "editing" some minutes ago. That is one
extra tap and it is the tap that means something.

By default the write lands on a branch with a pull request rather than on the
live branch, so the repository's own checks see a settings file before it goes
live. A member editing raw YAML can produce something that does not parse, and
the difference between catching that and not is a message versus a dead site.
`WRITE_MODE` is a broker setting and not a page setting on purpose: "commit
straight to the live branch" is not a member's decision to make.

**Set `url` in `_data/settings.yml` to turn it on.** Empty is the shipped
state, and nothing is deployed — so today `/settings/` still hands you your
edited file to send over, exactly as before. That fallback stays: a broker
having a bad afternoon puts the page back where it was rather than losing
somebody's work.

**How it writes.** As a **GitHub App**, for the reasons already set out under
"The token, and not having to manage it" above — the same argument, now with an
implementation. `src/app-auth.js` signs a short RS256 JWT with the App's
private key and exchanges it for an installation token.

The passkeys mean no *member* holds a credential. They do not mean nothing
does: GitHub only accepts GitHub credentials, so something has to hold one to
write. What the device work bought is that the credential is never in a
browser, is never per-member, and cannot move at all without a signed
assertion bound to one specific edit arriving first.

Two properties that fall out of using an App rather than a token:

- **Each token is narrowed at the moment of minting** to one repository and
  two permissions. An installation covering forty member sites still produces
  a credential good for one of them, for one hour.
- **Revoking a site is uninstalling the App from it.** No list to edit, and no
  way to forget. That is also what a member sees if it was never installed, so
  the two cases have one explanation.

Withholding the Workflows permission is what makes the `.github/` path refusal
a second lock rather than the only one — GitHub refuses that write regardless
of what the broker's own code does.

**Enrolment, and staff leaving the loop.** `/bind` and `/device` are what move
approval from per-submission to per-device-once. A claim link enrols a device;
being enrolled does nothing until an existing device approves it — except for
the first device on a site, where there is nobody to approve it and nobody to
protect it from. So the owner sets themselves up with no staff involvement at
all, and then approves a co-producer's phone from their own phone. A forwarded
link is worthless the moment the owner has enrolled, which they will have,
because they are the one who asked for the site.

Two refusals worth knowing: a device cannot approve itself, and the last device
that can publish cannot be revoked — that would leave a site nobody can change.

**Uploads.** `/upload` signs a URL and gets out of the way — the file goes from
the browser straight to R2 and the broker never sees a byte of it. Above 4 GiB
it is split into presigned parts, so a finished episode is one upload rather
than a problem.

The signature binds differently here, and the difference is worth knowing:
`/write` binds to a hash of the exact content, and this binds to the *grant* —
this member, this site, this object key, this size. Hashing six gigabytes in a
browser would roughly double the wait, to protect bytes the broker never sees.
What that costs is that whoever holds the URL can put different bytes at that
key, and whoever holds the URL is the member whose device just signed for it.

Two things the bucket needs that are not code: CORS exposing the `ETag` header,
without which a multipart upload cannot be completed; and a lifecycle rule
aborting incomplete uploads, because abandoned parts are billed.

**Cost is a decision nobody has made yet.** R2 is $0.015 per GB-month with 10 GB
free and no egress charge. One 6 GB episode a week is roughly $5/month after a
year and $10 after two, growing forever unless something deletes. `R2_MAX_BYTES`
defaults to no cap, which should be set alongside a retention rule rather than
instead of one.

`worker/README.md` has the endpoint shapes, the configuration, the token
scoping, and an honest account of what is not built. Tests are `npm test` in
that directory; they need nothing installed and run on every push.

#### Cloudflare Access

Almost nothing happens in this repository. That is the appeal.

**In Cloudflare (Zero Trust dashboard):**

1. Add an Access application for the path `fcpublicmedia.org/check-in/sign-in/`.
2. Add login methods — Google, Microsoft, GitHub, one-time PIN by email. The
   visitor picks; you do not choose for them.
3. Set the policy to Allow with the rule *Emails ending in* `@` — that is,
   anyone who can prove an email address. This is a check-in, not a vault.

**In this repository:** set `identity.mode: access` in `_data/checkin.yml`.
That is the whole change.

**How the result is caught.** After a visitor authenticates, Cloudflare sets a
`CF_Authorization` cookie on the hostname. `assets/js/checkin.js` then calls:

```
GET /cdn-cgi/access/get-identity   →   { "email": "…", "name": "…", … }
```

That endpoint is served by Cloudflare's edge, not by this site. No client
secret, no redirect handling, no token parsing, no OAuth library.

**Protect a sub-path, not `/check-in/` itself.** Access gates a whole route: a
protected `/check-in/` would demand a login before anyone could see the page,
which breaks the one-tap flow and makes anonymous check-in impossible. Putting
Access on `/check-in/sign-in/` instead keeps the page public — someone taps
"sign in", authenticates, comes back, and the identity call now returns their
email because the cookie is set for the hostname.

**Two things to know before turning it on:**

- **A seat is one authenticated human, and the free plan has 50.** Not a
  device, not a session — a person. So seats scale with the number of members
  who ever sign in, which for a public-facing check-in is the wrong shape
  entirely: beyond 50 it is around $7 per user per month, or roughly $1,400 a
  month at 200 members to record that someone came to a class. **Access is for
  bounded populations** — staff, board, an admin view — where the answer to
  "how many people log in" is a number you already know. For members, use email
  claims above, which are metered by nothing.
- **Access authenticates the visitor to Cloudflare.** The page reads that
  identity client-side. It does not by itself give FCPM a server-side record —
  that still needs the Worker above. Access answers "who is this?", not "how do
  we find out later?".

Left at `none` because enabling it is a dashboard change; flipping the config
before the route is protected would show everyone an error. When the route is
not behind Access the identity call 404s and the page records an anonymous
check-in, so both states are safe. That fallback is verified against the live
deployment, not just reasoned about.

## Tests

Browser smoke tests, run with Playwright against a real Chromium in both a
desktop and a phone viewport.

```
bundle exec jekyll build
cd tests && npm ci && npx playwright install chromium
npx playwright test
```

They exist because the failures that matter here are the ones you cannot see:
a JavaScript error on a phone, an embed that silently does not mount, a link
that looks fine and 404s. Each page is checked for:

- HTTP status, a title, exactly one `<h1>`
- No uncaught JavaScript errors and no console errors
- No failed same-origin requests
- Every internal link resolving — this is not a crawl of the whole site, it is
  every link on every listed page, fetched
- No link with an invisible label (blank text, no image, no `aria-label`)
- No horizontal scrolling, which is the classic phone bug

Plus the mobile menu opening and closing, and the archive filter actually
filtering.

They caught two real bugs the first time they ran: all 38 category links on
`/watch/` pointed at `/watch-archive-news`-style paths that 404ed, because
`slugify` had been chained after `append` and slugified the path along with
the name; and the archive scrolled sideways on a phone because Cablecast
titles are often one long underscore-joined token with nowhere to break.

### Tests marked @external

`embeds.spec.js` checks the Cablecast player, show links, thumbnails, and
outbound links. These need network and depend on someone else's servers, so
they are excluded from the pull request run:

```
npx playwright test --grep-invert @external   # what CI runs
npx playwright test --grep @external          # third-party health
```

The external ones run on a weekly schedule with `continue-on-error`, because
a suite that goes red when a third party has a bad afternoon is a suite people
stop reading.

**Why these are browser tests rather than link checks:** Cablecast's viewer is
a single-page app. `/internetchannel/show/999999` returns HTTP 200 with a full
HTML shell for a show that does not exist. A status check proves nothing; you
have to render the page and look for the player.

### Testing the deployed site

```
cd tests && BASE_URL=https://www.fcpublicmedia.org npx playwright test
```

Worth doing after a deploy, because redirects, custom 404s, and trailing-slash
handling are host behavior and do not exist in the local preview server.

## The Cablecast catalog

The station's Cablecast instance has a public API that needs no key and sends
`Access-Control-Allow-Origin: *`. It holds **1,486 programs** going back to
2011, 740 of them watchable online, 1,462 with thumbnails, across 36
categories and 80 producers. That is the archive, and it was already there.

`script/sync-cablecast.py` pulls it into `_data/cablecast.json` (standard
library only, nothing to install):

```
python3 script/sync-cablecast.py
```

`.github/workflows/sync-cablecast.yml` runs it weekly and commits the result
if anything changed.

Snapshotting at build time rather than fetching in the browser means the
archive is real HTML — indexable, findable with ⌘F, and still there if
Cablecast is down. The one thing that *is* live is the "on now" strip
(`assets/js/onair.js`), which reads the schedule directly because a weekly
snapshot cannot tell you what is playing right now. It removes itself if the
request fails.

The script's one judgement call is `LOCAL_PREFIXES` — which categories count
as locally produced. This matters: the raw "most recent" list is dominated by
Free Speech TV and Paltrocast, which buries the work Fort Collins people
actually made, so the site features local production separately.

## Class mode

The homepage knows when a class is running and rearranges itself around it.
Two gears, deliberately separate:

**The build** bakes `_data/classes.yml` into the page as inline JSON. Session
titles, times, rooms, and drop-in prices come along with the HTML.

**The browser** reads the wall clock and decides. No request, no API, no key —
`assets/js/classmode.js` is arithmetic on numbers already in memory. A page
built last night knows about tonight's class. It re-checks each minute while
the tab is visible, so a page left open switches on by itself when the class
starts and off again when it ends.

Three windows: `soon` (the `lead_minutes` before), `now`, and `late` (the first
`late_minutes`, when someone walking in is still worth inviting). Outside all
three the block stays hidden and the ordinary check-in card is untouched.

### One QR, two pages, one answer

`assets/js/classes.js` holds the window logic. The homepage and the check-in
page both import it and run it over the same baked-in schedule, so they cannot
disagree about whether a class is on.

That has a consequence worth stating plainly, because it removes work:

**The QR carries no class information.** It is a permanent link to
`/check-in/`. There is no per-class code to generate, print, swap on the door,
or take down afterwards. The page works out on arrival that a class is
running — which is also the only place that decision can be correct, since a
link shared two hours ago would still be claiming a class is on.

The homepage's job shrinks to decorating the panel that already holds the QR
and the link. It does not encode anything.

Same reasoning for a class held elsewhere: what would change is the venue
coordinates the page checks against, not the code on the door. The QR is the
door; the location is the fact.

### On the check-in page

When a class window is open, the check-in page:

- shows the class, with the same wording as the homepage
- preselects `Class` as the reason — but **only if the visitor has not chosen
  something else**, so a page open since before the class does not have its
  answer overwritten
- changes the button to "I'm here for the class"
- before the start, offers "I'm planning to come"

That last one is recorded **on the device only**, and the page says so. There
is nowhere to send it yet. It becomes a real RSVP the day the Worker exists,
and the wording changes then — until it does, telling someone we received
their RSVP would be a lie.

Because the intent, the name, and the reason are all the same stored profile,
someone who noted intent on the way in is already set up to check in when they
arrive. No second form.

The cost of the split is staleness — a class added this morning is not on the
site until the next build. The weekly sync already rebuilds; if classes get
added at short notice, move that job to daily. Eventually `classes.yml` should
be generated from the Microsoft 365 calendar the same way `cablecast.json` is
generated from Cablecast, at which point the gear on this side does not change
at all.

**Times must carry an offset** — `2026-08-11T18:00:00-06:00`, never a bare
local time. A time without an offset is read as the *visitor's* zone, which is
wrong for anyone travelling and silently wrong, which is worse. The template
normalises through `date_to_xmlschema` so what reaches the browser is always
unambiguous.

### Where the schedule comes from

`_includes/class-config.html` picks a source, in this order:

1. **`_data/calendar.json`** — written by `script/sync-calendar.py` from the
   Microsoft 365 calendar. Used whenever it has anything in it.
2. **`_data/classes.yml`** — hand-maintained. The fallback, and what the site
   uses today.

Switching is a matter of configuring a source and running the sync. No
template change, and `assets/js/classes.js` never learns where the data came
from.

```
python3 script/sync-calendar.py --ics "$FCPM_CALENDAR_ICS" --weeks 12
python3 script/test_sync_calendar.py     # 17 tests, no dependencies
```

**Why at build time.** The schedule changes a few times a month and is the
same for everybody. Every visitor's browser asking Microsoft for it would be
the same answer fetched thousands of times, would put a key or a public
endpoint in the client, and would leave the page blank whenever Microsoft is
slow. Fetching once per build is faster, cheaper, private, and works offline.
Same reasoning as the Cablecast sync.

### Two ways into the calendar

**A published ICS link** is what the script implements, and it is the one to
start with. In Outlook on the web: Settings → Calendar → Shared calendars →
Publish a calendar. **No app registration, no admin consent, no client secret,
nothing that expires.**

The trade is that the link works for anyone who has it. That is fine for a
class schedule and wrong for anything else — so publish a dedicated *Public
Programming* calendar rather than someone's own.

**Microsoft Graph** is needed for anything not public: room free/busy,
reservation details, a hidden nonce on a booking. Three things to know:

- Use **`calendarView`**, not `/events`. `/events` returns the recurrence
  *master*; `calendarView` expands a series into real occurrences across a date
  window, which is the shape a website wants.
- From GitHub Actions, authenticate with **workload identity federation**
  rather than a client secret. GitHub's OIDC token is exchanged for a Graph
  token, so there is no stored secret and nothing to rotate — Entra client
  secrets expire within 24 months otherwise.
- **`Calendars.Read` as an application permission grants read access to every
  mailbox in the tenant.** Scope it with an Application Access Policy
  (`New-ApplicationAccessPolicy`) pointed at a mail-enabled security group
  containing only the calendars in question. This is the sharp edge.

### Recurring events

Published ICS describes a repeating event once, with an `RRULE`, rather than
listing occurrences. Expanding those correctly — with exceptions, moved
instances, and daylight saving — is real work and not worth hand-rolling.

**The script does not.** It reports them and skips them, loudly. If FCPM starts
running recurring classes, that is the moment to move to Graph `calendarView`,
which expands them server-side.

The parser is deliberately strict about time zones for the same reason. Outlook
writes Windows zone names (`Mountain Standard Time`) that `zoneinfo` has never
heard of; the common US ones are mapped, and anything unrecognised is refused
rather than guessed at. Being silently an hour out twice a year is worse than a
visible error.

### Drop-in pricing

Shown as one plain line, not a gate. Someone who balks at the drop-in rate is
exactly the person for whom membership is the better deal, so the membership
link sits beside the price rather than behind it, and "other classes" is
offered next to "I'm here for the class". A person who came for one class and
leaves having browsed three and considered joining is a better outcome than a
completed drop-in payment.

This is not ticketing. People who signed up already paid through registration;
this is only the walk-in case.

**Every price in `_data/classes.yml` is a placeholder.** Nothing renders the
price block until real figures replace them.

### What is not built

Tier-aware pricing — showing someone their own rate rather than the public one
— needs the device to know the member's tier, which needs identity, which
needs Access or a Worker. The payment hand-off itself is blocked on the same
provider decision as everything else in `_data/providers.yml`.

## Featuring things on the homepage

`_data/featured.yml` is the whole content management system. It is a list.
Add an entry to put something on the front page; it removes itself when `ends`
passes. Four archetypes — `class`, `event`, `show`, `notice` — which is what
the actual pattern of announcements looks like.

Expiry is evaluated at build time, which is why the weekly workflow rebuilds
even when nothing changed. Otherwise a class that happened on Tuesday would
still be advertised on Friday.

If nothing is currently in its date window, the section renders nothing and
the page closes up around it. An empty `featured.yml` is a valid state.

## Hosted forms

`/book/` and `/register/` frame a Microsoft Form inside our own pages, so
nobody is handed a `forms.office.com` URL and asked to trust it. Configure
them in `_data/forms.yml`.

Both paths are chosen to work equally well as subdomains — `book.` and
`register.` read naturally, `/booking/` and `/sign-up/` redirect in for
forgiveness.

### Set the form to "Anyone can respond"

**A Form set to "Only people in my organization can respond" will not work
embedded in Safari.** Signing in needs an Entra session cookie, which counts
as third-party inside an iframe, and Safari blocks those by default. It works
in Chrome and fails on iPhones — the worst possible split for a studio whose
visitors arrive holding phones.

If a form genuinely needs sign-in, set `requires_signin: true` and the include
stops framing it: it renders a button that opens the form directly instead.
Better an honest handoff than something that works on the laptop it was tested
on.

### What framing buys, and what it doesn't

It buys the address bar, our header and footer, and the context around the
form — who it's for, what happens next, what it costs. That is most of feeling
first-party.

It does not restyle the form. A Microsoft Form in a frame still looks like a
Microsoft Form. Forms has its own theming in the designer and matching it
roughly to the site is worth ten minutes, but no amount of framing makes it
ours.

The direct link is shown permanently rather than as a fallback, because an
iframe that fails does so silently and cross-origin — we cannot detect it, so
the only honest thing is to offer both routes at once.

## Booking on a subdomain

Booking is expected to end up hosted elsewhere — likely Microsoft-built and
Microsoft-hosted, on something like `book.fcpublicmedia.org`. The concern is
that it should feel like part of this organization, not like scheduling a
video call with a stranger.

### Mapping a subdomain onto one of these paths

Two ways, and they differ in whether the subdomain survives in the address bar.

**Redirect rule (no code).** In Cloudflare: Rules → Redirect Rules, sending
`book.fcpublicmedia.org/*` to `fcpublicmedia.org/book/`. Two minutes, nothing
to deploy, nothing to maintain. The visitor ends up on the main domain, which
still reads as unmistakably ours — this is almost certainly enough.

**Worker rewrite (keeps the subdomain).** If `book.fcpublicmedia.org` must
stay in the address bar throughout, the Worker has to serve that hostname's
requests from the `/book/` path. That means adding a `main` script and
`run_worker_first` to `wrangler.jsonc` — perhaps fifteen lines, but it turns a
static-assets-only Worker into one with code in the request path, which is a
real step up in things that can break.

Worth being clear about what the subdomain actually buys: a visitor reading
`fcpublicmedia.org/book/` already knows whose page it is. The subdomain is
mostly useful if booking later moves to something FCPM doesn't host, at which
point it can be pointed elsewhere without the main site caring. That is a good
reason — but it is a future-proofing reason, not a trust one, and it does not
need solving today.

### Keeping an externally hosted booking tool feeling first-party

Three things carry most of that, in order of effect per unit of work:

1. **Same domain, not a redirect to a vendor URL.** A subdomain of
   `fcpublicmedia.org` reads as first-party; `outlook.office365.com/...` does
   not. This is most of the perceived difference and it costs one DNS record.
2. **Arrive and leave inside the site.** Link out from `/reservations/` with
   context already given — who can book, what the spaces are, what happens
   after — so the external page only has to collect a time. Send people back
   to a page here on completion.
3. **Carry the tokens across.** The palette, type scale, and spacing all live
   in the `:root` block of `assets/css/site.css`. Where the booking host
   allows custom CSS or a logo and color, copy those values rather than
   re-picking them by eye.

What not to spend effort on: recreating this site's header on the booking
host. Partial imitation reads worse than an honest, clean handoff.

Set `booking.subdomain` in `_data/providers.yml` once the host is chosen.

## Forms

A static site can't accept a form post. Two options, both fine:

- **A function in `/api`** that relays the submission to `info@fcpublicmedia.org`
  through Microsoft Graph. No third party, no per-submission cost, and the mail
  is already in the tenant.
- **A hosted form service** for the ones with real complexity — the program
  submission form has ranked scheduling preferences, a file upload, and a legal
  agreement, and is not worth hand-building.

## Deploying to Cloudflare

This is the fastest path to a real URL on a real domain, and it is what the
demo runs on.

Cloudflare now creates new projects as **Workers** rather than Pages, and the
two behave differently at deploy time. This repository is set up for the
Workers flow, which is what you get by default today.

Point the Cloudflare GitHub app at this repository and set:

| Setting | Value |
|---|---|
| Build command | `bundle exec jekyll build` |
| Deploy command | `npx wrangler deploy` |
| Build output directory | `_site` |
| Root directory | `/` (leave it alone) |

Everything else is in `wrangler.jsonc`, which is committed.

### Why wrangler.jsonc has to be committed

`wrangler deploy` looks for a config file. If it does not find one it runs
auto-configuration: it inspects the repository, decides what kind of project
this is, and **re-runs the build command through npx**. For a Ruby project
that produces `npx bundle exec jekyll build`, which fails with:

```
npm error could not determine executable to run
```

The Jekyll build has already succeeded at that point. The failure is wrangler
guessing, not the build. Committing `wrangler.jsonc` skips the guess.

### Notes

- **`bundle exec` is deliberate.** Cloudflare finds the `Gemfile` and runs
  `bundle install` on its own, so plain `jekyll build` also works. Prefixing
  with `bundle exec` guarantees the bundled Jekyll rather than whatever
  happens to be on `PATH`.
- **`_site` appears twice** — in the dashboard and in `wrangler.jsonc` under
  `assets.directory`. Both need it. It is Jekyll's default and is not
  overridden in `_config.yml`.
- **`.ruby-version` pins Ruby 3.2.2**, the default in Cloudflare's build
  image, and CI reads the same file. Without it the builder can fall back to
  a Ruby too old for Jekyll 4. Do not delete it.
- **Leave the root directory as `/`.** The `api/` folder is Azure Functions
  source, not a second site, and `_config.yml` excludes it from the output.
  There is one buildable component here, at the root.
- **`Gemfile.lock` is intentionally not committed.** A lock file resolved on a
  different platform is a common cause of `bundle install` failures on hosted
  builders. Jekyll is the only direct dependency.

### If you are on classic Pages instead

Same build command and output directory, no deploy command, and
`wrangler.jsonc` is ignored. Both flows serve `_redirects` and `_headers`
from the output, so the redirect handling below applies either way.

### Redirects and headers

Cloudflare Pages reads `_redirects` and `_headers` from the root of the
published output. Azure reads `staticwebapp.config.json`. **All three are
generated from `_data/redirects.yml`** at build time, so the hosts cannot
drift apart — add a redirect once and both get it.

The 20 legacy Wix URLs therefore keep working on either host, which matters:
those are the links currently indexed by Google and sitting in other people's
bookmarks.

## Deploying to Azure Static Web Apps

`.github/workflows/deploy.yml` builds with Jekyll and deploys to Azure Static
Web Apps on every push to `main`. Pull requests get their own preview URL,
which means the board can look at a change before it goes live — something Wix
has never offered.

One secret is required: `AZURE_STATIC_WEB_APPS_API_TOKEN`, from the Static Web
App resource in the Azure portal.

The free tier covers the static hosting, the managed functions, the auth, and a
custom domain with a certificate.

### Cloudflare or Azure?

Both, for now, and that is not indecision.

**Cloudflare Pages** is the demo host: it attaches to the domain in minutes
and needs no Azure setup. It serves static files, which is all this site
currently is.

**Azure Static Web Apps** is where this goes if members-only pages are
wanted, because it bundles static hosting, Entra ID sign-in, and a small
serverless API into one free resource inside the Microsoft 365 tenant the
organization already has. Cloudflare Pages can do auth and functions too, but
not with Entra sitting right there.

Nothing about the site favours one over the other — that is the point of it
being static files. `_site/` deploys anywhere, both hosts build from the same
command, and the redirect list feeds both. Switching later is a DNS change,
not a rewrite.

---

## Known issues on the current site

Carried over as a to-do list, since each is a one-line fix here:

- Footer copyright reads 2025
- The instructor page slug is misspelled: `/innstructor-application`
- Donate is not linked from the site navigation
- Two abandoned store sitemaps from 2022 are still published
- Membership term is stated two contradictory ways (calendar year vs. rolling
  year from signup)
- Several pages load slowly because of Wix widgets, including one that displays
  the weather
- The equipment page is a photo gallery of the inventory, which is neither
  searchable nor the question visitors are asking. Bookable is the system of
  record and staff pick the gear, so the page should summarise categories
  rather than list items
