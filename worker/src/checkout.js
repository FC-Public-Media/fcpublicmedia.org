// Checkout Session parameters. The browser chooses a SKU and recurring, never an amount, a discount
// or a return origin. See docs/payments.md.

import catalog from './prices.js';

/** Everything that can be bought, for the page that has to draw the buttons. */
export function priceList() {
  return Object.entries(catalog.items).map(([sku, item]) => ({ sku, ...item }));
}

/** The item, or a reason there isn't one ("TODO" prices are absent from the catalog). */
export function lookup(sku) {
  if (typeof sku !== 'string' || !sku) return { ok: false, detail: 'No item was named.' };
  const item = catalog.items[sku];
  if (!item) return { ok: false, detail: `There is nothing for sale under "${sku}".` };
  return { ok: true, item, sku };
}

/** A return URL: the path from the request, the origin always ours (no open redirect). */
export function returnUrl(origins, path, fallback) {
  const origin = origins[0];
  if (!origin) return null;
  const wanted = typeof path === 'string' && path.startsWith('/') ? path : fallback;
  // "//evil.example" starts with '/' but is protocol-relative.
  if (wanted.startsWith('//')) return `${origin}${fallback}`;
  return `${origin}${wanted}`;
}

/** The form-encoded body for POST /v1/checkout/sessions, with inline price_data. */
export function sessionParams({ item, sku, recurring, success, cancel, reference, email }) {
  const params = new URLSearchParams();

  // Same amount either way: one payment for the year, or a yearly subscription.
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

    // reprice-subscriptions.py reads these; the session's own metadata does not reach the subscription.
    params.set('subscription_data[metadata][sku]', sku);
    params.set('subscription_data[metadata][priced]', String(item.amount));
  }

  params.set('success_url', success);
  params.set('cancel_url', cancel);

  // The nonprofit rate arrives as a staff-issued promotion code. See docs/payments.md#nonprofit-rate.
  params.set('allow_promotion_codes', 'true');

  // For reconciliation only: it is whatever the browser said.
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
