# `site/assets/js/lights.js`

Moved out of the file. Unreviewed.

## 1

Above `import { encodeQR } from "./qr-encode.mjs";`

lights.js — the lights reply, as a code to hold up to the kiosk's camera
(site/lights.md). A person in the studio off host hours says "I'm here,
keep the screens awake until X". The kiosk reads it with anecdote.channel's
qr-decode; this draws it with the same project's qr-encode, so the two
cannot disagree.

The reply is compact JSON, byte mode, ECC M, one frame: every byte shrinks
the squares, and the camera needs about 3 pixels a module. No personal data.
`sig` is null: the control case, accepted for lights only. A passkey
assertion takes its place later (the challenge is the sha256 of the
canonical reply minus `sig`); nothing here assumes it stays null.

## 2

Above `const box = canvas.parentElement.getBoundingClientRect();`

As large as the box allows, at a whole number of device pixels a module,
so every edge is crisp.
