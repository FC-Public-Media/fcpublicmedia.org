# `site/bin/test_reprice_subscriptions.py`

Moved out of the file. Unreviewed.

## 1

Above `import importlib.util`

Moving existing subscribers onto the current price.

Stripe is faked here, because the decisions worth testing are made before any
request goes out: which subscriptions need moving, which are already right,
and which cannot be placed at all. Those are the ones that would cost somebody
money if they were wrong, and none of them need a network.

The one thing a fake cannot check is whether Stripe accepts the parameters,
which is why `--apply` prints what it did and why the first live run should be
against a Stripe sandbox with a test clock rather than the real membership.

## 2

Above `move, steady, _ = reprice.plan([subscription("sub_1", "membership:creator", 7000)], ITEMS)`

Not merely a no-op worth having: updating a subscription that does
not need it resets the quantity and can generate an invoice, so
"change nothing" has to actually mean no request.

## 3

Above `move, _, _ = reprice.plan([subscription("sub_1", "membership:sponsor", 5000)], ITEMS)`

Not an upgrade path. If the board lowers a price, everybody gets it —
that is what having no grandfathered plans means in both directions,
and it is the direction people notice if you get it wrong.

## 4

Above `move, steady, unplaceable = reprice.plan([subscription("sub_1", None, 7000)], ITEMS)`

Predates the metadata, or was made by hand in the dashboard. Its
amount might match a tier exactly and still be a different thing, so
it goes in front of a person.

## 5

Above `_, _, unplaceable = reprice.plan([subscription("sub_1", "membership:legacy", 3000)], ITEMS)`

A retired tier. Repricing it to something is a decision about what
those members become, which is a board question and not a script's.

## 6

Above `move, _, _ = reprice.plan([subscription("sub_1", "membership:creator", 6000)], ITEMS)`

The assertion this file exists for. Proration would take money from
people between announcements — mid-term, for a change they were told
about but have not reached yet.

## 7

Above `move, _, _ = reprice.plan([subscription("sub_1", "membership:creator", 6000, "si_abc")], ITEMS)`

Stripe ADDS a price if you do not name the item to replace, leaving
the member subscribed to both and billed for both. The docs warn
about it twice, which is usually a sign people get it wrong.

## 8

Above `move, _, _ = reprice.plan([subscription("sub_1", "membership:creator", 6000)], ITEMS)`

Updating a subscription price silently resets quantity to 1. It is
already 1 for every membership, so this changes nothing today and
stops being free the day somebody sells a two-seat anything.

## 9

Above `prices = reprice.catalog()`

The file is JavaScript with a banner comment, so this is a small
piece of parsing that would fail silently if the generator's shape
changed. It reads what the broker actually charges from.

## 10

Above `pages = [`

The default page size is what a small organization never hits and
then hits once. Members 101 onwards staying on an old price, with a
report saying everything is fine, is the failure this prevents.
