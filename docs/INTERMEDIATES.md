# Intermediates: what we hand over to be deployed

`status: design, not built.` Written 2026-09-24 on the media node (machines/kiosk-1),
from Autumn's direction that day. The builder half is jekyll-enough, which built this
whole site with zero gaps in a browser on that box (FCCN-ANTIBODY/jekyll-enough#1).

**Read with [`member-sites.md`](member-sites.md), "Intermediates are the deliverable" and
"How an update reaches us"**, which record the decision in Autumn's words: intermediates
are what we deliver, signed by us, possibly a folder, and carried as a tar of a file
structure where a network cannot be assumed. That page says *that* and *why*. This page
says **what is inside a domain's folder**, and how far each file inside it got.

The idea comes from anecdote.channel's `docs/intermediates.md`: *an intermediate overrides
the sources it was built from, by convention, not by force*, and *a stale or missing
intermediate is never a refusal. It falls through to rendering from source.* This page is
what that means for a whole domain rather than a single page.

## Why we make one

> "We commit source; station-node builds and deploys." Autumn, 2026-09-24.

So the only thing we control about what goes live is **what we commit**. The
intermediate is how we bake our own concerns in, so that rendering it no longer needs
our data references or a build system that understands our whole site. station-node
relays it. It does not have to understand it.

**No Ruby and no real Jekyll are used to make it.** It is built by jekyll-enough, in a
browser, on the media node. That is the proof being made.

## One folder per deployable domain

A single file is enough for a page. A domain is many pages, so **a domain's intermediate
is a folder**:

    _intermediates/
      www.fcpublicmedia.org/        from site/
      you.fcpublicmedia.org/        later: from a mounted .you-engine, the way
                                    discoverywritten.com publishes you.discoverywritten.com

Each folder is deployable on its own. The name is the domain it deploys to, so the relay
needs no mapping table. It lives at the repository root, outside `site/`, for the reason
`brand/` does: anything under the build root is one `exclude:` entry away from being
published by accident.

## What is in a folder

    www.fcpublicmedia.org/
      INTERMEDIATE.yml     the manifest: read this first
      _site/               fully rendered. Preferred. Serve this if it is fresh
      _layouts/            baked: site.* resolved, only page-local Liquid left
      _includes/           only the includes that survived collapse
      about.md, …          pages, baked, front matter kept
      podcasts/<name>.md   collection documents lifted to plain pages at their URL
      _data/, _config.yml  ONLY if some file could not be baked and still needs them

It is a **source distribution with a build beside it.** The source-shaped content *is*
the intermediate. It is source that is better than our source: still Jekyll-shaped and
still renderable, but no longer needing our `_data/`, our collections, or our includes
that only forward to other includes. It is what a markdown browser, or any consumer that
is not Jekyll, reads. `_site/` rides beside it for a consumer that only serves HTML,
and for that consumer it is preferred. It never replaces the content. A folder of
rendered HTML alone would serve one kind of consumer and strand the rest
(`member-sites.md`, "What it is source for").

## Halfway is a normal state: each file says how far it got

Every file in the manifest carries a **degree**:

| degree | what the file is | what rendering it needs |
|---|---|---|
| `rendered` | final HTML at its output path, under `_site/` | nothing: serve it |
| `baked` | our data and site-wide references resolved, forwarding includes collapsed, collections dissolved. Liquid remains only where it reads `page.*` or `content` | its layouts and any surviving includes. **Not** `_data/`, **not** a whole-site build |
| `source` | the original file, byte for byte | everything the original needed, which then ships in the folder too |

**`source` is the fail-through, and it is allowed.** If the reduce pass cannot bake a
file, it passes that file through raw, and whatever it depends on (`_data/`,
`_config.yml`, includes) travels with it, so the folder stays buildable. A folder that
is `source` all the way down is just a copy of our site: correct, and useless to a
builder that cannot run Jekyll. It is still never wrong. It is only unreduced.

### What a consumer owes a file it cannot interpret

Autumn, 2026-09-24 (`member-sites.md`): *"if your intermediate happens to be raw source,
or it happens to be fully cooked HTML, it falls inside parameters"*, and outside them
*"we want to promise that it degrades gracefully. So we're fine showing the raw Liquid.
We can probably mark it up a little, but we want it to be clearly not interpreted."*

So a renderer that meets Liquid it cannot run **shows it as itself, visibly
uninterpreted.** Markup is allowed only if it makes that state more obvious. The failure
is the other way round: something that *looks* rendered but is not, such as a blank where
a loop was, or an empty frame where an include was. It is the same rule as `unwitnessed` on
the kiosk's depot panel: a surface does not present what it could not confirm as though
it had been confirmed.

This site is fully static, so every file here can reach `rendered`, and `baked` exists
beside it anyway. The lower degrees are for what is known only later: a page that reads
something at request time, a partial someone else will render into their own frame, or
a member site delivered as partials that still contain Liquid.

## The manifest

    domain: www.fcpublicmedia.org
    kind: source-distribution
    prefers: _site
    built_from: sha256:…      # over the sorted (path, sha256) of every source file read
    builder: jekyll-enough@<commit>, in <browser> on <host>
    files:
      about.md:                { degree: baked, out: about/index.html }
      _site/about/index.html:  { degree: rendered }
      …
    gaps: []                  # anything jekyll-enough named but could not do
    signature: …              # by FCPM's key, over this manifest. See below

**It is signed by us**, which is the decision in `member-sites.md`. Because the manifest
names every file with its hash, signing the manifest signs the folder. The shape exists in
`site/bin/mint-claim.py`, which signs with a private key and verifies against the public
half in `site/_data/identity.yml`. But no key has been minted (`keys: []`), so a key
ceremony comes first, and where that private key lives is a decision. It must not live
in this repository, and it should not be on a kiosk anyone can walk up to.

**Staleness is checked, not guessed.** `built_from` is a hash over the sources, so anyone
holding the sources can recompute it. If it no longer matches, the intermediate is stale,
and the right move is to render from source. It is never "refuse to deploy", and never a
blank page.

## What "reduced" means, concretely

The reduce pass runs jekyll-enough over the site. Instead of stopping at HTML, it also
keeps a source-shaped copy of each file with everything knowable at build time resolved:

- `site.data.*`, `site.<collection>`, `site.pages` and `_config.yml` values become literals.
- An `{% include %}` with fixed arguments that renders nothing of its own (a **forwarding
  node**) is collapsed into what it forwards to. An include that renders something and
  takes only page-local arguments stays, as a smaller include.
- A collection document becomes a plain page with its permalink written into its front
  matter, so no collection machinery is needed downstream.
- What cannot be decided at build time stays as Liquid, and the file is `baked`, not
  `rendered`.

## Not decided

- Whether `_intermediates/` is committed on every change, or only when the manifest's
  `built_from` moves. The second avoids churn. The first is simpler to reason about.
- How station-node's relay is told to prefer `_intermediates/<domain>/_site`. The
  manifest is written to be that instruction, and the relay's side is theirs.
- The you-engine: mounting it is its own pull request, and so is its `you.yml`.
- The signing key's custody. See above.
- Whether a manifest's per-file hashes are sha256 of the bytes as committed, which is
  what makes the tar form and the git form verify the same way. This is the likely answer,
  and it is not yet a decision.
