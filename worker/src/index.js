// see docs/inline/worker/src/index.js.md#1

import { appCredential, patCredential } from './app-auth.js';
import { challengeStore } from './challenges.js';
import { lookup, readSession, returnUrl, sessionParams } from './checkout.js';
import { deviceList, mayPublish } from './devices.js';
import { addDevice, allowDevice, revokeDevice, serialize } from './enroll.js';
import { github } from './github.js';
import { ACTIONS, contentHash, matchesIntent, readIntent } from './intent.js';
import { grantUpload, objectKey } from './r2.js';
import { verifyAssertion } from './webauthn.js';

// see docs/inline/worker/src/index.js.md#2
import { verifyClaim } from '../../site/assets/js/claims.js';

/* ---------------------------------------------------------------- responses */

const json = (body, { status = 200, headers = {} } = {}) =>
  new Response(JSON.stringify(body, null, 2), {
    status,
    headers: { 'Content-Type': 'application/json; charset=utf-8', ...headers },
  });

// see docs/inline/worker/src/index.js.md#3
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

// see docs/inline/worker/src/index.js.md#4
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
    // see docs/inline/worker/src/index.js.md#5
    writeMode: env.WRITE_MODE === 'direct' ? 'direct' : 'branch',

    // see docs/inline/worker/src/index.js.md#6
    claimKeys: readClaimKeys(env.CLAIM_KEYS),

    // see docs/inline/worker/src/index.js.md#7
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

    // see docs/inline/worker/src/index.js.md#8
    stripe: (env.PUBLIC_STRIPE_API_KEY || env.STRIPE_KEY || '').trim() || null,

    // see docs/inline/worker/src/index.js.md#9
    uploadTtl: Number(env.UPLOAD_TTL || 21600),
    maxUpload: Number(env.R2_MAX_BYTES || 0),

    now,
  };
}

// see docs/inline/worker/src/index.js.md#10
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

// see docs/inline/worker/src/index.js.md#11
async function handleChallenge(request, { config, challenges }) {
  const body = await readBody(request);
  if (!body) return json({ ok: false, detail: 'Send JSON.' }, { status: 400 });

  const intent = readIntent(body, { owner: config.owner, maxUpload: config.maxUpload });
  if (!intent.ok) return json({ ok: false, detail: intent.detail }, { status: 400 });

  // see docs/inline/worker/src/index.js.md#12
  if (intent.intent.action === 'upload.grant') {
    intent.intent.key = objectKey(intent.intent.repo, intent.intent.filename, config.now());
  }

  const issued = await challenges.issue(intent.intent);
  return json({
    ok: true,
    challenge: issued.challenge,
    expires_in: issued.expiresIn,
    // see docs/inline/worker/src/index.js.md#13
    intent: intent.intent,
  });
}

// see docs/inline/worker/src/index.js.md#14
async function authorize(request, { config, challenges, devices }) {
  const refuse = (status, fields) => ({ ok: false, response: json({ ok: false, ...fields }, { status }) });

  const body = await readBody(request);
  if (!body) return refuse(400, { detail: 'Send JSON.' });

  const assertion = body.assertion;
  if (!assertion?.client_data_json) {
    return refuse(400, { detail: 'No assertion was sent.' });
  }

  // see docs/inline/worker/src/index.js.md#15
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

  // see docs/inline/worker/src/index.js.md#16
  if (ACTIONS[intent.action]?.unlisted) {
    return refuse(409, { reason: 'intent', detail: 'That challenge belongs to a different flow.' });
  }

  const found = await devices.find(intent.repo, assertion.credential_id);
  if (!found.ok) {
    // see docs/inline/worker/src/index.js.md#17
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

  // see docs/inline/worker/src/index.js.md#18
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
    // see docs/inline/worker/src/index.js.md#19
    performed: false,
  });
}

// see docs/inline/worker/src/index.js.md#20
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

  // see docs/inline/worker/src/index.js.md#21
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
    // see docs/inline/worker/src/index.js.md#22
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
    // see docs/inline/worker/src/index.js.md#23
    repeated: written.repeated === true,
    ...(written.detail ? { detail: written.detail } : {}),
  });
}

/* ------------------------------------------------------------------ uploads */

// see docs/inline/worker/src/index.js.md#24
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

// see docs/inline/worker/src/index.js.md#25
const DEVICES = '.auth/devices.json';

// see docs/inline/worker/src/index.js.md#26
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

// see docs/inline/worker/src/index.js.md#27
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

  // see docs/inline/worker/src/index.js.md#28
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
  // see docs/inline/worker/src/index.js.md#29
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
    // see docs/inline/worker/src/index.js.md#30
    may_publish: added.granted,
    first_device: added.granted,
  });
}

// see docs/inline/worker/src/index.js.md#31
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
  // see docs/inline/worker/src/index.js.md#32
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

// see docs/inline/worker/src/index.js.md#33
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
      // see docs/inline/worker/src/index.js.md#34
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
    // see docs/inline/worker/src/index.js.md#35
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

// see docs/inline/worker/src/index.js.md#36
export function createBroker(env, { fetchImpl, now } = {}) {
  const config = readConfig(env, now);
  const challenges = config.missing.length
    ? null
    : challengeStore(env.CHALLENGES, { ttl: config.ttl, now });
  // see docs/inline/worker/src/index.js.md#37
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

  // see docs/inline/worker/src/index.js.md#38
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
