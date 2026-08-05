// Being a GitHub App.
//
// The JWT is signed with a real RSA key and verified against its public half,
// because a broker that assembled the claims wrongly would look exactly like
// one that got them right — until the first real request, at which point the
// only symptom is "401 Bad credentials" and no indication of which field.

import { strict as assert } from 'node:assert';
import { test } from 'node:test';

import { appCredential } from '../src/app-auth.js';
import { contentHash } from '../src/intent.js';
import { createBroker } from '../src/index.js';
import { fakeApp, fakeGitHub, makeAssertion, makeCredential, memoryKV } from './helpers.mjs';

const RP_ID = 'fcpublicmedia.org';
const ORIGIN = 'https://www.fcpublicmedia.org';
const REPO = 'fcpublicmedia/janes-show';
const PATH = '_data/site.yml';
const SETTINGS = 'name: Jane Live\n';

// One key pair for the file. Generating RSA is slow enough to notice.
const app = await fakeApp({ installed: [REPO] });

const post = (path, body) =>
  new Request(`https://broker.example${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Origin: ORIGIN },
    body: JSON.stringify(body),
  });

async function setUp({ appId = app.appId, privateKey = app.pem, token, installed = [REPO] } = {}) {
  const credential = await makeCredential();
  const hub = fakeGitHub(
    { [REPO]: { version: 1, devices: [credential.record] } },
    { app: { ...app, installedOn: (repo) => installed.includes(repo) } }
  );

  const service = createBroker(
    {
      RP_ID,
      ORIGINS: ORIGIN,
      OWNER: 'fcpublicmedia',
      CHALLENGES: memoryKV(),
      ...(appId ? { GITHUB_APP_ID: appId } : {}),
      ...(privateKey ? { GITHUB_APP_KEY: privateKey } : {}),
      ...(token ? { GITHUB_TOKEN: token } : {}),
    },
    { fetchImpl: hub.fetchImpl, now: app.now }
  );

  const save = async (content = SETTINGS, { repo = REPO } = {}) => {
    const declared = await service.fetch(
      post('/challenge', {
        action: 'settings.write',
        repo,
        path: PATH,
        sha: '',
        content_hash: await contentHash(content),
      })
    );
    const { challenge } = await declared.json();
    const assertion = await makeAssertion(credential, { challenge, origin: ORIGIN, rpId: RP_ID });
    const response = await service.fetch(post('/write', { assertion, content }));
    return { response, body: await response.json() };
  };

  return { service, hub, save };
}

/* ------------------------------------------------------------------ the JWT */

test('the broker signs a JWT GitHub would accept', async () => {
  const { save } = await setUp();

  const { response, body } = await save();
  assert.equal(response.status, 200, body.detail);

  const claim = app.claims.at(-1);
  assert.equal(claim.iss, app.appId);
  // Back-dated against clock skew, and inside GitHub's ten-minute ceiling.
  const seconds = Math.floor(app.now() / 1000);
  assert.ok(claim.iat <= seconds, 'the JWT is issued in GitHub\'s future');
  assert.ok(claim.exp - claim.iat <= 600, 'the JWT outlives what GitHub allows');
  assert.ok(claim.exp > seconds);
});

test('a PKCS#1 key says exactly which command fixes it', async () => {
  // What GitHub's download button hands you. WebCrypto's own error is
  // "Invalid keyData", which tells nobody anything.
  const { save } = await setUp({
    privateKey: '-----BEGIN RSA PRIVATE KEY-----\nMIIEow==\n-----END RSA PRIVATE KEY-----\n',
  });

  const { response, body } = await save();

  assert.equal(response.status, 500);
  assert.match(body.detail, /PKCS#1/);
  assert.match(body.detail, /openssl pkcs8 -topk8/);
});

/* ------------------------------------------------------------ minted tokens */

test('a token is minted for one repository and two permissions', async () => {
  // An installation may span every member site. What comes out of it here
  // never does.
  const { save } = await setUp();

  await save();

  const minted = app.minted.at(-1);
  assert.deepEqual(minted.repositories, ['janes-show']);
  assert.deepEqual(minted.permissions, { contents: 'write', pull_requests: 'write' });
  assert.equal(minted.permissions.workflows, undefined, 'workflows must never be requested');
});

test('the token is reused rather than minted per request', async () => {
  const { save } = await setUp();
  const before = app.minted.length;

  await save('name: One\n');
  await save('name: Two\n');

  assert.equal(app.minted.length - before, 1, 'a second token was minted inside the hour');
});

test('a site the app is not installed on is refused, and says why', async () => {
  // The same answer as "this site was revoked", which is the point of
  // revoking by uninstalling.
  const { hub, save } = await setUp({ installed: [] });

  const { response, body } = await save();

  assert.equal(response.status, 500);
  assert.match(body.detail, /not installed/);
  assert.match(body.detail, /uninstalling is how it is revoked/);
  assert.equal(hub.written.length, 0);
});

/* -------------------------------------------------------------- precedence */

test('the app wins when a personal token is also lying around', async () => {
  // A token left behind from an afternoon of trying this out must not quietly
  // remain the thing in use.
  const { save } = await setUp({ token: 'ghp_leftover' });
  const before = app.minted.length;

  const { response } = await save();

  assert.equal(response.status, 200);
  assert.equal(app.minted.length - before, 1, 'the personal token was used instead');
});

test('a broker with neither says which settings it wants', async () => {
  const { save } = await setUp({ appId: null, privateKey: null });

  const { response, body } = await save();

  assert.equal(response.status, 500);
  assert.match(body.detail, /GITHUB_APP_ID/);
});

/* ------------------------------------------------------------- the unit, bare */

test('a missing key is reported without throwing', async () => {
  const credential = appCredential({ appId: '1', privateKey: '', fetchImpl: async () => {
    throw new Error('the network should not have been reached');
  } });

  const issued = await credential(REPO);
  assert.equal(issued.ok, false);
  assert.match(issued.detail, /GITHUB_APP_KEY/);
});
