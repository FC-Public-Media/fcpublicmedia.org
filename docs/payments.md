# Payments

Who takes which payment, how prices are built, the rules about keys, and what has to be true before
anyone is charged. The site-worker itself is [FC-Public-Media/site-worker](https://github.com/FC-Public-Media/site-worker).

## Transactions

A hand-off to a paid or stateful service is a link written on the page that owns it, once the
service exists. Until then the page says nothing about it: no placeholder block.

| Hand-off | What | Today |
|---|---|---|
| `tickets` | Class registration | Wix Events |
| `membership` | Dues | The Wix membership form's tier field |
| `donate` | Donations | Off-site entirely: `fcpm.donate` in `site/_config.yml` is the header's button, and there is no `/donate/` page |
| `booking` | Studio and bay reservations | Booqable |
| `submit` | Program submissions | Wix form and Dropbox |

## Who charges

| What | Charged by | Price from |
|---|---|---|
| Membership | Stripe, through the site-worker's `POST /checkout` | `site/_data/membership.yml` |
| Class drop-in | Stripe, through the site-worker | Undecided; no price file |
| Equipment rental | Booqable, on its own Stripe connection | Booqable |

One Stripe account, two credentials. The site-worker sells no equipment: two systems charging for one
booking bills somebody twice.

## Keys

| Key | Publishable | Lives in | Scope |
|---|---|---|---|
| `pk_live_…` / `pk_test_…` | Yes | `site/_data/payments.yml` `stripe.publishable_key` | Starts a payment |
| `PUBLIC_STRIPE_API_KEY` (`rk_live_…`, `rk_test_…`) | No | digitization's keychain → Cloudflare secret | Write Checkout Sessions only |
| `STAFF_STRIPE_API_KEY` (`rk_live_…`) | No | The staff member's shell | Read and write subscriptions and prices |
| `SYNC_STRIPE_API_KEY` (`rk_live_…`) | No | digitization's keychain, `stripe-sync` | Read products and prices only |
| `sk_live_…` | No | Not used | |

- The prefix names who makes the key act. `/checkout` authenticates nobody, so a stranger triggers
  `PUBLIC_`, and it may only do what the public may do. A public endpoint that needs more gets a
  different key, never a wider one.
- `PUBLIC_` is still secret: never rendered, logged or returned. `site/bin/test_no_secrets.py` fails CI
  if anything shaped like a secret key reaches the built site or a tracked file.
- The two `rk_` values must differ; `site/bin/reprice-subscriptions.py` refuses to run if they match.
- An `rk_` or `sk_` key that reaches a commit is burned: rotate it in the Stripe dashboard.

Secrets are held in digitization's keychain (`machines/digitization/keys.yml`, PROFILE.md, Keys), not in
GitHub. The site-worker's `bin/deploy`, run under `keys run cloudflare stripe-live`, deploys it and pipes
the key into `wrangler secret put PUBLIC_STRIPE_API_KEY` on every run, so a rotation lands. A test key is
tried without deploying anything: `keys run stripe-test -- node try-checkout.mjs` in a site-worker checkout.

## Tiers

The membership tiers are Stripe's. A tier is an active, yearly, recurring Price whose lookup key is
`membership:<slug>`, on an active Product; the Product's name is what the tile says. Anything else in
the account (donations, Booqable's own) is ignored.

Until Stripe holds the prices, `python3 site/bin/sync-tiers.py --catalog <site-worker>/src/prices.js` writes
them from what `/checkout` actually charges, so the page and the charge agree. Once it does,
`keys run stripe-sync -- python3 site/bin/sync-tiers.py` writes them, cheapest first, to
`site/_data/tiers.json` (`sku`, `name`, `amount` in cents, `currency`, `price` as printed); commit it.
Run by hand after a tier changes in Stripe, like the calendar: a pull, never a live call from the page.
With no tier found it writes nothing and exits 1, so a wrong key never empties `/join/`; with no
`tiers.json`, `/join/` shows no tier grid. The nonprofit price on each tile is
`fcpm.membership.nonprofit_rate` in `site/_config.yml`, to the dollar.

## Prices

The browser posts a SKU (`membership:creator`), never an amount; the site-worker looks the amount up in
its own `src/prices.js` (cents), edited in that repository. Nothing here writes it any more. `/join/`'s
tiles read it back through `sync-tiers.py --catalog` ([Tiers](#tiers)); run that after a price changes
there, so the page and the charge agree.

- An item absent from `prices.js` answers 400 at `/checkout`. Drop-ins have no price at all yet, so they are not for sale.
- Sessions use inline `price_data`. Once the tiers are Prices in Stripe, the site-worker should charge by
  lookup key and `prices.js` retires.
- Subscriptions carry `metadata[sku]` and `[priced]`, which repricing reads.

### Price changes

Stripe pins a subscription to its original amount and never reads this repository, so a price edit
reaches only new members until `site/bin/reprice-subscriptions.py --apply` moves existing ones
(without `--apply` it reports). It sets `proration_behavior=none`, and lists rather than moves any
subscription without a known `sku`.

1. In Stripe, give the tier's Product a new yearly Price with the same lookup key (it moves over) and
   archive the old one; run `sync-tiers.py` and commit `tiers.json`.
2. New members pay the new price once it deploys.
3. Email the membership (`terms.announcements` in `site/_data/payments.yml`).
4. After `terms.price_change_notice_days`, run `reprice-subscriptions.py --apply`.
5. Everyone renews at the new price on their own anniversary.

Paying the year up front fixes that year's price; a subscription renews at the current price.

### Nonprofit rate

Nonprofits pay half (`fcpm.membership.nonprofit_rate` in `site/_config.yml`), settled before payment. `site/bin/sync-nonprofits.py` writes
Larimer County 501(c)(3)s from the IRS master file to `site/assets/nonprofits.json` (on every
`bin/deploy-site`). The organization picks itself on `/membership/`; "not listed"
is an equal path to a person. Staff verify the EIN and issue a Stripe promotion code
(`allow_promotion_codes` is on every session). The site-worker ignores any `nonprofit` field in a request.

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

## Requests

Join (a paid checkout), a room request (`/reserve/`), a class signup (`/learn/`) and a check-in each
become one row in one log: a list on the Operations SharePoint site, added to by the site-worker and
by nothing else. Each form is written in its page, field names being the site-worker's tank keys (its `src/tanks.js`), and
`site/assets/js/answers.js` posts it to `/answers` and shows the reference. With `site_worker.yml` `url` empty,
or a send refused, the same answers open as an email to info@. Built: `/submit/` (`program`); the program
file goes to Dropbox's file request in a new tab, never framed (Dropbox refuses) and never a precondition.
`/join/` (`membership`, `site/assets/js/join.js`): the answers go to the tank with the tier's SKU, then `/checkout`
with the same `reference`, then Stripe; answers that fail to keep never stop the payment page. Stripe returns to
`/join/?joined`. "Just send these" keeps the answers and tier without paying. The terms it links are
`site/assets/docs/studio-terms.pdf` and `equipment-terms.pdf`, from the Wix copy. A request asks on the
page that owns the thing; `/book/` and `/register/` were Wix's separate pages and are dropped
(2026-10-25). The site-worker's access is the `m365` group in digitization's keychain.

## Before charging

| Item | Where | Status |
|---|---|---|
| `CLOUDFLARE_API_TOKEN` | digitization's keychain, `cloudflare` | Not held; the site-worker does not deploy |
| `PUBLIC_STRIPE_API_KEY` | digitization's keychain, `stripe-live` (`stripe-test` beside it) | Live not held |
| Publishable key | `payments.yml` `stripe.publishable_key` | Empty |
| Site-worker URL | `url` in `site/_data/settings.yml`, `authorize.yml`, `upload.yml` | Empty |
| What each tier includes | `membership.yml` `tiers[].includes` | Board; all `[]` |
| Student, Creator, Producer summaries | `membership.yml` `tiers[].summary` | Board; `TODO` |
| Class drop-in prices | None yet | Board |
| Who emails a price change | `payments.yml` `terms.announcements.owner` | Board; `TODO` |
| 30 days' notice | `payments.yml` `terms.price_change_notice_days` | Board to confirm |
| Membership terms page | `terms.page`, `/policies/membership-terms/` | Missing; subscriptions only |
| A buy button calling `POST /checkout` | `/membership/` | Not built |
| Success page | `/thanks/`, the default `success_path` | Missing |
| Switch on | `payments.yml` `stripe.live` | `false` |
