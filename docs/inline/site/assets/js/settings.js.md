# `site/assets/js/settings.js`

Moved out of the file. Unreviewed.

## 1

Above `import { act, contentHash } from './broker.js';`

Editing a member site's settings file.

Same passkey as /upload/, different verb. The member signs in, the page
fetches their own _data/site.yml from their own repository, and they edit
the text.

THE TEXT, NOT A FORM
--------------------
That file is mostly comments, and those comments are the only documentation
a member has for what the settings do. Parsing the YAML and re-serialising
it would strip every one of them on the first save. So the editor is a
textarea, what they see is the file, and what gets committed is what they
saw. See _data/settings.yml for the full argument.

THE SHA IS NOT DECORATION
-------------------------
GitHub hands back the blob SHA with the file, and it goes back with the
edit. If somebody changed the file in between — the member on another
device, or us — GitHub refuses the write instead of silently discarding
their change. Losing that field turns a rare conflict into a rare, silent
data loss.

## 2

Above `async function load() {`

Fetch the file the member is actually running, not a copy of the template.

The contents API returns the text and the SHA together, which is why it is
used here rather than raw.githubusercontent — one request, and the SHA is
needed for the write anyway.

## 3

Above `throw new Error(`

Unauthenticated API requests are capped per address, and a shared
network can exhaust it. Worth naming, because "try again later"
sounds like a brush-off when it is literally the fix.

## 4

Above `function check() {`

A smoke check, deliberately not a parser.

There is no YAML parser in the browser here and adding one would be a
dependency for a page that already has a real validator behind it — the
workflow refuses to merge anything that does not parse. So this catches the
two mistakes people actually make, and says nothing about the rest rather
than implying it checked.

## 5

Above `const tabLine = text.split('\n').findIndex((line) => /^\s*\t/.test(line));`

Tabs are invalid for indentation in YAML, and an editor that helpfully
inserted one leaves no visible trace.

## 6

Above `const topLevel = (body) =>`

Losing a whole setting is usually an accident — a stray selection, a
paste over the top. Reported rather than blocked, because removing one on
purpose is legitimate.

## 7

Above `el('settings-status').textContent = 'Confirming with your device…';`

A SECOND PROMPT, ON PURPOSE
---------------------------
Signing in was wayfinding — it told this page which site the passkey
belongs to, and proved nothing to anybody else. This is the ceremony that
counts, and it is bound to these exact bytes, this path and this SHA. The
member is approving one specific edit, at the moment they make it, rather
than having approved "editing" some minutes ago.

## 8

Above `original = text;`

What was saved is now what is there, so a second save should say nothing
has changed rather than writing the same bytes again.
