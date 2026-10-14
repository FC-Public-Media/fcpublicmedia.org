// The broker: routing, configuration, and every endpoint. See worker/README.md.

import { appCredential, patCredential } from './app-auth.js';
import { challengeStore } from './challenges.js';
import { lookup, readSession, returnUrl, sessionParams } from './checkout.js';
import { deviceList, mayPublish } from './devices.js';
import { addDevice, allowDevice, revokeDevice, serialize } from './enroll.js';
import { github } from './github.js';
import { ACTIONS, contentHash, matchesIntent, readIntent } from './intent.js';
import { grantUpload, objectKey } from './r2.js';
import { verifyAssertion } from './webauthn.js';

// The browser's own claim verifier, imported so the two cannot drift; it must stay free of DOM globals.
import { verifyClaim } from '../../site/assets/js/claims.js';

/* ---------------------------------------------------------------- responses */

const json = (body, { status = 200, headers = {} } = {}) =>
  new Response(JSON.stringify(body, null, 2), {
    status,
    headers: { 'Content-Type': 'application/json; charset=utf-8', ...headers },
  });

/** CORS for the site's own origins only. */
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

/** Read the settings; `missing` names whatever stops the broker answering at all. */
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
    // Never taken from the page: going straight to the live branch is not a member's choice.
    writeMode: env.WRITE_MODE === 'direct' ? 'direct' : 'branch',
    claimKeys: readClaimKeys(env.CLAIM_KEYS),

    // All four or none.
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

    // Not in `missing`: unset, it disables /checkout alone. See docs/payments.md#keys.
    stripe: (env.PUBLIC_STRIPE_API_KEY || env.STRIPE_KEY || '').trim() || null,

    uploadTtl: Number(env.UPLOAD_TTL || 21600),
    maxUpload: Number(env.R2_MAX_BYTES || 0),

    now,
  };
}

/** Parse CLAIM_KEYS; a malformed value means no keys, so every enrolment is refused. */
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

/** Issue a challenge for one declared action; unauthenticated, as only a listed passkey can use it. */
async function handleChallenge(request, { config, challenges }) {
  const body = await readBody(request);
  if (!body) return json({ ok: false, detail: 'Send JSON.' }, { status: 400 });

  const intent = readIntent(body, { owner: config.owner, maxUpload: config.maxUpload });
  if (!intent.ok) return json({ ok: false, detail: intent.detail }, { status: 400 });

  // The object key is fixed before signing, under the challenge's own repository.
  if (intent.intent.action === 'upload.grant') {
    intent.intent.key = objectKey(intent.intent.repo, intent.intent.filename, config.now());
  }

  const issued = await challenges.issue(intent.intent);
  return json({
    ok: true,
    challenge: issued.challenge,
    expires_in: issued.expiresIn,
    intent: intent.intent,
  });
}

/** The one authorization order (worker/README.md#routes); no endpoint re-implements a step. */
async function authorize(request, { config, challenges, devices }) {
  const refuse = (status, fields) => ({ ok: false, response: json({ ok: false, ...fields }, { status }) });

  const body = await readBody(request);
  if (!body) return refuse(400, { detail: 'Send JSON.' });

  const assertion = body.assertion;
  if (!assertion?.client_data_json) {
    return refuse(400, { detail: 'No assertion was sent.' });
  }

  // Read from the signed client data, never a separate field.
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

  // device.add belongs to /bind alone; presented here it is spent and refused.
  if (ACTIONS[intent.action]?.unlisted) {
    return refuse(409, { reason: 'intent', detail: 'That challenge belongs to a different flow.' });
  }

  const found = await devices.find(intent.repo, assertion.credential_id);
  if (!found.ok) {
    // Our setup (500), GitHub's outage (503), or a refusal of this device (403).
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

  // Listed is not allowed; `verify` alone works for a device that may not publish.
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
    performed: false,
  });
}

/** Check an assertion, then write the one file it was signed for. */
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

  // The device label is all the broker knows; it never guesses a person's name.
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
    // conflict: the SHA moved. credential: our setup, including an uninstalled (revoked) site.
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
    // The bytes were already there: a double tap or a retry.
    repeated: written.repeated === true,
    ...(written.detail ? { detail: written.detail } : {}),
  });
}

/* ------------------------------------------------------------------ uploads */

/** Sign URLs for one file; the bytes go straight to R2, never through here. */
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

// Never sent by a page; intent.js refuses it as a settings target.
const DEVICES = '.auth/devices.json';

/** Read the device list through the API, current, as the first half of a read-modify-write. */
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

/** Add a passkey: a signature by the new key proves possession, a claim naming this repo grants it. */
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

  // Against the key in the intent: this proves possession only; the claim grants enrolment.
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
    may_publish: added.granted,
    first_device: added.granted,
  });
}

/** Approve or revoke a device, signed by one that may already publish (authorize() checks that). */
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
  // Already in the asked-for state: success, nothing written.
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

/** Start a Stripe Checkout for a SKU; unauthenticated, priced from prices.js. See docs/payments.md. */
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
      // Per request, not per SKU: two genuine purchases must get two sessions.
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
    // Stripe's developer-facing message goes to the log, not to the visitor.
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

/** Build the worker; fetchImpl and now are injectable so tests run it whole without KV or GitHub. */
export function createBroker(env, { fetchImpl, now } = {}) {
  const config = readConfig(env, now);
  const challenges = config.missing.length
    ? null
    : challengeStore(env.CHALLENGES, { ttl: config.ttl, now });
  // Optional: /challenge and /verify work without it. The App wins over a leftover GITHUB_TOKEN.
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

  // Through the API when possible: the raw copy is minutes stale, so revocations and new binds lag.
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
