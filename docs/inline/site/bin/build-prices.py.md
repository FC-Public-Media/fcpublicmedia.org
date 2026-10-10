# `site/bin/build-prices.py`

Moved out of the file. Unreviewed.

## 1

Above `import argparse`

WHY THIS EXISTS
---------------
There is exactly one rule that matters when a static site takes money: the
browser must never be able to name a price. A page that posts `amount: 4000`
to a checkout endpoint is a page that can post `amount: 1`, and no amount of
JavaScript on our side changes that, because the JavaScript is theirs.

So the browser sends a SKU — "membership:creator" — and the broker looks the
amount up in a table the browser cannot reach. This script builds that table.

WHERE THE PRICES LIVE, AND WHY IT IS HERE RATHER THAN IN STRIPE
---------------------------------------------------------------
Stripe can hold Price objects, and most integrations put them there. This one
does not, because of something Autumn said while scoping the work: if we sell
memberships as subscriptions, "we would have to be accountable to a flow where
we are announcing our price changes."

Prices in the Stripe dashboard have no such flow. Somebody with a login edits a
number and there is no review, no diff, and no announcement — the first anyone
hears of it is a card statement.

Prices in site/_data/membership.yml have all three for free. Changing one is a
commit: it shows up in a pull request as a red line and a green line, somebody
approves it, and `git log -p site/_data/membership.yml` is a complete price history
with dates and names attached. That is the accountability flow, and it already
exists.

Stripe still does the charging. It just does not hold the number — every
Checkout Session is created with an inline `price_data`, so there are no Price
objects to drift from this file.

THE GENERATED FILE IS COMMITTED
-------------------------------
worker/src/prices.js is checked in, because the worker bundles it at deploy
time and Cloudflare's build does not run Python. `--check` fails if it has
drifted from the YAML, which is what CI runs — the same shape as a lock file.

It is a JavaScript module rather than the JSON it obviously wants to be.
Importing JSON needs `with { type: 'json' }` under Node's ESM loader, which
bundlers accept and Node's test runner did not until recently; a module that
exports an object needs no attribute and behaves the same in both.

TODO IS NOT A PRICE
-------------------
Several figures in the data files are the string "TODO", waiting on the board.
Those are skipped rather than defaulted, and the site asks people to get in
touch instead of showing a buy button. A placeholder that becomes a real charge
is the one failure mode here that costs somebody actual money.

## 2

Above `SITE = pathlib.Path(__file__).resolve().parent.parent`

`site/bin/` is inside the Jekyll source, so a path here is relative to the
site rather than to the repository. SITE is the build root; REPO is the node.

## 3

Above `CENTS = 100`

Stripe works in the currency's smallest unit. Dollars never appear below this
line: money in floating point is a bug waiting for a price that ends in .99.

## 4

Above `if isinstance(value, bool) or not isinstance(value, (int, float)):`

Cents, or None if this is not a number somebody has decided yet.

Accepts int and float because YAML will hand back either depending on how
the figure was typed, and rejects everything else — "TODO", None, "$40",
an empty string. Rejecting is the whole job.

## 5

Above `if abs(value * CENTS - cents) > 0.001:`

round() on a float can only be trusted this far. Prices are dollars and
cents, so anything that does not land on a whole cent was not a price.

## 6

Above `"description": "One year from today. Renews on the day you joined, not in January.",`

What the buyer is agreeing to, shown on the Stripe page. The term
is the thing people were confused about, so it goes where they
are about to spend money rather than only on the page they came
from.

## 7

Above `"interval": "year",`

Both are offered for every tier: a single charge covering a year,
or the same amount on a yearly subscription. The buyer picks;
neither changes what is owed today.

## 8

Above `classes = load("classes.yml")`

Drop-in class attendance. Registration for a course is a different flow
with a roster behind it — this is the walk-in who turns up on the night.
