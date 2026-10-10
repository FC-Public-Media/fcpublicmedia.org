# `site/tests/devices.spec.js`

Moved out of the file. Unreviewed.

## 1

Above `const { test, expect } = require('@playwright/test');`

Approving a co-producer's phone.

This page is where "approve once, publish every week" stops being a design
note and becomes something a person does. The behaviour worth pinning is not
that buttons exist — it is which ones do NOT, and what each refusal says,
because those are the parts that decide whether somebody ends up phoning
staff after all.

GitHub and the broker are both stubbed. The tests are about what the page
does with an answer.

## 2

Above `async function signedIn(page, { devices, broker = null, decision } = {}) {`

Sign in with a real passkey, holding a device list of our choosing.

`devices` is what the member's repository says. The passkey the browser
makes is not any of them — the page never checks that the signed-in
credential is in the list, because the broker is what enforces that, so the
list is free to describe whatever situation is being tested.

## 3

Above `await signedIn(page, { devices: [owner()] });`

The broker refuses this write — a site nobody can change needs staff
with a text editor to rescue. A button that fails is worse than no
button, so it is not offered and the reason is on screen.

## 4

Above `await signedIn(page, {`

Different advice: one means "wait for somebody", the other means
"something is broken".

## 5

Above `const seen = await signedIn(page, {`

The whole reason a per-change ceremony exists: the member is agreeing to
"let Raj's phone publish", not to "I am signed in".
