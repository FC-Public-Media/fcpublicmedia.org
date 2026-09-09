# Switching payments on

**Everything standing between this repository and taking a payment, in the
order it has to happen.** Written 2026-09-09.

This is a runbook, not a design document. The design is in
[`_data/payments.yml`](_data/payments.yml), which is the best-commented file
here and explains *why* each of these exists. This file only answers "what is
left, and who can do it."

## The short version

The machinery is finished and switched off. The broker is written, its 119
tests pass, the price list generates from `_data/` and CI fails if the two
disagree. **Nothing here needs designing.** What is missing is four values,
one namespace, one page, and two board decisions.

Today the honest answer to "can FCPM take money on its own website" is **no,
except Booqable equipment rental**, which runs on Booqable's own Stripe
connection and not on anything in this repository.

## 1. Things only an account holder can do

Each of these is a value someone has to paste. None can be worked out from the
repository, and none of them is a decision.

| # | What | Where it goes | Blocks |
|---|---|---|---|
| 1.1 | Create the KV namespace: `cd worker && npx wrangler kv namespace create CHALLENGES` | add a `kv_namespaces` block to `worker/wrangler.jsonc` with the printed id | **the broker deploying at all** |
| 1.2 | A Cloudflare API token, *Edit Cloudflare Workers* template | org secret `CLOUDFLARE_API_TOKEN` | the broker deploying |
| 1.3 | The restricted Stripe key (`rk_live_…`, scoped to writing Checkout Sessions) | org secret `PUBLIC_STRIPE_API_KEY` | the broker charging |
| 1.4 | The publishable key (`pk_live_…` or `pk_test_…`) | `_data/payments.yml`, `stripe.publishable_key` | nothing yet — it is for the page |
| 1.5 | The broker's deployed URL | `_data/settings.yml`, the broker `url` | the site reaching the broker |

**1.1 is the one that surprises people.** The broker needs a KV namespace for
WebAuthn challenges, and it has none, so this blocks everything downstream of
it — including the two steps in `broker.yml` that are currently skipping for a
different reason. Fixing the token without fixing this just moves the failure.

The binding is deliberately **absent** from `worker/wrangler.jsonc` rather than
present-and-empty. Wrangler validates the whole file before running any
command and rejects an entry whose `id` is `""` — so a placeholder locked the
directory and refused the very command that produces the id. Add the block
once you have it; the file explains the shape.

**On the naming of 1.3.** The secret is called `PUBLIC_STRIPE_API_KEY` and its
value is not public in any sense. The name says *who causes the key to be
used* — `/checkout` authenticates nobody, so a stranger makes it act — and the
key is scoped to exactly what a stranger may cause. `script/test_no_secrets.py`
fails the build if anything shaped like it reaches the site, because somebody
will eventually read that name, believe it, and put the value in a template.

## 2. The board's decisions

These are not ours and a plausible guess at any of them is worse than a blank.

| # | Decision | Where it lands |
|---|---|---|
| 2.1 | What each membership tier actually includes | `_data/membership.yml`, `tiers[].includes` — all four are `[]` |
| 2.2 | Tier summaries for Student, Creator and Producer | `_data/membership.yml`, `tiers[].summary` — all three say `TODO` |
| 2.3 | Class drop-in prices, public and member | `_data/classes.yml`, `dropin` — both `TODO` |
| 2.4 | Who owns emailing the membership before a price change | `_data/payments.yml`, `terms.announcements.owner` — says `TODO` |
| 2.5 | Confirm 30 days' notice before a price change | `_data/payments.yml`, `terms.price_change_notice_days` |

**2.1 and 2.2 are live on the public site right now.** `membership.md` renders
`tier.summary` unconditionally, so `/membership/` currently publishes the word
"TODO" to visitors under three of the four tiers.

**2.3 is why class drop-ins cannot be sold.** `script/build-prices.py` refuses
to put a `TODO` price in the catalogue — an unpriced thing is absent rather
than present at zero — so the broker returns a 400 for `class-dropin:*` and
the page hides the price rather than showing a number nobody approved. That
refusal is correct. It is also the entire blocker.

## 3. A page that has to exist before subscriptions

`_data/payments.yml` points `terms.page` at **`/policies/membership-terms/`**,
which **does not exist** — `policies/` contains only `non-discrimination.md`.

A link to recurring-payment terms is required on the checkout page for
subscriptions; it is what the card networks expect to see when a cardholder
disputes a renewal. The text is largely written already, in
`_data/payments.yml` under `terms.summary` and `terms.lock`. It needs a page
built from it, not new wording.

**One-off payments do not need this.** If the goal is to take money soon, sell
the up-front year first and leave renewals until the page exists.

## 4. The build step that is still missing

**Nothing on the site calls the broker.** `POST /checkout` is implemented,
tested and routed; no page, include or script sends it anything.
`membership.md` renders tiers and prices as static cards with no buy button.

So even with every value above in place, a visitor could not pay. This is
code rather than a value or a decision, and it is the one remaining item that
is ours.

The contract, for whoever builds it:

```
POST <broker>/checkout      { sku, recurring, success_path, cancel_path, reference, email }
                         →  { ok: true, url }        send the browser there
                         →  503 unconfigured         payments are not switched on
```

`sku` is `membership:` plus the slugified tier name — `membership:creator`.
The browser is trusted with the sku and nothing else: the amount comes from
`worker/src/prices.js`, which is generated from `_data/`, so a page claiming a
different price gets the real one and a page inventing a sku gets a 400.

A success page at **`/thanks/`** is needed too — it is the default
`success_path` and does not exist yet.

## 5. Flip the switch

Last, and only once 1 and 2 are done:

```yaml
# _data/payments.yml
stripe:
  live: true
```

Every buy button checks it, so the whole thing turns off again in one line
without unpicking any pages.

## What is already true and needs nothing

Worth stating, because it is most of the work and it is easy to look at the
list above and conclude nothing has been done.

- **The broker is written and tested.** 119 tests, passing, covering routing,
  CORS, statuses, signature checking and the refusals.
- **Prices cannot drift.** They are edited in `_data/`, generated into
  `worker/src/prices.js`, and CI fails if the two disagree — so the page and
  the card cannot disagree about an amount.
- **The price history is the git history**, which is why prices are not kept
  in the Stripe dashboard where a change leaves no trace.
- **Repricing existing subscribers is written**
  (`script/reprice-subscriptions.py`), because Stripe pins a subscription to
  the amount it was created at and renews at that amount forever.
- **The nonprofit half-rate is designed and cannot be self-claimed** — staff
  verify an EIN and issue a promotion code; the browser is never trusted with
  the discount.
- **Equipment is deliberately not sold here.** Booqable has its own Stripe
  connection, and two systems charging for one booking is how somebody gets
  billed twice.

## Keeping this file honest

Strike an item when it ships rather than deleting it, the way
[`REVIEW-NOTES.md`](REVIEW-NOTES.md) does — what was blocking is worth
remembering. When everything here is struck, delete the file; a runbook for a
thing that is already running is a trap for the next reader.

Excluded from the Jekyll build in `_config.yml`, like every other internal
document here.
