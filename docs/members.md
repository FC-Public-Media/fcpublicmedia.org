# Members

FCPM builds and lists sites for its members' projects. A project is one
repository, and its member owns it; FCPM holds a pointer to it and a policy
about it. This doc covers the member-site factory, the directory, and the
library and wizards as they stand. Plans and open questions are in
[`OPEN.md`](OPEN.md).

## Tenancy

| term | meaning |
|---|---|
| project | the unit of tenancy: one repository, one site. A member may hold several, and draws the line between them |
| tenant | a project whose site FCPM builds and publishes |
| core | `member-site-core/`, the managed half every member site is built with |
| eject | a member taking their site somewhere of their own; they stay in the list as `listed` |

- A member's site is their own repository, mounted here as a submodule and
  entered in `sites.yml`. The gitlink records where it is; `sites.yml` records
  what FCPM does about it.
- Managed, ejected and affiliated projects are one kind of entry in one list.
  Only the role differs ([sites.yml](#sitesyml)).
- Member site repositories hosted here are public. A publishing state is scheduling,
  never secrecy; a member who needs secrecy ejects and goes private. Say so
  first whenever the offer is described.
- A member site is a `trade` object in the library; what plays on it is media.
- Station-node is the prototype for the shape of a tenancy, not for its role.
  Its workflows and most of its mechanisms carry over; its posture of
  observing itself for nobody does not. What a tenant's machinery logs, who
  may read it, and what happens to it when the tenant leaves are owed to FCPM
  and to the tenant.
- The site exists for a member who loses momentum for want of a tool, an
  answer or support at the moment they need it. It makes their work
  addressable, so a service (stem this audio, enhance this video) can be
  offered against it. Local discoverability is a separate aggregator, not a
  constraint on the factory.

## Member repository and core

```
site-template/          what a member's repository holds
  _data/site.yml        settings; the one file an editing UI writes
  _data/programs.yml    one entry per program
  .gitignore            keeps build output and finished media out of git

member-site-core/       what FCPM supplies at build time
  _config.yml           permalink: pretty; no plugins, no theme
  _layouts/default.html markup; links the feed and the stylesheet
  assets/css/site.css   the visual design
  index.html            the page, driven entirely by _data
  feed.xml              /feed.xml, the contract with FCPM
  Gemfile               jekyll ~> 4.4, for a site that ejects
```

- A member repository needs no markup, Gemfile, lockfile or Ruby pin. Every
  site is built with `site/`'s toolchain: given `--source`, Jekyll reads
  `<source>/_config.yml`, not the one in the working directory.
- `site-template/` carries no `.html`, `.xml` or `.css`
  (`bin/test_build_sites.py` checks). A member who wants other markup ejects.
- `site-template/` has no README. The one a member reads is theirs to write.
- `site/bin/check-template.py`, run by `.github/workflows/smoke.yml`, composes
  the template with a fixture from `site/tests/fixtures/` and parses the
  resulting feed with this repository's own reader.

### `_data/site.yml`

| key | |
|---|---|
| `name`, `tagline` | the site's title and description; `_config.yml` repeats neither |
| `producer`, `location` | who makes it, and where |
| `about` | a short paragraph |
| `email`, `website` | skipped when blank |
| `platforms` | `name` and `url` of where people subscribe; blank URLs are skipped |
| `feed.title`, `feed.description` | default to `name` and `tagline` |
| `feed.months` | programs older than this leave the feed (default 24); the page keeps them |

### `_data/programs.yml`

`programs:` is a list. It ships empty, with one commented example.

| field | |
|---|---|
| `title` | required |
| `status` | `draft`, `scheduled` or `released` ([Publishing states](#publishing-states)) |
| `drop` | when it goes out; required unless `draft`. Must carry a UTC offset, `"2026-08-14T18:00:00-06:00"`: Colorado is -06:00 in summer, -07:00 in winter |
| `summary` | a paragraph; what FCPM's site shows |
| `image` | a thumbnail URL |
| `links` | `name` and `url` where it can be watched; the first with a URL is the item's link and guid |
| `artifact` | `url`, `type` and `bytes` of the finished file, carried as the feed's `<enclosure>` |
| `runtime` | `"12:40"` |

Finished files stay out of git: `.gitignore` excludes `*.mp4 *.mov *.wav *.aiff
*.mkv *.prproj`. `artifact.url` points at wherever the member already keeps
them, and the enclosure is how the file reaches FCPM.

### Feed

`/feed.xml` (RSS 2.0, with `media:thumbnail`) is the whole contract between a
member site and FCPM. `site/bin/sync-feeds.py` reads the feeds listed in
`site/_data/feeds.yml` into `site/_data/member_programs.json`
([`programming.md`](programming.md)). A member who never looks at their own
site stays listed as long as the feed parses.

## Publishing states

| `status` | on the page | in the feed | meaning |
|---|---|---|---|
| `draft` | no | no | being worked on; anyone reading the repository can see it |
| `scheduled` | yes, marked *Coming* | yes, with a future `pubDate` | finished and waiting for a drop day, which is how FCPM sees it coming |
| `released` | yes | yes | out |

## sites.yml

The canonical list of every site this node knows about.

| key | |
|---|---|
| `core` | the directory composed under every `scaffold` and `tenant`: `member-site-core` |
| `publish_to` | where built tenants are committed: `site/member-sites`. It must be inside the build root `site/`, or nothing serves it |
| `sites` | entries: `path` and `role`, and optionally `name`, `domain`, `deliver`, `why` |

| role | built | published by `--publish` | its failure |
|---|---|---|---|
| `site` | yes, whole | no: the host's git build publishes it | ours: exit 1 |
| `scaffold` | yes, composed | never | ours: exit 1 |
| `tenant` | yes, composed | yes | reported, exit 0; exit 1 with `--strict` |
| `listed` | never, and never fetched | no | none |

- `name` is the public address: the subdomain label and the folder under
  `publish_to`. It defaults to the last segment of `path` and is kept apart
  from it, so moving a checkout cannot change an address.
- `deliver` is how a host deploys the site. `source`: the host runs its own
  build in `path`, the fallback that needs no machine of ours. `intermediate`:
  the host serves `_intermediates/<domain>/`, which must hold
  `INTERMEDIATE.yml`, `wrangler.jsonc` and `_site`, and the entry must name a
  `domain`. `--deploy-root DOMAIN` prints the delivery and the root directory a
  host should be set to. See [`station.md`](station.md#intermediates) and
  [`site.md`](site.md#deploy).
- Listed today: `site` (`www.fcpublicmedia.org`, `deliver: source`) and
  `site-template` (`scaffold`). There are no tenants, and
  `site/_data/member_sites.json` lists none.

## Build

```
python3 bin/build-sites.py                       build everything buildable
python3 bin/build-sites.py --list                show the manifest, build nothing
python3 bin/build-sites.py --only PATH           build one
python3 bin/build-sites.py --strict              a tenant failure is fatal too
python3 bin/build-sites.py --publish             publish tenants, prune, rewrite the listing
python3 bin/build-sites.py --deploy-root DOMAIN  print how DOMAIN is delivered, and its root
```

It needs PyYAML. Each entry is built on its own, and the run continues past a
failure:

1. A composed site is staged in a temporary directory: `core` first, then the
   site's own files on top. `_site`, `.jekyll-cache`, `.git`, `vendor`,
   `Gemfile.lock` and `.DS_Store` are never staged.
2. If the site carries a file `core` also provides, the result is `diverged`
   and nothing is built. That collision is the eject signal; the builder never
   builds over a member's own copy.
3. `bundle exec jekyll build --source <staged> --destination <path>/_site` runs
   from `site/`.

| status | when | fatal |
|---|---|---|
| `built` | the build exited 0 and wrote `index.html` | never |
| `failed` | a non-zero exit (stdout and stderr kept, since Liquid errors land on stdout), a missing core, or a zero exit with no `index.html` | for `site` and `scaffold`, or with `--strict` |
| `diverged` | the site carries managed files | for `scaffold`, or with `--strict` |
| `absent` | nothing at `path` (for `site`, no `_config.yml`); for a tenant that is an unhydrated gitlink, the list's normal state | for `site` and `scaffold` only |
| `skipped` | the role is `listed` | never |

Exit 1 when anything is fatal; exit 2 for an unknown `--only` path or
`--deploy-root` domain, or `--publish` with no `publish_to`. It never fetches,
hydrates or deploys.

### Publishing

`--publish`, after building:

- copies each built tenant's `_site` to `site/member-sites/<name>/`, replacing
  what was there;
- keeps a tenant that failed this run at what it published last time;
- prunes every direct subdirectory of `site/member-sites/` that is no longer a
  `tenant` entry, which is how delisting takes a site down. Files at that root
  (`.gitkeep`) stay. The root must resolve inside the repository and not be it,
  checked before anything on disk is read. `--only` prunes nothing, since every
  site it did not look at would seem unlisted;
- writes `site/_data/member_sites.json`, `{"prefix": "member-sites", "sites":
  [{"name": …}]}`, sorted and with no timestamp, so it changes only when the
  list does. FCPM's own pages render the listing from it.

It commits nothing. `python3 bin/test_build_sites.py` runs the tests; all but
one use a fake runner, and that one really builds the listed sites, skipping
when bundler is absent.

## Publish workflow

`.github/workflows/publish-member-sites.yml` keeps the cadence: Thursdays at
13:00 UTC (07:00 in Denver in summer, 06:00 in winter), and on demand. FCPM
promises a day it can keep, not real time; a member who commits on a Friday
appears the next Thursday.

1. Checks out with `submodules: recursive`, so pinned tenants are present.
2. Sets up Ruby in `site/` and installs PyYAML. `ruby-version: .ruby-version`
   is resolved inside `working-directory`; a path there fails as an unknown
   engine.
3. Runs `build-sites.py --publish` under `shell: bash`, for `pipefail` through
   `tee`, and copies the log into the run summary.
4. Stages `site/member-sites` and `site/_data/member_sites.json` before
   comparing, because a newly published site is untracked; the committed
   `site/member-sites/.gitkeep` keeps that pathspec matching when there are no
   tenants. Commits `Publish member sites: N listed` only if something changed.

- Runs never overlap and never cancel each other; two writers in
  `site/member-sites/` could publish a half-composed site.
- It does not deploy. The host's git build publishes the commit like any other
  change to `site/`. Nothing may add a second path that publishes a member
  site, or a trigger that can fire twice for one.
- Only failures of ours turn it red. FCPM builds, so a tenant repository needs
  no `.github/`.
- It runs on no push, so a change to `sites.yml` takes effect at the next run.
- Serving `<name>.fcpublicmedia.org` from `site/member-sites/<name>/` needs a
  wildcard rewrite that does not exist yet ([`site.md`](site.md#deploy)).
  Member sites are built with no `baseurl`.

## Ejection and withdrawal

FCPM owns nothing of a member's. Its claim is one gitlink and one entry.

| a member | what happens |
|---|---|
| carries a managed file | `bin/build-sites.py` reports `diverged` and builds nothing for them; the run stays green |
| ejects | their role becomes `listed`: enumerated, never built or fetched. They are owed the core as a commit to their repository, so their site builds alone; the tool that writes it is not built |
| asks to be removed | their entry is deleted, and the next `--publish` prunes their site and drops them from the listing |
| withdraws their feed | their source is removed from `site/_data/feeds.yml`; the sync runs on that push and drops their items |
| goes private | a submodule to a private repository cannot be cloned, so they are unhooked |

Tell members plainly:

- Taking their own feed down does not withdraw them. It looks like an outage,
  and `site/bin/sync-feeds.py` carries their items forward. Withdrawal is an act on
  FCPM's list.
- Git history keeps everything ever committed here, including published sites
  and feed items. That cannot be undone.
- A hosting account is a deploy target, not a system of record. The source is
  in the member's repository, and moving accounts is rebuilding it elsewhere.

## Directory

This repository is an Atlas (a directory) and the first Tell (an inbox
fronting members' data piles) listed in it. It mounts `.atlas-engine` and
`.tell-engine`. They read their data from the repository root, outside the
build root, so the site publishes none of it.

```
member data pile ──registers to──▶ our Tell ──registers to──▶ our Atlas
(private repos, FCPM's org)          tell.yml                   atlas.yml
                                     keys/tell.*                _data/tells.yml
```

| file | |
|---|---|
| `tell.yml` | our Tell: `id`, `name`, `url`, `scope`, `reports`. The signer is read from `keys/tell.fpr`, never copied in |
| `atlas.yml` | our Atlas; read only to peer with another Atlas |
| `keys/tell.pub`, `keys/tell.signers`, `keys/tell.fpr` | the Tell's public signer, written with LF endings because piles compare them byte for byte. A pile pins `tell.fpr` |
| `_data/tells.yml` | the Tells our Atlas lists. Registration appends to it, and fails if `_data/` is missing |

- Data piles are FCPM's private multi-tenant repositories in the
  FC-Public-Media org, mounted here when needed. A pile may attach to several
  Tells. Deliveries to a pile are `age`-encrypted, and delivery is completion.
- Registration is consent: an Atlas merges a Tell's PR. Here it is
  self-consent.
- The Atlas keeps history for now; the Tell is transient.
- An Atlas enforces only its own constitution when it admits a Tell, and a
  human operator makes that call.

### Signer

`machines/kiosk-1/door.py tell mint` on kiosk minted the signer, an ed25519 key commented
`tell-delivery-signer`. Its private half is only in kiosk's Windows Credential
Manager, as `fcpm-tell-signer`. `mint` refuses when a signer exists; losing it
means minting again, and every pile re-pins.

Not minted: `TELL_SEED_IDENTITY` (`age`, needed for delivery; `age` is not on
kiosk), `TELL_QR_SECRET` (polls), and an Atlas signer (peering).

### Registering

On kiosk, with `machines/kiosk-1/door.py`:

```
door.py tell            the published signer, and whether this machine holds its key
door.py tell register   .tell-engine/bin/register pr, against this repository
```

`register` clones `main`, branches `tell/fort-collins/fcpublicmedia` (the
branch is the claim), appends our entry to `_data/tells.yml` in a commit signed
with the Tell's key, and opens a PR here. The key is written to a temporary
file for that one call. Merging the PR is the Atlas's consent; checking its
signature against `keys/tell.fpr` is manual.

## Library and wizards

| piece | where | state |
|---|---|---|
| library engine | `.library-engine` | mounted; its `wants:` (stacks, catalogue, intake, seats, petitions) are unanswered |
| FCPM's library | `library` branch: `library/README.md`, `library/{city,trade,voices}/`, `PLACE`, a buildable site stub | a skeleton; `trade/` is the tenant list |
| you engine | you.anecdote.channel | not mounted here |
| wizard declaration | library engine branch `wizards/residency-declares-them` | unmerged |
| wizard listing | station-node `bin/wizards`, into `library/share/wizards/` | built there |
| `you + greet` | you.anecdote.channel | built there |
| bottle codec | you.anecdote.channel `bottle/` | built: bytes to a GIF of QR frames and back |
| moving-QR sender and reader | anecdote.channel `press/broadcast.mjs`, `composer/carrier-loop-demo.html`, `composer/carrier-catch-demo.html` | demos |
| check-in | `site/check-in.md`, `site/assets/js/checkin.js` | local-only and geofenced; makes no network request |
| FCPM's own wizards, a screen that plays a bottle, the signed return | | not built |

- A wizard is a declaration in an engine's residency, referenced as
  `<engine>+<label>` and resolved to that engine's current head. It invites a
  commit and never compels one.
- A bottle is bytes in transit, rendered as a sequence of QR frames.
