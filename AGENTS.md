# Board's wording is authoritative. Do not improve it.

When the board's phrasing and ours or council's differ, the board's wins.

## Wix

Without exception, any Wix connectors or ready authorizations shall be
READ-ONLY interfaces.

## Personal-machine conventions do not reach this repository

This one is org-owned, public, and built by a host. Guidance about unifying
tooling across a personal projects folder is not guidance about here.

Specifically: **no `.tool-versions`.** Cloudflare's builder detects it
undocumentedly and the file's presence alone can fail the build. `.ruby-version`
is the pin, the `Gemfile` carries a `>= 3.2` floor, and there is no second file
to keep in agreement. See `docs/deploying.md`.
