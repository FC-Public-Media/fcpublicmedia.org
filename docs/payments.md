# Payments

Who takes which payment, how prices are built, the rules about keys, and what has to be true before
anyone is charged. The broker itself is [`worker/README.md`](../worker/README.md).

## Transactions

Every hand-off to a paid or stateful service is an entry in `site/_data/providers.yml`, rendered by
`site/_includes/transaction.html`. An empty `url` renders a visible "not wired up yet" block.

| Key | What | Today |
|---|---|---|
| `tickets` | Class registration | Wix Events |
| `membership` | Dues | The Wix membership form's tier field |
| `donate` | Donations | Nothing (Wix's page is empty) |
| `booking` | Studio and bay reservations | Booqable |
| `submit` | Program submissions | Wix form and Dropbox |

## Who charges

| What | Charged by | Price from |
|---|---|---|
| Membership | Stripe, through the broker's `POST /checkout` | `site/_data/membership.yml` |
| Class drop-in | Stripe, through the broker | `site/_data/classes.yml` `dropin` |
| Equipment rental | Booqable, on its own Stripe connection | Booqable |

One Stripe account, two credentials. The broker sells no equipment: two systems charging for one
booking bills somebody twice.

## Keys

| Key | Publishable | Lives in | Scope |
|---|---|---|---|
| `pk_live_…` / `pk_test_…` | Yes | `site/_data/payments.yml` `stripe.publishable_key` | Starts a payment |
| `PUBLIC_STRIPE_API_KEY` (`rk_live_…`, `rk_test_…`) | No | digitization's keychain → Cloudflare secret | Write Checkout Sessions only |
| `STAFF_STRIPE_API_KEY` (`rk_live_…`) | No | The staff member's shell | Read and write subscriptions and prices |
| `sk_live_…` | No | Not used | |

- The prefix names who makes the key act. `/checkout` authenticates nobody, so a stranger triggers
  `PUBLIC_`, and it may only do what the public may do. A public endpoint that needs more gets a
  different key, never a wider one.
- `PUBLIC_` is still secret: never rendered, logged or returned. `site/bin/test_no_secrets.py` fails CI
  if anything shaped like a secret key reaches the built site or a tracked file.
- The two `rk_` values must differ; `site/bin/reprice-subscriptions.py` refuses to run if they match.
- An `rk_` or `sk_` key that reaches a commit is burned: rotate it in the Stripe dashboard.

Secrets are held in digitization's keychain (`machines/digitization/keys.yml`, PROFILE.md, Keys), not in
GitHub. `machines/digitization/deploy-broker live` deploys the Worker and pipes the key into
`wrangler secret put PUBLIC_STRIPE_API_KEY` on every run, so a rotation lands. A test key is tried without
deploying anything: `machines/digitization/keys run stripe-test -- node worker/try-checkout.mjs`.

## Prices

The browser posts a SKU (`membership:creator`), never an amount; the broker looks the amount up in
`worker/src/prices.js`.

- `site/bin/build-prices.py` generates `prices.js` (cents) from `membership.yml` and `classes.yml`.
  It is committed, because Cloudflare's build runs no Python; `.github/workflows/smoke.yml` runs
  `build-prices.py --check` and fails on drift. Run `build-prices.py` after editing a price.
- A `TODO` price is left out, so `/checkout` answers 400 for it. That is why drop-ins are not for sale.
- Sessions use inline `price_data`; there are no Price objects in the Stripe dashboard, and
  `git log -p site/_data/membership.yml` is the price history.
- Subscriptions carry `metadata[sku]` and `[priced]`, which repricing reads.

### Price changes

Stripe pins a subscription to its original amount and never reads this repository, so a price edit
reaches only new members until `site/bin/reprice-subscriptions.py --apply` moves existing ones
(without `--apply` it reports). It sets `proration_behavior=none`, and lists rather than moves any
subscription without a known `sku`.

1. Edit the price in `site/_data/membership.yml`; pull request, review, merge.
2. New members pay the new price once it deploys.
3. Email the membership (`terms.announcements` in `site/_data/payments.yml`).
4. After `terms.price_change_notice_days`, run `reprice-subscriptions.py --apply`.
5. Everyone renews at the new price on their own anniversary.

Paying the year up front fixes that year's price; a subscription renews at the current price.

### Nonprofit rate

Nonprofits pay half (`nonprofit.rate`), settled before payment. `site/bin/sync-nonprofits.py` writes
Larimer County 501(c)(3)s from the IRS master file to `site/assets/nonprofits.json` (monthly, by
`.github/workflows/sync-nonprofits.yml`). The organization picks itself on `/membership/`; "not listed"
is an equal path to a person. Staff verify the EIN and issue a Stripe promotion code
(`allow_promotion_codes` is on every session). The broker ignores any `nonprofit` field in a request.

## Booqable

`site/_includes/booqable.html` renders Booqable inline on `/reserve/` only, not in an iframe.

- `booqable.snippet` in `payments.yml` is pasted verbatim from Settings → Online Bookings → Website
  integration. It carries a public company ID; no access token is stored.
- Booqable sells: the datepicker, the cart drawer and the checkout are theirs. Checkout leaves our site
  for `fort-collins-public-media.booqableshop.com` (no `checkoutDomain`, so no custom domain). The
  Terms checkbox, the security deposit and the members' note are Booqable settings, not page text.
- Tiles | List (`site/assets/js/booqable-view.js`): tiles are Booqable's markup untouched; list is
  `site.css` under `.booqable-store.is-list`, the default, remembered per browser. A Booqable markup
  change can break the list, never the tiles or the checkout.
- The cart and quickview are portaled to `<body>`; nothing in `site.css` may hide them.

## Hosted forms

`/book/` and `/register/` frame a Microsoft Form (`site/_includes/hosted-form.html`,
`site/_data/forms.yml`). Set each form to "Anyone can respond": Safari blocks the Entra sign-in cookie
in a frame. `requires_signin: true` links out instead. The direct link is always shown. A booking
subdomain goes in `booking.subdomain` in `providers.yml`, mapped by a Cloudflare Redirect Rule.

## Before charging

| Item | Where | Status |
|---|---|---|
| `CLOUDFLARE_API_TOKEN` | digitization's keychain, `cloudflare` | Not held; the broker does not deploy |
| `PUBLIC_STRIPE_API_KEY` | digitization's keychain, `stripe-live` (`stripe-test` beside it) | Live not held |
| Publishable key | `payments.yml` `stripe.publishable_key` | Empty |
| Broker URL | `url` in `site/_data/settings.yml`, `authorize.yml`, `upload.yml` | Empty |
| What each tier includes | `membership.yml` `tiers[].includes` | Board; all `[]` |
| Student, Creator, Producer summaries | `membership.yml` `tiers[].summary` | Board; `TODO` |
| Class drop-in prices | `classes.yml` `dropin` | Board; `TODO` |
| Who emails a price change | `payments.yml` `terms.announcements.owner` | Board; `TODO` |
| 30 days' notice | `payments.yml` `terms.price_change_notice_days` | Board to confirm |
| Membership terms page | `terms.page`, `/policies/membership-terms/` | Missing; subscriptions only |
| A buy button calling `POST /checkout` | `/membership/` | Not built |
| Success page | `/thanks/`, the default `success_path` | Missing |
| Switch on | `payments.yml` `stripe.live` | `false` |
