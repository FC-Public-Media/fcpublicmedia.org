// /upload/: sign in to find the member's site, then build a future-dated programs.yml entry.
// The sign-in is not a security boundary. See docs/identity.md.

import { signIn } from './passkey.js';

const config = JSON.parse(document.getElementById('upload-config').textContent);

const el = (id) => document.getElementById(id);

function show(state) {
  for (const panel of document.querySelectorAll('[data-state]')) {
    panel.hidden = panel.dataset.state !== state;
  }
}

let session = null;

/* ------------------------------------------------------------------- times */

/** ISO timestamp with Colorado's offset, in two passes; can be an hour off near a DST change. */
function withVenueOffset(date, time) {
  if (!date) return '';
  const clock = time || config.defaultTime || '18:00';

  const offsetAt = (instant) => {
    try {
      const parts = new Intl.DateTimeFormat('en-US', {
        timeZone: config.timezone || 'America/Denver',
        timeZoneName: 'longOffset',
      }).formatToParts(instant);
      const name = parts.find((p) => p.type === 'timeZoneName')?.value || '';
      const match = name.match(/GMT([+-]\d{2}:\d{2})/);
      return match ? match[1] : null;
    } catch (error) {
      // No longOffset support: refuse rather than write the wrong zone.
      return null;
    }
  };

  let offset = offsetAt(new Date(`${date}T${clock}:00Z`));
  if (!offset) return `${date}T${clock}:00`;

  offset = offsetAt(new Date(`${date}T${clock}:00${offset}`)) || offset;
  return `${date}T${clock}:00${offset}`;
}

function refreshStamp() {
  el('ep-iso').textContent =
    withVenueOffset(el('ep-date').value, el('ep-time').value) || '—';
}

/* ------------------------------------------------------------------ output */

/** YAML is written by hand rather than generated — it is nine lines. */
function toYaml(entry) {
  const quote = (value) => `"${String(value).replace(/"/g, '\\"')}"`;
  const lines = [
    `  - title: ${quote(entry.title)}`,
    '    status: scheduled',
    `    drop: ${quote(entry.drop)}`,
  ];

  if (entry.runtime) lines.push(`    runtime: ${quote(entry.runtime)}`);
  if (entry.summary) {
    lines.push('    summary: >-');
    // Folded scalar, wrapped so it diffs readably.
    const words = entry.summary.split(/\s+/);
    let row = '     ';
    for (const word of words) {
      if ((row + ' ' + word).length > 74) {
        lines.push(row);
        row = '     ';
      }
      row += ` ${word}`;
    }
    lines.push(row);
  }

  if (entry.artifact.path || entry.artifact.name) {
    lines.push('    artifact:');
    if (entry.artifact.path) lines.push(`      url: ${quote(entry.artifact.path)}`);
    if (entry.artifact.name) lines.push(`      file: ${quote(entry.artifact.name)}`);
    if (entry.artifact.type) lines.push(`      type: ${quote(entry.artifact.type)}`);
    if (entry.artifact.bytes) lines.push(`      bytes: ${entry.artifact.bytes}`);
  }

  return lines.join('\n');
}

function collect() {
  const title = el('ep-title').value.trim();
  const drop = withVenueOffset(el('ep-date').value, el('ep-time').value);

  if (!title) return { error: 'Give it a title — everything else is optional.' };
  if (!drop) return { error: 'Pick a drop date so we know which week it is for.' };

  const file = el('ep-file').files[0];
  return {
    entry: {
      title,
      drop,
      summary: el('ep-summary').value.trim(),
      runtime: el('ep-runtime').value.trim(),
      artifact: {
        path: el('ep-path').value.trim(),
        name: file ? file.name : '',
        type: file ? file.type : '',
        bytes: file ? file.size : 0,
      },
    },
  };
}

/* ---------------------------------------------------------------- sending */

/** No broker: show the entry and let the member pass it along. */
function offerManually(entry) {
  const yaml = toYaml(entry);
  el('entry-yaml').textContent = yaml;

  const subject = `Episode for ${session.repo}: ${entry.title}`;
  el('email-entry').href =
    `mailto:?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(yaml)}`;

  show('manual');
}

async function submit() {
  const { entry, error } = collect();
  if (error) {
    el('ep-error').textContent = error;
    return;
  }
  el('ep-error').textContent = '';

  if (!config.brokerUrl) {
    offerManually(entry);
    return;
  }

  try {
    const response = await fetch(config.brokerUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        repo: session.repo,
        credentialId: session.credentialId,
        path: config.programsPath,
        entry,
      }),
    });
    if (!response.ok) throw new Error(`the server said no (HTTP ${response.status})`);
  } catch (sendError) {
    // Fall back to handing over what they typed.
    el('copy-status').textContent =
      `We couldn't send it automatically (${sendError.message}).`;
    offerManually(entry);
    return;
  }

  el('done-detail').textContent =
    `${entry.title} is queued for ${new Date(entry.drop).toLocaleDateString()}.`;
  show('done');
}

/* --------------------------------------------------------------- sign in */

async function authenticate() {
  show('checking');
  const result = await signIn({ rpId: config.rpId });

  if (!result.ok) {
    if (result.reason === 'unsupported') {
      show('unsupported');
      return;
    }
    el('sign-in-detail').textContent = {
      cancelled: 'The sign-in was cancelled, so nothing happened.',
      unreadable:
        "That passkey doesn't say which site it belongs to. It was probably set up before we changed how that works — ask us for a fresh link and it'll take a minute.",
      failed: result.detail || 'Your device would not complete the sign-in.',
    }[result.reason] || 'That did not work.';
    show('sign-in-failed');
    return;
  }

  session = result;
  el('ready-site').textContent = result.repo.split('/')[1] || result.repo;

  // Default the drop to next week, the common case.
  const soon = new Date(Date.now() + 7 * 86400000);
  el('ep-date').value = soon.toISOString().slice(0, 10);
  el('ep-time').value = config.defaultTime || '18:00';
  refreshStamp();

  show('ready');
}

/* -------------------------------------------------------------------- init */

function init() {
  el('sign-in').addEventListener('click', authenticate);
  el('sign-out').addEventListener('click', () => {
    session = null;
    show('signed-out');
  });

  document.querySelectorAll('[data-action="retry"]').forEach((button) => {
    button.addEventListener('click', () => show(session ? 'ready' : 'signed-out'));
  });

  for (const id of ['ep-date', 'ep-time']) {
    el(id).addEventListener('change', refreshStamp);
  }

  el('ep-file').addEventListener('change', (event) => {
    const file = event.target.files[0];
    el('ep-file-detail').textContent = file
      ? `${file.name} — ${(file.size / 1048576).toFixed(1)} MB. ` +
        (config.destination
          ? 'This will be uploaded when you submit.'
          : 'Recorded, but not uploaded from here — see below.')
      : '';
  });

  el('ep-submit').addEventListener('click', submit);

  // Only when there is nowhere to upload to.
  const notice = document.querySelector('[data-no-destination]');
  if (notice) notice.hidden = Boolean(config.destination);

  show('signed-out');
}

init();
