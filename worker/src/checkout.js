// see docs/inline/worker/src/checkout.js.md#1

import catalog from './prices.js';

/** Everything that can be bought, for the page that has to draw the buttons. */
export function priceList() {
  return Object.entries(catalog.items).map(([sku, item]) => ({ sku, ...item }));
}

// see docs/inline/worker/src/checkout.js.md#2
export function lookup(sku) {
  if (typeof sku !== 'string' || !sku) return { ok: false, detail: 'No item was named.' };
  const item = catalog.items[sku];
  if (!item) return { ok: false, detail: `There is nothing for sale under "${sku}".` };
  return { ok: true, item, sku };
}

// see docs/inline/worker/src/checkout.js.md#3
export function returnUrl(origins, path, fallback) {
  const origin = origins[0];
  if (!origin) return null;
  const wanted = typeof path === 'string' && path.startsWith('/') ? path : fallback;
  // see docs/inline/worker/src/checkout.js.md#4
  if (wanted.startsWith('//')) return `${origin}${fallback}`;
  return `${origin}${wanted}`;
}

// see docs/inline/worker/src/checkout.js.md#5
export function sessionParams({ item, sku, recurring, success, cancel, reference, email }) {
  const params = new URLSearchParams();

  // see docs/inline/worker/src/checkout.js.md#6
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

    // see docs/inline/worker/src/checkout.js.md#7
    params.set('subscription_data[metadata][sku]', sku);
    params.set('subscription_data[metadata][priced]', String(item.amount));
  }

  params.set('success_url', success);
  params.set('cancel_url', cancel);

  // see docs/inline/worker/src/checkout.js.md#8
  params.set('allow_promotion_codes', 'true');

  // see docs/inline/worker/src/checkout.js.md#9
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
