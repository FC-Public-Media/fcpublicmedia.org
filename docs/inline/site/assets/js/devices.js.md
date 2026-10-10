# `site/assets/js/devices.js`

Moved out of the file. Unreviewed.

## 1

Above `import { act } from './broker.js';`

Approving a co-producer's phone from your own.

This is the page that makes the whole passkey design worth operating. The
point was never nicer sign-in; it was moving approval from per-submission to
per-device, once. Without somewhere to do that approving, adding a
co-producer still means asking staff — which is exactly the loop being left.

WHAT SIGNING IN HERE DOES AND DOES NOT DO
-----------------------------------------
The sign-in is wayfinding, the same as everywhere else on this site: it
tells the page which site the passkey belongs to so it can show the right
list. It proves nothing to us. Each individual approval is its own ceremony,
bound by the broker to that one device and that one change — so what the
member is agreeing to is "let Raj's phone publish", at the moment they mean
it, rather than "I am signed in" some minutes earlier.

## 2

Above `async function load() {`

Read the list the same way anybody else can: it is a public file.

Nothing here is secret — public keys and the labels people gave their own
devices. Reading it without the broker means this page still shows something
useful when there is no broker configured at all.

## 3

Above `row(device, allowed.length > 1 ? [['Remove', 'device.revoke']] : [])`

The last one that can publish cannot be removed — the broker refuses
it, because a site nobody can change needs staff with a text editor to
rescue. Not offering the button is kinder than offering it and failing.

## 4

Above `el('allowed-note').textContent =`

Deliberately NOT the status line. Every change redraws this list, and
writing here would wipe the confirmation of what the member just did —
replacing "Done." with a note about removal, which reads like a refusal.

## 5

Above `async function decide(action, device) {`

Approve or remove one device.

A ceremony per change, on purpose. Approving a device is the single act that
replaces every future weekly approval, so it is worth the member confirming
that specific thing rather than it riding on a sign-in from minutes ago.

## 6

Above `el('devices-status').textContent = done.detail;`

The broker refusing on its own rules — already approved, or the last
publisher. Its wording is better than anything guessable from here.
