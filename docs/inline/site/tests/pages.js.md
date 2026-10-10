# `site/tests/pages.js`

Moved out of the file. Unreviewed.

## 1

Above `const PAGES = [`

Every page the smoke tests visit. Add a page here and it is covered by all
of them at once.

## 2

Above `const THIRD_PARTY = [`

Hosts we embed from. Requests to these are expected and are reported
separately from same-origin failures, because "Cablecast is down" and "we
shipped a broken link" need different responses.

## 3

Above `'booqable.com',`

Booqable's embed on /reserve/. It renders the products inline rather
than in an iframe, but the script itself still comes from their asset
host, and it does not load on a runner with no route to it. That is their
availability, not our page being broken — which is the whole reason this
list exists. Whether the mount points actually get hydrated is a question
for the @external suite, where a third party being down is allowed to be
a red mark rather than a build failure.

## 4

Above `const THIRD_PARTY_CONSOLE = [`

Console output we know comes from an embedded player rather than our code.
Matched by text as a backstop, because not every console message carries a
usable source URL — an iframe error with an empty location would otherwise
be blamed on this site.
