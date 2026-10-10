# `worker/test/write.test.mjs`

Moved out of the file. Unreviewed.

## 1

Above `import { strict as assert } from 'node:assert';`

Writing the file.

The verification is tested in broker.test.mjs and is not repeated here; what
these are about is what happens after it passes, and the two failures that
matter are opposite in shape. Writing when it should not have is the obvious
one. Reporting a failure for a write that actually landed is the other, and
it is worse in practice: the member edits again, and now there are two.

## 2

Above `async function setUp({ writeMode, mayPublish = true, blobs = {}, token = 'ghp_test' } = {}) {`

A broker with a token, a repository, and one registered device.

`blobs` seeds what GitHub already holds at a path, so a test can arrange for
the file to have moved on since the member read it.

## 3

Above `const { hub, save } = await setUp();`

The reason /settings/ is a textarea. If a comment can be lost anywhere in
this path, the argument for the whole page collapses.

## 4

Above `const { hub, save } = await setUp();`

A member who taps save twice, or a page that retried a request it never
saw the answer to. The branch name comes from the content hash, so the
second attempt finds its own work rather than making a second copy.

## 5

Above `assert.equal(first.body.repeated, false);`

Reported as a repeat rather than as a fresh save, so the page is not
claiming something happened that did not.

## 6

Above `const { hub, save } = await setUp({ blobs: { [${REPO}/${PATH}]: 'a'.repeat(40) } });`

The member read the file, somebody else changed it, the member saved. The
SHA is the only thing standing between that and a silent overwrite.

## 7

Above `const { hub, save } = await setUp();`

Both are genuine signatures from a device that is allowed to publish. The
difference is what the member was asked to approve, and that difference
has to survive all the way to the write.

## 8

Above `const declared = await service.fetch(post('/challenge', { action: 'verify', repo: REPO }));`

The half it is configured for keeps working. A broker that refused to
prove anything because it cannot write would be worse than one that does
the job it is set up for.
