// Talking to the broker.
//
// Two functions, because every page that asks the broker to do something does
// the same three things: hash what it is about to ask for, run the ceremony
// bound to that, and post the result. Keeping it here means a page cannot
// accidentally skip the binding — the hash is computed from the same bytes
// that get sent, in one place, rather than by each caller remembering to.
//
// With no broker URL configured, nothing here is reached: the pages fall back
// to handing the member their own file. See worker/README.md.

import { signIn } from './passkey.js';

/**
 * The hash a page declares up front and the broker recomputes at the end.
 *
 * Must agree byte for byte with worker/src/intent.js. Both are SHA-256 of the
 * UTF-8 bytes, base64url, unpadded — a disagreement here would look like the
 * member changing their mind mid-save.
 */
export async function contentHash(text) {
  const bytes = new TextEncoder().encode(String(text));
  const digest = new Uint8Array(await crypto.subtle.digest('SHA-256', bytes));
  let binary = '';
  for (const byte of digest) binary += String.fromCharCode(byte);
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

/**
 * Sign for one action and carry it out.
 *
 * Resolves to { ok: true, result } or { ok: false, reason, detail }. Never
 * throws: dismissing the passkey sheet is an ordinary thing to do, and a
 * server that is down is an ordinary thing for a server to be.
 *
 * `reason` is what the caller branches on:
 *   cancelled      the member dismissed the prompt
 *   no-challenge   the broker could not be reached, or refused the request
 *   conflict       somebody else changed the file while they were editing
 *   not-allowed    the device is registered but may not publish
 *   failed         anything else, with `detail` carrying what was said
 */
export async function act({ brokerUrl, rpId, endpoint, intent, payload = {} }) {
  const signed = await signIn({ rpId, brokerUrl, intent });
  if (!signed.ok) return { ok: false, reason: signed.reason, detail: signed.detail };

  let response;
  try {
    response = await fetch(`${brokerUrl.replace(/\/+$/, '')}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ assertion: signed.assertion, ...payload }),
    });
  } catch (error) {
    return { ok: false, reason: 'failed', detail: 'We could not reach the server.' };
  }

  const result = await response.json().catch(() => ({}));
  if (!response.ok) {
    return {
      ok: false,
      reason: result.reason || 'failed',
      detail: result.detail || `The server said no (HTTP ${response.status}).`,
    };
  }

  return { ok: true, result };
}
