# Identity

Who somebody is, how they prove it, and check-in at the door. There are no accounts or passwords.
Only the site-worker ([FC-Public-Media/site-worker](https://github.com/FC-Public-Media/site-worker)) checks proof for FCPM; a check in the
visitor's own browser is wayfinding.

| Mechanism | Proves | Checked by |
|---|---|---|
| Typed email | Nothing; recorded as unconfirmed | Nobody |
| Email claim | The holder received mail at an address | The browser (`site/assets/js/claims.js`), and anything downstream |
| Cloudflare Access | An address, at the edge | Cloudflare |
| Passkey | A device holds a private key | The site-worker, against `.auth/devices.json` |

## Email claims

Staff prove an address to the visitor and let them keep the proof.

```
python3 site/bin/mint-claim.py --new-key claim-key.pem   # once; prints the block for identity.yml
python3 site/bin/mint-claim.py --email someone@example.com [--repo owner/site] [--days N]
```

- The token is `v1.<payload>.<signature>`: base64url JSON (`email`, `iat`, `exp`, `kid`, optional
  `repo`) signed ECDSA P-256 over `v1.<payload>` by openssl.
- The link is `/check-in/#claim=…`, or `/authorize/#claim=…` with `--repo`. In the fragment, it reaches
  no server log. Staff paste it into an email themselves.
- Public keys are the `keys` list in `site/_data/identity.yml` (a list so a key can rotate without
  breaking links in inboxes); the private key stays out of git (`*-key.pem` is ignored).
- The page stores the whole token, so anything downstream re-verifies the signature rather than
  trusting a flag the device set. Imports from a backup are re-verified too.
- No revocation: a claim lasts `days` (120) or until its key leaves the list, which voids every claim
  it signed. A claim is not a login; gate nothing on it you would leave on a clipboard by the door.
- With `keys: []` (shipped), the page offers a typed address, recorded as unconfirmed.

## Passkeys and devices

`site/assets/js/passkey.js` makes and uses passkeys. The relying party is the registrable domain
(`rp_id` in `site/_data/authorize.yml` and `upload.yml`; the site-worker's `RP_ID` must match). Member sites
on github.io (a public suffix) cannot host a ceremony, so every passkey page is on fcpublicmedia.org.

- The user handle is `v1|owner/repository|<digest>`: the site in clear so a sign-in says which site, a
  per-person digest so a second person's registration does not replace the first's.
- Without a site-worker URL the page makes its own challenge and returns `verified: false`; it proves
  nothing to anyone.

A site's devices are `.auth/devices.json` in the member's own repository, public:
`credential_id`, `public_key` (SPKI), `algorithm`, `label`, `added`, `may_publish`, and `revoked` once
revoked (records are kept). Listed is not allowed: only `may_publish: true` changes anything.

| Rule | Where enforced |
|---|---|
| A claim with `repo` enrols a device: listed, not publishing | `/bind` |
| The first device on a site with no publisher is trusted | the site-worker's `src/enroll.js` |
| A publishing device approves or revokes others | `/device`, from `/devices/` |
| A device cannot approve itself | `authorize()` checks `may_publish` first |
| The last publishing device cannot be revoked | `revokeDevice()` |

A `--repo` claim link is forwardable on purpose and gets the holder only listed. Mint them with a
short `--days`. Restoring a site with no publisher means staff editing the file by hand.

## Authorize

`/authorize/` (`site/assets/js/authorize.js`) binds a device to a member site:

1. Read the claim from the fragment, check its signature, and strip it from the address bar. A claim
   without `repo` (the check-in kind) is refused before any ceremony.
2. Create a passkey labelled by the visitor.
3. With a site-worker: request a `device.add` challenge for the new credential, sign it with that passkey
   (proving possession), and `POST /bind` with the claim. The answer says whether the device may
   publish yet.
4. Without a site-worker, or if delivery fails: show the device record for the member to send to staff.

`/devices/` lists the site's devices (read from raw.githubusercontent) and runs one ceremony per
approval or removal. `/settings/` signs in to find the site, then signs each save separately.

## Check-in

`/check-in/` (`site/check-in.md`, `site/assets/js/checkin.js`, `site/_layouts/pass.html`) is the QR
destination. One tap records a visit in the browser's own storage; nothing is sent anywhere, and
`site/tests/checkin.spec.js` fails if checking in makes a network request.

The plain code (the poster, the homepage, a kiosk) only opens the page. The page is a wizard,
`wizard:kiosk+checkin`: each visit keeps a reply (`fcpm.reply/v0`: name, email, reason, `issued`, a
nonce, `at` = the commit the site was built from), made once at the tap and never changed. `#show`
pours it for our camera whenever the visitor likes (tonight at home, in the line, next week within a
day of `issued`) as a bottle: signed with the browser's own Ed25519 key and drawn as AC1 fountain
frames by `site/assets/js/bottle.js` and the vendored composer (`site/assets/js/composer/`). The
visitor's camera opened a page; our camera reads what the page made. The door's intake applies it as one
visit (`replies.py`, `visits.ndjson`), timed when it was read; showing it again is the same nonce and is
held. See docs/kiosk.md#replies.

- The pass is one screen; `#visits`, `#device` and `#show` are separate views. Any visit in the list opens
  `#show` with it. The device id is a random UUID, shown only as a fragment, deleted by "Forget this
  device" (with the signing key).
- The reason comes from the scanned code (`?reason=Class`, limited to `reasons` in
  `site/_data/checkin.yml`) or a running class (`site/assets/js/classes.js`); nobody is asked.
- History keeps `history_limit` (200) visits, exports to JSON, and imports by merging.
- The address on a visit comes from, in order: a claim, Cloudflare Access, a typed address.
- `navigator.storage.persist()` is requested. Safari evicts storage after about seven days without a
  visit unless the site is on the Home Screen, so FCPM receives nothing and history is not durable:
  keep the paper log by the door.

The poster is `/check-in/poster/`. Its QR is a committed SVG encoding `url` in `checkin.yml`;
regenerate with `pip install qrcode && python3 site/bin/make-qr.py` when the URL changes.

## Yours

`/you/` (`site/you/index.md`, `site/assets/js/yours.js`) is what a device keeps for its person. Nothing on it
is sent unless they say so.

- **Lock it in.** Every form keeps its reply on the device before it sends anything (`site/assets/js/keep.js`,
  called by `answers.js`, `join.js` and `book.js`): `fcpm.replies`, newest first, up to 200. The reply is
  `wizard:site+answers` (`fcpm.reply/v0`: `tank`, the `reference` the tank and Stripe also get, `answers`,
  `issued`, a nonce, `at` = the commit the page was built from, from `<meta name="fcpm-revision">`), kept as
  text beside the labelled `lines`, the tank POST exactly as it goes, the email link, and `sent`.
- **Sending is separate,** by any way out: the tank, our camera (Show it pours the same reply as a bottle,
  as the check-in does), or the email link. A send that fails loses nothing; the form says it is kept, and
  `/you/` offers *Send it* (the same POST, same reference) and *Email it* until it has gone.
- **A record, not the form.** `/you/#reply-<reference>` reads the reply back from its `lines`. Replies are never
  edited: their bytes are what we verify. A change will be a new reply that names the one it replaces.
- **Contact cards** (`fcpm.cards`): name, email and phone are noticed in any form, by the standard
  `autocomplete` tokens (`name`, `given-name`/`family-name`, `email`, `tel`), and by the check-in. The same email
  or phone is the same card, brought up to date; anything else is another card. Never refused, removable,
  and never used to fill a form in (the check-in's own pass, and the reservation request reading it, aside).

### Location

Off (`location.required: false`): showing the reply to our camera is the proof of arrival, and a check-in
made somewhere else first is a good one. Turned on, `location` in `site/_data/checkin.yml` sets the venue, `radius_m` (200), `accuracy_slack_m` (100) and
`recheck_seconds` (300). A reading counts when `distance - accuracy` is inside the radius, with accuracy
credited up to the slack. Out of range, the check-in is held as pending with distance and directions,
survives a reload, and completes on arrival. Re-checks run only while the tab is visible and reuse a
cached fix; a tap asks for a fresh one. Only the distance and a `verified` flag are stored, never
coordinates.

### Cloudflare Access

Set `identity.mode: access` in `checkin.yml` after adding a Zero Trust Access application on
`/check-in/sign-in/` (a sub-path, so `/check-in/` stays public) that allows emails ending in `@`. The
page then reads `/cdn-cgi/access/get-identity`; while the route is unprotected that call fails and the
check-in is anonymous. The free plan has 50 seats, one per person who ever signs in, so Access suits
staff and board; members use claims. Shipped `mode` is `none`.
