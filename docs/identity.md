<!--
Split out of the root README on 2026-09-17, unchanged apart from paths.

The README was 68 KB and had become the only place a lot of this was written
down, which made it both the first thing a visitor saw and the last place
anybody wanted to edit. Nothing here was rewritten in the move; if something
reads as out of date, it was out of date before it moved, and saying so is
welcome.
-->

# Identity and check-in

Who somebody is, how they prove it, and what happens at the door.

## Members and sign-in

The current site has no real accounts, and it doesn't need them. What it needs
is a way to tell whether the person asking to book a studio has paid.

Azure Static Web Apps does this without a user table:

1. A visitor clicks sign in and authenticates against **Entra ID**. FCPM never
   stores a password and never has one to leak.
2. SWA calls **`api/GetRoles`** once, with the visitor's email.
3. That function looks up whether the email has paid dues and hasn't expired,
   and returns `["member"]` or `[]`.
4. `site/staticwebapp.config.json` gates `/members/*` on that role.

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
python3 site/bin/make-qr.py
```

The generated code was decoded back to `https://www.fcpublicmedia.org/check-in/`
to confirm it is correct — a printed poster with a wrong URL is worse than no
poster.

### Location

Checking in requires being at the studio. Coordinates, radius, and re-check
interval are in `site/_data/checkin.yml`.

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
   python3 site/bin/mint-claim.py --new-key claim-key.pem   # once, ever
   python3 site/bin/mint-claim.py --email someone@example.com
   ```

2. Receiving the mail is the proof — only the holder of that mailbox gets it.
3. Opening the link verifies an ECDSA P-256 signature against the public key in
   `site/_data/identity.yml` and stores the token on that device.

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
  `site/_data/identity.yml`, default 120) or until its signing key is removed from
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
  `site/_data/authorize.yml` safe.

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

**Set `url` in `site/_data/settings.yml` to turn it on.** Empty is the shipped
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

**In this repository:** set `identity.mode: access` in `site/_data/checkin.yml`.
That is the whole change.

**How the result is caught.** After a visitor authenticates, Cloudflare sets a
`CF_Authorization` cookie on the hostname. `site/assets/js/checkin.js` then calls:

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
