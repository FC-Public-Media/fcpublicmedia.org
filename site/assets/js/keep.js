// Lock it in: a form's reply is kept on this device before it goes anywhere. Sending it is a separate
// act, by any way out: the tank (the site-worker's POST), our camera (/you/'s Show it pours the same
// reply as a bottle), or the email link. A send that fails loses nothing; /you/ offers it again.
// The reply is `wizard:site+answers` (fcpm.reply/v0): the tank, the reference the tank and Stripe
// also get, the answers, and `at`, the commit the page was built from. Kept as text, so its bytes
// never change. Name, email and phone typed into any form are noticed as a contact card, a list
// that never blocks a save and never fills a form in. See docs/identity.md#yours.

import { localIso, nonce } from './bottle.js';

export const REPLIES_KEY = 'fcpm.replies';
export const CARDS_KEY = 'fcpm.cards';
const KEEP = 200;

// Private browsing makes localStorage throw, so every access goes through these.
export function readStore(key, fallback) {
  try {
    const raw = window.localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch (error) {
    return fallback;
  }
}

export function writeStore(key, value) {
  try {
    window.localStorage.setItem(key, JSON.stringify(value));
    return true;
  } catch (error) {
    return false;
  }
}

const revision = () => document.querySelector('meta[name="fcpm-revision"]')?.content || 'dev';

/* --------------------------------------------------------------- replies */

export const getReplies = () => readStore(REPLIES_KEY, []);

/**
 * Keep what `form` is about to send. `body` is the tank's POST body as it will go; `lines` the labelled
 * answers, so the reply reads back without its form. The same reference kept again (a form sent twice
 * from one page) replaces the one before. Returns the record, or null if nothing could be saved.
 */
export function keep(form, { answers, lines, reference, body, mailto }) {
  const tank = form.dataset.tank;
  const reply = JSON.stringify({
    schema: 'fcpm.reply/v0',
    wizard: 'wizard:site+answers',
    at: revision(),
    tank,
    reference,
    answers,
    issued: localIso(new Date()),
    nonce: nonce(),
    sig: null,
  });
  const record = {
    reference,
    tank,
    title: form.dataset.subject || tank,
    page: location.pathname,
    kept: new Date().toISOString(),
    reply,
    lines,
    post: form.dataset.worker && body ? { url: `${form.dataset.worker}/answers`, body } : null,
    mailto: mailto || null,
    sent: null,
  };
  noticeCard(cardFrom(form));
  const others = getReplies().filter((r) => r.reference !== reference);
  return writeStore(REPLIES_KEY, [record, ...others].slice(0, KEEP)) ? record : null;
}

/** It went: `via` is how (tank). */
export function markSent(reference, via) {
  const replies = getReplies();
  const record = replies.find((r) => r.reference === reference);
  if (!record) return;
  record.sent = { via, at: new Date().toISOString() };
  writeStore(REPLIES_KEY, replies);
}

export function dropReply(reference) {
  writeStore(REPLIES_KEY, getReplies().filter((r) => r.reference !== reference));
}

/* ------------------------------------------------------------ the card */

export const getCards = () => readStore(CARDS_KEY, []);

// The standard autocomplete tokens every form already carries; the last token is the field's kind.
export function cardFrom(form) {
  const parts = {};
  for (const input of form.querySelectorAll('input[autocomplete]')) {
    const kind = input.getAttribute('autocomplete').trim().split(/\s+/).pop();
    if (['name', 'given-name', 'family-name', 'email', 'tel'].includes(kind) && input.value.trim()) {
      parts[kind] = input.value.trim();
    }
  }
  return {
    name: parts.name || [parts['given-name'], parts['family-name']].filter(Boolean).join(' '),
    email: parts.email || '',
    phone: parts.tel || '',
  };
}

const digits = (s) => String(s || '').replace(/\D/g, '');

/**
 * Notice a card. The same email or phone is the same card, brought up to date; a name alone joins the
 * card of that name that has nothing to say against it; anything else is a new card. Never refuses.
 */
export function noticeCard({ name = '', email = '', phone = '' }) {
  name = name.trim();
  email = email.trim().toLowerCase();
  phone = phone.trim();
  if (!name && !email && !phone) return;
  const now = new Date().toISOString();
  const cards = getCards();
  let card = cards.find((c) => (email && c.email === email) || (digits(phone) && digits(c.phone) === digits(phone)));
  if (!card && name) {
    card = cards.find((c) => c.name.toLowerCase() === name.toLowerCase()
      && !(email && c.email) && !(phone && c.phone));
  }
  if (card) {
    if (name) card.name = name;
    if (email) card.email = email;
    if (phone) card.phone = phone;
    card.last = now;
  } else {
    const id = crypto.randomUUID ? crypto.randomUUID() : String(Date.now());
    cards.push({ id, name, email, phone, first: now, last: now });
  }
  cards.sort((a, b) => (a.last < b.last ? 1 : -1));
  writeStore(CARDS_KEY, cards);
}

export function dropCard(id) {
  writeStore(CARDS_KEY, getCards().filter((c) => c.id !== id));
}
