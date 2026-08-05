// Binding devices, and approving them.
//
// The rule under test is the one in DESIGN-NOTES: enrolment and authority are
// different things. A claim link can be forwarded, and that is survivable only
// because forwarding it gets somebody LISTED and nothing more. If that ever
// stops being true, the whole reason staff can leave the loop goes with it.
//
// The claims here are minted by script/mint-claim.py — the real script, run as
// a subprocess — rather than assembled by the test. The broker's claim
// checking is worth nothing if it agrees with a fixture instead of with the
// thing that actually issues links.

import { strict as assert } from 'node:assert';
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { test } from 'node:test';

import { addDevice, allowDevice, anyPublisher, revokeDevice } from '../src/enroll.js';
import { createBroker } from '../src/index.js';
import { fakeGitHub, makeAssertion, makeCredential, memoryKV } from './helpers.mjs';

const RP_ID = 'fcpublicmedia.org';
const ORIGIN = 'https://www.fcpublicmedia.org';
const REPO = 'fcpublicmedia/janes-show';
const DEVICES = '.auth/devices.json';

const SCRIPT = path.resolve(import.meta.dirname, '..', '..', 'script', 'mint-claim.py');

/* ------------------------------------------------- a real claim signing key */

const workdir = fs.mkdtempSync(path.join(os.tmpdir(), 'fcpm-enroll-'));
const keyPath = path.join(workdir, 'key.pem');

const mint = (args) => execFileSync('python3', [SCRIPT, ...args], { encoding: 'utf8' }).trim();

const keyBlock = mint(['--new-key', keyPath]);
const grab = (field) => keyBlock.match(new RegExp(`${field}:\\s*"([^"]+)"`))[1];
const CLAIM_KEYS = JSON.stringify([{ id: grab('id'), x: grab('x'), y: grab('y') }]);

/** A claim link, as staff would send it. The token rides in the fragment. */
const claimFor = (email, { repo = REPO, days = 30 } = {}) =>
  mint(['--key', keyPath, '--email', email, '--repo', repo, '--days', String(days)])
    .split('#claim=')[1];

process.on('exit', () => fs.rmSync(workdir, { recursive: true, force: true }));

/* --------------------------------------------------------------- the rules */

test('the first device to bind is trusted and the next one is not', async () => {
  const first = addDevice([], { credential_id: 'a'.repeat(20), public_key: 'k' });
  assert.equal(first.granted, true);
  assert.equal(first.devices[0].may_publish, true);

  const second = addDevice(first.devices, { credential_id: 'b'.repeat(20), public_key: 'k' });
  assert.equal(second.granted, false);
  assert.equal(second.devices[1].may_publish, false);
});

test('first means first that counts, not first in the file', async () => {
  // A site whose only devices are listed-but-not-allowed has nobody who could
  // approve anything, so the next to arrive is still the first that matters.
  const listed = [{ credential_id: 'a'.repeat(20), public_key: 'k', may_publish: false }];
  assert.equal(anyPublisher(listed), false);
  assert.equal(addDevice(listed, { credential_id: 'b'.repeat(20), public_key: 'k' }).granted, true);
});

test('a revoked publisher does not keep counting as one', async () => {
  const listed = [{ credential_id: 'a'.repeat(20), may_publish: true, revoked: true }];
  assert.equal(anyPublisher(listed), false);
});

test('the last device that can publish cannot revoke itself', async () => {
  // Doing it would leave a site nobody can change, and the way back is staff
  // editing the file by hand. Refusing is kinder than allowing.
  const only = [{ credential_id: 'a'.repeat(20), may_publish: true }];

  const stranded = revokeDevice(only, 'a'.repeat(20));
  assert.equal(stranded.ok, false);
  assert.match(stranded.detail, /only device/);

  const two = allowDevice(
    [...only, { credential_id: 'b'.repeat(20), may_publish: false }],
    'b'.repeat(20)
  ).devices;
  assert.equal(revokeDevice(two, 'a'.repeat(20)).ok, true);
});

test('approving something already approved is not an error', async () => {
  const listed = [{ credential_id: 'a'.repeat(20), may_publish: true }];
  const again = allowDevice(listed, 'a'.repeat(20));
  assert.equal(again.already, true);
});

/* ------------------------------------------------------------- end to end */

const post = (path_, body) =>
  new Request(`https://broker.example${path_}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Origin: ORIGIN },
    body: JSON.stringify(body),
  });

function setUp({ claimKeys = CLAIM_KEYS } = {}) {
  const hub = fakeGitHub({});

  const service = createBroker(
    {
      RP_ID,
      ORIGINS: ORIGIN,
      OWNER: 'fcpublicmedia',
      CHALLENGES: memoryKV(),
      GITHUB_TOKEN: 'ghp_test',
      CLAIM_KEYS: claimKeys,
    },
    { fetchImpl: hub.fetchImpl }
  );

  /** What /authorize/ would do: make a passkey, then prove you hold it. */
  const bind = async (credential, { claim, label = 'A phone', repo = REPO } = {}) => {
    const declared = await service.fetch(
      post('/challenge', {
        action: 'device.add',
        repo,
        credential_id: credential.credentialId,
        public_key: credential.record.public_key,
      })
    );
    const issued = await declared.json();
    if (!issued.challenge) return { response: declared, body: issued };

    const assertion = await makeAssertion(credential, {
      challenge: issued.challenge,
      origin: ORIGIN,
      rpId: RP_ID,
    });
    const response = await service.fetch(post('/bind', { assertion, claim, label }));
    return { response, body: await response.json() };
  };

  /** What an owner does from their own phone. */
  const decide = async (signer, action, subject) => {
    const declared = await service.fetch(
      post('/challenge', { action, repo: REPO, credential_id: subject })
    );
    const { challenge } = await declared.json();
    const assertion = await makeAssertion(signer, { challenge, origin: ORIGIN, rpId: RP_ID });
    const response = await service.fetch(post('/device', { assertion }));
    return { response, body: await response.json() };
  };

  const listed = () => JSON.parse(hub.read(REPO, DEVICES) || '{"devices":[]}').devices;

  return { service, hub, bind, decide, listed };
}

test('the owner binds their own phone and can publish immediately', async () => {
  // No staff involvement at all, which is the entire point.
  const jane = await makeCredential();
  const { bind, listed } = setUp();

  const { response, body } = await bind(jane, { claim: claimFor('jane@example.com') });

  assert.equal(response.status, 200, body.detail);
  assert.equal(body.may_publish, true);
  assert.equal(body.first_device, true);
  assert.equal(listed()[0].credential_id, jane.credentialId);
  assert.equal(listed()[0].may_publish, true);
});

test('a forwarded link gets a co-producer listed and nothing more', async () => {
  // The link is the same link. Forwarding it is expected. What it buys is a
  // device that cannot change anything until somebody says so.
  const jane = await makeCredential();
  const raj = await makeCredential();
  const { bind, listed } = setUp();

  const claim = claimFor('jane@example.com');
  await bind(jane, { claim });
  const { response, body } = await bind(raj, { claim, label: "Raj's phone" });

  assert.equal(response.status, 200, body.detail);
  assert.equal(body.may_publish, false);
  assert.equal(listed().length, 2);
  assert.equal(listed()[1].may_publish, false);
});

test('the owner approves the co-producer from their own phone', async () => {
  const jane = await makeCredential();
  const raj = await makeCredential();
  const { bind, decide, listed } = setUp();

  const claim = claimFor('jane@example.com');
  await bind(jane, { claim });
  await bind(raj, { claim });

  const { response, body } = await decide(jane, 'device.allow', raj.credentialId);

  assert.equal(response.status, 200, body.detail);
  assert.equal(listed()[1].may_publish, true);
});

test('a co-producer cannot approve themselves', async () => {
  const jane = await makeCredential();
  const raj = await makeCredential();
  const { bind, decide, listed } = setUp();

  const claim = claimFor('jane@example.com');
  await bind(jane, { claim });
  await bind(raj, { claim });

  const { response, body } = await decide(raj, 'device.allow', raj.credentialId);

  assert.equal(response.status, 403);
  assert.equal(body.reason, 'not-allowed');
  assert.equal(listed()[1].may_publish, false);
});

/* ------------------------------------------------------------- the claim */

test('a claim for another site does not enrol here', async () => {
  const jane = await makeCredential();
  const { bind, listed } = setUp();

  const { response, body } = await bind(jane, {
    claim: claimFor('jane@example.com', { repo: 'fcpublicmedia/somebody-else' }),
  });

  assert.equal(response.status, 403);
  assert.equal(body.reason, 'claim');
  assert.match(body.detail, /different site/);
  assert.equal(listed().length, 0);
});

test('an expired claim says to ask for a new link', async () => {
  const jane = await makeCredential();
  const { bind } = setUp();

  const { response, body } = await bind(jane, {
    claim: claimFor('jane@example.com', { days: -1 }),
  });

  assert.equal(response.status, 403);
  assert.match(body.detail, /expired/);
});

test('a claim we did not sign is refused', async () => {
  const jane = await makeCredential();
  const stranger = path.join(workdir, 'stranger.pem');
  mint(['--new-key', stranger]);
  const forged = mint(['--key', stranger, '--email', 'jane@example.com', '--repo', REPO])
    .split('#claim=')[1];

  const { bind } = setUp();
  const { response, body } = await bind(jane, { claim: forged });

  assert.equal(response.status, 403);
  assert.match(body.detail, /not issued by us/);
});

test('no claim, no enrolment', async () => {
  const jane = await makeCredential();
  const { bind, listed } = setUp();

  const { response } = await bind(jane, { claim: undefined });

  assert.equal(response.status, 403);
  assert.equal(listed().length, 0);
});

/* --------------------------------------------------- proving the new key */

test('you cannot enrol somebody else’s public key', async () => {
  // Device lists are public, so anybody can read a key out of one. Binding it
  // needs the private half, which is the point of signing the challenge with
  // the key being registered.
  const jane = await makeCredential();
  const impostor = await makeCredential();
  const { service, listed } = setUp();

  const declared = await service.fetch(
    post('/challenge', {
      action: 'device.add',
      repo: REPO,
      // Jane's key...
      credential_id: jane.credentialId,
      public_key: jane.record.public_key,
    })
  );
  const { challenge } = await declared.json();
  // ...signed by somebody else's.
  const assertion = await makeAssertion(impostor, { challenge, origin: ORIGIN, rpId: RP_ID });
  assertion.credential_id = jane.credentialId;

  const response = await service.fetch(
    post('/bind', { assertion, claim: claimFor('jane@example.com') })
  );

  assert.equal(response.status, 403);
  assert.equal((await response.json()).reason, 'signature');
  assert.equal(listed().length, 0);
});

test('a device.add challenge cannot be spent on the endpoints that trust the list', async () => {
  const jane = await makeCredential();
  const { service } = setUp();

  const declared = await service.fetch(
    post('/challenge', {
      action: 'device.add',
      repo: REPO,
      credential_id: jane.credentialId,
      public_key: jane.record.public_key,
    })
  );
  const { challenge } = await declared.json();
  const assertion = await makeAssertion(jane, { challenge, origin: ORIGIN, rpId: RP_ID });

  const response = await service.fetch(post('/verify', { assertion }));
  assert.equal(response.status, 409);
  assert.equal((await response.json()).reason, 'intent');
});

test('binding the same device twice is refused rather than duplicated', async () => {
  const jane = await makeCredential();
  const { bind, listed } = setUp();

  const claim = claimFor('jane@example.com');
  await bind(jane, { claim });
  const { response, body } = await bind(jane, { claim });

  assert.equal(response.status, 409);
  assert.match(body.detail, /already registered/);
  assert.equal(listed().length, 1);
});

test('an unconfigured claim list refuses every enrolment rather than half-checking', async () => {
  const jane = await makeCredential();
  const { bind } = setUp({ claimKeys: 'not json at all' });

  const { response, body } = await bind(jane, { claim: claimFor('jane@example.com') });

  assert.equal(response.status, 500);
  assert.match(body.detail, /CLAIM_KEYS/);
});

/* ------------------------------------------------------------ the import */

test('the browser’s claim verifier runs here unmodified', async () => {
  // index.js imports assets/js/claims.js rather than keeping a second copy.
  // The day somebody adds a top-level `window` to that file, this fails here
  // instead of in production.
  const claims = await import('../../assets/js/claims.js');

  assert.equal(typeof claims.verifyClaim, 'function');
  const checked = await claims.verifyClaim(claimFor('jane@example.com'), JSON.parse(CLAIM_KEYS));
  assert.equal(checked.ok, true);
  assert.equal(checked.payload.repo, REPO);
});
