// /join/: the membership tank's answers, then Stripe's payment page for the tier picked. The answers are
// never in the way of paying: kept or not, the payment page opens. Without a worker, it all becomes an
// email. Sends `reference` to both, so a payment and its answers match. See docs/payments.md#requests.
// Every word shown is in join.md; this only picks which (answers.js, say and settle).

import { read, emailLink, say, settle, post } from './answers.js';

const form = document.querySelector('form[data-checkout]');
const tier = () => document.querySelector('.tiers input[name="tier"]:checked');
const reference = crypto.randomUUID();

// Back from Stripe.
if (new URLSearchParams(location.search).has('joined')) settle(form, 'joined');

function described(lines, chosen) {
  return chosen ? [`Tier: ${chosen.dataset.name}, $${chosen.dataset.price} a year`, ...lines] : lines;
}

async function keep(answers, trap, sku) {
  try {
    await post(form, '/answers', {
      form: 'membership', answers: trap ? { ...answers, website: trap } : answers, sku, reference,
    });
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
    say(form, 'unsent', mailto);
    return;
  }

  say(form, 'opening');
  const kept = await keep(answers, trap, chosen.value);
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
    say(form, 'unsent', mailto);
    return;
  }
  say(form, 'sending');
  if (await keep(answers, trap, chosen ? chosen.value : null)) {
    settle(form, 'sent', reference);
  } else {
    say(form, 'failed', mailto);
  }
});
