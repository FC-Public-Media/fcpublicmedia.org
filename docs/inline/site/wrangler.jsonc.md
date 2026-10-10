# `site/wrangler.jsonc`

Moved out of the file. Unreviewed.

## 1

Above `{`

Cloudflare Workers configuration.

This file exists to stop `wrangler deploy` from trying to configure itself.

Without it, wrangler runs auto-configuration, decides the project is a
Node project, and re-runs the build command prefixed with npx — producing
`npx bundle exec jekyll build`, which fails with "could not determine
executable to run" because bundle is not an npm package. The Jekyll build
has already succeeded by that point; the failure is purely wrangler
guessing.

With this file present, wrangler skips auto-configuration and just uploads
what is already in _site.

There is no Worker script here on purpose. This is a static site: no
`main`, no runtime, nothing to execute. Cloudflare serves the files.

## 2

Above `"html_handling": "auto-trailing-slash"`

Folder index files are served with a trailing slash, individual files
without. This matches Jekyll's pretty permalinks (/classes/ from
_site/classes/index.html), so no URL changes shape between local
preview and production.
