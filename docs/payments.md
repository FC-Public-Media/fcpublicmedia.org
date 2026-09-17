<!--
Split out of the root README on 2026-09-17, unchanged apart from paths.

The README was 68 KB and had become the only place a lot of this was written
down, which made it both the first thing a visitor saw and the last place
anybody wanted to edit. Nothing here was rewritten in the move; if something
reads as out of date, it was out of date before it moved, and saying so is
welcome.
-->

# Taking payments

The five transactions, who processes each, and the rules about keys.

## The five transactions

Everything on this site that isn't a static file goes through
`site/_data/providers.yml` and `site/_includes/transaction.html`. That's on purpose:
switching a vendor is a one-line edit, and it's impossible to lose track of how
many paid integrations the organization has.

| Key | What it is | Now |
|---|---|---|
| `tickets` | Class registration | Wix Events |
| `membership` | Dues | Wix Pricing Plans |
| `donate` | Donations | Wix Donations |
| `booking` | Studio and bay reservations | Booqable — staying |
| `submit` | Program submissions | Wix form + Dropbox |

An entry with an empty `url` renders as a visible "not wired up yet" block
rather than a dead button, so nothing ships silently broken.

Booking stays on Booqable. Microsoft 365 calendar integration is being built
separately; when it lands, only the `booking` entry changes.

---

## Taking payments

Two systems, one Stripe account, and a rule about keys. `site/_data/payments.yml`
holds the decisions; this is the operating manual.

| What | Who charges | Where the money is decided |
|---|---|---|
| Membership | Stripe, via the broker | `site/_data/membership.yml` |
| Class drop-in | Stripe, via the broker | `site/_data/classes.yml` (still TODO) |
| Equipment rental | Booqable's own Stripe connection | Booqable |

### The rule about keys

Stripe issues three kinds and they are not interchangeable.

| Prefix | Publishable? | Where it lives |
|---|---|---|
| `pk_live_…` | **Yes** | `site/_data/payments.yml`, in git |
| `rk_live_…` | No | GitHub org secret → Cloudflare secret |
| `sk_live_…` | No | Not used at all |

### The naming convention: who causes the key to be used

Our secrets are named for **blast radius, not visibility**. The prefix answers
"who makes this key act?", and the answer determines how tightly it is scoped.

| Name | Who triggers it | Scoped to |
|---|---|---|
| `PUBLIC_STRIPE_API_KEY` | A stranger on the internet | Write a Checkout Session. Nothing else. |
| `STAFF_STRIPE_API_KEY` | A person, at a terminal | Read and write subscriptions and prices. |

`/checkout` authenticates nobody — it cannot, since requiring a passkey to
join would mean being a member before you could become one. So every use of
that key is caused by a stranger, and it holds exactly the permission a
stranger is allowed to cause. No refunds, no customer list, no balance.

The name is a standing instruction to whoever scopes the next one: **a
credential named `PUBLIC_` may only do what the public may do.** If a
public endpoint ever needs to read a customer or issue a credit, that is a
signal to reach for a different key rather than to widen this one.

**`PUBLIC_` still does not mean publishable.** The value is a secret and must
never be rendered into a page, logged, or returned in a response — only `pk_`
may be. That is a reasonable thing to misread in a hurry, so the guarantee is
mechanical rather than documentary: `site/bin/test_no_secrets.py` fails the
build if anything shaped like a secret key reaches the built site or a tracked
file, whatever anybody believed while putting it there.

The two keys are deliberately never the same value. `reprice-subscriptions.py`
refuses to run if they match — if one key could do both jobs, the public one
has been given the power to rewrite the membership's billing, which is exactly
what the naming exists to prevent.

### A GitHub secret is not a Cloudflare secret

They are separate stores and neither can see the other. A GitHub organization
secret is readable by GitHub Actions and nothing else; the worker runs at
Cloudflare and reads its own environment. Putting the key in one place does
not put it in the other, which is a thing that looks configured and is not.

`.github/workflows/broker.yml` is the bridge: it deploys the broker and then
pushes the org secret into Cloudflare's store on every run, so GitHub stays
the single place a human ever pastes the value and a rotation reaches
production without anybody remembering a manual step. It needs
`CLOUDFLARE_API_TOKEN` (Cloudflare dashboard → My Profile → API Tokens → *Edit
Cloudflare Workers*) and skips entirely until that exists.

To set it by hand instead:

```
cd worker && npx wrangler secret put PUBLIC_STRIPE_API_KEY
```

It prompts, reads the value from the terminal, and stores it encrypted. It is
never written to disk and never appears in `wrangler.jsonc`. The broker also
accepts `STRIPE_KEY`, so a secret already set under that name keeps working.

The publishable key can start a payment and do nothing else, so it is safe in
the repository — that is what it is for. The restricted key is the one that
acts on the account, and ours is scoped to writing Checkout Sessions and
nothing more: if the worker were compromised tomorrow, the key it holds could
not issue a refund, read the customer list, or move the balance. Stripe now
recommends restricted keys over `sk_` for exactly this reason.

If an `rk_` or `sk_` key ever lands in a commit, it is burned the moment it is
pushed. Rotate it in the Stripe dashboard rather than just deleting the line.

### Why the browser cannot name a price

This is the only rule that really matters. A page that posts an amount to a
checkout endpoint is a page that can post `1`, and no amount of JavaScript on
our side changes that, because the JavaScript is theirs.

So the browser posts a SKU — `membership:creator` — and the broker looks the
amount up in a table the browser cannot reach. `worker/test/checkout.test.mjs`
opens with that assertion and it is the reason the file exists.

### Why the prices are not in the Stripe dashboard

Because subscriptions are a standing promise about future prices, and we have
to be able to show that we announced a change.

A price in the Stripe dashboard has no such trail: somebody with a login edits
a number, and the first anyone hears of it is a card statement. A price in
`site/_data/membership.yml` is a commit — a red line, a green line, a reviewer, and
a date. `git log -p site/_data/membership.yml` **is** the price history.

Stripe still does the charging; it just does not hold the number. Every
Checkout Session is created with an inline `price_data`, so there are no Price
objects anywhere to drift from the data files.

```
python3 site/bin/build-prices.py          # after editing a price
python3 site/bin/build-prices.py --check  # what CI runs
```

The generated `worker/src/prices.js` is committed, because the worker bundles
it at deploy time and Cloudflare's build does not run Python. CI fails if the
two disagree — the same shape as a lock file, and for the same reason.

A price of `TODO` is skipped rather than defaulted, so an undecided figure
cannot become a real charge. That is why the class drop-ins are not for sale
yet.

### Stripe does not know this repository exists

Worth stating plainly, because it is the opposite of what it feels like.

When somebody subscribes, Stripe turns our inline `price_data` into a Price
object, pins the subscription to it, and renews against that pinned amount for
as long as the subscription lives. It never calls back. It never re-reads
`site/_data/membership.yml`. There is no webhook asking what a renewal should cost.

So editing a price here changes what **new** members pay and nothing else.
Existing subscribers keep renewing at what they signed up at — silently,
forever. That is grandfathering, and it is a real decision some organizations
make on purpose. FCPM never has: everybody is always on the current plan.

Which means the grandfathering has to be undone deliberately:

```
python3 site/bin/reprice-subscriptions.py            # report, changes nothing
python3 site/bin/reprice-subscriptions.py --apply    # move them
```

Nobody is prorated — `proration_behavior=none`, so the year already bought
runs out at the price it was bought at and the new amount applies at the next
renewal. Anything else takes money from people between announcements.

### The order a price change happens in

1. Edit the price in `site/_data/membership.yml`.
2. Pull request, review, merge. **That is the price history.**
3. New members pay the new price as soon as it deploys.
4. Email the membership.
5. **After the notice period has elapsed**, run `--apply`.
6. Everyone renews at the new price on their own anniversary.

Step 5 is deliberately manual. A price change that reaches people's cards the
moment a pull request merges is a price change nobody announced, and "we told
you thirty days ago" has to be true before the charge moves. Dry-run is the
default so reaching for it by accident produces a report, not a bill.

### One year up front is a price lock; subscribing is not

The two options differ on more than convenience, and the page has to say so.

Paying for the year up front **is** a price lock for that year — there is no
renewal to reprice, so a change during those twelve months cannot reach you.
Subscribing renews at whatever the price is on your anniversary, because there
are no grandfathered plans.

### How a nonprofit actually pays half

Not by ticking a box. The old sequence was: pick a tier, pay full price, staff
notice, somebody posts a cheque back — and organizations learned to buy the
wrong thing deliberately and wait for the refund.

The fix is not a stricter rule, it is checking **earlier**:

1. `site/bin/sync-nonprofits.py` puts the IRS 501(c)(3) list on the site.
2. The organization picks itself off that list before paying.
3. Staff verify the EIN and issue a Stripe promotion code.
4. The code halves the price at checkout.

Stripe holds the codes, so an unverified visitor cannot mint one and a
verified one never has to be trusted with an amount. `allow_promotion_codes`
is set on every session; the broker ignores a `nonprofit: true` in the request
body entirely, and there is a test that it does.

### Booqable

Spelled with a q — [booqable.com](https://booqable.com), a rental system.

**No credential is needed to show products or take a booking.** This is worth
being precise about, because the two things Booqable calls "authentication"
are for different jobs:

| | What it is | Where it goes |
|---|---|---|
| Company ID | Public, baked into the embed snippet | `site/_data/payments.yml`, in git |
| Access token | Employee-scoped, reads and writes the business | Nowhere, currently |

The embed snippet carries the company ID and that is all it needs. Products,
live availability, real pricing, cart and checkout all work from it. Booqable
pre-populates it precisely so it can be pasted into any website's HTML, and
their docs say to keep access tokens *out* of client-side code.

So the access token buys exactly one thing we do not currently have: the
catalog as **data at build time**, so gear appears in our own HTML rather than
being drawn by their JavaScript after load — indexable, readable with
JavaScript off, styled entirely by us. That is a real benefit, and it is also
a GitHub Action, a stored secret, and a sync that can drift. Not yet.

To switch reservations on: paste the snippet from Settings → Online Bookings →
Website integration into `booqable.snippet` in `site/_data/payments.yml`. Until
then `/equipment/` shows a visible "not wired up yet" block, same as the other
unconfigured transactions.

The snippet is stored **pasted, not reconstructed**. The script URL and its
attributes are Booqable's to change, and one assembled from a guess reviews
fine and loads nothing.

### Why this is not an iframe

The iframe on the current site is a **Wix constraint, not a Booqable one**.
There are more than six items and nothing says so — you have to discover that
the inner box scrolls. Wix's HTML element *is* an iframe, so it was the only
thing Wix could do.

Here the components are ordinary divs in our own document:

```html
<div class="booqable-datepicker"></div>
<div class="booqable-product-list" data-per="12" data-show-search="true"></div>
```

The page grows to fit them, our stylesheet applies, and `data-per` makes the
list **paginate with a control you can see** instead of hiding the seventh
item below the fold of a fixed-height box. Other attributes: `data-tags`,
`data-collections`, `data-limit`, and there are separate mount points for
`booqable-collections`, `booqable-sidebar`, `booqable-sort` and
`booqable-bar`.

### We restyle their store into a list

Their layout is a grid of cards. Ours is one item per row — thumbnail, name,
price, add button — because gear is picked from by scanning names, and names
read faster in a column than in a grid. A card grid also spends most of a
phone screen on photographs of black rectangles that all look alike: six rows
fit where one and a half cards did.

That is possible because their bundle has no `attachShadow`, no custom
elements, and ships a global stylesheet — a React app rendering into our light
DOM, which our CSS can reach. Each override in `site.css` names the rule it is
fighting, and they are all real rules read out of their stylesheet.

The one they all descend from: `.booqable-product { min-width: 280px }` in a
flex-wrap container. Two of those plus the gap need 576px, so a 390px phone
could only ever show one. The width was never responsive — it is a floor, and
the floor is wider than half a phone.

**If Booqable changes their markup, these stop applying.** The failure mode is
their card grid coming back, not a broken page. Their script does not load on
a CI runner, so none of it is covered by a test — it is checked by looking.

The script loads on `/equipment/` only, not site-wide — it is a third party,
and there is no reason for it to run on the twenty-five pages with nothing to
book.

---

## Hosted forms

`/book/` and `/register/` frame a Microsoft Form inside our own pages, so
nobody is handed a `forms.office.com` URL and asked to trust it. Configure
them in `site/_data/forms.yml`.

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
   in the `:root` block of `site/assets/css/site.css`. Where the booking host
   allows custom CSS or a logo and color, copy those values rather than
   re-picking them by eye.

What not to spend effort on: recreating this site's header on the booking
host. Partial imitation reads worse than an honest, clean handoff.

Set `booking.subdomain` in `site/_data/providers.yml` once the host is chosen.

## Forms

A static site can't accept a form post. Two options, both fine:

- **A function in `/api`** that relays the submission to `info@fcpublicmedia.org`
  through Microsoft Graph. No third party, no per-submission cost, and the mail
  is already in the tenant.
- **A hosted form service** for the ones with real complexity — the program
  submission form has ranked scheduling preferences, a file upload, and a legal
  agreement, and is not worth hand-building.
