# `worker/src/github.js`

Moved out of the file. Unreviewed.

## 1

Above `import { contentHash as hashOf } from './intent.js';`

Writing to a member's repository.

The credential comes from app-auth.js, one repository at a time, and this
file never sees where it came from. That is the point of the seam: the
question "what is allowed to write here" is answered in one place, by an App
installation, and not by whatever each call site happens to pass.

WHY THE DEFAULT IS A BRANCH AND NOT THE MAIN LINE
-------------------------------------------------
A member editing their settings file can produce YAML that does not parse.
Committed straight to the default branch that takes their site down until
somebody notices. On a branch, the repository's own checks run first and the
merge only happens if it builds — so the worst case is an open pull request
and a message, instead of a broken site and a phone call.

site/_data/settings.yml has the same argument written for the person reading it.

## 2

Above `async readFile({ repo, path }) {`

Read a file, authenticated.

Not raw.githubusercontent: that is served with cache headers measured in
minutes, and this read is the first half of a read-modify-write. Getting
a stale device list here would mean writing back a list with somebody
else's change removed from it.

Returns { ok: true, content, sha } — with `content: null` and `sha: ''`
when there is no file yet, which is an ordinary first enrolment — or
{ ok: false, reason, detail }.

## 3

Above `async writeFile({ repo, path, content, sha, contentHash, message, mode = 'branch' }) {`

Put `content` at `path`, and return where it can be looked at.

`sha` is the blob SHA the page read before editing. Sending it back is
what makes GitHub refuse the write if somebody changed the file in
between, rather than silently discarding their change. An empty string
means the file did not exist, which is a legitimate first write.

Returns { ok: true, mode, url } or { ok: false, reason, detail }.

## 4

Above `const issued = await credential(repo);`

One token, minted for this repository and this write. If the App is
not installed here, that is the answer — and it is the same answer as
"this site was revoked", which is the point of revoking that way.

## 5

Above `const alreadyThere = async (branch) => {`

A rejected SHA has two meanings and they need opposite answers.

Somebody else changed the file: refuse, and tell the member so they
can go and look. This edit already landed — a double tap, or a retry
of a request whose answer never arrived: say it worked, because it
did. Telling that member it failed is how you end up with two.

Only the bytes can tell them apart, so go and read them.

## 6

Above `if (!created.ok && created.status !== 422) {`

422 is "already exists", which is what a retry of the same edit looks
like. The branch name is derived from the content, so the one sitting
there is this edit and not somebody else's.

## 7

Above `let repeated = false;`

The branch was forked from the default one, so the SHA the member read
is still the right SHA here — unless this edit is already on it, which
is exactly what a retry looks like.

## 8

Above `if (pull.status === 422) {`

Also 422 when one is already open for this branch — the same retry
case as above. Find it rather than reporting a failure for something
that has already happened.

## 9

Above `return {`

The file IS written; only the pull request is missing. Saying so beats
reporting a failure the member would respond to by editing again.
