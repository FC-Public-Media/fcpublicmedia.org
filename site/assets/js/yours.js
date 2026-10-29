// /you/: what this device keeps for its person. Every form's reply, kept before it was sent (keep.js),
// read back as a record rather than the form; each can be shown to our camera, sent again if it never
// went, emailed, or deleted. And the contact cards noticed in them, each removable. See docs/identity.md#yours.

import { getReplies, getCards, markSent, dropReply, dropCard } from './keep.js';
import { pour } from './bottle.js';

const el = (id) => document.getElementById(id);
const make = (tag, text) => {
  const node = document.createElement(tag);
  if (text != null) node.textContent = text;
  return node;
};

function formatWhen(iso) {
  return new Date(iso).toLocaleString([], {
    weekday: 'short', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit',
  });
}

const stateOf = (r) => (r.sent ? `sent ${formatWhen(r.sent.at)}` : 'kept, not sent');
const find = (reference) => getReplies().find((r) => r.reference === reference);

/* ------------------------------------------------------------------ list */

function renderList() {
  const replies = getReplies();
  const list = el('replies');
  list.innerHTML = '';
  el('replies-empty').hidden = replies.length > 0;
  for (const r of replies) {
    const item = make('li');
    const title = make('b');
    const link = make('a', r.title);
    link.href = `#reply-${r.reference}`;
    title.append(link);
    item.append(title, make('span', `${formatWhen(r.kept)} · ${stateOf(r)}`));
    list.append(item);
  }

  const cards = getCards();
  const box = el('cards');
  box.innerHTML = '';
  el('cards-empty').hidden = cards.length > 0;
  for (const c of cards) {
    const item = make('li');
    item.append(make('b', c.name || c.email || c.phone),
      make('span', [c.name ? c.email : '', c.phone].filter(Boolean).join(' · ')));
    const remove = make('button', 'Remove');
    remove.type = 'button';
    remove.className = 'btn';
    remove.addEventListener('click', () => { dropCard(c.id); renderList(); });
    item.append(remove);
    box.append(item);
  }
}

/* ----------------------------------------------------------------- reply */

function renderReply(r) {
  el('reply-title').textContent = r.title;
  el('reply-state').textContent = `Kept ${formatWhen(r.kept)} · ${stateOf(r)} · ${r.reference.slice(0, 8)}`;
  const lines = el('reply-lines');
  lines.innerHTML = '';
  for (const line of r.lines || []) {
    const item = make('li');
    const pair = /^([^:\n]{1,60}): ([\s\S]*)$/.exec(line);
    if (pair) item.append(make('b', pair[1]), make('span', pair[2]));
    else item.append(make('span', line));
    lines.append(item);
  }
  el('reply-show').href = `#show-${r.reference}`;
  el('reply-send').hidden = Boolean(r.sent || !r.post);
  el('reply-email').hidden = Boolean(r.sent || !r.mailto);
  if (r.mailto) el('reply-email').href = r.mailto;
  el('reply-said').textContent = '';
}

// Sent again exactly as it was first sent, with the same reference, so the tank knows it.
async function sendAgain() {
  const r = find(current);
  if (!r?.post) return;
  const said = el('reply-said');
  said.textContent = 'Sending…';
  try {
    const response = await fetch(r.post.url, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(r.post.body),
    });
    const result = await response.json();
    if (!result.ok) throw new Error(result.detail || response.status);
    markSent(r.reference, 'tank');
    renderReply(find(r.reference));
    said.textContent = 'Sent.';
  } catch (error) {
    said.textContent = `That didn't send (${error.message}). It's still kept here; try again, or show it at the studio.`;
  }
}

function deleteReply() {
  if (!window.confirm('Delete this from this phone? Anything already sent to us stays with us.')) return;
  dropReply(current);
  location.hash = '';
}

/* ------------------------------------------------------------------ show */

let pouring = null;
let pours = 0;          // a pour that finishes after its view was left stops itself

async function startShowing(r) {
  const mine = ++pours;
  el('show-what').textContent = `${r.title} · ${formatWhen(r.kept)}`;
  el('show-read').textContent = '';
  const poured = await pour(el('show-code'), r.reply);
  if (mine !== pours) { poured.stop(); return; }
  pouring = poured;
  el('show-read').textContent = poured.read;
  navigator.wakeLock?.request('screen').then((lock) => {
    if (pouring === poured) poured.lock = lock; else lock.release();
  }).catch(() => {});
}

function stopShowing() {
  pours += 1;
  if (!pouring) return;
  pouring.stop();
  pouring.lock?.release().catch(() => {});
  pouring = null;
}

/* ----------------------------------------------------------------- views */

let current = null;

function route() {
  const [, view, reference] = /^#(reply|show)-(.+)$/.exec(location.hash) || [];
  const r = reference ? find(reference) : null;
  const next = r ? view : 'list';
  current = r ? r.reference : null;
  for (const section of document.querySelectorAll('[data-view]')) section.hidden = section.dataset.view !== next;
  stopShowing();
  if (next === 'list') renderList();
  if (next === 'reply') renderReply(r);
  if (next === 'show') startShowing(r);
}

for (const back of document.querySelectorAll('[data-back]')) {
  back.addEventListener('click', (event) => {
    event.preventDefault();
    location.hash = back.closest('[data-view="show"]') && current ? `reply-${current}` : '';
  });
}
el('reply-send').addEventListener('click', sendAgain);
el('reply-drop').addEventListener('click', deleteReply);
window.addEventListener('hashchange', route);
route();
