// /check-in/: visits recorded in this browser's storage, never sent. See docs/identity.md#check-in.

import { readConfig, pickSession, sessionKey, clockTime, watch } from './classes.js';
import { verifyClaim, claimFromLocation, clearClaimFromLocation } from './claims.js';

const DEVICE_KEY = 'fcpm.device';
const HISTORY_KEY = 'fcpm.checkins';
const PROFILE_KEY = 'fcpm.profile';
const PENDING_KEY = 'fcpm.pending';
const RSVP_KEY = 'fcpm.rsvp';
const CLAIM_KEY = 'fcpm.claim';

const config = JSON.parse(document.getElementById('checkin-config').textContent);
const classConfig = readConfig();

// The class session in its window now, or null; re-read so an open page sees a class start.
let session = null;

let timer = null;

/* ---------------------------------------------------------------- storage */

// Private browsing makes localStorage throw, so every access goes through these.
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

// Ask to be exempt from eviction; Safari mostly grants it only to Home Screen apps.
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
const getProfile = () => readStore(PROFILE_KEY, { name: '', reason: '', note: '', email: '' });
const getPending = () => readStore(PENDING_KEY, null);
const getRsvps = () => readStore(RSVP_KEY, []);
const getClaim = () => readStore(CLAIM_KEY, null);

function saveHistory(entries) {
  return writeStore(HISTORY_KEY, entries.slice(0, config.historyLimit));
}

/* -------------------------------------------------------------- distance */

// Haversine, far more precise than a phone's fix.
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
        // A coarse fix is plenty against a 200m radius and spares the battery.
        enableHighAccuracy: false,
        timeout: 20000,
        // A tap wants a fresh fix (they just moved); background polls reuse a recent one.
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
  // A number beside "Visits" on the pass, nothing when there are none.
  count.textContent = history.length ? String(history.length) : '';

  for (const entry of history) {
    const item = document.createElement('li');

    const when = document.createElement('b');
    when.textContent = formatWhen(entry.at);

    const detail = document.createElement('span');
    // Unconfirmed addresses are marked in the list.
    const who = entry.email
      ? entry.email_verified
        ? entry.email
        : `${entry.email} (unconfirmed)`
      : null;
    detail.textContent = [entry.reason, who].filter(Boolean).join(' · ') || 'checked in';

    item.append(when, detail);
    list.append(item);
  }
}

// A default name for this phone ("iPhone", "Windows PC"): its kind, never a fingerprint.
function deviceKind(ua = navigator.userAgent, model = '') {
  if (/iPhone/.test(ua)) return 'iPhone';
  if (/iPad/.test(ua) || (/Macintosh/.test(ua) && navigator.maxTouchPoints > 1)) return 'iPad';
  if (/Macintosh/.test(ua)) return 'Mac';
  if (/Android/.test(ua)) {
    if (/Pixel/i.test(model) || /Pixel/.test(ua)) return model && /Pixel/i.test(model) ? model : 'Pixel';
    if (/SamsungBrowser|SM-[A-Z]/.test(ua) || /^SM-/.test(model)) return 'Samsung';
    return 'Android phone';
  }
  if (/CrOS/.test(ua)) return 'Chromebook';
  if (/Windows/.test(ua)) return 'Windows PC';
  if (/Linux/.test(ua)) return 'Linux';
  return '';
}

async function guessDeviceLabel() {
  let model = '';
  try {
    if (navigator.userAgentData?.getHighEntropyValues) {
      ({ model = '' } = await navigator.userAgentData.getHighEntropyValues(['model']));
    }
  } catch (error) {
    model = '';
  }
  return deviceKind(navigator.userAgent, model);
}

function renderDevice() {
  const device = getDevice();
  el('device-label').value = device.label || '';
  // Named once, the first time, and kept: after that it is theirs to change.
  if (!device.label) {
    guessDeviceLabel().then((label) => {
      if (!label || getDevice().label) return;
      writeStore(DEVICE_KEY, { ...getDevice(), label });
      if (!el('device-label').value) el('device-label').value = label;
    });
  }
  // A fragment is enough to tell devices apart.
  el('device-id').textContent = device.id.slice(0, 8);
  el('device-since').textContent = new Date(device.created).toLocaleDateString();
}

function renderProfile() {
  const profile = getProfile();
  el('profile-name').value = profile.name || '';
  el('profile-email').value = profile.email || '';
}

function saveProfile() {
  writeStore(PROFILE_KEY, {
    ...getProfile(),
    name: el('profile-name').value.trim(),
    // A claim supersedes the typed address without overwriting it.
    email: el('profile-email').value.trim().toLowerCase(),
  });
}

/* ----------------------------------------------------------------- reason */

// The reason comes from ?reason= (only those in _data/checkin.yml) or a running class.
function visitReason() {
  const primed = new URLSearchParams(window.location.search).get('reason');
  if (primed && (config.reasons || []).includes(primed)) return primed;
  if (session) return 'Class';
  return null;
}

function renderReason() {
  const reason = visitReason();
  const label = el('visit-reason');
  label.textContent = reason || '';
  label.hidden = !reason;
}

/* --------------------------------------------------------------- identity */

// An address comes from, in order: a claim, Cloudflare Access, or typing (recorded unverified).

async function getAccessIdentity() {
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

async function getIdentity() {
  const claim = getClaim();
  if (claim?.email) return { email: claim.email, verified: true, via: 'claim' };

  const access = await getAccessIdentity();
  if (access) return { email: access, verified: true, via: 'access' };

  const typed = getProfile().email;
  if (typed) return { email: typed, verified: false, via: 'typed' };

  return { email: null, verified: false, via: null };
}

/** Take a claim from the URL, check it, and keep the whole token if it holds. */
async function redeemClaim(token) {
  const status = el('claim-status');
  const result = await verifyClaim(token, config.identity.keys);

  if (!result.ok) {
    const message = {
      expired: 'That link has expired. Ask us for a new one and it will work again.',
      signature: "That link didn't check out. It may have been altered in transit — ask us to send another.",
      malformed: 'That link looks incomplete. Email clients sometimes break long links across lines; try opening it from the original message.',
      unsupported: 'This browser cannot check the link. Your address can still be entered by hand below.',
      missing: '',
    }[result.reason] || 'That link could not be used.';

    if (status) {
      status.textContent = message;
      status.hidden = !message;
    }
    return false;
  }

  writeStore(CLAIM_KEY, {
    token,
    email: result.payload.email,
    issued: new Date(result.payload.iat * 1000).toISOString(),
    expires: new Date(result.payload.exp * 1000).toISOString(),
    verifiedAt: new Date().toISOString(),
  });

  if (status) {
    status.textContent = `${result.payload.email} is confirmed on this device.`;
    status.hidden = false;
  }
  return true;
}

function renderClaim() {
  const claim = getClaim();
  const verified = Boolean(claim?.email);

  for (const panel of document.querySelectorAll('[data-claim]')) {
    panel.hidden = (panel.dataset.claim === 'verified') !== verified;
  }

  if (verified) {
    el('claim-email').textContent = claim.email;
    el('claim-expires').textContent = new Date(claim.expires).toLocaleDateString();
  } else {
    el('profile-email').value = getProfile().email || '';
  }
}

function dropClaim() {
  if (!window.confirm('Remove the confirmed email address from this device?')) return;
  dropStore(CLAIM_KEY);
  renderClaim();
  renderHistory();
  el('claim-status').hidden = true;
}

/* ---------------------------------------------------------------- actions */

function complete(reading) {
  const profile = getProfile();
  const device = getDevice();

  return getIdentity().then((identity) => {
    const { email, verified } = identity;
    const entry = {
      at: new Date().toISOString(),
      device: device.id,
      email,
      // Recorded, not inferred.
      email_verified: Boolean(email) && verified,
      name: profile.name || null,
      // A held check-in keeps the reason it was started with.
      reason: getPending()?.reason || visitReason(),
      // Distance only; coordinates are never kept, even locally.
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

    // When, and whether the visit's address was checked.
    el('done-detail').textContent = [
      clockTime(Date.parse(entry.at)),
      email && !verified ? 'email unconfirmed' : null,
    ].filter(Boolean).join(' · ');
    show('done');
    renderHistory();
    stopTimer();
  });
}

function goPending(reading) {
  writeStore(PENDING_KEY, {
    since: new Date().toISOString(),
    reason: visitReason(),
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
    // Returning to the page: check now and restart the clock.
    attempt({ silent: true });
    startTimer();
  } else {
    stopTimer();
  }
}

/* ------------------------------------------------------------------ class */

// The homepage's class logic over the same data; the door QR carries no class information.
function renderClass() {
  const banner = el('class-banner-root');
  if (!banner || !classConfig) return;

  session = pickSession(classConfig);

  if (!session) {
    banner.hidden = true;
    renderReason();
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

  // Before a class starts, offer to note intent; once running, just check in.
  const noted = getRsvps().includes(sessionKey(session));
  q('[data-rsvp-offer]').hidden = session.running || noted;
  q('[data-rsvp-noted]').hidden = !noted || session.running;

  // A class arrival carries its reason unless the scanned code said otherwise.
  renderReason();

  // The button says what it is for.
  for (const label of document.querySelectorAll('[data-check-in-label]')) {
    label.textContent = session.running ? "I'm here for the class" : 'Check in';
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
    // The whole token, so a restored backup is verified again, not trusted.
    claim: getClaim(),
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

    // Merge, so newer visits survive an import.
    const seen = new Set(getHistory().map((entry) => entry.at));
    const merged = [...getHistory(), ...payload.checkins.filter((e) => !seen.has(e.at))]
      .sort((a, b) => new Date(b.at) - new Date(a.at));

    saveHistory(merged);
    renderHistory();

    // A claim in the file is re-checked from scratch.
    let note = '';
    if (payload.claim?.token && !getClaim()) {
      note = (await redeemClaim(payload.claim.token))
        ? ' Your confirmed email came across too.'
        : ' The confirmed email in that file no longer checks out.';
      renderClaim();
    }

    status.textContent = `Restored ${payload.checkins.length} visits.${note}`;
  } catch (error) {
    status.textContent = `That file could not be read: ${error.message}`;
  }
}

function forgetDevice() {
  if (!window.confirm('Delete this device identifier and every visit recorded on it? This cannot be undone.')) {
    return;
  }
  [DEVICE_KEY, HISTORY_KEY, PROFILE_KEY, PENDING_KEY, CLAIM_KEY].forEach(dropStore);
  stopTimer();
  renderDevice();
  renderProfile();
  renderClaim();
  renderHistory();
  show('idle');
  el('storage-status').textContent = 'Deleted. A new device identifier has been generated.';
}

/* ------------------------------------------------------------------ views */

// Views by #: #visits, #device; anything else (a claim link, say) is the pass.
const VIEWS = ['visits', 'device'];
let view = 'pass';
let cameFromPass = false;

function route() {
  const wanted = location.hash.slice(1);
  const next = VIEWS.includes(wanted) ? wanted : 'pass';
  cameFromPass = view === 'pass' && next !== 'pass';
  view = next;
  for (const section of document.querySelectorAll('[data-view]')) {
    section.hidden = section.dataset.view !== view;
  }
}

// "Pass" goes Back when it can, else replaces, so history does not fill with screens.
function backToPass(event) {
  event.preventDefault();
  if (cameFromPass) {
    history.back();
  } else {
    history.replaceState(null, '', location.pathname + location.search);
    route();
  }
}

/* -------------------------------------------------------------------- init */

async function init() {
  if (!storageWorks()) {
    show('blocked');
    return;
  }

  renderDevice();
  renderProfile();
  renderReason();

  // Take a claim from the URL before rendering anything that depends on it.
  const arriving = claimFromLocation();
  if (arriving) {
    await redeemClaim(arriving);
    clearClaimFromLocation();
  }
  renderClaim();
  renderHistory();

  el('venue-directions').href =
    `https://www.google.com/maps/dir/?api=1&destination=${config.location.latitude},${config.location.longitude}`;

  // Saved on every change, so closing mid-answer loses nothing.
  for (const id of ['profile-name', 'profile-email']) {
    el(id).addEventListener('input', saveProfile);
    el(id).addEventListener('change', saveProfile);
  }

  el('claim-forget').addEventListener('click', dropClaim);

  // The Contact Picker where it exists (reads only the picked card); else autocomplete.
  const contact = el('use-contact');
  if (contact && navigator.contacts?.select) {
    const offer = () => { contact.hidden = Boolean(el('profile-name').value.trim()); };
    offer();
    el('profile-name').addEventListener('input', offer);
    contact.addEventListener('click', async () => {
      try {
        const [card] = await navigator.contacts.select(['name', 'email'], { multiple: false });
        if (!card) return;
        if (card.name?.[0]) el('profile-name').value = card.name[0];
        if (card.email?.[0] && !el('profile-email').value) el('profile-email').value = card.email[0];
        saveProfile();
        offer();
      } catch (error) {
        // Declined or unavailable: the fields are still there to type in.
      }
    });
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

  window.addEventListener('hashchange', route);
  document.querySelectorAll('[data-back]').forEach((link) => link.addEventListener('click', backToPass));
  route();

  const rsvp = el('rsvp-button');
  if (rsvp) rsvp.addEventListener('click', noteRsvp);

  // Re-evaluated on a timer while visible, as the homepage does.
  if (classConfig) watch(renderClass);

  const persisted = await requestPersistence();
  el('persist-state').textContent =
    persisted === true
      ? 'Until you delete it'
      : 'Only while the browser allows. Save a copy, or add this to your Home Screen';

  // A pending check-in survives a reload.
  if (getPending()) {
    show('far');
    startTimer();
    attempt({ silent: true });
  } else {
    show('idle');
  }
}

init();
