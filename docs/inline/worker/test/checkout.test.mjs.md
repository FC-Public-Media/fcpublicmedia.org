# `worker/test/checkout.test.mjs`

Moved out of the file. Unreviewed.

## 1

Above `import { strict as assert } from 'node:assert';`

Taking money.

The tests that matter here are the ones about what the browser is NOT
allowed to decide. A checkout endpoint is the one place on a static site
where believing the page costs real money, and every failure below was
reachable from the browser's console before the code stopped it.

Stripe is faked, and only Stripe. The catalog is the real generated
prices.json, the parameter building is the real code, and the routing goes
through the real worker — because a test that mocked the price lookup would
be asserting that our fake charges the right amount.

## 2

Above `assert.equal(lookup('class-dropin:public').ok, false);`

site/_data/classes.yml has "TODO" where the drop-in prices will go. The
generator skips those rather than defaulting them, so the failure is a
400 rather than a class that costs nothing. This is the assertion that
notices if somebody makes the generator "more forgiving".

## 3

Above `const byName = Object.fromEntries(priceList().map((item) => [item.sku, item.amount]));`

Guards the units. A price list that quietly became dollars would charge
everybody one hundredth of what it should, and every other test here
would still pass.

## 4

Above `const stripe = fakeStripe();`

The obvious implementation of "nonprofits pay half" is to accept a flag
and halve it, which hands a fifty percent discount to anybody who opens
the console. Verification happens before the money — staff check the EIN
against the IRS list and issue a promotion code — so the flag means
nothing here.

## 5

Above `const stripe = fakeStripe();`

The choice is the buyer's and changes nothing about what is owed today.
If the recurring option ever charged a different amount, offering it
alongside the one-off would be a way of talking somebody into the pricier
one without saying so.

## 6

Above `const stripe = fakeStripe();`

Stripe never asks us what a renewal costs — the subscription is pinned to
the amount it was created at and renews at that forever. Moving people
onto a new price is site/bin/reprice-subscriptions.py, and that script has
to know which tier a year-old subscription is for.

The session's own metadata does NOT survive onto the subscription, which
is why this is set separately. Without it the script would have to guess
the tier from the amount, which stops working the day two tiers cost the
same — and quietly, on somebody's card.

## 7

Above `const stripe = fakeStripe();`

subscription_data is rejected outright by Stripe in payment mode, so this
is not merely tidy — sending it would fail every single-payment checkout.

## 8

Above `const stripe = fakeStripe();`

PUBLIC_STRIPE_API_KEY, where "public" names who causes the key to be used
rather than whether it may be published. This endpoint authenticates
nobody, so a stranger makes this key act — and it is scoped to what a
stranger may cause. Without this test the mismatch would surface as
"payments are not switched on yet" long after somebody was sure they had
switched them on.

## 9

Above `assert.equal(stripe.calls[0].authorization, 'Bearer rk_test_from_github');`

Whichever the deploy pipeline sets is the one that gets rotated, so a
leftover hand-set secret must not quietly shadow it.

## 10

Above `const service = broker(fakeStripe(), { STRIPE_KEY: '' });`

These are unrelated systems sharing a worker. Before `stripe` was left out
of readConfig's `missing` list, adding the payment code would have made
every /challenge return 500 until somebody pasted a Stripe key in.

## 11

Above `assert.ok(!JSON.stringify(payload).includes('rk_leak'));`

Stripe's message is written for whoever wrote the integration and can name
parameters and ids. The visitor gets told it failed and that it was not
their fault; the detail goes to the log.

## 12

Above `const stripe = fakeStripe();`

Stripe replays the first response for a repeated Idempotency-Key, so the
key has to actually be sent — and has to differ between genuinely separate
purchases, which is why it is per request rather than derived from the SKU.

## 13

Above `for (const item of priceList()) {`

Booqable takes rental payments through its own Stripe connection. If this
worker also sold equipment, a booking could be paid for twice — once in
each system — and only one of them would know to release the item.

## 14

Above `const params = sessionParams({`

sessionParams is exported so the shape can be asserted without a fake
service in the way — and so a future caller (a class registration flow,
say) has one place to build a session rather than a second copy of this.
