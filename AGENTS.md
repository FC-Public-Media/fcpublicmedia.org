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

- **Every document is reachable from [`docs/README.md`](docs/README.md).** A
  doc may live beside what it describes, such as a profile's `PROFILE.md` or a
  trove's `README.md`, but the index links to it. A doc the index does not
  link to is not finished.
- **A machine's root instructions live in its profile, in this repository.**
  The machine's own `~/code/CLAUDE.md` just points at that path in its mirror
  (`@refs/fcpublicmedia.org/machines/<profile>/code/AGENTS.md`). A root keeps
  no notes of its own that the repository does not hold.
- **No bulky header comments.** A file says what it is in at most five lines,
  and names the doc that explains it. Rationale, history, usage tables and
  "why not X" go in that doc. A comment on a line that would surprise a reader
  is still welcome.
- **Existing long headers shrink when their file is next touched.** The
  explanation moves to the doc, and nothing is lost. This is not a sweep.
  `docs/OPEN.md` lists the worst of them.
