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

## Documentation is gathered, not hung at the leaves

Autumn, 2026-10-05: agents could not find what they needed, because it was
spread through the opening comments of hundreds of files.

- **Every document lives under `docs/` and is reachable from
  [`docs/README.md`](docs/README.md).** The exceptions are files a tool reads
  in place: agent instructions (`AGENTS.md`, `CLAUDE.md`), the one-line
  `PROFILE.md` markers `machines/binding` looks for, and what ships to member
  sites (`site-template/`, `member-site-core/`).
- **A machine's root instructions live in its profile, in this repository.**
  The machine's own `~/code/CLAUDE.md` just points at that path in its mirror
  (`@refs/fcpublicmedia.org/machines/<profile>/code/AGENTS.md`). A root keeps
  no notes of its own that the repository does not hold.
- **A comment is one line.** Anything longer goes in
  `docs/inline/<path>.md` under a numbered heading, and the file keeps one
  line in its place: `see docs/inline/<path>.md#<n>`. Usage text a script
  prints is output, not a comment.
