# Identity

Who somebody is, how they prove it, and check-in at the door. There are no accounts or passwords.
Only the broker ([`worker/README.md`](../worker/README.md)) checks proof for FCPM; a check in the
visitor's own browser is wayfinding.

| Mechanism | Proves | Checked by |
|---|---|---|
| Typed email | Nothing; recorded as unconfirmed | Nobody |
| Email claim | The holder received mail at an address | The browser (`site/assets/js/claims.js`), and anything downstream |
| Cloudflare Access | An address, at the edge | Cloudflare |
| Passkey | A device holds a private key | The broker, against `.auth/devices.json` |

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
(`rp_id` in `site/_data/authorize.yml` and `upload.yml`; the broker's `RP_ID` must match). Member sites
on github.io (a public suffix) cannot host a ceremony, so every passkey page is on fcpublicmedia.org.

- The user handle is `v1|owner/repository|<digest>`: the site in clear so a sign-in says which site, a
  per-person digest so a second person's registration does not replace the first's.
- Without a broker URL the page makes its own challenge and returns `verified: false`; it proves
  nothing to anyone.

A site's devices are `.auth/devices.json` in the member's own repository, public:
`credential_id`, `public_key` (SPKI), `algorithm`, `label`, `added`, `may_publish`, and `revoked` once
revoked (records are kept). Listed is not allowed: only `may_publish: true` changes anything.

| Rule | Where enforced |
|---|---|
| A claim with `repo` enrols a device: listed, not publishing | `/bind` |
| The first device on a site with no publisher is trusted | `worker/src/enroll.js` |
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
3. With a broker: request a `device.add` challenge for the new credential, sign it with that passkey
   (proving possession), and `POST /bind` with the claim. The answer says whether the device may
   publish yet.
4. Without a broker, or if delivery fails: show the device record for the member to send to staff.

`/devices/` lists the site's devices (read from raw.githubusercontent) and runs one ceremony per
approval or removal. `/settings/` signs in to find the site, then signs each save separately.

## Check-in

`/check-in/` (`site/check-in.md`, `site/assets/js/checkin.js`, `site/_layouts/pass.html`) is the QR
destination. One tap records a visit in the browser's own storage; nothing is sent anywhere, and
`site/tests/checkin.spec.js` fails if checking in makes a network request.

- The pass is one screen; `#visits` and `#device` are separate views. The device id is a random UUID,
  shown only as a fragment, deleted by "Forget this device".
- The reason comes from the scanned code (`?reason=Class`, limited to `reasons` in
  `site/_data/checkin.yml`) or a running class (`site/assets/js/classes.js`); nobody is asked.
- History keeps `history_limit` (200) visits, exports to JSON, and imports by merging.
- The address on a visit comes from, in order: a claim, Cloudflare Access, a typed address.
- `navigator.storage.persist()` is requested. Safari evicts storage after about seven days without a
  visit unless the site is on the Home Screen, so FCPM receives nothing and history is not durable:
  keep the paper log by the door.

The poster is `/check-in/poster/`. Its QR is a committed SVG encoding `url` in `checkin.yml`;
regenerate with `pip install qrcode && python3 site/bin/make-qr.py` when the URL changes.

### Location

`location` in `site/_data/checkin.yml` sets the venue, `radius_m` (200), `accuracy_slack_m` (100) and
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
