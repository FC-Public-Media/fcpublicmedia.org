// Starts one real Checkout Session through the site-worker's own /checkout, on this machine, with a
// test key, and prints the payment page's URL. Nothing deploys; Stripe's test mode charges nothing.
//
//   machines/digitization/keys run stripe-test -- node site-worker/try-checkout.mjs [SKU]
//
// Refuses a live key. Pay on the page with Stripe's test card 4242 4242 4242 4242. See docs/payments.md#keys.

import { readFileSync } from 'node:fs';
import { createBroker } from './src/index.js';

// The deployed Worker's own vars; wrangler.jsonc's comments are whole lines.
const jsonc = readFileSync(new URL('./wrangler.jsonc', import.meta.url), 'utf8');
const { vars } = JSON.parse(jsonc.split('\n').filter((line) => !/^\s*\/\//.test(line)).join('\n'));

const key = (process.env.PUBLIC_STRIPE_API_KEY || '').trim();
if (!key.startsWith('rk_test_') && !key.startsWith('sk_test_')) {
  console.error('try-checkout: needs a test key in PUBLIC_STRIPE_API_KEY (keys run stripe-test -- ...)');
  process.exit(2);
}

const sku = process.argv[2] || 'membership:sponsor';
const origin = vars.ORIGINS.split(',')[0].trim();

// The KV namespace holds passkey challenges, which /checkout never touches.
const kv = new Map();
const broker = createBroker({
  ...vars,
  CHALLENGES: {
    async get(k) { return kv.get(k) ?? null; },
    async put(k, v) { kv.set(k, v); },
    async delete(k) { kv.delete(k); },
  },
  PUBLIC_STRIPE_API_KEY: key,
});

const response = await broker.fetch(new Request('https://broker.local/checkout', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json', Origin: origin },
  body: JSON.stringify({ sku, reference: 'try-checkout' }),
}));
const answer = await response.json();

if (!answer.ok) {
  console.error(`try-checkout: ${response.status} ${answer.reason || ''} ${answer.detail || ''}`.trim());
  process.exit(1);
}
console.log(`${sku}: ${answer.id}`);
console.log(answer.url);
