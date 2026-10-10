# `site/assets/js/upload.js`

Moved out of the file. Unreviewed.

## 1

Above `import { signIn } from './passkey.js';`

Submitting an episode.

Sign in with the passkey registered at /authorize/, describe the episode,
and produce a well-formed entry for the member's own site. A feed entry with
a future drop date IS the submission — /community/ reads it as "coming up"
and nothing else has to happen for us to know about it.

WHAT THE SIGN-IN IS FOR
-----------------------
Working out which member site this person is submitting to, and nothing
else. The passkey's user handle carries the repository, so signing in is how
the page knows whose site to write an entry for.

It is not a security boundary — see the note on signIn() in passkey.js. When
the broker exists it issues the challenge and checks the signature; until
then nothing is written anywhere as a result of it, so there is nothing to
forge your way into.

## 2

Above `function withVenueOffset(date, time) {`

Build an ISO timestamp with COLORADO's offset, not the browser's.

A producer submitting from a hotel two zones over must not schedule their
own episode two hours out. Everything else on this site follows the same
rule — see the note in _data/classes.yml about times carrying an offset.

Two passes because the offset depends on the instant, and the instant
depends on the offset: guess at UTC, ask what Colorado was doing then, apply
it, and ask again. The second answer is right except within an hour of a DST
transition, where an hour either way is the worst case.

## 3

Above `return null;`

An engine without longOffset support. Better to say so than to write
a timestamp that is quietly in the wrong zone.

## 4

Above `const words = entry.summary.split(/\s+/);`

Folded scalar, wrapped so the file stays readable rather than one very
long line nobody can diff.

## 5

Above `el('copy-status').textContent =`

Everything the member typed is still here, so falling back to handing
it over loses nothing — making them retype it would.

## 6

Above `const soon = new Date(Date.now() + 7 * 86400000);`

Default the drop to next week, which is the common case, rather than
leaving someone to work out what date next Friday is.

## 7

Above `const notice = document.querySelector('[data-no-destination]');`

Only shown when there is genuinely nowhere to upload to, so it never
contradicts a working uploader.
