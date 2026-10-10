#!/usr/bin/env python3
"""Move existing subscribers onto the current price.

Run only after the notice period; no proration. See docs/payments.md#price-changes.

    export STAFF_STRIPE_API_KEY=rk_live_...   # restricted; see docs/payments.md#keys
    python3 site/bin/reprice-subscriptions.py            # report only
    python3 site/bin/reprice-subscriptions.py --apply    # actually move them
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
PRICES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "worker", "src", "prices.js")


def catalog():
    """The price list parsed from worker/src/prices.js, what is actually deployed."""
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
    """Every status=active subscription, following pagination to the end."""
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
    """(move, steady, unplaceable); no tier is ever guessed from an amount."""
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
    """A Stripe Price for this amount, found again by lookup_key "<sku>-<amount>" on later runs."""
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
    """Move each subscription in turn; one failure does not stop the rest."""
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
                    # Renewal date unchanged; nobody billed today.
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

    key = os.environ.get("STAFF_STRIPE_API_KEY", "").strip()
    if not key:
        print(
            "STAFF_STRIPE_API_KEY is not set.\n\n"
            "This is deliberately NOT the same key the site uses. That one is "
            "named PUBLIC_ because the public causes it to be used, so it is "
            "scoped to writing a Checkout Session and cannot read or change a "
            "subscription. See the README section on keys.",
            file=sys.stderr,
        )
        return 2
    if key.startswith("pk_"):
        print(
            "That is the publishable key. It cannot read subscriptions — use "
            "the restricted key (rk_).",
            file=sys.stderr,
        )
        return 2
    if os.environ.get("PUBLIC_STRIPE_API_KEY", "").strip() == key:
        # One value doing both jobs means the public key was widened.
        print(
            "This is the same value as PUBLIC_STRIPE_API_KEY.\n\n"
            "Those are meant to be two different keys with different "
            "permissions. If this one works, the public key has been given "
            "the power to rewrite subscriptions — which is the thing the "
            "naming exists to prevent. Mint a separate staff key.",
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
            "site/_data/payments.yml has elapsed — the whole reason this is a "
            "separate step is so a merge cannot move anybody's payment."
        )
        return 0

    done, failed = apply(move, items, prices["currency"], key)
    print(f"\nMoved {len(done)}.")
    for record in failed:
        print(f"  FAILED {record['id']} ({record['sku']}): {record['error']}", file=sys.stderr)

    # A partial run exits non-zero.
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
