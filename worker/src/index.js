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
// WHAT IS NOT BUILT YET
// ---------------------
// This verifies. It does not write. /verify says so in its own response
// rather than implying otherwise: `performed: false`. Writing a file through
// the GitHub Contents API, presigning an upload, and co-signing a second
// device are the next three steps, and each of them is this verification plus
// one action.

import { challengeStore } from './challenges.js';
import { deviceList, mayPublish } from './devices.js';
import { ACTIONS, matchesIntent, readIntent } from './intent.js';
import { verifyAssertion } from './webauthn.js';

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
function readConfig(env) {
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
  };
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

  const intent = readIntent(body, { owner: config.owner });
  if (!intent.ok) return json({ ok: false, detail: intent.detail }, { status: 400 });

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
 * Check an assertion against the challenge it claims to answer.
 *
 * The order below is the whole design in miniature:
 *
 *   1. Spend the challenge. Gone whatever happens next.
 *   2. Find the recorded key, in the repository the CHALLENGE named — never
 *      the one the request names. The request's copy is checked against it
 *      afterwards, but it is not what the lookup is done with.
 *   3. Verify the signature.
 *   4. Only then, check the request does what the challenge was issued for.
 */
async function handleVerify(request, { config, challenges, devices }) {
  const body = await readBody(request);
  if (!body) return json({ ok: false, detail: 'Send JSON.' }, { status: 400 });

  const assertion = body.assertion;
  if (!assertion?.client_data_json) {
    return json({ ok: false, detail: 'No assertion was sent.' }, { status: 400 });
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
    return json({ ok: false, detail: 'The client data could not be read.' }, { status: 400 });
  }

  const intent = await challenges.take(presented);
  if (!intent) {
    return json(
      {
        ok: false,
        reason: 'challenge',
        detail: 'That challenge is unknown, spent, or expired. Start again.',
      },
      { status: 403 }
    );
  }

  const found = await devices.find(intent.repo, assertion.credential_id);
  if (!found.ok) {
    const status = found.reason === 'unreachable' ? 503 : 403;
    return json({ ok: false, reason: found.reason, detail: found.detail }, { status });
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
    return json({ ok: false, reason: result.reason, detail: result.detail }, { status: 403 });
  }

  const matches = await matchesIntent(intent, body);
  if (!matches.ok) {
    return json({ ok: false, reason: 'intent', detail: matches.detail }, { status: 409 });
  }

  // Listed and proven, but that is not permission. An action that changes the
  // site needs the record to say so; `verify` does not, which is what makes it
  // useful for telling somebody they are bound but not yet allowed.
  if (intent.action !== 'verify' && !mayPublish(found.device)) {
    return json(
      {
        ok: false,
        reason: 'not-allowed',
        detail: 'That device is registered but is not allowed to change this site yet.',
      },
      { status: 403 }
    );
  }

  return json({
    ok: true,
    repo: intent.repo,
    action: intent.action,
    device: { label: found.device.label || 'Unnamed device', may_publish: mayPublish(found.device) },
    user_verified: result.flags.userVerified,
    // Said out loud, because a page that treats a verification as a save would
    // tell somebody their edit went through when nothing has been written.
    performed: false,
  });
}

/* -------------------------------------------------------------------- router */

const ROUTES = {
  '/challenge': handleChallenge,
  '/verify': handleVerify,
};

/**
 * Build the worker. Dependencies are injectable so the tests can run the whole
 * thing — routing, CORS, statuses and all — without KV or GitHub.
 */
export function createBroker(env, { fetchImpl, now } = {}) {
  const config = readConfig(env);
  const challenges = config.missing.length
    ? null
    : challengeStore(env.CHALLENGES, { ttl: config.ttl, now });
  const devices = deviceList({ fetchImpl });

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

      const response = await route(request, { config, challenges, devices });
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
