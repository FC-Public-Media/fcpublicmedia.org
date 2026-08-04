// Binding a device to a member site.
//
// The visitor arrives from a signed link that names their repository. This
// page checks the signature, makes a passkey, and hands the public half to
// the broker — or, when there is no broker yet, shows it to them to send on.
//
// WHY THE REPOSITORY COMES FROM INSIDE THE SIGNATURE
// -------------------------------------------------
// It would be easier to put it in the URL as a plain parameter. Then anyone
// with a link could edit it and bind their device to somebody else's site.
// Carrying it inside the signed payload means the link can be forwarded — as
// it is meant to be — without being re-aimed.

import { verifyClaim, claimFromLocation, clearClaimFromLocation } from './claims.js';
import { createPasskey, supported } from './passkey.js';

const config = JSON.parse(document.getElementById('authorize-config').textContent);

const el = (id) => document.getElementById(id);

function show(state) {
  for (const panel of document.querySelectorAll('[data-state]')) {
    panel.hidden = panel.dataset.state !== state;
  }
}

/** What the visitor is setting up, in their terms rather than ours. */
function siteName(repo) {
  return (repo || '').split('/')[1] || repo || 'your site';
}

let claim = null;

/* ------------------------------------------------------------------ sending */

/**
 * Hand the device record to the broker.
 *
 * The claim goes along with it. The broker re-verifies that signature itself
 * rather than trusting this page's word for it — the check here is only so a
 * visitor with a bad link finds out before making a passkey they cannot use.
 */
async function send(device) {
  const response = await fetch(config.brokerUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ claim: claim.token, device }),
  });

  if (!response.ok) {
    throw new Error(`the server said no (HTTP ${response.status})`);
  }

  return response.json().catch(() => ({}));
}

/** No broker: show the record and let the visitor pass it along. */
function offerManually(device) {
  const record = JSON.stringify(device, null, 2);
  el('device-record').textContent = record;

  const subject = `Device for ${claim.payload.repo}`;
  el('email-record').href =
    `mailto:?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(record)}`;

  el('copy-record').addEventListener('click', async () => {
    const status = el('copy-status');
    try {
      await navigator.clipboard.writeText(record);
      status.textContent = 'Copied. Paste it into an email to us.';
    } catch (error) {
      // Clipboard access is blocked in plenty of ordinary situations, and the
      // text is on screen anyway.
      status.textContent = 'Your browser blocked copying — select the text below instead.';
    }
  });

  show('manual');
}

/* ----------------------------------------------------------------- ceremony */

async function bind() {
  if (!supported()) {
    show('unsupported');
    return;
  }

  show('working');

  const result = await createPasskey({
    email: claim.payload.email,
    repo: claim.payload.repo,
    label: el('device-name').value,
    rpId: config.rpId,
    issuer: config.issuer,
  });

  if (!result.ok) {
    if (result.reason === 'cancelled') {
      show('cancelled');
    } else if (result.reason === 'unsupported' || result.reason === 'no-public-key') {
      show('unsupported');
    } else {
      el('error-detail').textContent = result.detail || 'The passkey could not be created.';
      show('error');
    }
    return;
  }

  if (!config.brokerUrl) {
    offerManually(result.device);
    return;
  }

  try {
    await send(result.device);
  } catch (error) {
    // The passkey exists at this point — it is on the device and cannot be
    // un-made from here. So this is a delivery failure, and the useful thing
    // is to fall back to handing the record over rather than to report a
    // failure that would make someone try the whole thing again.
    el('copy-status').textContent = `We couldn't send it automatically (${error.message}).`;
    offerManually(result.device);
    return;
  }

  el('done-detail').textContent =
    config.writeMode === 'pull_request'
      ? `${siteName(claim.payload.repo)} — we'll confirm once someone approves it.`
      : `${siteName(claim.payload.repo)} is ready to manage from this device.`;
  show('done');
}

/* --------------------------------------------------------------------- init */

async function init() {
  document.querySelectorAll('[data-action="retry"]').forEach((button) => {
    button.addEventListener('click', () => show('ready'));
  });
  el('create-passkey').addEventListener('click', bind);

  // Opening a second link in a tab that already has this page loaded changes
  // only the fragment, which is not a navigation — without this, the page
  // would sit there still showing the first link's site.
  window.addEventListener('hashchange', () => {
    if (claimFromLocation()) start();
  });

  await start();
}

async function start() {
  const token = claimFromLocation();
  if (!token) {
    show('no-link');
    return;
  }

  show('checking');
  const result = await verifyClaim(token, config.keys);

  // Taken out of the address bar either way. It is a capability, and a URL
  // still carrying one is a URL someone might paste into a group chat.
  clearClaimFromLocation();

  if (!result.ok) {
    el('bad-link-detail').textContent = {
      expired: 'That link has expired. They only last a short while on purpose.',
      signature: "That link didn't check out. It may have been altered in transit.",
      malformed: 'That link looks incomplete. Email clients sometimes break long links across lines — try opening it from the original message.',
      unsupported: 'This browser cannot check the link.',
    }[result.reason] || 'That link could not be used.';
    show('bad-link');
    return;
  }

  // A claim with no repository is the check-in kind. Sending someone through a
  // passkey ceremony for a site they were not invited to would leave them with
  // a credential authorizing nothing.
  if (!result.payload.repo) {
    el('bad-link-detail').textContent =
      "That link confirms your email address, but it doesn't name a site to set up.";
    show('bad-link');
    return;
  }

  claim = { token, payload: result.payload };

  el('ready-site').textContent = siteName(result.payload.repo);
  el('ready-email').textContent = result.payload.email;
  show('ready');
}

init();
