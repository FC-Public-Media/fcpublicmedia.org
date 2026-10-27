#!/usr/bin/env python3
"""Pull the membership tiers into site/_data/tiers.json, from Stripe or from what the site-worker charges.

    keys run stripe-sync -- python3 site/bin/sync-tiers.py
    python3 site/bin/sync-tiers.py --file prices.json     # a saved /v1/prices response
    python3 site/bin/sync-tiers.py --catalog ../site-worker/src/prices.js

`--catalog` reads the site-worker's own price list, which /checkout charges from, until Stripe holds the
prices; each `membership:` item that renews yearly is a tier, its name without " membership".

A tier is an active, yearly, recurring Price whose lookup key is `membership:<slug>`, on an active
Product; the Product's name is the tier's name. Everything else in the account is ignored. Nothing
is written when no tier is found, so a wrong key or an empty account never blanks /join/.
See docs/payments.md#tiers.
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.stripe.com/v1"
OUT = os.path.join(os.path.dirname(__file__), "..", "_data", "tiers.json")
PREFIX = "membership:"


def fetch(key):
    """Every active recurring price, its product expanded, across pages."""
    prices, after = [], None
    while True:
        query = [("active", "true"), ("type", "recurring"), ("limit", "100"),
                 ("expand[]", "data.product")]
        if after:
            query.append(("starting_after", after))
        request = urllib.request.Request(
            f"{API}/prices?{urllib.parse.urlencode(query)}",
            headers={"Authorization": f"Bearer {key}"},
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                page = json.load(response)
        except urllib.error.HTTPError as error:
            raise SystemExit(f"Stripe answered {error.code}: {error.read().decode(errors='replace')}")
        prices.extend(page.get("data") or [])
        if not page.get("has_more") or not page.get("data"):
            return prices
        after = page["data"][-1]["id"]


def dollars(cents):
    """40 for 4000, 40.50 for 4050: how the page prints a price."""
    return str(cents // 100) if cents % 100 == 0 else f"{cents / 100:.2f}"


def tiers(prices):
    """The tiers, cheapest first, and why any membership-looking price was left out."""
    out, skipped = [], []
    for price in prices:
        sku = price.get("lookup_key") or ""
        if not sku.startswith(PREFIX):
            continue
        product = price.get("product")
        recurring = price.get("recurring") or {}
        if not isinstance(product, dict):
            skipped.append(f"{sku}: product not expanded")
        elif not product.get("active", True) or product.get("deleted"):
            skipped.append(f"{sku}: its product is archived")
        elif recurring.get("interval") != "year" or recurring.get("interval_count", 1) != 1:
            skipped.append(f"{sku}: not yearly")
        elif not isinstance(price.get("unit_amount"), int):
            skipped.append(f"{sku}: no fixed amount")
        else:
            out.append({
                "sku": sku,
                "name": product.get("name") or sku[len(PREFIX):].title(),
                "amount": price["unit_amount"],
                "currency": price.get("currency", "usd"),
                "price": dollars(price["unit_amount"]),
            })

    seen = {}
    for tier in out:
        if tier["sku"] in seen:
            skipped.append(f"{tier['sku']}: more than one active price; lookup keys should be unique")
        seen[tier["sku"]] = tier
    return sorted(seen.values(), key=lambda t: (t["amount"], t["name"])), skipped


def from_catalog(source):
    """Tiers from the site-worker's src/prices.js (`export default {...};`), cheapest first."""
    body = source[source.index("export default ") + len("export default "):].rstrip().rstrip(";")
    out = []
    for sku, item in json.loads(body).get("items", {}).items():
        if not sku.startswith(PREFIX) or item.get("interval") != "year" or not isinstance(item.get("amount"), int):
            continue
        name = item.get("name") or sku[len(PREFIX):].title()
        out.append({
            "sku": sku,
            "name": name[: -len(" membership")] if name.lower().endswith(" membership") else name,
            "amount": item["amount"],
            "currency": json.loads(body).get("currency", "usd"),
            "price": dollars(item["amount"]),
        })
    return sorted(out, key=lambda t: (t["amount"], t["name"])), []


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--file", help="Read a saved /v1/prices response instead of asking Stripe.")
    parser.add_argument("--catalog", help="Read the site-worker's src/prices.js instead of asking Stripe.")
    args = parser.parse_args(argv)

    if args.catalog:
        with open(args.catalog, encoding="utf-8") as handle:
            found, skipped = from_catalog(handle.read())
    elif args.file:
        with open(args.file, encoding="utf-8") as handle:
            prices = json.load(handle).get("data") or []
    else:
        key = os.environ.get("SYNC_STRIPE_API_KEY", "")
        if not key:
            raise SystemExit("No SYNC_STRIPE_API_KEY. Run under `keys run stripe-sync`; see docs/payments.md#keys.")
        # Read-only by construction: a restricted key, never the account's secret key.
        if not key.startswith("rk_"):
            raise SystemExit("SYNC_STRIPE_API_KEY must be a restricted key (rk_…) that can only read prices and products.")
        prices = fetch(key)
    if not args.catalog:
        found, skipped = tiers(prices)
    for reason in skipped:
        print(f"  skipped {reason}", file=sys.stderr)
    if not found:
        print(f"No tier found: no active yearly price has a `{PREFIX}…` lookup key. "
              f"{os.path.normpath(OUT)} left as it was.", file=sys.stderr)
        return 1

    with open(OUT, "w", encoding="utf-8") as handle:
        json.dump({"tiers": found}, handle, indent=1, sort_keys=True)
        handle.write("\n")
    print(f"Wrote {os.path.normpath(OUT)}: " + ", ".join(f"{t['name']} ${t['price']}" for t in found))
    return 0


if __name__ == "__main__":
    sys.exit(main())
