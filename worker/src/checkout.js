// Taking money.
//
// WHAT THE BROWSER IS TRUSTED WITH
// --------------------------------
// A SKU, and whether to make it recurring. That is the entire list.
//
// It is not trusted with the amount. `catalog` below is bundled into the
// worker at deploy time from _data/, so a page asking for
// "membership:creator" gets 7000 cents whatever it claims to believe, and a
// page asking for "membership:free-actually" gets a 400. This is the only
// property in this file that really matters; everything else is manners.
//
// It is not trusted with the nonprofit rate either, which is the interesting
// case. Nonprofits pay half, and the obvious implementation — accept
// `nonprofit: true` and halve it — hands every visitor a fifty percent
// discount. What is done instead is in sessionParams, under the note about
// promotion codes.
//
// It is not trusted with where to go afterwards. A `success_url` taken at
// face value is an open redirect wearing our domain, and one attached to a
// payment page is a decent phishing primitive.
//
// WHY THERE IS NO EQUIPMENT SKU HERE
// ----------------------------------
// Equipment rental is Booqable's, and Booqable has its own Stripe connection.
// Two systems taking money for the same booking is how a double charge
// happens, so this one does not offer equipment at all. The site reads
// Booqable's catalog and hands the booking to Booqable.

import catalog from './prices.js';

/** Everything that can be bought, for the page that has to draw the buttons. */
export function priceList() {
  return Object.entries(catalog.items).map(([sku, item]) => ({ sku, ...item }));
}

/**
 * The item, or a reason there isn't one.
 *
 * "TODO" prices are absent from the catalog rather than present and zero, so
 * an unpriced thing fails here rather than quietly selling for nothing.
 */
export function lookup(sku) {
  if (typeof sku !== 'string' || !sku) return { ok: false, detail: 'No item was named.' };
  const item = catalog.items[sku];
  if (!item) return { ok: false, detail: `There is nothing for sale under "${sku}".` };
  return { ok: true, item, sku };
}

/**
 * Where Stripe may send somebody back to.
 *
 * Same list the CORS check uses. The path is taken from the request and the
 * origin never is — so a caller can choose which of our pages they land on and
 * cannot choose whose site it is.
 */
export function returnUrl(origins, path, fallback) {
  const origin = origins[0];
  if (!origin) return null;
  const wanted = typeof path === 'string' && path.startsWith('/') ? path : fallback;
  // A path, not a URL. "//evil.example" is a protocol-relative URL that passes
  // a naive startsWith('/') check and leaves the site entirely.
  if (wanted.startsWith('//')) return `${origin}${fallback}`;
  return `${origin}${wanted}`;
}

/**
 * The form body for POST /v1/checkout/sessions.
 *
 * Stripe takes form encoding with bracketed keys rather than JSON, so this
 * builds URLSearchParams directly. `price_data` is inline on purpose: there
 * are no Price objects in the Stripe dashboard to drift from _data/, and the
 * price history lives in git. See script/build-prices.py.
 */
export function sessionParams({ item, sku, recurring, success, cancel, reference, email }) {
  const params = new URLSearchParams();

  // `subscription` renews on the anniversary; `payment` is one charge covering
  // the year and then it lapses. Both are honest, so the buyer chooses — and
  // the amount today is identical either way, which is what makes offering the
  // choice safe rather than a way to be talked into the pricier one.
  const asSubscription = Boolean(recurring) && Boolean(item.interval);
  params.set('mode', asSubscription ? 'subscription' : 'payment');

  params.set('line_items[0][quantity]', '1');
  params.set('line_items[0][price_data][currency]', catalog.currency);
  params.set('line_items[0][price_data][unit_amount]', String(item.amount));
  params.set('line_items[0][price_data][product_data][name]', item.name);
  if (item.description) {
    params.set('line_items[0][price_data][product_data][description]', item.description);
  }
  if (asSubscription) {
    params.set('line_items[0][price_data][recurring][interval]', item.interval);

    // WHAT THIS METADATA IS FOR, AND WHY IT IS NOT OPTIONAL.
    //
    // Stripe never asks us what a subscription costs. `price_data` creates an
    // ad-hoc Price, the subscription is pinned to it, and it renews at that
    // amount forever — Stripe has no idea this repository exists and never
    // fetches anything back. Left alone, that grandfathers every subscriber,
    // which is the opposite of how FCPM has ever priced: there are no legacy
    // plans, everybody is on the current one.
    //
    // So a price change has to be PUSHED to existing subscriptions, and that
    // means being able to look at a subscription a year from now and say which
    // tier it is. The session's own metadata does not survive onto the
    // subscription — this does. Without it, script/reprice-subscriptions.py
    // would have to guess a tier from an amount, which stops working the first
    // time two tiers cost the same.
    params.set('subscription_data[metadata][sku]', sku);
    params.set('subscription_data[metadata][priced]', String(item.amount));
  }

  params.set('success_url', success);
  params.set('cancel_url', cancel);

  // HOW A NONPROFIT ACTUALLY PAYS HALF.
  //
  // Not by asking. The old sequence was: pick a tier, pay full price, staff
  // notice, somebody posts a cheque back — and organizations learned to buy
  // the wrong thing on purpose and wait for the refund. The fix was never a
  // stricter rule, it was checking earlier: script/sync-nonprofits.py puts the
  // IRS list on the site, an organization picks itself off it, and staff have
  // an EIN to verify before any money moves.
  //
  // This is the last link in that chain. Staff issue a promotion code once
  // they have verified the EIN, and the code halves the price at checkout.
  // Stripe holds the codes, which means an unverified visitor cannot mint one
  // and a verified one does not have to be trusted with an amount.
  params.set('allow_promotion_codes', 'true');

  // Ties the payment back to whatever we already know — which class, which
  // organization asked. Reconciliation, not authorization: it is whatever the
  // browser said, so nothing may be decided from it.
  if (reference) params.set('client_reference_id', String(reference).slice(0, 200));
  if (reference) params.set('metadata[reference]', String(reference).slice(0, 500));
  params.set('metadata[sku]', sku);

  if (email) params.set('customer_email', String(email).slice(0, 800));

  params.set('submit_type', asSubscription ? 'subscribe' : 'pay');

  return params;
}

/** Fails closed: an unreadable answer from Stripe is not a checkout page. */
export function readSession(payload) {
  if (!payload || typeof payload.url !== 'string' || !payload.url.startsWith('https://')) {
    return { ok: false, detail: 'Stripe did not return a checkout page.' };
  }
  return { ok: true, url: payload.url, id: payload.id };
}
