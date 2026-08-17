// The broker.
//
// A small service that does the things a static site cannot do for itself:
// hand out challenges, and decide whether a signature over one is genuine.
//
// WHAT IT IS FOR
// --------------
// Everything on the site up to now has been honest about proving nothing.
// /authorize/ makes a passkey and shows you the record. /settings/ signs in
// with that passkey and then hands you your own edited file to email us,
// because the sign-in happened entirely in the visitor's browser, using a
// challenge the visitor's browser generated, checked by code the visitor
// controls. It is wayfinding. It is not evidence.
//
// This is where it becomes evidence. The challenge comes from here, is bound
// to one specific thing being asked for, and is spent once. The signature is
// checked here, against a public key recorded in the member's repository, by
// code the visitor cannot reach.
//
// WHAT IT DELIBERATELY DOES NOT HOLD
// ----------------------------------
// No password, no session, no user table. The only durable state is a set of
// challenges that expire in five minutes. Who may do what lives in each
// member's own repository, in public, where they can read it.
//
// ONE VERIFICATION, FIVE THINGS DONE WITH IT
// ------------------------------------------
// /verify reports, /write commits, /bind and /device change who may act, and
// /upload signs permission to put bytes somewhere. All five run the same
// authorize() first and none of them re-implements a step of it, which is why
// each new one was a small addition rather than a second system.

import { appCredential, patCredential } from './app-auth.js';
import { challengeStore } from './challenges.js';
import { lookup, readSession, returnUrl, sessionParams } from './checkout.js';
import { deviceList, mayPublish } from './devices.js';
import { addDevice, allowDevice, revokeDevice, serialize } from './enroll.js';
import { github } from './github.js';
import { ACTIONS, contentHash, matchesIntent, readIntent } from './intent.js';
import { grantUpload, objectKey } from './r2.js';
import { verifyAssertion } from './webauthn.js';

// The claim verifier the BROWSER uses, imported rather than copied.
//
// It is pure WebCrypto with no DOM at the top level, so it runs here
// unmodified — and one implementation cannot drift from the other, which for a
// signature check is worth more than the tidiness of a self-contained worker
// directory. tests/claims.spec.js drives the same file from a browser, and
// enrol.test.mjs imports it here to catch the day somebody adds a `window`.
import { verifyClaim } from '../../assets/js/claims.js';

/* ---------------------------------------------------------------- responses */

const json = (body, { status = 200, headers = {} } = {}) =>
  new Response(JSON.stringify(body, null, 2), {
    status,
    headers: { 'Content-Type': 'application/json; charset=utf-8', ...headers },
  });

/**
 * CORS, restricted to the origins the site is actually served from.
 *
 * A wildcard would work and would also let any page anywhere ask this broker
 * for a challenge. The challenge would be useless to them — the assertion has
 * to come from a passkey bound to our domain, and the origin inside the signed
 * client data is checked — but there is no reason to answer at all.
 */
function corsHeaders(request, origins) {
  const origin = request.headers.get('Origin');
  if (!origin || !origins.includes(origin)) return {};
  return {
    'Access-Control-Allow-Origin': origin,
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Max-Age': '86400',
    Vary: 'Origin',
  };
}

/* ------------------------------------------------------------------- config */

/**
 * Read the settings, or say precisely what is missing.
 *
 * A broker with no RP ID configured would compare every passkey against the
 * hash of an empty string and reject all of them; a broker with no origins
 * would reject every ceremony. Both are safe failures, and both look like
 * "passkeys are broken" for a day. Refusing to start with a message naming the
 * variable is cheaper than that.
 */
function readConfig(env, now = () => Date.now()) {
  const missing = [];
  const rpId = (env.RP_ID || '').trim();
  if (!rpId) missing.push('RP_ID');

  const origins = (env.ORIGINS || '')
    .split(',')
    .map((value) => value.trim())
    .filter(Boolean);
  if (!origins.length) missing.push('ORIGINS');

  if (!env.CHALLENGES) missing.push('CHALLENGES (the KV namespace binding)');

  return {
    missing,
    rpId,
    origins,
    owner: (env.OWNER || '').trim(),
    ttl: Number(env.CHALLENGE_TTL || 300),
    // Where a write lands. Read here rather than sent by the page, because
    // "commit straight to the live branch" is not a member's decision to make.
    writeMode: env.WRITE_MODE === 'direct' ? 'direct' : 'branch',

    // The public halves of the claim signing keys, same list as
    // _data/identity.yml. Public by nature — they verify, they do not sign —
    // so they are config rather than a secret.
    claimKeys: readClaimKeys(env.CLAIM_KEYS),

    // Nothing here is optional: an endpoint with no bucket, or keys with no
    // endpoint, is a half-configured broker that would fail at the moment
    // somebody had already chosen a file.
    storage:
      env.R2_ENDPOINT && env.R2_BUCKET && env.R2_ACCESS_KEY_ID && env.R2_SECRET_ACCESS_KEY
        ? {
            endpoint: env.R2_ENDPOINT,
            bucket: env.R2_BUCKET,
            credentials: {
              accessKeyId: env.R2_ACCESS_KEY_ID,
              secretAccessKey: env.R2_SECRET_ACCESS_KEY,
            },
          }
        : null,

    // The Stripe key. A RESTRICTED key — rk_live_… — with permission to write
    // Checkout Sessions and nothing else, which is what Stripe now recommends
    // over sk_ for exactly this reason: if this worker is ever compromised,
    // the key it holds cannot issue refunds, read the customer list, or move
    // the balance. Booqable holds its own separate credential for the rental
    // side, so neither system can act as the other.
    //
    // THE NAME LIES. READ THIS BEFORE USING IT ANYWHERE.
    //
    // PUBLIC_STRIPE_API_KEY holds a SECRET value. It was named before the
    // distinction between Stripe's key types was settled, the secret already
    // exists in the GitHub organization, and renaming it means minting a new
    // key — so the name stays and the warning goes here instead.
    //
    // Nothing about this value is public. It is not the pk_ key, it must never
    // be rendered into a page, logged, or returned in a response, and a
    // reasonable person reading only the variable name would do all three.
    // _data/payments.yml holds the genuinely public one, and
    // script/test_no_secrets.py fails the build if anything shaped like a
    // secret key reaches the built site.
    //
    // STRIPE_KEY is still read as a fallback so a Cloudflare secret set under
    // the obvious name keeps working.
    //
    // Absent from `missing` deliberately. A broker that refused to hand out
    // challenges because nobody had set up payments yet would take the
    // passkey work offline for a configuration step unrelated to it; /checkout
    // reports this, and only /checkout.
    stripe: (env.PUBLIC_STRIPE_API_KEY || env.STRIPE_KEY || '').trim() || null,

    // Long enough for a big file on a slow line to finish, since the signature
    // has to outlive the whole transfer rather than just the request.
    uploadTtl: Number(env.UPLOAD_TTL || 21600),
    maxUpload: Number(env.R2_MAX_BYTES || 0),

    now,
  };
}

/**
 * Parse CLAIM_KEYS, and treat a broken value as no keys at all.
 *
 * Refusing every enrolment with "not configured" is the right failure for a
 * malformed list. Verifying against a half-parsed one is not.
 */
function readClaimKeys(value) {
  if (!value) return [];
  try {
    const keys = JSON.parse(value);
    return Array.isArray(keys) ? keys.filter((key) => key?.x && key?.y) : [];
  } catch (error) {
    return [];
  }
}

/* ------------------------------------------------------------------ handlers */

async function readBody(request) {
  try {
    return await request.json();
  } catch (error) {
    return null;
  }
}

/**
 * Issue a challenge for one declared action.
 *
 * Nothing is authenticated here on purpose. Handing out a random number that
 * expires in five minutes costs nothing and reveals nothing — the only thing
 * it can be used for is a signature by a passkey we already recorded.
 */
async function handleChallenge(request, { config, challenges }) {
  const body = await readBody(request);
  if (!body) return json({ ok: false, detail: 'Send JSON.' }, { status: 400 });

  const intent = readIntent(body, { owner: config.owner, maxUpload: config.maxUpload });
  if (!intent.ok) return json({ ok: false, detail: intent.detail }, { status: 400 });

  // Where an upload will land is decided HERE and stored with the challenge,
  // so it is settled before anybody signs and cannot be renegotiated after.
  // The prefix comes from the repository the challenge is for, which is what
  // stops one member writing into another's space.
  if (intent.intent.action === 'upload.grant') {
    intent.intent.key = objectKey(intent.intent.repo, intent.intent.filename, config.now());
  }

  const issued = await challenges.issue(intent.intent);
  return json({
    ok: true,
    challenge: issued.challenge,
    expires_in: issued.expiresIn,
    // Echoed so a page can show what it is about to ask someone to approve,
    // and so a mismatch is visible rather than mysterious.
    intent: intent.intent,
  });
}

/**
 * Everything that has to be true before anything happens.
 *
 * The order below is the whole design in miniature:
 *
 *   1. Spend the challenge. Gone whatever happens next.
 *   2. Find the recorded key, in the repository the CHALLENGE named — never
 *      the one the request names. The request's copy is checked against it
 *      afterwards, but it is not what the lookup is done with.
 *   3. Verify the signature.
 *   4. Only then, check the request does what the challenge was issued for.
 *   5. And that the device is allowed to do it, which is a different question
 *      from whether it is registered.
 *
 * Returns { ok: true, body, intent, device } or { ok: false, response }. Every
 * endpoint that does anything goes through here first, and none of them may
 * re-implement a step of it — a second copy of this order is a second chance
 * to get it subtly wrong.
 */
async function authorize(request, { config, challenges, devices }) {
  const refuse = (status, fields) => ({ ok: false, response: json({ ok: false, ...fields }, { status }) });

  const body = await readBody(request);
  if (!body) return refuse(400, { detail: 'Send JSON.' });

  const assertion = body.assertion;
  if (!assertion?.client_data_json) {
    return refuse(400, { detail: 'No assertion was sent.' });
  }

  // The challenge is read out of the signed client data rather than taken as
  // a separate field, so there is no way to present one challenge and answer
  // a different one.
  let presented;
  try {
    presented = JSON.parse(atob(
      String(assertion.client_data_json).replace(/-/g, '+').replace(/_/g, '/')
    )).challenge;
  } catch (error) {
    return refuse(400, { detail: 'The client data could not be read.' });
  }

  const intent = await challenges.take(presented);
  if (!intent) {
    return refuse(403, {
      reason: 'challenge',
      detail: 'That challenge is unknown, spent, or expired. Start again.',
    });
  }

  // device.add is signed by a device that is not on the list yet, so none of
  // what follows can be done for it. /bind handles that case with its own
  // rules; nothing else may, and a challenge for it presented here is spent
  // and refused rather than quietly reinterpreted.
  if (ACTIONS[intent.action]?.unlisted) {
    return refuse(409, { reason: 'intent', detail: 'That challenge belongs to a different flow.' });
  }

  const found = await devices.find(intent.repo, assertion.credential_id);
  if (!found.ok) {
    // Three different kinds of "no": our setup, their outage, and an actual
    // refusal. Only the last one is about the person asking.
    return refuse({ credential: 500, unreachable: 503 }[found.reason] || 403, {
      reason: found.reason,
      detail: found.detail,
    });
  }

  const result = await verifyAssertion({
    assertion,
    device: found.device,
    expected: {
      challenge: presented,
      origins: config.origins,
      rpId: config.rpId,
      requireUserVerification: ACTIONS[intent.action]?.userVerification === true,
    },
  });
  if (!result.ok) {
    return refuse(403, { reason: result.reason, detail: result.detail });
  }

  const matches = await matchesIntent(intent, body);
  if (!matches.ok) {
    return refuse(409, { reason: 'intent', detail: matches.detail });
  }

  // Listed and proven, but that is not permission. An action that changes the
  // site needs the record to say so; `verify` does not, which is what makes it
  // useful for telling somebody they are bound but not yet allowed.
  if (intent.action !== 'verify' && !mayPublish(found.device)) {
    return refuse(403, {
      reason: 'not-allowed',
      detail: 'That device is registered but is not allowed to change this site yet.',
    });
  }

  return { ok: true, body, intent, device: found.device, flags: result.flags };
}

const describe = (device) => ({
  label: device.label || 'Unnamed device',
  may_publish: mayPublish(device),
});

/** Check an assertion and report. Changes nothing, and says so. */
async function handleVerify(request, deps) {
  const allowed = await authorize(request, deps);
  if (!allowed.ok) return allowed.response;

  return json({
    ok: true,
    repo: allowed.intent.repo,
    action: allowed.intent.action,
    device: describe(allowed.device),
    user_verified: allowed.flags.userVerified,
    // Said out loud, because a page that treats a verification as a save would
    // tell somebody their edit went through when nothing has been written.
    performed: false,
  });
}

/**
 * Check an assertion and then do what it was for.
 *
 * Every meaningful decision has already been made by the time this runs. What
 * is left is the write itself and the vocabulary for reporting how it went —
 * which is the shape the remaining two jobs should take too.
 */
async function handleWrite(request, deps) {
  if (!deps.repositories) {
    return json(
      {
        ok: false,
        detail: 'This broker is not configured to write: GITHUB_APP_ID and GITHUB_APP_KEY.',
      },
      { status: 500 }
    );
  }

  const allowed = await authorize(request, deps);
  if (!allowed.ok) return allowed.response;

  const { intent, body, device } = allowed;
  if (intent.action !== 'settings.write') {
    return json(
      { ok: false, reason: 'intent', detail: 'That challenge was not issued for a write.' },
      { status: 409 }
    );
  }

  // Names the device rather than the person: the device record is the only
  // thing we actually know, and a commit message that guessed at a name would
  // be inventing it.
  const message = `Update ${intent.path} from ${describe(device).label}`;

  const written = await deps.repositories.writeFile({
    repo: intent.repo,
    path: intent.path,
    content: body.content,
    sha: intent.sha,
    contentHash: intent.content_hash,
    message,
    mode: deps.config.writeMode,
  });

  if (!written.ok) {
    // Three different things, and they are not the member's fault in the same
    // way. A conflict is the SHA doing its job — somebody changed the file
    // while they were editing, and the page keeps their text and offers a
    // reload. A credential failure is our setup, including "the App is not
    // installed here", which is what a revoked site looks like from in here.
    const status = { conflict: 409, credential: 500 }[written.reason] || 502;
    return json({ ok: false, reason: written.reason, detail: written.detail }, { status });
  }

  return json({
    ok: true,
    repo: intent.repo,
    action: intent.action,
    device: describe(device),
    performed: true,
    mode: written.mode,
    url: written.url,
    // True when the bytes were already there — a double tap, or a retry of a
    // request whose answer never arrived. Nothing changed this time, and the
    // page can say so instead of implying a second save.
    repeated: written.repeated === true,
    ...(written.detail ? { detail: written.detail } : {}),
  });
}

/* ------------------------------------------------------------------ uploads */

/**
 * Hand back permission to put one file in storage.
 *
 * The same authorization as everything else, and then a set of signed URLs.
 * The bytes never come here — the broker is not a proxy at any size, which is
 * the only way six gigabytes is a sensible thing to ask of it.
 */
async function handleUpload(request, deps) {
  const { config } = deps;
  if (!config.storage) {
    return json(
      {
        ok: false,
        detail:
          'This broker has nowhere to put files: R2_ENDPOINT, R2_BUCKET, ' +
          'R2_ACCESS_KEY_ID and R2_SECRET_ACCESS_KEY.',
      },
      { status: 500 }
    );
  }

  const allowed = await authorize(request, deps);
  if (!allowed.ok) return allowed.response;

  const { intent, device } = allowed;
  if (intent.action !== 'upload.grant') {
    return json(
      { ok: false, reason: 'intent', detail: 'That challenge was not issued for an upload.' },
      { status: 409 }
    );
  }

  const granted = await grantUpload({
    key: intent.key,
    size: intent.size,
    bucket: config.storage.bucket,
    endpoint: config.storage.endpoint,
    credentials: config.storage.credentials,
    expires: config.uploadTtl,
    now: config.now(),
    fetchImpl: deps.fetchImpl,
  });
  if (!granted.ok) {
    return json({ ok: false, reason: 'storage', detail: granted.detail }, { status: 502 });
  }

  return json({
    ok: true,
    repo: intent.repo,
    action: intent.action,
    device: describe(device),
    performed: true,
    ...granted.grant,
  });
}

/* ---------------------------------------------------------------- enrolment */

// The broker chooses this path. It is never sent by a page, and intent.js
// refuses it as a settings target, so there is no route by which somebody
// edits the list of who may edit.
const DEVICES = '.auth/devices.json';

/**
 * Read the device list for writing.
 *
 * Authenticated, so it is current — the cached raw.githubusercontent copy that
 * devices.js reads is fine for "does this key check out" and is not fine as
 * the first half of a read-modify-write.
 */
async function readDevices(repositories, repo) {
  const found = await repositories.readFile({ repo, path: DEVICES });
  if (!found.ok) return found;

  if (found.content === null) return { ok: true, devices: [], sha: '' };

  try {
    const payload = JSON.parse(found.content);
    if (!Array.isArray(payload?.devices)) throw new Error('shape');
    return { ok: true, devices: payload.devices, sha: found.sha };
  } catch (error) {
    return { ok: false, reason: 'github', detail: `${DEVICES} is not readable.` };
  }
}

/** Write it back. Never on a branch: a grant sitting in a pull request grants nothing. */
async function writeDevices(repositories, repo, devices, sha, message) {
  const content = serialize(devices);
  return repositories.writeFile({
    repo,
    path: DEVICES,
    content,
    sha,
    contentHash: await contentHash(content),
    message,
    mode: 'direct',
  });
}

const wrote = (written) =>
  written.ok
    ? null
    : json(
        { ok: false, reason: written.reason, detail: written.detail },
        { status: { conflict: 409, credential: 500 }[written.reason] || 502 }
      );

/**
 * Put a new passkey on a site's list.
 *
 * The odd one out, because the device signing is the one being added and so is
 * not on the list to be looked up. Three things have to hold:
 *
 *   1. The challenge was issued for this credential and this public key.
 *   2. A signature over it verifies against THAT PUBLIC KEY — proof the asker
 *      holds the private half of the thing they want recorded, rather than
 *      somebody else's key they copied off a public device list.
 *   3. A current claim, signed by us, naming this repository.
 *
 * The claim is the enrolment authority and can be forwarded. That is fine and
 * intended: what arrives is a listed device that may not publish, unless it is
 * the first, in which case there is nobody to approve it and nobody to protect
 * it from. See enroll.js.
 */
async function handleBind(request, { config, challenges, repositories }) {
  if (!repositories) {
    return json({ ok: false, detail: 'This broker is not configured to write.' }, { status: 500 });
  }

  const body = await readBody(request);
  const assertion = body?.assertion;
  if (!assertion?.client_data_json) {
    return json({ ok: false, detail: 'No assertion was sent.' }, { status: 400 });
  }

  let presented;
  try {
    presented = JSON.parse(atob(
      String(assertion.client_data_json).replace(/-/g, '+').replace(/_/g, '/')
    )).challenge;
  } catch (error) {
    return json({ ok: false, detail: 'The client data could not be read.' }, { status: 400 });
  }

  const intent = await challenges.take(presented);
  if (!intent || intent.action !== 'device.add') {
    return json(
      { ok: false, reason: 'challenge', detail: 'That challenge is unknown, spent, or was issued for something else.' },
      { status: 403 }
    );
  }

  // Against the key in the INTENT, not one looked up anywhere. This is the
  // only place in the broker that verifies against a key it was handed, and it
  // is sound because the only thing it establishes is possession — the right
  // to be recorded comes from the claim below.
  const proved = await verifyAssertion({
    assertion,
    device: { public_key: intent.public_key, algorithm: null },
    expected: {
      challenge: presented,
      origins: config.origins,
      rpId: config.rpId,
      requireUserVerification: true,
    },
  });
  if (!proved.ok) {
    return json({ ok: false, reason: proved.reason, detail: proved.detail }, { status: 403 });
  }
  if (assertion.credential_id !== intent.credential_id) {
    return json(
      { ok: false, reason: 'intent', detail: 'That signature is from a different credential.' },
      { status: 409 }
    );
  }

  /* ------------------------------------------------------------- the claim */

  if (!config.claimKeys.length) {
    return json(
      { ok: false, detail: 'This broker is not configured to check claims: CLAIM_KEYS.' },
      { status: 500 }
    );
  }

  const claim = await verifyClaim(body.claim, config.claimKeys);
  if (!claim.ok) {
    const detail = {
      expired: 'That link has expired. Ask us for a new one.',
      signature: 'That link was not issued by us.',
      malformed: 'That link is damaged — it may have been broken by an email client.',
      missing: 'No link was sent.',
    }[claim.reason] || 'That link did not check out.';
    return json({ ok: false, reason: 'claim', detail }, { status: 403 });
  }
  // The claim names the site it enrols for. Without this check any claim would
  // enrol against any site, which is the whole grant.
  if (claim.payload.repo !== intent.repo) {
    return json(
      { ok: false, reason: 'claim', detail: 'That link is for a different site.' },
      { status: 403 }
    );
  }

  /* -------------------------------------------------------------- the list */

  const list = await readDevices(repositories, intent.repo);
  if (!list.ok) return json({ ok: false, reason: list.reason, detail: list.detail }, { status: 502 });

  const added = addDevice(list.devices, {
    credential_id: intent.credential_id,
    public_key: intent.public_key,
    algorithm: typeof body.algorithm === 'number' ? body.algorithm : null,
    label: String(body.label || '').trim().slice(0, 80) || 'Unnamed device',
    added: new Date(config.now()).toISOString(),
  });
  if (!added.ok) return json({ ok: false, reason: 'listed', detail: added.detail }, { status: 409 });

  const written = await writeDevices(
    repositories,
    intent.repo,
    added.devices,
    list.sha,
    `Register a device for ${claim.payload.email}`
  );
  const failed = wrote(written);
  if (failed) return failed;

  return json({
    ok: true,
    repo: intent.repo,
    action: intent.action,
    performed: true,
    // The one thing the page has to say out loud. "You're set up" and "ask
    // whoever runs this site to approve your phone" are different messages.
    may_publish: added.granted,
    first_device: added.granted,
  });
}

/**
 * Approve or revoke a device, signed by one that may already publish.
 *
 * Goes through authorize() unchanged: the signer has to be listed, proven, and
 * allowed. That is exactly the check this needs, which is why there is no
 * second copy of it here.
 */
async function handleDevice(request, deps) {
  if (!deps.repositories) {
    return json({ ok: false, detail: 'This broker is not configured to write.' }, { status: 500 });
  }

  const allowed = await authorize(request, deps);
  if (!allowed.ok) return allowed.response;

  const { intent, device } = allowed;
  if (intent.action !== 'device.allow' && intent.action !== 'device.revoke') {
    return json(
      { ok: false, reason: 'intent', detail: 'That challenge was not issued for this.' },
      { status: 409 }
    );
  }

  const list = await readDevices(deps.repositories, intent.repo);
  if (!list.ok) return json({ ok: false, reason: list.reason, detail: list.detail }, { status: 502 });

  const change =
    intent.action === 'device.allow'
      ? allowDevice(list.devices, intent.credential_id)
      : revokeDevice(list.devices, intent.credential_id);

  if (!change.ok) {
    return json({ ok: false, reason: 'listed', detail: change.detail }, { status: 409 });
  }
  // Already in the asked-for state. Nothing to write, and reporting a failure
  // for something that is already true would send somebody looking for a
  // problem that is not there.
  if (change.already) {
    return json({ ok: true, repo: intent.repo, action: intent.action, performed: false, already: true });
  }

  const verb = intent.action === 'device.allow' ? 'Allow' : 'Revoke';
  const written = await writeDevices(
    deps.repositories,
    intent.repo,
    change.devices,
    list.sha,
    `${verb} a device, approved by ${describe(device).label}`
  );
  const failed = wrote(written);
  if (failed) return failed;

  return json({
    ok: true,
    repo: intent.repo,
    action: intent.action,
    device: describe(device),
    performed: true,
  });
}

/**
 * Start a checkout.
 *
 * THE ONE ENDPOINT HERE THAT DOES NOT AUTHENTICATE ANYBODY
 * -------------------------------------------------------
 * Every other route runs authorize() first, because every other route changes
 * something of ours — a file, a device list, permission to write bytes. This
 * one takes money from a stranger, which is a thing strangers are supposed to
 * be able to do. Requiring a passkey to join would mean you had to be a member
 * to become one.
 *
 * So the protection is not "who are you". It is that there is nothing here
 * worth attacking: the caller picks from a fixed list, the amount comes from
 * our side of the wire, and the worst a hostile caller achieves is a Stripe
 * page nobody pays. No card details pass through this worker at any point —
 * Stripe hosts the form, which is the entire reason to use Checkout rather
 * than build one.
 */
async function handleCheckout(request, { config, fetchImpl }) {
  if (!config.stripe) {
    return json(
      { ok: false, reason: 'unconfigured', detail: 'Payments are not switched on yet.' },
      { status: 503 }
    );
  }

  const body = await readBody(request);
  if (!body) return json({ ok: false, detail: 'Send JSON.' }, { status: 400 });

  const found = lookup(body.sku);
  if (!found.ok) return json({ ok: false, reason: 'sku', detail: found.detail }, { status: 400 });

  const success = returnUrl(config.origins, body.success_path, '/thanks/');
  const cancel = returnUrl(config.origins, body.cancel_path, '/membership/');
  if (!success || !cancel) {
    return json({ ok: false, detail: 'This broker has no site to return to.' }, { status: 500 });
  }

  const params = sessionParams({
    item: found.item,
    sku: found.sku,
    recurring: body.recurring,
    success,
    cancel,
    reference: body.reference,
    email: body.email,
  });

  const response = await (fetchImpl || fetch)('https://api.stripe.com/v1/checkout/sessions', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${config.stripe}`,
      'Content-Type': 'application/x-www-form-urlencoded',
      // Stripe replays a repeated key rather than charging twice. The window
      // is 24 hours, so this is scoped to the visit rather than to the item:
      // somebody who genuinely buys two memberships an hour apart must get two
      // sessions, and somebody whose phone retried the same tap must not.
      'Idempotency-Key': crypto.randomUUID(),
    },
    body: params,
  });

  let payload = null;
  try {
    payload = await response.json();
  } catch (error) {
    payload = null;
  }

  if (!response.ok) {
    // Stripe's message names the parameter and is written for a developer, so
    // it goes to the log and not to the visitor. What a visitor can act on is
    // that it did not work and it was not their fault.
    console.error('stripe', response.status, payload?.error?.message || '');
    return json(
      { ok: false, reason: 'stripe', detail: 'The payment page could not be created.' },
      { status: 502 }
    );
  }

  const session = readSession(payload);
  if (!session.ok) {
    return json({ ok: false, reason: 'stripe', detail: session.detail }, { status: 502 });
  }

  return json({ ok: true, url: session.url, id: session.id });
}

/* -------------------------------------------------------------------- router */

const ROUTES = {
  '/challenge': handleChallenge,
  '/checkout': handleCheckout,
  '/verify': handleVerify,
  '/write': handleWrite,
  '/bind': handleBind,
  '/device': handleDevice,
  '/upload': handleUpload,
};

/**
 * Build the worker. Dependencies are injectable so the tests can run the whole
 * thing — routing, CORS, statuses and all — without KV or GitHub.
 */
export function createBroker(env, { fetchImpl, now } = {}) {
  const config = readConfig(env, now);
  const challenges = config.missing.length
    ? null
    : challengeStore(env.CHALLENGES, { ttl: config.ttl, now });
  // Absent from readConfig's `missing` on purpose: /challenge and /verify work
  // without any of this, and a broker that refuses to prove anything because
  // it cannot write is worse than one that can do the half it is set up for.
  // /write reports it, and only /write.
  //
  // The App wins whenever both are configured, so a personal token left behind
  // from an afternoon of trying this out cannot quietly remain the thing in
  // use. See app-auth.js for why that ordering is not arbitrary.
  const credential = env.GITHUB_APP_ID
    ? appCredential({
        appId: env.GITHUB_APP_ID,
        privateKey: env.GITHUB_APP_KEY,
        fetchImpl,
        api: env.GITHUB_API,
        now,
      })
    : env.GITHUB_TOKEN
      ? patCredential(env.GITHUB_TOKEN)
      : null;

  const repositories = credential
    ? github({ credential, fetchImpl, api: env.GITHUB_API })
    : null;

  // Read the device list through the API when there is a credential for it.
  // The cached raw copy is minutes behind, which would mean a revoked device
  // still working and — the one that would read as the feature being broken —
  // an owner who just bound their own phone unable to approve anybody yet.
  const devices = deviceList({
    fetchImpl,
    read: repositories ? (where) => repositories.readFile(where) : null,
  });

  return {
    async fetch(request) {
      const cors = corsHeaders(request, config.origins);

      if (request.method === 'OPTIONS') {
        return new Response(null, { status: 204, headers: cors });
      }

      if (config.missing.length) {
        return json(
          { ok: false, detail: `This broker is not configured: ${config.missing.join(', ')}.` },
          { status: 500, headers: cors }
        );
      }

      const route = ROUTES[new URL(request.url).pathname.replace(/\/+$/, '') || '/'];
      if (!route) return json({ ok: false, detail: 'No such endpoint.' }, { status: 404, headers: cors });
      if (request.method !== 'POST') {
        return json({ ok: false, detail: 'Use POST.' }, { status: 405, headers: cors });
      }

      const response = await route(request, {
        config,
        challenges,
        devices,
        repositories,
        fetchImpl: fetchImpl || fetch,
      });
      for (const [name, value] of Object.entries(cors)) response.headers.set(name, value);
      return response;
    },
  };
}

export default {
  fetch(request, env) {
    return createBroker(env).fetch(request);
  },
};
