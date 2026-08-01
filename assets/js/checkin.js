// Check-in, recorded on the visitor's own device.
//
// There is no server. Everything here reads and writes localStorage on the
// phone or laptop in front of the person, and nothing leaves it.
//
// The device identifier is a random UUID generated on first visit. It is not
// derived from anything about the device or the person, it is never sent
// anywhere, and "Forget this device" deletes it. It exists so a returning
// visitor sees their own history rather than a blank page — that is the whole
// job it does.

const DEVICE_KEY = 'fcpm.device';
const HISTORY_KEY = 'fcpm.checkins';

const config = JSON.parse(document.getElementById('checkin-config').textContent);

/* ---------------------------------------------------------------- storage */

// Private browsing and locked-down settings make localStorage throw rather
// than return null, so every access goes through these.
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

/* ----------------------------------------------------------------- device */

function randomId() {
  if (window.crypto?.randomUUID) return window.crypto.randomUUID();
  // Older browsers: still random, still not derived from the device.
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

/* ---------------------------------------------------------------- history */

const getHistory = () => readStore(HISTORY_KEY, []);

function addCheckIn(entry) {
  const history = getHistory();
  history.unshift(entry);
  writeStore(HISTORY_KEY, history.slice(0, config.historyLimit));
  return history;
}

/* --------------------------------------------------------------- identity */

// With identity.mode = "access", Cloudflare Access has already authenticated
// the visitor against whichever provider they chose, and this endpoint hands
// back the verified identity. Nothing here holds a secret or runs an OAuth
// flow; if the route is not behind Access the request 404s and the page falls
// back to recording an anonymous check-in.
async function getIdentity() {
  if (config.identityMode !== 'access') return null;
  try {
    const response = await fetch('/cdn-cgi/access/get-identity', {
      headers: { Accept: 'application/json' },
    });
    if (!response.ok) return null;
    const identity = await response.json();
    return identity.email || null;
  } catch (error) {
    return null;
  }
}

/* --------------------------------------------------------------- rendering */

const el = (id) => document.getElementById(id);

function formatWhen(iso) {
  const date = new Date(iso);
  return date.toLocaleString([], {
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
  const empty = el('checkin-empty');
  const count = el('checkin-count');

  list.innerHTML = '';

  if (!history.length) {
    empty.hidden = false;
    count.textContent = '';
    return;
  }

  empty.hidden = true;
  count.textContent = `${history.length} visit${history.length === 1 ? '' : 's'} on this device`;

  for (const entry of history) {
    const item = document.createElement('li');

    const when = document.createElement('b');
    when.textContent = formatWhen(entry.at);

    const who = document.createElement('span');
    who.textContent = entry.email || 'not signed in';

    item.append(when, who);
    list.append(item);
  }
}

function renderDevice(device) {
  el('device-label').value = device.label || '';
  // Enough of the identifier to tell two devices apart, not the whole thing —
  // there is no reason to put a full identifier on screen.
  el('device-id').textContent = device.id.slice(0, 8);
  el('device-since').textContent = new Date(device.created).toLocaleDateString();
}

/* ----------------------------------------------------------------- actions */

async function checkIn() {
  const button = el('checkin-button');
  button.disabled = true;

  const email = await getIdentity();
  const device = getDevice();

  const stored = writeStore(HISTORY_KEY, [
    { at: new Date().toISOString(), device: device.id, email },
    ...getHistory(),
  ].slice(0, config.historyLimit));

  button.disabled = false;

  if (!stored) {
    el('checkin-status').textContent =
      'Your browser would not let this page save anything, so nothing was recorded.';
    return;
  }

  el('checkin-status').textContent = email
    ? `Checked in as ${email}.`
    : 'Checked in on this device.';
  renderHistory();
}

function exportHistory() {
  const payload = {
    exported: new Date().toISOString(),
    device: getDevice(),
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
  const status = el('checkin-status');
  try {
    const payload = JSON.parse(await file.text());
    if (!Array.isArray(payload.checkins)) throw new Error('no check-ins in that file');

    // Merge rather than replace, so importing a backup onto a device that has
    // been used since does not throw away the newer visits.
    const seen = new Set(getHistory().map((entry) => entry.at));
    const merged = [...getHistory(), ...payload.checkins.filter((entry) => !seen.has(entry.at))]
      .sort((a, b) => new Date(b.at) - new Date(a.at))
      .slice(0, config.historyLimit);

    writeStore(HISTORY_KEY, merged);
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
  try {
    window.localStorage.removeItem(DEVICE_KEY);
    window.localStorage.removeItem(HISTORY_KEY);
  } catch (error) {
    /* nothing we can do, and nothing was stored anyway */
  }
  renderDevice(getDevice());
  renderHistory();
  el('checkin-status').textContent = 'Deleted. A new device identifier has been generated.';
}

/* -------------------------------------------------------------------- init */

function init() {
  if (!storageWorks()) {
    el('checkin-unavailable').hidden = false;
    el('checkin-app').hidden = true;
    return;
  }

  el('checkin-app').hidden = false;

  const device = getDevice();
  renderDevice(device);
  renderHistory();

  el('checkin-button').addEventListener('click', checkIn);
  el('export-button').addEventListener('click', exportHistory);
  el('forget-button').addEventListener('click', forgetDevice);

  el('import-input').addEventListener('change', (event) => {
    const [file] = event.target.files;
    if (file) importHistory(file);
    event.target.value = '';
  });

  el('device-label').addEventListener('change', (event) => {
    const current = getDevice();
    writeStore(DEVICE_KEY, { ...current, label: event.target.value.trim() });
  });
}

init();
