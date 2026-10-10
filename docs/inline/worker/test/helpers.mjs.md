# `worker/test/helpers.mjs`

Moved out of the file. Unreviewed.

## 1

Above `export const b64u = (bytes) => {`

Building real assertions to test against.

Nothing here is a mock of the verification. The tests generate an actual
P-256 key, assemble actual authenticator data, and produce an actual ECDSA
signature — because the failures worth catching in this code are failures of
byte layout, and a mock would agree with whatever the code already does.

rawToDer below is written from the DER rules rather than by inverting
derToRawSignature. Two implementations of the same encoding, arrived at
separately, is what makes the round trip a check instead of a mirror.

## 2

Above `export function fakeGitHub(byRepo = {}, { blobs = {}, defaultBranch = 'main', app = noApp() } = {}) `

GitHub, enough of it.

Both hosts, because the broker uses one fetch for both: raw.githubusercontent
for the device list and the API for the write. Stateful rather than
canned — the interesting questions are "does a retry land in the same place"
and "does a stale SHA get refused", and neither can be asked of a fake that
answers the same thing every time.

`byRepo` maps a repository to its .auth/devices.json. `undefined` is a 404
(no list) and `null` is a 500 (GitHub having a bad minute).

## 3

Above `const files = new Map(); // "repo#branch/path" -> { sha, content }`

Files are per branch, because that is what makes a retry different from a
conflict: the second attempt writes to a branch that already holds the
first attempt's bytes, and a fake that tracked one copy per repository
could not tell the two apart. `blobs` seeds the default branch.

## 4

Above `for (const [repo, held] of Object.entries(byRepo)) {`

One repository, two ways of reading it. A device list given as `byRepo` is
also a file in the repository, so the authenticated read finds the same
thing the cached raw copy serves — anything else would be a fake where the
two disagree, which is precisely the bug worth not having.

## 5

Above `const minting = url.match(/^https:\/\/api\.github\.com\/app\/installations\/(\d+)\/access_tokens$/);`

---------------------------------------------------------- being an App

The JWT is verified here rather than accepted. A broker that signed
nonsense would look identical to one that signed correctly, right up
until it met the real GitHub.

## 6

Above `if (byRepo[repo] === null && path === DEVICES) return json({ message: 'oh dear' }, 500);`

`null` in byRepo means GitHub is having a bad minute, and it has to
mean that through both readers or the test is only half a test.

## 7

Above `if ((files.get(key)?.sha || '') !== (body.sha || '')) {`

The SHA is the whole point: a write carrying a stale one is refused
rather than allowed to discard somebody else's change.

## 8

Above `export async function fakeApp({ appId = '123456', installed = [], now = () => 1_760_000_000_000 } = `

A real RSA key pair standing in for a GitHub App.

Generating one costs about a tenth of a second, so it is done once per test
file rather than per test. `verify` checks the signature the broker actually
produced against the public half, which is the only way to find out whether
the JWT assembly is right.
