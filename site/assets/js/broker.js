// see docs/inline/site/assets/js/broker.js.md#1

import { signIn } from './passkey.js';

// see docs/inline/site/assets/js/broker.js.md#2
export async function contentHash(text) {
  const bytes = new TextEncoder().encode(String(text));
  const digest = new Uint8Array(await crypto.subtle.digest('SHA-256', bytes));
  let binary = '';
  for (const byte of digest) binary += String.fromCharCode(byte);
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

// see docs/inline/site/assets/js/broker.js.md#3
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
