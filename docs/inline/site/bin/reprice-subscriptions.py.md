# `site/bin/reprice-subscriptions.py`

Moved out of the file. Unreviewed.

## 1

Above `import argparse`

WHY THIS HAS TO EXIST
---------------------
Stripe does not know this repository exists.

That is the whole thing in one line, and it surprised us, so it is worth
writing down properly. When somebody subscribes, the broker creates the
Checkout Session with an inline `price_data`. Stripe turns that into a Price
object, pins the subscription to it, and renews against that pinned Price for
as long as the subscription lives. It never calls back. It never re-reads
site/_data/membership.yml. There is no webhook where we get asked "what does this
cost now?" — the question is never put.

So editing a price in this repository changes what NEW members pay and nothing
else. Existing subscribers keep renewing at the amount they signed up at,
quietly, forever.

That is grandfathering, and it is a real product decision that some
organizations make deliberately. FCPM has never made it: there are no legacy
plans, everybody is on the current one, and that is the model the board
understands. Which means the grandfathering has to be undone on purpose, by
something, on a schedule — and this is that something.

WHERE IT SITS IN THE ANNOUNCEMENT FLOW
--------------------------------------
    1. Somebody edits a price in site/_data/membership.yml.
    2. Pull request, review, merge. That is the price history, with a date and
       a name on it.
    3. New members pay the new price from the moment it deploys.
    4. The membership is emailed — Constant Contact — with at least the notice
       period in site/_data/payments.yml (30 days as it stands).
    5. AFTER that notice has run, this script is applied. Existing
       subscriptions move to the new price.
    6. Everybody renews at the same price on their own anniversary.

Step 5 is deliberately not automatic. A price change that reaches people's
cards the moment a pull request merges is a price change nobody announced,
and "we told you thirty days ago" has to be true before the charge moves.
Running this is a person's decision, and dry-run is the default so that
reaching for it by accident shows you a report rather than billing anybody.

WHAT IT WILL NOT DO
-------------------
No proration. `proration_behavior=none` means nobody is charged or credited
mid-term for the difference: the year they already bought runs out at the
price they bought it at, and the new amount applies at their next renewal.
Anything else would take money from people between announcements, which is
exactly the surprise the notice period exists to prevent.

WHICH KEY THIS USES, AND WHY IT IS NOT THE OTHER ONE
----------------------------------------------------
Not PUBLIC_STRIPE_API_KEY. That name means "the public causes this key to be
used", so it is scoped to what a stranger is allowed to cause — writing a
Checkout Session. This script lists every subscription in the account and
changes what people are billed, which is nowhere near that.

So it reads STAFF_STRIPE_API_KEY: a second restricted key, scoped to reading
and writing subscriptions and prices, and never handed to anything a visitor
can reach. Two keys rather than one widened key. If the public key were given
enough permission to run this, then a flaw in a public endpoint would be worth
far more than a checkout page.

It also means this cannot be run by accident from a web request: the broker
does not have this credential and could not do this if it were asked to.

USAGE
-----
    export STAFF_STRIPE_API_KEY=rk_live_...   # restricted; see README
    python3 site/bin/reprice-subscriptions.py            # report only
    python3 site/bin/reprice-subscriptions.py --apply    # actually move them

## 2

Above `with open(PRICES, encoding="utf-8") as handle:`

The current price list, read from the file the broker charges from.

Parsed out of the generated module rather than regenerated from the YAML,
on purpose: this has to reason about what is actually deployed. If the
generated file has drifted from site/_data/ then CI is already failing, and
fixing that is a separate job from repricing anybody.

## 3

Above `out = []`

Every live subscription, following pagination to the end.

Cancelled ones are excluded by asking for status=active: repricing a
subscription somebody already ended would be both pointless and, if it
somehow revived it, alarming.

## 4

Above `move, steady, unplaceable = [], [], []`

Who needs moving, who does not, and who we cannot place.

The third group is the one worth having a name for. A subscription with no
`sku` in its metadata predates that metadata being set, or was created by
hand in the dashboard. Guessing its tier from the amount works right up
until two tiers cost the same, so it is reported for a person to look at
rather than repriced on a hunch.

## 5

Above `key_name = f"{sku}-{item['amount']}".replace(":", "-")`

A Stripe Price for this amount, made once and reused after that.

`lookup_key` carries the SKU and the amount, so a second run of the same
price change finds the Price it made the first time instead of leaving a
trail of identical objects behind it. `transfer_lookup_key` moves the key
off an older Price rather than failing on the collision.

## 6

Above `done, failed = [], []`

Move each subscription, one at a time, reporting as it goes.

Not batched, and not stopped by one failure: a card that has expired since
somebody subscribed makes their update fail, and that is not a reason for
the other two hundred to stay on last year's price.

## 7

Above `"proration_behavior": "none",`

The renewal date does not move and nobody is billed
today. See the note at the top of this file.

## 8

Above `print(`

Catching the shortcut before it is taken. If the same value is doing
both jobs, then either this cannot run or the public key has been
widened until a checkout endpoint can rewrite the membership's
billing — and the second is much likelier, because it is what makes
the error go away.

## 9

Above `return 1 if failed else 0`

A partial run is not a success. Exiting non-zero means a scheduled
invocation shows up as failed rather than as a green tick over a job
that left half the membership on last year's price.
