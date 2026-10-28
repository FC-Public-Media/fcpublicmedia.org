// "On now" for the cable channel, read in the browser from Cablecast's public API.
//
// Nothing here needs the player. The bar lives in the header on every page, so this keeps itself
// primed on its own: it asks again when the programme it is showing should have ended, rather than
// on a fixed interval, so a page left open all day makes a handful of requests instead of hundreds.
// See docs/site.md.

const API = 'https://reflect-fcpublicmedia.cablecast.tv/cablecastapi/v1';
const CHANNEL = 1;

// Every bar on the page: the header's, and the inline one on /watch/.
const boxes = document.querySelectorAll('[data-onair]');

// Never ask more often than this, however short the programme; never wait longer than this, so a
// schedule that changed under us is picked up anyway.
const MIN_WAIT = 30 * 1000;
const MAX_WAIT = 10 * 60 * 1000;
const RETRY = 2 * 60 * 1000;

let timer = null;

function day(offset) {
  const d = new Date();
  d.setDate(d.getDate() + offset);
  return d.toISOString().slice(0, 10);
}

function escape(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Fort Collins time, whatever the reader's clock says: "7:00 PM".
const clock = (date) =>
  date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', timeZone: 'America/Denver' });

// The slot it runs in, from its start to the next programme's: "7:00–8:30 PM", or "11:30 AM–1:00 PM"
// across noon. With nothing after it in the schedule, its start alone.
function slot(current, next) {
  const from = clock(current.at);
  if (!next) return from;
  const to = clock(next.at);
  const [fromTime, fromHalf] = from.split(' ');
  return fromHalf === to.split(' ')[1] ? `${fromTime}–${to}` : `${from}–${to}`;
}

// Two lines, as the wordmark beside it is: what is on, and when it runs.
function show(current, next) {
  for (const box of boxes) {
    box.innerHTML = `<span class="onair-label">${escape(current.title)}</span>` +
      `<span class="onair-slot">${escape(slot(current, next))}</span>`;
    box.hidden = false;
  }
}

// Hidden, not removed: the bar is part of the header now, and a later poll may well succeed.
function hide() {
  for (const box of boxes) {
    box.hidden = true;
    box.innerHTML = '';
  }
}

function sleep(ms) {
  clearTimeout(timer);
  timer = setTimeout(run, Math.min(Math.max(ms, MIN_WAIT), MAX_WAIT));
}

async function load() {
  const url = `${API}/scheduleitems?channel=${CHANNEL}&start=${day(0)}&end=${day(2)}&include=show&page_size=400`;
  const response = await fetch(url, { cache: 'no-store' });
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

  if (current) show(current, next);
  else hide();

  // Ask again when what we are showing should have given way to the next programme.
  return next ? next.at - now : MAX_WAIT;
}

async function run() {
  if (!boxes.length) return;

  // Nothing to keep fresh for a tab nobody is looking at; visibilitychange picks it back up.
  if (document.visibilityState === 'hidden') return;

  try {
    sleep(await load());
  } catch (error) {
    console.warn('on-air schedule unavailable:', error.message);
    hide();
    sleep(RETRY);
  }
}

document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'visible') run();
});

run();
