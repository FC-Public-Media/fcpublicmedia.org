// The broker end to end: routing, challenges, device lookup, and what each
// failure tells the page.
//
// Driven through Request and Response rather than by calling the handlers, so
// the statuses and the CORS headers are covered too. A 500 that should have
// been a 403 is a real bug — the page shows a different thing for each.

import { strict as assert } from 'node:assert';
import { test } from 'node:test';

import { createBroker } from '../src/index.js';
import { contentHash } from '../src/intent.js';
import { fakeRaw, makeAssertion, makeCredential, memoryKV } from './helpers.mjs';

const RP_ID = 'fcpublicmedia.org';
const ORIGIN = 'https://www.fcpublicmedia.org';
const REPO = 'fcpublicmedia/janes-show';
const SETTINGS = 'name: Jane Live\n';

function env(overrides = {}) {
  return {
    RP_ID,
    ORIGINS: `${ORIGIN},http://localhost:4000`,
    OWNER: 'fcpublicmedia',
    CHALLENGES: memoryKV(),
    ...overrides,
  };
}

/** A broker wired to a repository holding exactly these devices. */
function broker(devicesByRepo, options = {}) {
  return createBroker(env(options.env), {
    fetchImpl: fakeRaw(devicesByRepo),
    now: options.now,
  });
}

const post = (path, body, headers = {}) =>
  new Request(`https://broker.example${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Origin: ORIGIN, ...headers },
    body: JSON.stringify(body),
  });

/** Ask for a challenge the way a page would, and get it back. */
async function challengeFor(service, intent) {
  const response = await service.fetch(post('/challenge', intent));
  const body = await response.json();
  assert.equal(response.status, 200, body.detail);
  return body.challenge;
}

/* ------------------------------------------------------------------ routing */

test('an unconfigured broker says which setting is missing', async () => {
  const bare = createBroker({ ORIGINS: ORIGIN, CHALLENGES: memoryKV() });
  const response = await bare.fetch(post('/challenge', { action: 'verify', repo: REPO }));

  assert.equal(response.status, 500);
  assert.match((await response.json()).detail, /RP_ID/);
});

test('unknown endpoints and wrong methods are told apart', async () => {
  const service = broker({});

  assert.equal((await service.fetch(post('/nowhere', {}))).status, 404);
  assert.equal(
    (await service.fetch(new Request('https://broker.example/verify', { method: 'GET' }))).status,
    405
  );
});

test('CORS answers our own pages and nobody else', async () => {
  const service = broker({});

  const ours = await service.fetch(
    new Request('https://broker.example/challenge', { method: 'OPTIONS', headers: { Origin: ORIGIN } })
  );
  assert.equal(ours.status, 204);
  assert.equal(ours.headers.get('Access-Control-Allow-Origin'), ORIGIN);

  const theirs = await service.fetch(
    new Request('https://broker.example/challenge', {
      method: 'OPTIONS',
      headers: { Origin: 'https://elsewhere.example' },
    })
  );
  assert.equal(theirs.headers.get('Access-Control-Allow-Origin'), null);
});

/* --------------------------------------------------------------- challenges */

test('a challenge is issued for a declared action and echoes it back', async () => {
  const service = broker({});
  const response = await service.fetch(
    post('/challenge', {
      action: 'settings.write',
      repo: REPO,
      path: '_data/site.yml',
      sha: 'a'.repeat(40),
      content_hash: await contentHash(SETTINGS),
    })
  );

  const body = await response.json();
  assert.equal(response.status, 200);
  assert.equal(body.intent.path, '_data/site.yml');
  assert.ok(body.challenge.length >= 43, 'a challenge should be 32 bytes of base64url');
  assert.ok(body.expires_in > 0);
});

test('an action the broker does not do is refused', async () => {
  const service = broker({});
  const response = await service.fetch(post('/challenge', { action: 'repo.delete', repo: REPO }));

  assert.equal(response.status, 400);
});

test('a repository outside the configured owner is refused', async () => {
  const service = broker({});
  const response = await service.fetch(
    post('/challenge', { action: 'verify', repo: 'somebody-else/their-show' })
  );

  assert.equal(response.status, 400);
  assert.match((await response.json()).detail, /fcpublicmedia/);
});

test('a workflow file is not a settings file', async () => {
  // The escalation this exists to stop: a workflow runs with the
  // repository's secrets, so writing one is using all of them.
  const service = broker({});
  const forbidden = ['.github/workflows/deploy.yml', '.auth/devices.json', '../elsewhere/x.yml'];

  for (const path of forbidden) {
    const response = await service.fetch(
      post('/challenge', {
        action: 'settings.write',
        repo: REPO,
        path,
        sha: '',
        content_hash: await contentHash(SETTINGS),
      })
    );
    assert.equal(response.status, 400, `${path} was allowed`);
  }
});

/* ------------------------------------------------------------------- verify */

test('a genuine assertion verifies, and says it performed nothing', async () => {
  const credential = await makeCredential({ label: "Jane's phone" });
  const service = broker({ [REPO]: { version: 1, devices: [credential.record] } });

  const challenge = await challengeFor(service, { action: 'verify', repo: REPO });
  const assertion = await makeAssertion(credential, { challenge, origin: ORIGIN, rpId: RP_ID });

  const response = await service.fetch(post('/verify', { assertion }));
  const body = await response.json();

  assert.equal(response.status, 200, body.detail);
  assert.equal(body.repo, REPO);
  assert.equal(body.device.label, "Jane's phone");
  assert.equal(body.performed, false);
});

test('a challenge only works once', async () => {
  const credential = await makeCredential();
  const service = broker({ [REPO]: { version: 1, devices: [credential.record] } });

  const challenge = await challengeFor(service, { action: 'verify', repo: REPO });
  const assertion = await makeAssertion(credential, { challenge, origin: ORIGIN, rpId: RP_ID });

  assert.equal((await service.fetch(post('/verify', { assertion }))).status, 200);

  // Byte-identical replay of an assertion that was genuine a moment ago.
  const replay = await service.fetch(post('/verify', { assertion }));
  assert.equal(replay.status, 403);
  assert.equal((await replay.json()).reason, 'challenge');
});

test('a challenge left sitting expires', async () => {
  const credential = await makeCredential();
  let clock = 1_760_000_000_000;
  const service = broker({ [REPO]: { version: 1, devices: [credential.record] } }, {
    now: () => clock,
  });

  const challenge = await challengeFor(service, { action: 'verify', repo: REPO });
  const assertion = await makeAssertion(credential, { challenge, origin: ORIGIN, rpId: RP_ID });

  clock += 301_000;
  const response = await service.fetch(post('/verify', { assertion }));

  assert.equal(response.status, 403);
  assert.equal((await response.json()).reason, 'challenge');
});

test('a site with no device list says so rather than failing obscurely', async () => {
  const credential = await makeCredential();
  const service = broker({});

  const challenge = await challengeFor(service, { action: 'verify', repo: REPO });
  const assertion = await makeAssertion(credential, { challenge, origin: ORIGIN, rpId: RP_ID });

  const body = await (await service.fetch(post('/verify', { assertion }))).json();
  assert.equal(body.reason, 'no-list');
});

test('a device nobody registered is refused', async () => {
  const registered = await makeCredential();
  const stranger = await makeCredential();
  const service = broker({ [REPO]: { version: 1, devices: [registered.record] } });

  const challenge = await challengeFor(service, { action: 'verify', repo: REPO });
  const assertion = await makeAssertion(stranger, { challenge, origin: ORIGIN, rpId: RP_ID });

  const body = await (await service.fetch(post('/verify', { assertion }))).json();
  assert.equal(body.reason, 'unknown-device');
});

test('a revoked device is not on the list any more', async () => {
  const credential = await makeCredential();
  const service = broker({
    [REPO]: { version: 1, devices: [{ ...credential.record, revoked: true }] },
  });

  const challenge = await challengeFor(service, { action: 'verify', repo: REPO });
  const assertion = await makeAssertion(credential, { challenge, origin: ORIGIN, rpId: RP_ID });

  const body = await (await service.fetch(post('/verify', { assertion }))).json();
  assert.equal(body.reason, 'unknown-device');
});

test('GitHub being down is a 503, not a rejection', async () => {
  // A page that treats "GitHub had a bad minute" as "your device is not
  // authorized" sends somebody off to register a passkey they already have.
  const credential = await makeCredential();
  const service = broker({ [REPO]: null });

  const challenge = await challengeFor(service, { action: 'verify', repo: REPO });
  const assertion = await makeAssertion(credential, { challenge, origin: ORIGIN, rpId: RP_ID });

  assert.equal((await service.fetch(post('/verify', { assertion }))).status, 503);
});

/* ------------------------------------------------------- listed vs. allowed */

test('being listed is not being allowed to publish', async () => {
  const credential = await makeCredential({ mayPublish: false });
  const service = broker({ [REPO]: { version: 1, devices: [credential.record] } });

  // It can still prove it exists, which is what tells the member the
  // difference between "we have never seen this phone" and "wait for us".
  const proof = await challengeFor(service, { action: 'verify', repo: REPO });
  const proving = await makeAssertion(credential, { challenge: proof, origin: ORIGIN, rpId: RP_ID });
  const proved = await service.fetch(post('/verify', { assertion: proving }));
  assert.equal(proved.status, 200);
  assert.equal((await proved.json()).device.may_publish, false);

  // It cannot change anything.
  const challenge = await challengeFor(service, {
    action: 'settings.write',
    repo: REPO,
    path: '_data/site.yml',
    sha: '',
    content_hash: await contentHash(SETTINGS),
  });
  const writing = await makeAssertion(credential, { challenge, origin: ORIGIN, rpId: RP_ID });
  const refused = await service.fetch(post('/verify', { assertion: writing, content: SETTINGS }));

  assert.equal(refused.status, 403);
  assert.equal((await refused.json()).reason, 'not-allowed');
});

/* ------------------------------------------------------------ intent binding */

test('the signature is bound to the exact content that was declared', async () => {
  const credential = await makeCredential();
  const service = broker({ [REPO]: { version: 1, devices: [credential.record] } });

  const intent = {
    action: 'settings.write',
    repo: REPO,
    path: '_data/site.yml',
    sha: 'b'.repeat(40),
    content_hash: await contentHash(SETTINGS),
  };

  const challenge = await challengeFor(service, intent);
  const assertion = await makeAssertion(credential, { challenge, origin: ORIGIN, rpId: RP_ID });

  // Same valid assertion, different bytes than the member approved.
  const swapped = await service.fetch(
    post('/verify', { assertion, content: 'name: Somebody Else\n' })
  );
  assert.equal(swapped.status, 409);
  assert.equal((await swapped.json()).reason, 'intent');
});

test('the content that was declared goes through', async () => {
  const credential = await makeCredential();
  const service = broker({ [REPO]: { version: 1, devices: [credential.record] } });

  const challenge = await challengeFor(service, {
    action: 'settings.write',
    repo: REPO,
    path: '_data/site.yml',
    sha: 'c'.repeat(40),
    content_hash: await contentHash(SETTINGS),
  });
  const assertion = await makeAssertion(credential, { challenge, origin: ORIGIN, rpId: RP_ID });

  const response = await service.fetch(post('/verify', { assertion, content: SETTINGS }));
  const body = await response.json();

  assert.equal(response.status, 200, body.detail);
  assert.equal(body.action, 'settings.write');
});

test('the repository comes from the challenge, not from the request', async () => {
  // Both repositories are real and both devices are registered on their own
  // site. The question is whether naming the other one in the request body
  // can move the lookup — it must not, or a member of one site could spend
  // their own signature against another.
  const jane = await makeCredential();
  const raj = await makeCredential();
  const other = 'fcpublicmedia/rajs-show';
  const service = broker({
    [REPO]: { version: 1, devices: [jane.record] },
    [other]: { version: 1, devices: [raj.record] },
  });

  const challenge = await challengeFor(service, { action: 'verify', repo: REPO });
  const assertion = await makeAssertion(jane, { challenge, origin: ORIGIN, rpId: RP_ID });

  const response = await service.fetch(post('/verify', { assertion, repo: other }));
  assert.equal(response.status, 409);

  const body = await response.json();
  assert.equal(body.reason, 'intent');
});

test('a request with no assertion is a bad request, not a server error', async () => {
  const service = broker({});

  assert.equal((await service.fetch(post('/verify', {}))).status, 400);
  assert.equal(
    (await service.fetch(post('/verify', { assertion: { client_data_json: 'oh dear !!' } }))).status,
    400
  );
});
