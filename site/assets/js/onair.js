// "On now" and "up next" for the cable channel.
//
// Cablecast's API is public and sends Access-Control-Allow-Origin: *, so the
// browser can read the schedule directly. No backend, no key, no build step.
//
// This is progressive enhancement: the markup it fills already says something
// sensible, and if the request fails the block is removed rather than left
// showing a spinner forever.

const API = 'https://reflect-fcpublicmedia.cablecast.tv/cablecastapi/v1';
const CHANNEL = 1;

const box = document.querySelector('[data-onair]');

function day(offset) {
  const d = new Date();
  d.setDate(d.getDate() + offset);
  return d.toISOString().slice(0, 10);
}

function clock(iso) {
  return new Date(iso).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
}

async function load() {
  if (!box) return;

  const url = `${API}/scheduleitems?channel=${CHANNEL}&start=${day(0)}&end=${day(2)}&include=show&page_size=400`;
  const response = await fetch(url);
  if (!response.ok) throw new Error(`schedule request failed: ${response.status}`);

  const data = await response.json();
  const titles = new Map((data.shows || []).map((s) => [s.id, s.title]));

  const items = (data.scheduleItems || [])
    .map((i) => ({ at: new Date(i.runDateTime), title: titles.get(i.show) }))
    .filter((i) => i.title && !isNaN(i.at))
    .sort((a, b) => a.at - b.at);

  const now = new Date();
  let current = null;
  let next = null;
  for (const item of items) {
    if (item.at <= now) current = item;
    else { next = item; break; }
  }

  if (!current && !next) throw new Error('no schedule returned');

  const parts = [];
  if (current) {
    parts.push(`<span class="onair-label">On now</span> <b>${escape(current.title)}</b>`);
  }
  if (next) {
    parts.push(`<span class="onair-next">Next at ${clock(next.at)} &middot; ${escape(next.title)}</span>`);
  }
  box.innerHTML = parts.join('');
  box.hidden = false;
}

function escape(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// A failure here should leave no trace. The page is fine without it.
load().catch((error) => {
  console.warn('on-air schedule unavailable:', error.message);
  if (box) box.remove();
});
