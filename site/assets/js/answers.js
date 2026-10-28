// Forms that send to the site-worker's tanks: <form data-tank="program" data-worker="…" data-email="…">.
// Field names are the tank's keys (site-worker src/tanks.js). A checkbox is `yes`, a list when it carries
// data-list, or its own value as text when it has one (value="Yes"); a radio group is the checked one's
// value; everything else is text. The `website` field is the robots' trap. A control outside
// the <form> joins it with form="<id>", as /join/'s terms box does.
// No worker, or a send that fails: the same answers as an email to a person. See docs/payments.md#requests.
//
// The words are the page's. A script only shows one of the form's [data-say="…"] messages, or one of
// the [data-receipt="…"] blocks after it, and fills in values: a[data-mailto] gets the email, and
// [data-reference] the reference. A form with data-checkout is /join/'s, and join.js sends it; one with
// data-sends has its own page script (book.js for /reserve/'s studio request).

function labelOf(form, input) {
  const label = input.closest('label') || form.querySelector(`label[for="${input.id}"]`);
  return (label ? label.textContent : input.name).replace(/\s+/g, ' ').trim();
}

export function read(form) {
  const answers = {};
  const lines = [];
  for (const input of form.elements) {
    if (!input.name || input.name === 'website' || input.type === 'submit' || input.type === 'button') continue;
    if (input.type === 'checkbox' || input.type === 'radio') {
      if (!input.checked) continue;
      if ('list' in input.dataset) {
        (answers[input.name] = answers[input.name] || []).push(input.value);
      } else if (input.type === 'radio' || input.hasAttribute('value')) {
        answers[input.name] = input.value;
      } else {
        answers[input.name] = true;
      }
      lines.push(`[x] ${labelOf(form, input)}`);
    } else if (input.value.trim()) {
      answers[input.name] = input.value.trim();
      lines.push(`${labelOf(form, input)}: ${input.value.trim()}`);
    }
  }
  const trap = form.elements.namedItem('website');
  return { answers, lines, trap: trap ? trap.value : '' };
}

export function emailLink(form, lines, reference) {
  const subject = `${form.dataset.subject || form.dataset.tank} (${reference.slice(0, 8)})`;
  const body = `${lines.join('\n')}\n\nReference: ${reference}`;
  return `mailto:${form.dataset.email}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
}

/** Show the form's message `key` (none for null), its email links pointing at `mailto`. */
export function say(form, key, mailto) {
  for (const message of form.querySelectorAll('[data-say]')) message.hidden = message.dataset.say !== key;
  if (mailto) form.querySelectorAll('[data-say] a[data-mailto]').forEach((a) => { a.href = mailto; });
}

/** Put the form away and show its receipt `key`. */
export function settle(form, key, reference) {
  const receipt = form.parentElement.querySelector(`[data-receipt="${key}"]`);
  if (reference) receipt.querySelectorAll('[data-reference]').forEach((code) => { code.textContent = reference.slice(0, 8); });
  form.hidden = true;
  receipt.hidden = false;
  receipt.focus();
}

/** POST JSON to the site-worker; the parsed answer, or a thrown reason. */
export async function post(form, path, body) {
  const response = await fetch(`${form.dataset.worker}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  const result = await response.json();
  if (!result.ok) throw new Error(result.detail || response.status);
  return result;
}

for (const form of document.querySelectorAll('form[data-tank]:not([data-checkout]):not([data-sends])')) {
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const { answers, lines, trap } = read(form);
    const reference = crypto.randomUUID();
    const mailto = emailLink(form, lines, reference);

    if (!form.dataset.worker) {
      say(form, 'unsent', mailto);
      return;
    }

    say(form, 'sending');
    try {
      await post(form, '/answers', {
        form: form.dataset.tank,
        answers: trap ? { ...answers, website: trap } : answers,
        reference,
      });
      settle(form, 'sent', reference);
    } catch {
      say(form, 'failed', mailto);
    }
  });
}
