// /reserve/'s studio request: a space, who you are, a day and a start time (always two hours), and a
// host. The week is drawn from site/_data/hosts.yml as it is: a day in `days` with hours is a column,
// in the file's order, and a person's key for that day is their hours there. Hours are cut into
// two-hour slots with an hour between them, so 11–4 is 11–1 and 2–4.
//
// Picking a host when no time is picked by hand picks their slot; picking a slot when no host is
// picked by hand picks its host. Once both are picked by hand they no longer follow each other, and
// the day's own host keeps a yellow mark behind their card.
//
// Sent to the site-worker's `book` tank (answers.js). The name and email are check-in's profile on
// this phone (checkin.js), read to fill the form and written back when it is sent. Each request is
// kept on this phone too, as the person's receipt; nothing here shows anyone else's.

import { emailLink, say, settle, post } from './answers.js';

const PROFILE_KEY = 'fcpm.profile';
const MINE_KEY = 'fcpm.bookings';
const SLOT = 120;
const BREAK = 60;
const SNAP = 15;
const WEEKDAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

const form = document.getElementById('book');
const planner = form.querySelector('[data-planner]');
const grid = form.querySelector('[data-planner-grid]');
const hosts = JSON.parse(document.getElementById('hosts').textContent);
const words = Object.fromEntries(
  [...planner.querySelector('template[data-words]').content.querySelectorAll('[data-word]')]
    .map((span) => [span.dataset.word, span.textContent]),
);
const field = (name) => form.elements.namedItem(name);

/* ---------------------------------------------------------------- storage */

// Private browsing makes localStorage throw.
function readStore(key, fallback) {
  try {
    const raw = window.localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch (error) {
    return fallback;
  }
}

function writeStore(key, value) {
  try {
    window.localStorage.setItem(key, JSON.stringify(value));
  } catch (error) {
    /* kept for this page only */
  }
}

/* ------------------------------------------------------------------ time */

const minutes = (hhmm) => {
  const [h, m] = String(hhmm).split(':').map(Number);
  return h * 60 + (m || 0);
};
const hhmm = (mins) => `${String(Math.floor(mins / 60)).padStart(2, '0')}:${String(mins % 60).padStart(2, '0')}`;
// The site's way of writing an hour: 11, 2:30.
const clock = (mins) => {
  const h = Math.floor(mins / 60) % 12 || 12;
  return mins % 60 ? `${h}:${String(mins % 60).padStart(2, '0')}` : String(h);
};
const spoken = (mins) => `${clock(mins)} ${Math.floor(mins / 60) % 24 < 12 ? 'am' : 'pm'}`;

const iso = (date) => `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
const fromIso = (text) => {
  const [y, m, d] = text.split('-').map(Number);
  return new Date(y, m - 1, d);
};
const addDays = (date, n) => new Date(date.getFullYear(), date.getMonth(), date.getDate() + n);

const now = new Date();
const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
const nowMinutes = now.getHours() * 60 + now.getMinutes();
// Weeks run Sunday to Saturday, so on a Friday "this week" still has its Saturday.
const sunday = addDays(today, -today.getDay());
const weekPicks = [...form.querySelectorAll('[data-week]')];
const WEEKS = weekPicks.length;

/* ------------------------------------------------------------------ hosts */

// The days with hours, in the file's order: Tuesday to Saturday today.
const days = Object.entries(hosts.days || {})
  .filter(([, hours]) => Array.isArray(hours))
  .map(([code]) => ({ code, label: hosts.labels[code] || code, weekday: WEEKDAYS.indexOf(hosts.labels[code]) }))
  .filter((day) => day.weekday >= 0);

const people = hosts.people || [];
const supports = (person) => (person.supports || []).map((id) => (hosts.activities || {})[id] || id);

function slotsOf(person, code) {
  const hours = person[code];
  if (!Array.isArray(hours)) return [];
  const [from, to] = hours.map(minutes);
  const starts = [];
  for (let at = from; at + SLOT <= to; at += SLOT + BREAK) starts.push(at);
  return starts.length ? starts : [from];
}

const hostsOf = (code) => people.filter((person) => Array.isArray(person[code]));

// The shown span of the day: the earliest slot to the end of the latest, and a quarter hour either side.
const everySlot = days.flatMap((day) => people.flatMap((person) => slotsOf(person, day.code)));
const top = (everySlot.length ? Math.min(...everySlot) : 11 * 60) - SNAP;
const bottom = (everySlot.length ? Math.max(...everySlot) + SLOT : 17 * 60) + SNAP;
const span = bottom - top;
// What the bumpers ask for, until the start box is changed: before the day, and after it.
const EARLIER = Math.min(9 * 60, Math.floor((top - 60) / 60) * 60);
const LATER = Math.ceil((bottom + SNAP) / 30) * 30;

/* ------------------------------------------------------------------ state */

const state = {
  week: 0,
  // Picked by hand, so the other no longer follows it.
  hostByHand: false,
  timeByHand: false,
};

const dateOf = (week, day) => addDays(sunday, week * 7 + day.weekday);
const isPast = (date, mins) => date < today || (+date === +today && mins < nowMinutes);

function picked() {
  const date = field('date').value;
  const start = field('start').value;
  return date && start ? { date: fromIso(date), start: minutes(start) } : null;
}

function weekOf(date) {
  const week = Math.floor((date - sunday) / (7 * 86400000));
  return week >= 0 && week < WEEKS ? week : null;
}

function dayAt(date) {
  return days.find((day) => day.weekday === date.getDay()) || null;
}

// The host whose slot starts at this time on this date, if any.
function hostAt(date, start) {
  const day = dayAt(date);
  if (!day) return null;
  return hostsOf(day.code).find((person) => slotsOf(person, day.code).includes(start)) || null;
}

function setTime(date, start, byHand) {
  field('date').value = iso(date);
  field('start').value = hhmm(start);
  state.timeByHand = byHand;
  if (!state.hostByHand) {
    const host = hostAt(date, start);
    field('host').value = host ? host.name : '';
  }
  draw();
}

function setHost(name, day) {
  field('host').value = name;
  state.hostByHand = Boolean(name);
  const person = people.find((p) => p.name === name);
  if (person && !state.timeByHand) {
    // Their next slot in the week shown: on the day whose card was picked, or any of theirs.
    const choices = (day ? [day] : days).flatMap((d) => slotsOf(person, d.code)
      .map((start) => ({ date: dateOf(state.week, d), start })));
    const next = choices.find((choice) => !isPast(choice.date, choice.start));
    if (next) {
      field('date').value = iso(next.date);
      field('start').value = hhmm(next.start);
    }
  }
  draw();
}

/* ------------------------------------------------------------------ draw */

const el = (tag, className, text) => {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text != null) node.textContent = text;
  return node;
};

const place = (node, column, row) => {
  node.style.gridColumn = String(column);
  node.style.gridRow = String(row);
  return node;
};

const at = (mins) => `${((mins - top) / span) * 100}%`;

// The card sits in a seat, so the suggestion's mark can be behind the card even while it tilts.
function hostCard(person, day) {
  const seat = el('div', 'planner-seat');
  const card = el('button', 'planner-host');
  seat.append(card);
  card.type = 'button';
  card.dataset.host = person.name;
  if (person.photo) {
    const img = el('img');
    img.src = person.photo;
    img.alt = '';
    card.append(img);
  }
  card.append(el('span', null, person.name));
  card.addEventListener('click', () => setHost(field('host').value === person.name ? '' : person.name, day));
  return seat;
}

function draw() {
  grid.textContent = '';
  // Inline rather than var() in repeat(): old Safari (the podcast door's iPad) drops those.
  grid.style.gridTemplateColumns = `2rem repeat(${days.length}, minmax(5.25rem, 1fr))`;
  grid.style.gridTemplateRows = `auto auto ${(span / 60) * 3}rem auto`;

  const choice = picked();
  const chosenHost = field('host').value;
  const shownChoice = choice && weekOf(choice.date) === state.week ? choice : null;

  // The gutter: an hour mark wherever an hour falls inside the day shown.
  const gutter = place(el('div', 'planner-hours'), 1, 3);
  for (let hour = Math.ceil(top / 60) * 60; hour < bottom; hour += 60) {
    const mark = el('span', null, clock(hour));
    mark.style.top = at(hour);
    gutter.append(mark);
  }
  grid.append(gutter);

  days.forEach((day, index) => {
    const column = index + 2;
    const date = dateOf(state.week, day);
    const past = date < today;
    const here = shownChoice && +shownChoice.date === +date;

    const head = place(el('div', 'planner-head'), column, 1);
    const title = el('p', 'planner-date');
    title.append(el('b', null, day.label.slice(0, 3)), ` ${date.getDate()}`);
    head.append(title);
    for (const person of hostsOf(day.code)) {
      const seat = hostCard(person, day);
      const card = seat.firstChild;
      card.classList.toggle('is-picked', person.name === chosenHost);
      card.setAttribute('aria-pressed', String(person.name === chosenHost));
      seat.classList.toggle('is-suggested', Boolean(here));
      head.append(seat);
    }

    const earlier = place(el('button', 'planner-bumper', words.earlier), column, 2);
    const track = place(el('div', 'planner-track'), column, 3);
    const later = place(el('button', 'planner-bumper', words.later), column, 4);
    for (const node of [head, earlier, track, later]) node.classList.toggle('is-past', past);
    grid.append(head, earlier, track, later);

    for (const [bumper, mins] of [[earlier, EARLIER], [later, LATER]]) {
      bumper.type = 'button';
      bumper.disabled = isPast(date, mins);
      bumper.addEventListener('click', () => {
        setTime(date, mins, true);
        field('start').focus();
      });
    }

    for (let hour = Math.ceil(top / 60) * 60; hour < bottom; hour += 60) {
      const line = el('span', 'planner-line');
      line.style.top = at(hour);
      track.append(line);
    }

    // A time in the open part of the day, to the quarter hour.
    track.addEventListener('click', (event) => {
      if (event.target !== track) return;
      const box = track.getBoundingClientRect();
      const mins = Math.round((top + ((event.clientY - box.top) / box.height) * span) / SNAP) * SNAP;
      const start = Math.min(Math.max(mins, top), bottom - SNAP);
      if (!isPast(date, start)) setTime(date, start, true);
    });

    for (const person of hostsOf(day.code)) {
      for (const start of slotsOf(person, day.code)) {
        const slot = el('button', 'planner-slot');
        slot.type = 'button';
        slot.style.top = at(start);
        slot.style.height = at(top + Math.min(SLOT, bottom - start));
        slot.disabled = isPast(date, start);
        slot.classList.toggle('is-picked', Boolean(here && shownChoice.start === start));
        slot.append(el('b', null, `${clock(start)}–${clock(start + SLOT)}`), el('span', null, person.name));
        const can = supports(person);
        if (can.length) slot.append(el('small', null, can.join(' · ')));
        slot.addEventListener('click', () => setTime(date, start, true));
        track.append(slot);
      }
    }

    // Their own pick, wherever it falls: on the day, or on a bumper with its time.
    if (here) {
      const { start } = shownChoice;
      const label = `${words.you} ${clock(start)}–${clock(start + SLOT)}`;
      if (start < top) {
        earlier.textContent = label;
        earlier.classList.add('is-picked');
      } else if (start >= bottom) {
        later.textContent = label;
        later.classList.add('is-picked');
      } else if (!hostAt(date, start)) {
        const mine = el('div', 'planner-you', label);
        mine.style.top = at(start);
        mine.style.height = at(top + Math.min(SLOT, bottom - start));
        track.append(mine);
      }
    }
  });

  for (const pick of weekPicks) pick.setAttribute('aria-pressed', String(Number(pick.dataset.week) === state.week));
}

/* ------------------------------------------------------------------ the form */

function showSpace() {
  const space = field('space').value;
  for (const part of form.querySelectorAll('[data-space]')) part.hidden = part.dataset.space !== space;
}

function when(choice, host) {
  const date = choice.date.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' });
  return `${date}, ${spoken(choice.start)} to ${spoken(choice.start + SLOT)}${host ? `, with ${host}` : ''}`;
}

function drawMine() {
  const mine = readStore(MINE_KEY, []).filter((entry) => entry.date >= iso(today));
  const list = document.querySelector('[data-mine-list]');
  list.textContent = '';
  for (const entry of mine) {
    const row = el('li');
    row.append(el('b', null, entry.space), el('span', null, entry.when), el('code', null, entry.reference.slice(0, 8)));
    list.append(row);
  }
  document.querySelector('[data-mine]').hidden = !mine.length;
}

function remember(answers, entry) {
  const profile = readStore(PROFILE_KEY, { name: '', reason: '', note: '', email: '' });
  writeStore(PROFILE_KEY, {
    ...profile,
    name: field('name').value.trim() || profile.name,
    email: (answers.email || profile.email || '').toLowerCase(),
  });
  if (entry) writeStore(MINE_KEY, [entry, ...readStore(MINE_KEY, [])].slice(0, 20));
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const choice = picked();
  if (!choice) {
    say(form, 'pick-time');
    planner.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    return;
  }

  // The tank's fields: the one name box is split at its first space.
  const name = field('name').value.trim();
  const [first, ...rest] = name.split(/\s+/);
  const answers = {};
  if (first) answers.first_name = first;
  if (rest.length) answers.last_name = rest.join(' ');
  if (field('email').value.trim()) answers.email = field('email').value.trim();
  answers.space = field('space').value;
  answers.when = when(choice, field('host').value);
  if (field('notes').value.trim()) answers.notes = field('notes').value.trim();

  const lines = [`Space: ${answers.space}`, `When: ${answers.when}`];
  if (name) lines.push(`Name: ${name}`);
  if (answers.email) lines.push(`Email: ${answers.email}`);
  if (answers.notes) lines.push(`Notes: ${answers.notes}`);

  const reference = crypto.randomUUID();
  const mailto = emailLink(form, lines, reference);
  remember(answers, null);
  if (!form.dataset.worker) {
    say(form, 'unsent', mailto);
    return;
  }

  say(form, 'sending');
  try {
    const trap = field('website').value;
    await post(form, '/answers', { form: 'book', answers: trap ? { ...answers, website: trap } : answers, reference });
  } catch {
    say(form, 'failed', mailto);
    return;
  }
  remember(answers, { reference, space: answers.space, when: answers.when, date: iso(choice.date), sent: new Date().toISOString() });
  settle(form, 'sent', reference);
  drawMine();
});

document.querySelector('[data-again]').addEventListener('click', () => {
  field('date').value = '';
  field('start').value = '';
  field('host').value = '';
  state.hostByHand = false;
  state.timeByHand = false;
  say(form, null);
  draw();
  document.querySelector('[data-receipt="sent"]').hidden = true;
  form.hidden = false;
});

form.addEventListener('change', (event) => {
  const { name } = event.target;
  if (name === 'space') showSpace();
  if (name === 'host') setHost(field('host').value, null);
  if (name === 'date' || name === 'start') {
    const choice = picked();
    if (!choice) return;
    // The view goes to the week of a day typed in, when it is one of the weeks shown.
    const week = weekOf(choice.date);
    if (week != null) state.week = week;
    setTime(choice.date, choice.start, true);
  }
});

// Another week: the pick is no longer drawn, but stays in the form until something else is picked.
for (const pick of weekPicks) {
  pick.addEventListener('click', () => {
    state.week = Number(pick.dataset.week);
    draw();
  });
}

// The form, filled from check-in's profile on this phone.
const profile = readStore(PROFILE_KEY, {});
if (!field('name').value && profile.name) field('name').value = profile.name;
if (!field('email').value && profile.email) field('email').value = profile.email;

field('date').min = iso(today);
field('date').max = iso(addDays(sunday, WEEKS * 7 - 1));

// A form the browser kept from before: its own week, picked by hand.
const kept = picked();
if (kept) {
  state.week = weekOf(kept.date) ?? 0;
  state.timeByHand = true;
  state.hostByHand = Boolean(field('host').value);
}

showSpace();
draw();
drawMine();
planner.hidden = false;
form.querySelector('[data-weeks]').hidden = false;
