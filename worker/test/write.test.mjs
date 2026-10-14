// /write after verification passes: never write wrongly, never report a landed write as failed.

import { strict as assert } from 'node:assert';
import { test } from 'node:test';

import { createBroker } from '../src/index.js';
import { contentHash } from '../src/intent.js';
import { fakeGitHub, makeAssertion, makeCredential, memoryKV } from './helpers.mjs';

const RP_ID = 'fcpublicmedia.org';
const ORIGIN = 'https://www.fcpublicmedia.org';
const REPO = 'fcpublicmedia/janes-show';
const PATH = '_data/site.yml';
const SETTINGS = '# What people see\nname: Jane Live\ntagline: Thursdays at eight.\n';

const post = (path, body) =>
  new Request(`https://broker.example${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Origin: ORIGIN },
    body: JSON.stringify(body),
  });

/** A broker with a token, a repository and one device; `blobs` seeds what GitHub already holds. */
async function setUp({ writeMode, mayPublish = true, blobs = {}, token = 'ghp_test' } = {}) {
  const credential = await makeCredential({ mayPublish });
  const hub = fakeGitHub({ [REPO]: { version: 1, devices: [credential.record] } }, { blobs });

  const service = createBroker(
    {
      RP_ID,
      ORIGINS: ORIGIN,
      OWNER: 'fcpublicmedia',
      CHALLENGES: memoryKV(),
      ...(token ? { GITHUB_TOKEN: token } : {}),
      ...(writeMode ? { WRITE_MODE: writeMode } : {}),
    },
    { fetchImpl: hub.fetchImpl }
  );

  /** Everything a page does to save: declare, sign, send. */
  const save = async (content, { sha = '', action = 'settings.write', path = PATH } = {}) => {
    const declared = await service.fetch(
      post('/challenge', {
        action,
        repo: REPO,
        ...(action === 'settings.write'
          ? { path, sha, content_hash: await contentHash(content) }
          : {}),
      })
    );
    const { challenge } = await declared.json();
    const assertion = await makeAssertion(credential, { challenge, origin: ORIGIN, rpId: RP_ID });

    const response = await service.fetch(post('/write', { assertion, content }));
    return { response, body: await response.json() };
  };

  return { service, hub, credential, save };
}

/* ------------------------------------------------------------- branch mode */

test('a save lands on a branch and opens a pull request', async () => {
  const { hub, save } = await setUp();

  const { response, body } = await save(SETTINGS);

  assert.equal(response.status, 200, body.detail);
  assert.equal(body.performed, true);
  assert.equal(body.mode, 'branch');
  assert.match(body.url, /\/pull\/1$/);

  assert.equal(hub.written.length, 1);
  assert.equal(hub.written[0].path, PATH);
  assert.notEqual(hub.written[0].branch, 'main', 'the default branch was written directly');
  assert.equal(hub.pulls.length, 1);
});

test('what gets written is exactly what was signed for, comments and all', async () => {
  // /settings/ is a textarea so that YAML comments survive.
  const { hub, save } = await setUp();

  await save(SETTINGS);

  assert.equal(hub.written[0].content, SETTINGS);
  assert.match(hub.written[0].content, /^# What people see$/m);
});

test('the same edit retried reuses its branch and its pull request', async () => {
  // A double tap or retry; the branch is named from the content hash.
  const { hub, save } = await setUp();

  const first = await save(SETTINGS);
  const second = await save(SETTINGS);

  assert.equal(second.response.status, 200, second.body.detail);
  assert.equal(second.body.url, first.body.url);
  assert.equal(hub.pulls.length, 1, 'a second pull request was opened');

  assert.equal(first.body.repeated, false);
  assert.equal(second.body.repeated, true);
  assert.equal(hub.written.length, 1, 'the file was written twice');
});

test('the commit message names the device rather than guessing at a person', async () => {
  const { hub, save } = await setUp();

  await save(SETTINGS);

  assert.match(hub.written[0].message, /Test phone/);
  assert.match(hub.written[0].message, /_data\/site\.yml/);
});

/* ------------------------------------------------------------- direct mode */

test('direct mode commits to the default branch and opens nothing', async () => {
  const { hub, save } = await setUp({ writeMode: 'direct' });

  const { response, body } = await save(SETTINGS);

  assert.equal(response.status, 200, body.detail);
  assert.equal(body.mode, 'direct');
  assert.equal(hub.written[0].branch, 'main');
  assert.equal(hub.pulls.length, 0);
  assert.match(body.url, /\/commit\//);
});

/* -------------------------------------------------------------- refusals */

test('a stale SHA is refused rather than allowed to discard somebody', async () => {
  const { hub, save } = await setUp({ blobs: { [`${REPO}/${PATH}`]: 'a'.repeat(40) } });

  const { response, body } = await save(SETTINGS, { sha: 'b'.repeat(40) });

  assert.equal(response.status, 409);
  assert.equal(body.reason, 'conflict');
  assert.equal(hub.written.length, 0);
});

test('a device that may not publish cannot write', async () => {
  const { hub, save } = await setUp({ mayPublish: false });

  const { response, body } = await save(SETTINGS);

  assert.equal(response.status, 403);
  assert.equal(body.reason, 'not-allowed');
  assert.equal(hub.written.length, 0);
});

test('a challenge issued to prove a device cannot be spent on a write', async () => {
  const { hub, save } = await setUp();

  const { response, body } = await save(SETTINGS, { action: 'verify' });

  assert.equal(response.status, 409);
  assert.equal(body.reason, 'intent');
  assert.equal(hub.written.length, 0);
});

test('content that is not what was signed for is never written', async () => {
  const { hub, service, credential } = await setUp();

  const declared = await service.fetch(
    post('/challenge', {
      action: 'settings.write',
      repo: REPO,
      path: PATH,
      sha: '',
      content_hash: await contentHash(SETTINGS),
    })
  );
  const { challenge } = await declared.json();
  const assertion = await makeAssertion(credential, { challenge, origin: ORIGIN, rpId: RP_ID });

  const response = await service.fetch(
    post('/write', { assertion, content: 'name: Somebody Else\n' })
  );

  assert.equal(response.status, 409);
  assert.equal(hub.written.length, 0);
});

test('a broker with no credential says so, and still verifies', async () => {
  const { service, save, credential } = await setUp({ token: null });

  const { response, body } = await save(SETTINGS);
  assert.equal(response.status, 500);
  assert.match(body.detail, /GITHUB_APP_ID/);

  // Verification still works without a write credential.
  const declared = await service.fetch(post('/challenge', { action: 'verify', repo: REPO }));
  const { challenge } = await declared.json();
  const assertion = await makeAssertion(credential, { challenge, origin: ORIGIN, rpId: RP_ID });

  assert.equal((await service.fetch(post('/verify', { assertion }))).status, 200);
});

test('the token never leaves for anywhere but GitHub', async () => {
  const { hub, save } = await setUp();

  await save(SETTINGS);

  const leaked = hub.calls.filter(
    (call) => !call.url.startsWith('https://api.github.com/') && call.url.includes('ghp_test')
  );
  assert.equal(leaked.length, 0);
  assert.ok(hub.calls.some((call) => call.url.startsWith('https://api.github.com/')));
});
