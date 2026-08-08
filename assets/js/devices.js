// Approving a co-producer's phone from your own.
//
// This is the page that makes the whole passkey design worth operating. The
// point was never nicer sign-in; it was moving approval from per-submission to
// per-device, once. Without somewhere to do that approving, adding a
// co-producer still means asking staff — which is exactly the loop being left.
//
// WHAT SIGNING IN HERE DOES AND DOES NOT DO
// -----------------------------------------
// The sign-in is wayfinding, the same as everywhere else on this site: it
// tells the page which site the passkey belongs to so it can show the right
// list. It proves nothing to us. Each individual approval is its own ceremony,
// bound by the broker to that one device and that one change — so what the
// member is agreeing to is "let Raj's phone publish", at the moment they mean
// it, rather than "I am signed in" some minutes earlier.

import { act } from './broker.js';
import { signIn } from './passkey.js';

const config = JSON.parse(document.getElementById('devices-config').textContent);

const el = (id) => document.getElementById(id);

function show(state) {
  for (const panel of document.querySelectorAll('[data-state]')) {
    panel.hidden = panel.dataset.state !== state;
  }
}

let session = null;
let devices = [];

const active = () => devices.filter((device) => device.revoked !== true);

/* -------------------------------------------------------------------- read */

/**
 * Read the list the same way anybody else can: it is a public file.
 *
 * Nothing here is secret — public keys and the labels people gave their own
 * devices. Reading it without the broker means this page still shows something
 * useful when there is no broker configured at all.
 */
async function load() {
  show('loading');

  const url = `https://raw.githubusercontent.com/${session.repo}/HEAD/${config.devicesPath}`;
  try {
    const response = await fetch(url, { cache: 'no-store' });
    if (response.status === 404) {
      throw new Error(
        "This site has no registered devices yet, which shouldn't be possible " +
        'from a device that just signed in. Ask us to take a look.'
      );
    }
    if (!response.ok) throw new Error(`GitHub returned HTTP ${response.status}`);

    const payload = await response.json();
    if (!Array.isArray(payload?.devices)) throw new Error('The device list has the wrong shape.');
    devices = payload.devices;
  } catch (error) {
    el('load-detail').textContent = error.message;
    show('load-failed');
    return;
  }

  render();
}

/* ------------------------------------------------------------------ render */

const when = (value) => {
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? ''
    : date.toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' });
};

function row(device, actions) {
  const item = document.createElement('li');

  const name = document.createElement('b');
  name.textContent = device.label || 'Unnamed device';

  const detail = document.createElement('span');
  const added = when(device.added);
  detail.textContent = [
    added && `added ${added}`,
    device.credential_id === session.credentialId ? 'this device' : '',
  ]
    .filter(Boolean)
    .join(' · ');

  item.append(name, detail);

  for (const [label, action, style] of actions) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = style || 'btn';
    button.textContent = label;
    button.addEventListener('click', () => decide(action, device));
    item.append(' ', button);
  }

  return item;
}

function render() {
  el('devices-site').textContent = session.repo.split('/')[1] || session.repo;

  const waiting = active().filter((device) => device.may_publish !== true);
  const allowed = active().filter((device) => device.may_publish === true);

  el('waiting-section').hidden = waiting.length === 0;
  el('waiting-list').replaceChildren(
    ...waiting.map((device) =>
      row(device, [
        ['Approve', 'device.allow', 'btn btn-primary'],
        ['Remove', 'device.revoke'],
      ])
    )
  );

  el('allowed-list').replaceChildren(
    ...allowed.map((device) =>
      // The last one that can publish cannot be removed — the broker refuses
      // it, because a site nobody can change needs staff with a text editor to
      // rescue. Not offering the button is kinder than offering it and failing.
      row(device, allowed.length > 1 ? [['Remove', 'device.revoke']] : [])
    )
  );

  if (allowed.length === 1) {
    el('devices-status').textContent =
      'The only device that can publish here, so it cannot be removed — approve another one first.';
  }

  show('listing');
}

/* ------------------------------------------------------------------ change */

function offerManually(action, device) {
  const verb = action === 'device.allow' ? 'approve' : 'remove';
  el('manual-detail').textContent =
    `You asked to ${verb} "${device.label || 'a device'}" on ${session.repo}.`;
  el('email-change').href =
    `mailto:?subject=${encodeURIComponent(`Device change for ${session.repo}`)}` +
    `&body=${encodeURIComponent(
      `Please ${verb} this device.\n\nSite: ${session.repo}\n` +
      `Device: ${device.label || 'unnamed'}\nCredential: ${device.credential_id}\n`
    )}`;
  show('manual');
}

/**
 * Approve or remove one device.
 *
 * A ceremony per change, on purpose. Approving a device is the single act that
 * replaces every future weekly approval, so it is worth the member confirming
 * that specific thing rather than it riding on a sign-in from minutes ago.
 */
async function decide(action, device) {
  if (!config.brokerUrl) {
    offerManually(action, device);
    return;
  }

  el('devices-status').textContent = 'Confirming with your device…';

  const done = await act({
    brokerUrl: config.brokerUrl,
    rpId: config.rpId,
    endpoint: '/device',
    intent: { action, repo: session.repo, credential_id: device.credential_id },
  });

  if (!done.ok) {
    if (done.reason === 'cancelled') {
      el('devices-status').textContent = 'Nothing changed — that was cancelled.';
      return;
    }
    if (done.reason === 'not-allowed') {
      el('devices-status').textContent =
        'This device is registered but not allowed to change the site yet, so it cannot approve others.';
      return;
    }
    if (done.reason === 'listed') {
      // The broker refusing on its own rules — already approved, or the last
      // publisher. Its wording is better than anything guessable from here.
      el('devices-status').textContent = done.detail;
      await load();
      return;
    }
    el('devices-status').textContent = `That didn't go through (${done.detail}).`;
    return;
  }

  el('devices-status').textContent = done.result.already
    ? 'That was already the case.'
    : 'Done.';
  await load();
}

/* ----------------------------------------------------------------- sign in */

async function authenticate() {
  const result = await signIn({ rpId: config.rpId });

  if (!result.ok) {
    if (result.reason === 'unsupported') {
      show('unsupported');
      return;
    }
    el('sign-in-detail').textContent = {
      cancelled: 'The sign-in was cancelled, so nothing happened.',
      unreadable: "That passkey doesn't say which site it belongs to — ask us for a fresh link.",
      failed: result.detail || 'Your device would not complete the sign-in.',
    }[result.reason] || 'That did not work.';
    show('sign-in-failed');
    return;
  }

  session = result;
  await load();
}

/* -------------------------------------------------------------------- init */

function init() {
  el('sign-in').addEventListener('click', authenticate);

  document.querySelectorAll('[data-action="retry"]').forEach((button) => {
    button.addEventListener('click', () => show('signed-out'));
  });
  document.querySelectorAll('[data-action="reload"]').forEach((button) => {
    button.addEventListener('click', () => (session ? load() : show('signed-out')));
  });

  show('signed-out');
}

init();
