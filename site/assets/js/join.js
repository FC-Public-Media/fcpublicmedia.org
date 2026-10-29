// /join/: the membership tank's answers, then Stripe's payment page for the tier picked. The answers are
// never in the way of paying: kept or not, the payment page opens. Without a worker, it all becomes an
// email. Sends `reference` to both, so a payment and its answers match. See docs/payments.md#requests.
// Every word shown is in join.md; this only picks which (answers.js, say and settle).

import { read, emailLink, say, settle, post } from './answers.js';
import { keep as keepHere, markSent } from './keep.js';

const form = document.querySelector('form[data-checkout]');
const tier = () => document.querySelector('.tiers input[name="tier"]:checked');
const reference = crypto.randomUUID();

// Back from Stripe.
if (new URLSearchParams(location.search).has('joined')) settle(form, 'joined');

function described(lines, chosen) {
  return chosen ? [`Tier: ${chosen.dataset.name}, $${chosen.dataset.price} a year`, ...lines] : lines;
}

// Kept on the device first (keep.js), then sent to the tank.
async function keep(answers, trap, sku, lines, mailto) {
  const body = { form: 'membership', answers: trap ? { ...answers, website: trap } : answers, sku, reference };
  keepHere(form, { answers: sku ? { ...answers, sku } : answers, lines, reference, body, mailto });
  try {
    await post(form, '/answers', body);
    markSent(reference, 'tank');
    return true;
  } catch {
    return false;
  }
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const chosen = tier();
  if (!chosen) {
    say(form, 'pick-tier');
    document.querySelector('.tiers').scrollIntoView({ behavior: 'smooth' });
    return;
  }
  const { answers, lines, trap } = read(form);
  const mailto = emailLink(form, described(lines, chosen), reference);
  if (!form.dataset.worker) {
    keepHere(form, { answers: { ...answers, sku: chosen.value }, lines: described(lines, chosen), reference, mailto });
    say(form, 'unsent', mailto);
    return;
  }

  say(form, 'opening');
  const kept = await keep(answers, trap, chosen.value, described(lines, chosen), mailto);
  // Stripe refuses a malformed email, so only a plausible one is passed on.
  const email = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(answers.email || '') ? answers.email : undefined;
  try {
    const { url } = await post(form, '/checkout', {
      sku: chosen.value, reference, email, success_path: '/join/?joined', cancel_path: '/join/',
    });
    location.href = url;
  } catch {
    say(form, kept ? 'unpaid-kept' : 'unpaid', mailto);
  }
});

form.querySelector('[data-keep]').addEventListener('click', async () => {
  const chosen = tier();
  const { answers, lines, trap } = read(form);
  if (!Object.keys(answers).length) {
    say(form, 'empty');
    return;
  }
  const mailto = emailLink(form, described(lines, chosen), reference);
  if (!form.dataset.worker) {
    keepHere(form, { answers, lines: described(lines, chosen), reference, mailto });
    say(form, 'unsent', mailto);
    return;
  }
  say(form, 'sending');
  if (await keep(answers, trap, chosen ? chosen.value : null, described(lines, chosen), mailto)) {
    settle(form, 'sent', reference);
  } else {
    say(form, 'failed', mailto);
  }
});
