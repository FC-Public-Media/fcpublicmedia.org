# `site/assets/js/authorize.js`

Moved out of the file. Unreviewed.

## 1

Above `import { verifyClaim, claimFromLocation, clearClaimFromLocation } from './claims.js';`

Binding a device to a member site.

The visitor arrives from a signed link that names their repository. This
page checks the signature, makes a passkey, and hands the public half to
the broker — or, when there is no broker yet, shows it to them to send on.

WHY THE REPOSITORY COMES FROM INSIDE THE SIGNATURE
-------------------------------------------------
It would be easier to put it in the URL as a plain parameter. Then anyone
with a link could edit it and bind their device to somebody else's site.
Carrying it inside the signed payload means the link can be forwarded — as
it is meant to be — without being re-aimed.

## 2

Above `async function send(device) {`

Register the device with the broker.

Two things have to travel: the claim, which is the authority to enrol at
all, and a signature from the passkey that was just made, which is proof the
asker actually holds it. The broker re-verifies both itself rather than
trusting this page — the check here is only so a visitor with a bad link
finds out before making a passkey they cannot use.

WHY THERE IS A SECOND PROMPT
----------------------------
Creating the passkey does not prove possession to anybody: that ceremony's
challenge is generated here, and the alternative — having the broker issue
the registration challenge and then parse the attestation object out of
COSE — is a great deal of code to avoid one tap that platforms make cheap.
So the device is made, and then asked to sign something we were given.

Device lists are public on purpose, so anybody can read a key out of one.
This is what stops somebody enrolling a key they copied.

## 3

Above `status.textContent = 'Your browser blocked copying — select the text below instead.';`

Clipboard access is blocked in plenty of ordinary situations, and the
text is on screen anyway.

## 4

Above `el('copy-status').textContent = We couldn't send it automatically (${error.message}).;`

The passkey exists at this point — it is on the device and cannot be
un-made from here. So this is a delivery failure, and the useful thing
is to fall back to handing the record over rather than to report a
failure that would make someone try the whole thing again.

## 5

Above `el('done-detail').textContent = registered.may_publish`

The broker decides which of these is true, not this page: the first device
on a site is trusted because there is nobody to approve it, and every one
after arrives listed and waiting. Getting that backwards would either
strand the owner or tell a co-producer they can publish when they cannot.

## 6

Above `window.addEventListener('hashchange', () => {`

Opening a second link in a tab that already has this page loaded changes
only the fragment, which is not a navigation — without this, the page
would sit there still showing the first link's site.

## 7

Above `clearClaimFromLocation();`

Taken out of the address bar either way. It is a capability, and a URL
still carrying one is a URL someone might paste into a group chat.

## 8

Above `if (!result.payload.repo) {`

A claim with no repository is the check-in kind. Sending someone through a
passkey ceremony for a site they were not invited to would leave them with
a credential authorizing nothing.
