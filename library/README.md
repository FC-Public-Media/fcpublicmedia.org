# Holdings

Empty is a statement here, not a gap. See the branch README.

Nothing in this directory is consulted by the site build on `main`. A holding
that the site needs is copied into `site/_data/` by a script in `site/bin/`,
which is how every other external source already reaches the site — the
Cablecast catalog, the calendar, member feeds, the nonprofit registry.

## `trade/` is the tenant list

Settled in `docs/TENANCY.md` on `main`, after this branch was made. A member's
site is **its own repository**, pinned here as a submodule. `sites/<name>/` in
this repository does not happen.

Three properties, and the library already has all three:

- **Nothing is hydrated eagerly.** A pin is a reference until somebody asks for
  it by name, so a hundred member sites cost a hundred lines rather than a
  hundred checkouts.
- **They do not all have to be here.** An unfilled gitlink is the resting state,
  not a broken checkout.
- **The gitlink is the canonical list.** Version-controlled, reviewable, and it
  cannot drift from what was committed — which is the property a list in a
  database does not have.
