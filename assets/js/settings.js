// Editing a member site's settings file.
//
// Same passkey as /upload/, different verb. The member signs in, the page
// fetches their own _data/site.yml from their own repository, and they edit
// the text.
//
// THE TEXT, NOT A FORM
// --------------------
// That file is mostly comments, and those comments are the only documentation
// a member has for what the settings do. Parsing the YAML and re-serialising
// it would strip every one of them on the first save. So the editor is a
// textarea, what they see is the file, and what gets committed is what they
// saw. See _data/settings.yml for the full argument.
//
// THE SHA IS NOT DECORATION
// -------------------------
// GitHub hands back the blob SHA with the file, and it goes back with the
// edit. If somebody changed the file in between — the member on another
// device, or us — GitHub refuses the write instead of silently discarding
// their change. Losing that field turns a rare conflict into a rare, silent
// data loss.

import { signIn } from './passkey.js';

const config = JSON.parse(document.getElementById('settings-config').textContent);

const el = (id) => document.getElementById(id);

function show(state) {
  for (const panel of document.querySelectorAll('[data-state]')) {
    panel.hidden = panel.dataset.state !== state;
  }
}

let session = null;
let original = '';
let sha = '';

/* -------------------------------------------------------------------- read */

function decodeBase64(value) {
  const binary = atob(value.replace(/\s/g, ''));
  return new TextDecoder().decode(Uint8Array.from(binary, (c) => c.charCodeAt(0)));
}

/**
 * Fetch the file the member is actually running, not a copy of the template.
 *
 * The contents API returns the text and the SHA together, which is why it is
 * used here rather than raw.githubusercontent — one request, and the SHA is
 * needed for the write anyway.
 */
async function load() {
  show('loading');

  const url = `https://api.github.com/repos/${session.repo}/contents/${config.path}`;
  let payload;
  try {
    const response = await fetch(url, { headers: { Accept: 'application/vnd.github+json' } });
    if (response.status === 404) {
      throw new Error(
        `${config.path} isn't in your site yet. That usually means the site was ` +
        'set up before this file existed — ask us and we\'ll add it.'
      );
    }
    if (response.status === 403) {
      // Unauthenticated API requests are capped per address, and a shared
      // network can exhaust it. Worth naming, because "try again later"
      // sounds like a brush-off when it is literally the fix.
      throw new Error(
        'GitHub is rate-limiting requests from this network. It clears within ' +
        'the hour — or edit the file directly on GitHub if you have an account.'
      );
    }
    if (!response.ok) throw new Error(`GitHub returned HTTP ${response.status}`);
    payload = await response.json();
  } catch (error) {
    el('load-detail').textContent = error.message;
    show('load-failed');
    return;
  }

  original = decodeBase64(payload.content || '');
  sha = payload.sha || '';

  el('settings-text').value = original;
  el('editing-site').textContent = session.repo.split('/')[1] || session.repo;
  el('editing-path').textContent = config.path;
  el('settings-status').textContent = '';
  check();
  show('editing');
}

/* ------------------------------------------------------------------ checks */

/**
 * A smoke check, deliberately not a parser.
 *
 * There is no YAML parser in the browser here and adding one would be a
 * dependency for a page that already has a real validator behind it — the
 * workflow refuses to merge anything that does not parse. So this catches the
 * two mistakes people actually make, and says nothing about the rest rather
 * than implying it checked.
 */
function check() {
  const text = el('settings-text').value;
  const notes = [];

  if (!text.trim()) {
    notes.push('The file is empty.');
  }

  // Tabs are invalid for indentation in YAML, and an editor that helpfully
  // inserted one leaves no visible trace.
  const tabLine = text.split('\n').findIndex((line) => /^\s*\t/.test(line));
  if (tabLine >= 0) {
    notes.push(`Line ${tabLine + 1} starts with a tab. This format needs spaces.`);
  }

  // Losing a whole setting is usually an accident — a stray selection, a
  // paste over the top. Reported rather than blocked, because removing one on
  // purpose is legitimate.
  const topLevel = (body) =>
    new Set((body.match(/^[A-Za-z_][\w-]*(?=:)/gm) || []));
  const before = topLevel(original);
  const after = topLevel(text);
  const gone = [...before].filter((key) => !after.has(key));
  if (gone.length) {
    notes.push(`No longer in the file: ${gone.join(', ')}. Fine if you meant it.`);
  }

  el('settings-checks').textContent = notes.join(' ');
  return !notes.some((note) => note.includes('tab') || note.includes('empty'));
}

/* ------------------------------------------------------------------- write */

function offerManually(text) {
  el('settings-output').textContent = text;
  el('email-settings').href =
    `mailto:?subject=${encodeURIComponent(`Settings for ${session.repo}`)}` +
    `&body=${encodeURIComponent(text)}`;
  show('manual');
}

async function save() {
  const text = el('settings-text').value;

  if (!check()) {
    el('settings-status').textContent = 'Fix the note above first.';
    return;
  }
  if (text === original) {
    el('settings-status').textContent = 'Nothing has changed.';
    return;
  }

  if (!config.brokerUrl) {
    offerManually(text);
    return;
  }

  el('settings-status').textContent = 'Saving…';
  try {
    const response = await fetch(config.brokerUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        repo: session.repo,
        credentialId: session.credentialId,
        path: config.path,
        content: text,
        // Sent so the write can be refused rather than clobber somebody.
        sha,
      }),
    });

    if (response.status === 409) {
      el('settings-status').textContent =
        'Somebody else changed this file while you were editing. Reload to ' +
        'get their version — your text is still in the box, so copy it first.';
      return;
    }
    if (!response.ok) throw new Error(`the server said no (HTTP ${response.status})`);
  } catch (error) {
    // The edit is still in the textarea, so handing it over loses nothing.
    el('copy-status').textContent = `We couldn't save it automatically (${error.message}).`;
    offerManually(text);
    return;
  }

  el('saved-detail').textContent =
    config.writeMode === 'branch'
      ? 'Your changes are being checked. If the file is valid they go live at the next build; if not, we\'ll tell you what was wrong.'
      : 'Your changes are in. The site rebuilds shortly.';
  show('saved');
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
      unreadable:
        "That passkey doesn't say which site it belongs to — ask us for a fresh link.",
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
  el('settings-text').addEventListener('input', check);
  el('settings-save').addEventListener('click', save);

  el('settings-revert').addEventListener('click', () => {
    el('settings-text').value = original;
    check();
    el('settings-status').textContent = 'Back to what was there.';
  });

  el('copy-settings').addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(el('settings-output').textContent);
      el('copy-status').textContent = 'Copied. Paste it into an email to us.';
    } catch (error) {
      el('copy-status').textContent =
        'Your browser blocked copying — select the text below instead.';
    }
  });

  document.querySelectorAll('[data-action="retry"]').forEach((button) => {
    button.addEventListener('click', () => show(session ? 'editing' : 'signed-out'));
  });
  document.querySelectorAll('[data-action="reload"]').forEach((button) => {
    button.addEventListener('click', () => (session ? load() : show('signed-out')));
  });

  show('signed-out');
}

init();
