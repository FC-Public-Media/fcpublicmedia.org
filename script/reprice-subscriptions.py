#!/usr/bin/env python3
"""Move existing subscribers onto the current price.

WHY THIS HAS TO EXIST
---------------------
Stripe does not know this repository exists.

That is the whole thing in one line, and it surprised us, so it is worth
writing down properly. When somebody subscribes, the broker creates the
Checkout Session with an inline `price_data`. Stripe turns that into a Price
object, pins the subscription to it, and renews against that pinned Price for
as long as the subscription lives. It never calls back. It never re-reads
_data/membership.yml. There is no webhook where we get asked "what does this
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
    1. Somebody edits a price in _data/membership.yml.
    2. Pull request, review, merge. That is the price history, with a date and
       a name on it.
    3. New members pay the new price from the moment it deploys.
    4. The membership is emailed — Constant Contact — with at least the notice
       period in _data/payments.yml (30 days as it stands).
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

USAGE
-----
    export STRIPE_KEY=rk_live_...          # restricted; see README
    python3 script/reprice-subscriptions.py            # report only
    python3 script/reprice-subscriptions.py --apply    # actually move them
"""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.stripe.com/v1"
PRICES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "worker", "src", "prices.js")


def catalog():
    """The current price list, read from the file the broker charges from.

    Parsed out of the generated module rather than regenerated from the YAML,
    on purpose: this has to reason about what is actually deployed. If the
    generated file has drifted from _data/ then CI is already failing, and
    fixing that is a separate job from repricing anybody.
    """
    with open(PRICES, encoding="utf-8") as handle:
        source = handle.read()
    body = source[source.index("export default ") + len("export default ") :].rstrip().rstrip(";")
    return json.loads(body)


def call(path, params=None, method="GET", key=None):
    url = f"{API}{path}"
    data = None
    if params is not None:
        encoded = urllib.parse.urlencode(params, doseq=True)
        if method == "GET":
            url = f"{url}?{encoded}"
        else:
            data = encoded.encode()

    request = urllib.request.Request(url, data=data, method=method)
    request.add_header("Authorization", f"Bearer {key}")
    if data:
        request.add_header("Content-Type", "application/x-www-form-urlencoded")

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", "replace")
        raise SystemExit(f"Stripe said {error.code} to {method} {path}:\n{detail}") from error


def active_subscriptions(key, fetch=call):
    """Every live subscription, following pagination to the end.

    Cancelled ones are excluded by asking for status=active: repricing a
    subscription somebody already ended would be both pointless and, if it
    somehow revived it, alarming.
    """
    out = []
    starting_after = None
    while True:
        params = {"status": "active", "limit": 100, "expand[]": "data.items.data.price"}
        if starting_after:
            params["starting_after"] = starting_after
        page = fetch("/subscriptions", params, key=key)
        out.extend(page.get("data") or [])
        if not page.get("has_more"):
            return out
        starting_after = out[-1]["id"]


def plan(subscriptions, items):
    """Who needs moving, who does not, and who we cannot place.

    The third group is the one worth having a name for. A subscription with no
    `sku` in its metadata predates that metadata being set, or was created by
    hand in the dashboard. Guessing its tier from the amount works right up
    until two tiers cost the same, so it is reported for a person to look at
    rather than repriced on a hunch.
    """
    move, steady, unplaceable = [], [], []

    for subscription in subscriptions:
        entries = (subscription.get("items") or {}).get("data") or []
        sku = (subscription.get("metadata") or {}).get("sku")
        item = entries[0] if entries else None

        if not item or not sku or sku not in items:
            unplaceable.append(
                {
                    "id": subscription["id"],
                    "sku": sku,
                    "why": "no sku in metadata" if not sku else f"sku {sku!r} is not for sale",
                }
            )
            continue

        current = (item.get("price") or {}).get("unit_amount")
        wanted = items[sku]["amount"]
        record = {
            "id": subscription["id"],
            "item": item["id"],
            "sku": sku,
            "from": current,
            "to": wanted,
        }
        (steady if current == wanted else move).append(record)

    return move, steady, unplaceable


def price_for(sku, item, currency, key, fetch=call):
    """A Stripe Price for this amount, made once and reused after that.

    `lookup_key` carries the SKU and the amount, so a second run of the same
    price change finds the Price it made the first time instead of leaving a
    trail of identical objects behind it. `transfer_lookup_key` moves the key
    off an older Price rather than failing on the collision.
    """
    key_name = f"{sku}-{item['amount']}".replace(":", "-")
    existing = fetch("/prices", {"lookup_keys[]": key_name, "limit": 1}, key=key)
    found = existing.get("data") or []
    if found:
        return found[0]["id"]

    created = fetch(
        "/prices",
        {
            "currency": currency,
            "unit_amount": item["amount"],
            "recurring[interval]": item["interval"],
            "product_data[name]": item["name"],
            "lookup_key": key_name,
            "transfer_lookup_key": "true",
        },
        method="POST",
        key=key,
    )
    return created["id"]


def apply(move, items, currency, key, fetch=call):
    """Move each subscription, one at a time, reporting as it goes.

    Not batched, and not stopped by one failure: a card that has expired since
    somebody subscribed makes their update fail, and that is not a reason for
    the other two hundred to stay on last year's price.
    """
    done, failed = [], []
    for record in move:
        try:
            price = price_for(record["sku"], items[record["sku"]], currency, key, fetch=fetch)
            fetch(
                f"/subscriptions/{record['id']}",
                {
                    "items[0][id]": record["item"],
                    "items[0][price]": price,
                    "items[0][quantity]": 1,
                    # The renewal date does not move and nobody is billed
                    # today. See the note at the top of this file.
                    "proration_behavior": "none",
                    "metadata[priced]": str(record["to"]),
                },
                method="POST",
                key=key,
            )
            done.append(record)
        except SystemExit as error:
            failed.append({**record, "error": str(error)})
    return done, failed


def money(cents):
    return f"${cents / 100:,.2f}" if isinstance(cents, int) else "?"


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument(
        "--apply",
        action="store_true",
        help="actually move subscriptions. Without this, nothing is changed.",
    )
    args = parser.parse_args()

    key = os.environ.get("STRIPE_KEY", "").strip()
    if not key:
        print("STRIPE_KEY is not set. See the README section on keys.", file=sys.stderr)
        return 2
    if key.startswith("pk_"):
        print(
            "That is the publishable key. It cannot read subscriptions — use "
            "the restricted key (rk_).",
            file=sys.stderr,
        )
        return 2

    prices = catalog()
    items = prices["items"]

    subscriptions = active_subscriptions(key)
    move, steady, unplaceable = plan(subscriptions, items)

    print(f"{len(subscriptions)} active subscriptions.")
    print(f"  {len(steady)} already on the current price.")
    print(f"  {len(move)} to move.")
    if unplaceable:
        print(f"  {len(unplaceable)} could not be placed:")
        for record in unplaceable:
            print(f"    {record['id']} — {record['why']}")

    for record in move:
        direction = "up" if record["to"] > record["from"] else "down"
        print(
            f"    {record['id']}  {record['sku']}  "
            f"{money(record['from'])} -> {money(record['to'])} ({direction})"
        )

    if not move:
        print("\nNothing to do.")
        return 0

    if not args.apply:
        print(
            "\nNothing was changed. Before running with --apply, check that the "
            "announcement has actually gone out and that the notice period in "
            "_data/payments.yml has elapsed — the whole reason this is a "
            "separate step is so a merge cannot move anybody's payment."
        )
        return 0

    done, failed = apply(move, items, prices["currency"], key)
    print(f"\nMoved {len(done)}.")
    for record in failed:
        print(f"  FAILED {record['id']} ({record['sku']}): {record['error']}", file=sys.stderr)

    # A partial run is not a success. Exiting non-zero means a scheduled
    # invocation shows up as failed rather than as a green tick over a job
    # that left half the membership on last year's price.
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
