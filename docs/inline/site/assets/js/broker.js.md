# `site/assets/js/broker.js`

Moved out of the file. Unreviewed.

## 1

Above `import { signIn } from './passkey.js';`

Talking to the broker.

Two functions, because every page that asks the broker to do something does
the same three things: hash what it is about to ask for, run the ceremony
bound to that, and post the result. Keeping it here means a page cannot
accidentally skip the binding — the hash is computed from the same bytes
that get sent, in one place, rather than by each caller remembering to.

With no broker URL configured, nothing here is reached: the pages fall back
to handing the member their own file. See worker/README.md.

## 2

Above `export async function contentHash(text) {`

The hash a page declares up front and the broker recomputes at the end.

Must agree byte for byte with worker/src/intent.js. Both are SHA-256 of the
UTF-8 bytes, base64url, unpadded — a disagreement here would look like the
member changing their mind mid-save.

## 3

Above `export async function act({ brokerUrl, rpId, endpoint, intent, payload = {} }) {`

Sign for one action and carry it out.

Resolves to { ok: true, result } or { ok: false, reason, detail }. Never
throws: dismissing the passkey sheet is an ordinary thing to do, and a
server that is down is an ordinary thing for a server to be.

`reason` is what the caller branches on:
  cancelled      the member dismissed the prompt
  no-challenge   the broker could not be reached, or refused the request
  conflict       somebody else changed the file while they were editing
  not-allowed    the device is registered but may not publish
  failed         anything else, with `detail` carrying what was said
