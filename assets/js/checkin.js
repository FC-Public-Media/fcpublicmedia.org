// Check-in, recorded on the visitor's own device.
//
// There is no server. Everything here reads and writes storage on the phone in
// front of the person, and nothing leaves it.
//
// The shape of the thing:
//
//   1. Tap "Check in". The page asks for location once.
//   2. If you are at the studio, you are checked in.
//   3. If you are not, the check-in becomes *pending*: the page shows
//      directions, and finishes by itself when you arrive. Leave it open,
//      walk in, look down, it is done.
//
// Re-checks happen every few minutes and only while the tab is visible, so a
// page left open in a pocket costs nothing.
//
// The device identifier is a random UUID generated on first visit. It is not
// derived from anything about the device or the person, it is never sent
// anywhere, and "Forget this device" deletes it.

import { readConfig, pickSession, sessionKey, clockTime, watch } from './classes.js';

const DEVICE_KEY = 'fcpm.device';
const HISTORY_KEY = 'fcpm.checkins';
const PROFILE_KEY = 'fcpm.profile';
const PENDING_KEY = 'fcpm.pending';
const RSVP_KEY = 'fcpm.rsvp';

const config = JSON.parse(document.getElementById('checkin-config').textContent);
const classConfig = readConfig();

// The session currently in a window, or null. Re-read rather than cached, so
// a page left open through the start of a class behaves correctly.
let session = null;

let timer = null;

/* ---------------------------------------------------------------- storage */

// Private browsing makes localStorage throw rather than return null, so every
// access goes through these.
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
    return true;
  } catch (error) {
    return false;
  }
}

function dropStore(key) {
  try {
    window.localStorage.removeItem(key);
  } catch (error) {
    /* nothing stored, nothing to remove */
  }
}

function storageWorks() {
  try {
    const probe = '__fcpm_probe__';
    window.localStorage.setItem(probe, '1');
    window.localStorage.removeItem(probe);
    return true;
  } catch (error) {
    return false;
  }
}

// Ask the browser to exempt this origin from routine eviction. Chrome decides
// silently on engagement heuristics; Safari grants it largely when the site is
// a Home Screen web app, which is why the page says so rather than relying on
// this call alone.
async function requestPersistence() {
  if (!navigator.storage?.persist) return null;
  try {
    if (await navigator.storage.persisted()) return true;
    return await navigator.storage.persist();
  } catch (error) {
    return null;
  }
}

/* ----------------------------------------------------------------- device */

function randomId() {
  if (window.crypto?.randomUUID) return window.crypto.randomUUID();
  const bytes = new Uint8Array(16);
  window.crypto.getRandomValues(bytes);
  return Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join('');
}

function getDevice() {
  let device = readStore(DEVICE_KEY, null);
  if (!device?.id) {
    device = { id: randomId(), label: '', created: new Date().toISOString() };
    writeStore(DEVICE_KEY, device);
  }
  return device;
}

/* --------------------------------------------------------------- history */

const getHistory = () => readStore(HISTORY_KEY, []);
const getProfile = () => readStore(PROFILE_KEY, { name: '', reason: '', note: '' });
const getPending = () => readStore(PENDING_KEY, null);
const getRsvps = () => readStore(RSVP_KEY, []);

function saveHistory(entries) {
  return writeStore(HISTORY_KEY, entries.slice(0, config.historyLimit));
}

/* -------------------------------------------------------------- distance */

// Haversine. Good to a few metres at these distances, which is far better
// than a phone's own fix.
function metresBetween(lat1, lon1, lat2, lon2) {
  const R = 6371000;
  const toRad = (deg) => (deg * Math.PI) / 180;

  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2;

  return 2 * R * Math.asin(Math.sqrt(a));
}

function describeDistance(metres) {
  if (metres < 1000) return `${Math.round(metres / 10) * 10} m`;
  return `${(metres / 1000).toFixed(metres < 10000 ? 1 : 0)} km`;
}

/* -------------------------------------------------------------- location */

function locate({ fresh = false } = {}) {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error('This browser cannot report a location.'));
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => resolve(position),
      (error) => reject(error),
      {
        // Low accuracy on purpose: a coarse fix is plenty against a 200m
        // radius and costs far less battery than a GPS lock.
        enableHighAccuracy: false,
        timeout: 20000,
        // When someone taps "check again", they have almost certainly just
        // moved, so a cached fix is exactly the wrong answer — it would tell
        // a person standing in the doorway that they are still down the
        // street. Background polls reuse a recent fix instead, which is where
        // the battery saving actually comes from.
        maximumAge: fresh ? 0 : 120000,
      }
    );
  });
}

function evaluate(position) {
  const { latitude, longitude, accuracy } = position.coords;
  const venue = config.location;

  const distance = metresBetween(latitude, longitude, venue.latitude, venue.longitude);
  const slack = Math.min(accuracy || 0, venue.accuracySlack);

  return {
    distance,
    accuracy: accuracy || 0,
    here: distance - slack <= venue.radius,
  };
}

/* -------------------------------------------------------------- rendering */

const el = (id) => document.getElementById(id);

function show(state) {
  for (const panel of document.querySelectorAll('[data-state]')) {
    panel.hidden = panel.dataset.state !== state;
  }
}

function formatWhen(iso) {
  return new Date(iso).toLocaleString([], {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
}

function renderHistory() {
  const history = getHistory();
  const list = el('checkin-history');
  const count = el('checkin-count');

  list.innerHTML = '';
  el('checkin-empty').hidden = history.length > 0;
  count.textContent = history.length
    ? `${history.length} visit${history.length === 1 ? '' : 's'} on this device`
    : '';

  for (const entry of history) {
    const item = document.createElement('li');

    const when = document.createElement('b');
    when.textContent = formatWhen(entry.at);

    const detail = document.createElement('span');
    detail.textContent = [entry.reason, entry.email].filter(Boolean).join(' · ') || 'checked in';

    item.append(when, detail);
    list.append(item);
  }
}

function renderDevice() {
  const device = getDevice();
  el('device-label').value = device.label || '';
  // A fragment is enough to tell two devices apart. There is no reason to put
  // a full identifier on screen.
  el('device-id').textContent = device.id.slice(0, 8);
  el('device-since').textContent = new Date(device.created).toLocaleDateString();
}

function renderProfile() {
  const profile = getProfile();
  el('profile-name').value = profile.name || '';
  el('profile-note').value = profile.note || '';

  const reason = el('profile-reason');
  // A reason primed from the URL wins over the stored one, so a QR aimed at
  // /check-in/?reason=Class does what it looks like it does.
  const primed = new URLSearchParams(window.location.search).get('reason');
  reason.value = primed && [...reason.options].some((o) => o.value === primed)
    ? primed
    : profile.reason || '';
}

function saveProfile() {
  writeStore(PROFILE_KEY, {
    name: el('profile-name').value.trim(),
    reason: el('profile-reason').value,
    note: el('profile-note').value.trim(),
  });
}

/* --------------------------------------------------------------- identity */

// With identity.mode = "access", Cloudflare Access has already authenticated
// the visitor against whichever provider they chose. Nothing here holds a
// secret; if the route is not behind Access this 404s and the check-in is
// recorded anonymously.
async function getIdentity() {
  if (config.identityMode !== 'access') return null;
  try {
    const response = await fetch('/cdn-cgi/access/get-identity', {
      headers: { Accept: 'application/json' },
    });
    if (!response.ok) return null;
    return (await response.json()).email || null;
  } catch (error) {
    return null;
  }
}

/* ---------------------------------------------------------------- actions */

function complete(reading) {
  const profile = getProfile();
  const device = getDevice();

  return getIdentity().then((email) => {
    const entry = {
      at: new Date().toISOString(),
      device: device.id,
      email,
      name: profile.name || null,
      reason: profile.reason || null,
      note: profile.note || null,
      // Distance only — the coordinates themselves are not kept, even locally.
      // Knowing the check-in was verified is the useful part.
      verified: Boolean(reading),
      distance_m: reading ? Math.round(reading.distance) : null,
    };

    const stored = saveHistory([entry, ...getHistory()]);
    dropStore(PENDING_KEY);

    if (!stored) {
      el('done-detail').textContent =
        'Your browser would not let this page save anything, so nothing was recorded.';
      show('done');
      return;
    }

    el('done-detail').textContent = email
      ? `Checked in as ${email}.`
      : 'Checked in.';
    show('done');
    renderHistory();
    stopTimer();
  });
}

function goPending(reading) {
  writeStore(PENDING_KEY, {
    since: new Date().toISOString(),
    reason: getProfile().reason || null,
  });

  if (reading) {
    el('far-distance').textContent =
      `You are about ${describeDistance(reading.distance)} away.`;
  }
  show('far');
  startTimer();
}

async function attempt({ silent = false } = {}) {
  if (!config.location.required) {
    await complete(null);
    return;
  }

  if (!silent) show('locating');

  let position;
  try {
    // An explicit tap asks for a fresh fix; a background poll may reuse one.
    position = await locate({ fresh: !silent });
  } catch (error) {
    if (silent) return; // a failed background poll changes nothing on screen

    if (error.code === 1 /* PERMISSION_DENIED */) {
      show('denied');
    } else {
      el('error-detail').textContent =
        error.message || 'Your location could not be determined.';
      show('error');
    }
    return;
  }

  const reading = evaluate(position);
  if (reading.here) {
    await complete(reading);
  } else {
    goPending(reading);
  }
}

/* ------------------------------------------------------------------ timer */

// Only runs while a check-in is pending and the tab is visible.
function startTimer() {
  stopTimer();
  if (document.visibilityState !== 'visible') return;
  timer = window.setInterval(() => {
    if (getPending()) attempt({ silent: true });
    else stopTimer();
  }, config.location.recheckSeconds * 1000);
}

function stopTimer() {
  if (timer) window.clearInterval(timer);
  timer = null;
}

function onVisibilityChange() {
  if (document.visibilityState === 'visible' && getPending()) {
    // Coming back to the page is the strongest signal that something changed,
    // so check immediately as well as restarting the clock.
    attempt({ silent: true });
    startTimer();
  } else {
    stopTimer();
  }
}

/* ------------------------------------------------------------------ class */

// The same question the homepage asks, answered by the same function over the
// same data. Neither page can drift from the other, and the QR on the door
// stays a permanent link that carries no class information.
function renderClass() {
  const banner = el('class-banner-root');
  if (!banner || !classConfig) return;

  session = pickSession(classConfig);

  if (!session) {
    banner.hidden = true;
    return;
  }

  banner.hidden = false;

  const q = (sel) => banner.querySelector(sel);
  q('[data-class-title]').textContent = session.title;
  q('[data-class-room]').textContent = session.room || '';
  q('[data-class-eyebrow]').textContent = session.running ? 'Happening now' : 'Starting soon';
  q('[data-class-when]').textContent = session.running
    ? `On now until ${clockTime(session.ends)}`
    : `Starts at ${clockTime(session.starts)}`;
  q('[data-class-late]').hidden = session.phase !== 'late';

  // Before it starts, offer to note intent. Once it is running, the thing to
  // do is check in, so the offer goes away.
  const noted = getRsvps().includes(sessionKey(session));
  q('[data-rsvp-offer]').hidden = session.running || noted;
  q('[data-rsvp-noted]').hidden = !noted || session.running;

  // A class arrival is a check-in with the reason already known. Only fill it
  // in if the visitor has not chosen something else themselves.
  const reason = el('profile-reason');
  if (!reason.value) {
    reason.value = 'Class';
    saveProfile();
  }

  // The button says what it is for.
  for (const button of document.querySelectorAll('[data-state="idle"] [data-action="check-in"]')) {
    button.textContent = session.running ? "I'm here for the class" : 'Check in';
  }
}

function noteRsvp() {
  if (!session) return;
  const key = sessionKey(session);
  const rsvps = getRsvps();
  if (!rsvps.includes(key)) writeStore(RSVP_KEY, [...rsvps, key]);
  renderClass();
}

/* ---------------------------------------------------------------- exports */

function exportHistory() {
  const payload = {
    exported: new Date().toISOString(),
    device: getDevice(),
    profile: getProfile(),
    checkins: getHistory(),
  };

  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);

  const link = document.createElement('a');
  link.href = url;
  link.download = `fcpm-checkins-${new Date().toISOString().slice(0, 10)}.json`;
  link.click();

  URL.revokeObjectURL(url);
}

async function importHistory(file) {
  const status = el('storage-status');
  try {
    const payload = JSON.parse(await file.text());
    if (!Array.isArray(payload.checkins)) throw new Error('no check-ins in that file');

    // Merge rather than replace, so importing a backup onto a device used
    // since does not discard the newer visits.
    const seen = new Set(getHistory().map((entry) => entry.at));
    const merged = [...getHistory(), ...payload.checkins.filter((e) => !seen.has(e.at))]
      .sort((a, b) => new Date(b.at) - new Date(a.at));

    saveHistory(merged);
    renderHistory();
    status.textContent = `Restored ${payload.checkins.length} visits.`;
  } catch (error) {
    status.textContent = `That file could not be read: ${error.message}`;
  }
}

function forgetDevice() {
  if (!window.confirm('Delete this device identifier and every visit recorded on it? This cannot be undone.')) {
    return;
  }
  [DEVICE_KEY, HISTORY_KEY, PROFILE_KEY, PENDING_KEY].forEach(dropStore);
  stopTimer();
  renderDevice();
  renderProfile();
  renderHistory();
  show('idle');
  el('storage-status').textContent = 'Deleted. A new device identifier has been generated.';
}

/* -------------------------------------------------------------------- init */

async function init() {
  if (!storageWorks()) {
    show('blocked');
    return;
  }

  renderDevice();
  renderProfile();
  renderHistory();

  el('venue-directions').href =
    `https://www.google.com/maps/dir/?api=1&destination=${config.location.latitude},${config.location.longitude}`;

  // Form state is written on every change, so closing the page mid-answer and
  // coming back later loses nothing.
  for (const id of ['profile-name', 'profile-reason', 'profile-note']) {
    el(id).addEventListener('input', saveProfile);
    el(id).addEventListener('change', saveProfile);
  }

  el('device-label').addEventListener('change', () => {
    writeStore(DEVICE_KEY, { ...getDevice(), label: el('device-label').value.trim() });
  });

  document.querySelectorAll('[data-action="check-in"]').forEach((button) => {
    button.addEventListener('click', () => attempt());
  });
  el('cancel-pending').addEventListener('click', () => {
    dropStore(PENDING_KEY);
    stopTimer();
    show('idle');
  });
  el('again-button').addEventListener('click', () => show('idle'));

  el('export-button').addEventListener('click', exportHistory);
  el('forget-button').addEventListener('click', forgetDevice);
  el('import-input').addEventListener('change', (event) => {
    const [file] = event.target.files;
    if (file) importHistory(file);
    event.target.value = '';
  });

  document.addEventListener('visibilitychange', onVisibilityChange);

  const rsvp = el('rsvp-button');
  if (rsvp) rsvp.addEventListener('click', noteRsvp);

  // Re-evaluated on a timer while visible, so a page open through the start of
  // a class updates itself the same way the homepage does.
  if (classConfig) watch(renderClass);

  const persisted = await requestPersistence();
  el('persist-state').textContent =
    persisted === true
      ? 'This browser has agreed to keep your history until you delete it.'
      : 'This browser has not promised to keep your history. Saving a copy, or adding this page to your Home Screen, makes it stick.';

  // A pending check-in survives a reload — pick it back up rather than making
  // someone start again.
  if (getPending()) {
    show('far');
    startTimer();
    attempt({ silent: true });
  } else {
    show('idle');
  }
}

init();
