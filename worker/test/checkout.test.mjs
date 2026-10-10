// see docs/inline/worker/test/checkout.test.mjs.md#1

import { strict as assert } from 'node:assert';
import { test } from 'node:test';

import { lookup, priceList, returnUrl, sessionParams } from '../src/checkout.js';
import { createBroker } from '../src/index.js';
import { memoryKV } from './helpers.mjs';

const ORIGIN = 'https://www.fcpublicmedia.org';

/** A Stripe that always agrees, and records what it was asked for. */
function fakeStripe({ status = 200, body } = {}) {
  const calls = [];
  const impl = async (url, options = {}) => {
    calls.push({
      url,
      authorization: options.headers?.Authorization,
      idempotency: options.headers?.['Idempotency-Key'],
      params: new URLSearchParams(options.body ? String(options.body) : ''),
    });
    return new Response(
      JSON.stringify(body ?? { id: 'cs_test_123', url: 'https://checkout.stripe.com/c/pay/cs_test_123' }),
      { status, headers: { 'Content-Type': 'application/json' } }
    );
  };
  impl.calls = calls;
  return impl;
}

function broker(fetchImpl, overrides = {}) {
  return createBroker(
    {
      RP_ID: 'fcpublicmedia.org',
      ORIGINS: ORIGIN,
      CHALLENGES: memoryKV(),
      STRIPE_KEY: 'rk_test_pretend',
      ...overrides,
    },
    { fetchImpl }
  );
}

const post = (body) =>
  new Request('https://broker.example/checkout', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Origin: ORIGIN },
    body: JSON.stringify(body),
  });

/* --------------------------------------------------- the price is not theirs */

test('the amount comes from our catalog, whatever the page claims', async () => {
  // THE test. Everything else in this file is a detail next to it.
  const stripe = fakeStripe();
  const response = await broker(stripe).fetch(
    post({ sku: 'membership:creator', amount: 1, unit_amount: 1, price: 1 })
  );

  assert.equal(response.status, 200);
  assert.equal(stripe.calls[0].params.get('line_items[0][price_data][unit_amount]'), '7000');
});

test('nothing can be bought that is not on the list', async () => {
  const stripe = fakeStripe();
  const response = await broker(stripe).fetch(post({ sku: 'membership:free-actually' }));

  assert.equal(response.status, 400);
  assert.equal(stripe.calls.length, 0, 'Stripe was called for an item we do not sell');
});

test('a price nobody has decided yet is not for sale', () => {
  // see docs/inline/worker/test/checkout.test.mjs.md#2
  assert.equal(lookup('class-dropin:public').ok, false);

  for (const item of priceList()) {
    assert.ok(Number.isInteger(item.amount), `${item.sku} has a non-integer amount`);
    assert.ok(item.amount > 0, `${item.sku} is free`);
  }
});

test('the catalog is in cents, and matches the tiers on the page', () => {
  // see docs/inline/worker/test/checkout.test.mjs.md#3
  const byName = Object.fromEntries(priceList().map((item) => [item.sku, item.amount]));
  assert.equal(byName['membership:sponsor'], 4000);
  assert.equal(byName['membership:student'], 6000);
  assert.equal(byName['membership:creator'], 7000);
  assert.equal(byName['membership:producer'], 14000);
});

/* ------------------------------------------------------- the nonprofit rate */

test('asking to be a nonprofit does not halve the price', async () => {
  // see docs/inline/worker/test/checkout.test.mjs.md#4
  const stripe = fakeStripe();
  await broker(stripe).fetch(
    post({ sku: 'membership:producer', nonprofit: true, rate: 0.5, discount: 0.9 })
  );

  assert.equal(stripe.calls[0].params.get('line_items[0][price_data][unit_amount]'), '14000');
});

test('a verified nonprofit can still redeem the code staff gave them', async () => {
  const stripe = fakeStripe();
  await broker(stripe).fetch(post({ sku: 'membership:producer' }));

  assert.equal(stripe.calls[0].params.get('allow_promotion_codes'), 'true');
});

/* ------------------------------------------------------------ one year, or every year */

test('a single payment covers the year and does not renew', async () => {
  const stripe = fakeStripe();
  await broker(stripe).fetch(post({ sku: 'membership:creator' }));

  const params = stripe.calls[0].params;
  assert.equal(params.get('mode'), 'payment');
  assert.equal(params.get('line_items[0][price_data][recurring][interval]'), null);
});

test('choosing to renew makes it a yearly subscription at the same amount', async () => {
  // see docs/inline/worker/test/checkout.test.mjs.md#5
  const stripe = fakeStripe();
  await broker(stripe).fetch(post({ sku: 'membership:creator', recurring: true }));

  const params = stripe.calls[0].params;
  assert.equal(params.get('mode'), 'subscription');
  assert.equal(params.get('line_items[0][price_data][recurring][interval]'), 'year');
  assert.equal(params.get('line_items[0][price_data][unit_amount]'), '7000');
  assert.equal(params.get('submit_type'), 'subscribe');
});

test('a subscription carries its tier, so it can be repriced later', async () => {
  // see docs/inline/worker/test/checkout.test.mjs.md#6
  const stripe = fakeStripe();
  await broker(stripe).fetch(post({ sku: 'membership:creator', recurring: true }));

  const params = stripe.calls[0].params;
  assert.equal(params.get('subscription_data[metadata][sku]'), 'membership:creator');
  assert.equal(params.get('subscription_data[metadata][priced]'), '7000');
});

test('a one-off payment does not pretend to be a subscription', async () => {
  // see docs/inline/worker/test/checkout.test.mjs.md#7
  const stripe = fakeStripe();
  await broker(stripe).fetch(post({ sku: 'membership:creator' }));

  assert.equal(stripe.calls[0].params.get('subscription_data[metadata][sku]'), null);
});

test('the term is stated where the money is, not only on the page they came from', async () => {
  const stripe = fakeStripe();
  await broker(stripe).fetch(post({ sku: 'membership:sponsor' }));

  const description = stripe.calls[0].params.get(
    'line_items[0][price_data][product_data][description]'
  );
  assert.match(description, /year from today/i);
  assert.match(description, /not in January/i);
});

/* ------------------------------------------------------- where you come back to */

test('the page cannot choose whose site you land on afterwards', () => {
  const origins = [ORIGIN];

  assert.equal(returnUrl(origins, '/thanks/', '/x/'), `${ORIGIN}/thanks/`);
  // An absolute URL, a protocol-relative one, and a bare word all fall back.
  assert.equal(returnUrl(origins, 'https://evil.example/', '/x/'), `${ORIGIN}/x/`);
  assert.equal(returnUrl(origins, '//evil.example', '/x/'), `${ORIGIN}/x/`);
  assert.equal(returnUrl(origins, 'thanks', '/x/'), `${ORIGIN}/x/`);
  assert.equal(returnUrl(origins, null, '/x/'), `${ORIGIN}/x/`);
});

test('the redirect Stripe is given is on our own origin', async () => {
  const stripe = fakeStripe();
  await broker(stripe).fetch(
    post({ sku: 'membership:sponsor', success_path: 'https://evil.example/collect' })
  );

  const success = stripe.calls[0].params.get('success_url');
  assert.ok(success.startsWith(`${ORIGIN}/`), `success_url escaped to ${success}`);
});

/* ------------------------------------------------------------------ the key */

test('the restricted key is sent to Stripe and never comes back out', async () => {
  const stripe = fakeStripe();
  const response = await broker(stripe).fetch(post({ sku: 'membership:sponsor' }));

  assert.equal(stripe.calls[0].authorization, 'Bearer rk_test_pretend');
  assert.ok(!(await response.text()).includes('rk_test_pretend'), 'the key was echoed to the page');
});

test('the key is read from the variable it actually lives in', async () => {
  // see docs/inline/worker/test/checkout.test.mjs.md#8
  const stripe = fakeStripe();
  const service = createBroker(
    {
      RP_ID: 'fcpublicmedia.org',
      ORIGINS: ORIGIN,
      CHALLENGES: memoryKV(),
      PUBLIC_STRIPE_API_KEY: 'rk_test_named_badly',
    },
    { fetchImpl: stripe }
  );

  const response = await service.fetch(post({ sku: 'membership:sponsor' }));

  assert.equal(response.status, 200);
  assert.equal(stripe.calls[0].authorization, 'Bearer rk_test_named_badly');
});

test('the obvious name still works, and the real one wins', async () => {
  const stripe = fakeStripe();
  const service = createBroker(
    {
      RP_ID: 'fcpublicmedia.org',
      ORIGINS: ORIGIN,
      CHALLENGES: memoryKV(),
      PUBLIC_STRIPE_API_KEY: 'rk_test_from_github',
      STRIPE_KEY: 'rk_test_set_by_hand',
    },
    { fetchImpl: stripe }
  );

  await service.fetch(post({ sku: 'membership:sponsor' }));

  // see docs/inline/worker/test/checkout.test.mjs.md#9
  assert.equal(stripe.calls[0].authorization, 'Bearer rk_test_from_github');
});

test('with no key configured, it says so instead of half-working', async () => {
  const stripe = fakeStripe();
  const response = await broker(stripe, { STRIPE_KEY: '' }).fetch(post({ sku: 'membership:sponsor' }));

  assert.equal(response.status, 503);
  assert.equal((await response.json()).reason, 'unconfigured');
  assert.equal(stripe.calls.length, 0);
});

test('payments being unconfigured does not take the passkey endpoints down', async () => {
  // see docs/inline/worker/test/checkout.test.mjs.md#10
  const service = broker(fakeStripe(), { STRIPE_KEY: '' });
  const response = await service.fetch(
    new Request('https://broker.example/challenge', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Origin: ORIGIN },
      body: JSON.stringify({ action: 'verify', repo: 'fcpublicmedia/janes-show' }),
    })
  );

  assert.equal(response.status, 200);
});

/* -------------------------------------------------------- when Stripe is unhappy */

test('a refusal from Stripe is not dressed up as a checkout page', async () => {
  const stripe = fakeStripe({ status: 400, body: { error: { message: 'No such coupon: rk_leak' } } });
  const response = await broker(stripe).fetch(post({ sku: 'membership:sponsor' }));

  assert.equal(response.status, 502);
  const payload = await response.json();
  assert.equal(payload.ok, false);
  // see docs/inline/worker/test/checkout.test.mjs.md#11
  assert.ok(!JSON.stringify(payload).includes('rk_leak'));
});

test('a 200 with no checkout URL in it is still a failure', async () => {
  const stripe = fakeStripe({ body: { id: 'cs_test_123', object: 'checkout.session' } });
  const response = await broker(stripe).fetch(post({ sku: 'membership:sponsor' }));

  assert.equal(response.status, 502);
});

test('a repeated tap is not a second charge', async () => {
  // see docs/inline/worker/test/checkout.test.mjs.md#12
  const stripe = fakeStripe();
  const service = broker(stripe);
  await service.fetch(post({ sku: 'membership:sponsor' }));
  await service.fetch(post({ sku: 'membership:sponsor' }));

  assert.ok(stripe.calls[0].idempotency, 'no idempotency key was sent');
  assert.notEqual(stripe.calls[0].idempotency, stripe.calls[1].idempotency);
});

/* ------------------------------------------------------------- housekeeping */

test('what we already know is carried through for reconciliation', async () => {
  const stripe = fakeStripe();
  await broker(stripe).fetch(
    post({ sku: 'membership:student', reference: 'signup-2026-08-17', email: 'jane@example.com' })
  );

  const params = stripe.calls[0].params;
  assert.equal(params.get('client_reference_id'), 'signup-2026-08-17');
  assert.equal(params.get('metadata[sku]'), 'membership:student');
  assert.equal(params.get('customer_email'), 'jane@example.com');
});

test('an oversized reference is trimmed rather than rejected by Stripe', async () => {
  const stripe = fakeStripe();
  await broker(stripe).fetch(post({ sku: 'membership:sponsor', reference: 'x'.repeat(500) }));

  assert.equal(stripe.calls[0].params.get('client_reference_id').length, 200);
});

test('equipment is not for sale here', () => {
  // see docs/inline/worker/test/checkout.test.mjs.md#13
  for (const item of priceList()) {
    assert.notEqual(item.kind, 'equipment', `${item.sku} would double-charge against Booqable`);
  }
});

test('a request with no JSON in it is a 400, not a 500', async () => {
  const stripe = fakeStripe();
  const response = await broker(stripe).fetch(
    new Request('https://broker.example/checkout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Origin: ORIGIN },
      body: 'not json',
    })
  );

  assert.equal(response.status, 400);
});

test('the parameters are built the same way when called directly', () => {
  // see docs/inline/worker/test/checkout.test.mjs.md#14
  const params = sessionParams({
    item: { name: 'Thing', amount: 500, interval: 'year', description: 'A thing' },
    sku: 'test:thing',
    recurring: false,
    success: `${ORIGIN}/thanks/`,
    cancel: `${ORIGIN}/back/`,
  });

  assert.equal(params.get('mode'), 'payment');
  assert.equal(params.get('line_items[0][quantity]'), '1');
  assert.equal(params.get('line_items[0][price_data][currency]'), 'usd');
  assert.equal(params.get('line_items[0][price_data][unit_amount]'), '500');
});
