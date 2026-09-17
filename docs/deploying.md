<!--
Split out of the root README on 2026-09-17, unchanged apart from paths.

The README was 68 KB and had become the only place a lot of this was written
down, which made it both the first thing a visitor saw and the last place
anybody wanted to edit. Nothing here was rewritten in the move; if something
reads as out of date, it was out of date before it moved, and saying so is
welcome.
-->

# Deploying

Cloudflare is the live path. Azure is the one that came first.

## Deploying to Cloudflare

This is the fastest path to a real URL on a real domain, and it is what the
live site runs on.

Cloudflare now creates new projects as **Workers** rather than Pages, and the
two behave differently at deploy time. This repository is set up for the
Workers flow, which is what you get by default today.

**Cloudflare builds and publishes it, from the git connection.** Point the
Cloudflare GitHub app at this repository and set:

| Setting | Value |
|---|---|
| Build command | `bundle exec jekyll build` |
| Deploy command | `npx wrangler deploy` |
| Non-production branch deploy command | `npx wrangler versions upload` |
| Path / root directory | `/` |
| Build output directory | `_site` |

**`/` is the whole repository, and it matters.** That one field is both the
working directory for those commands and where wrangler starts looking for its
config, and both want the root: the `Gemfile` is there, `wrangler.jsonc` is
there, and `assets.directory` inside it resolves relative to the config file.
Pointing it at `worker/` would deploy the **broker** instead of the site —
that directory is a second, complete Worker config with a `main` and no
assets.

**Moving the site into `site/` did not change any of these five fields**, which
was the point of leaving `_config.yml` at the root and setting `source:` in it
rather than moving the config down. The command is still run from `/`, still
writes `_site`, and wrangler still finds `wrangler.jsonc` beside it. Nobody had
to open the Cloudflare dashboard.

Everything else is in `wrangler.jsonc`, which is committed.

### There is a second path in Actions, and it only runs when you say so

`.github/workflows/deploy-cloudflare.yml` builds and publishes the same site
with `wrangler deploy`. It is **`workflow_dispatch` only** — Actions tab, Run
workflow — so it cannot fire on its own.

| What | Where | Value |
|---|---|---|
| `CLOUDFLARE_PAGES_TOKEN` | organization **secret** | API token, *Edit Cloudflare Workers* template, **account-scoped** |
| `CLOUDFLARE_ACCOUNT_ID` | secret or variable | Only if the token can see more than one account |
| `CLOUDFLARE_PAGES_PROJECT` | repository **variable**, optional | Overrides `name` in `wrangler.jsonc`. A wrong value **creates a second Worker** |

**Manual-only is the safety, and that is deliberate.** An earlier version ran on
`push` and was kept harmless by the token being absent — which turned an
ordinary act, adding an organization secret, into a way to start publishing the
same site twice by accident. Safety that depends on a credential *not* existing
is a landmine with a note on it. The trigger is the guard instead, so the secret
can exist for the broker's sake without arming anything.

This is the same arrangement `DiscoveryWritten/lesbistrology` uses, on purpose.
Two projects agreeing about how this is done is worth more than either being
individually clever.

To switch to it permanently: **disconnect the repository in the Cloudflare
dashboard first**, then add a `push: branches: [main]` trigger.

### When the git build fails

Two failures have been seen, and they look nothing alike.

**`Could not locate Gemfile or .bundle/ directory`, with an empty
`Detected the following tools from environment:` line.** The checkout was
empty or partial — bundler ran, so the image was fine; there was simply no
repository under it. **This is not the Root directory setting.** `/` is
correct and is what `lesbistrology` uses successfully. Look at the GitHub App's
access to the repository instead; this appeared while several of the account's
git connections were being reauthorized.

**The repository reported as damaged.** Deleting and recreating the project
cleared it. See below.

**Neither takes the site down.** A failed build leaves the last good deployment
serving, so there is time to look properly. Check what actually changed in
`_site` before treating it as urgent — a run of merges that only touch
excluded files publishes identical bytes.

### Why the git connection broke once, and the warning that came out of it

Cloudflare's builder began reporting the repository as **damaged** and stopped
deploying. Deleting and recreating the project fixed it. Nothing in the
repository was ever broken — CI was green throughout, and still is.

A hypothesis, recorded because it is cheap to keep and expensive to re-derive,
and **not** because it was confirmed. `.advocate-engine` is a submodule, added
2026-09-04, pinned to a commit that is not at the tip of a branch. Cloudflare's
builder clones shallow and then initialises submodules, which is exactly the
combination that cannot fetch such a commit — and a superproject whose
submodule will not resolve is fairly described as damaged.

**The asymmetry is what suggested it**, and it is suggestive rather than
conclusive. `actions/checkout` does not fetch submodules unless asked, and the
site build has never needed one: nothing in `_site` comes from
`.advocate-engine`. So CI kept working throughout, which is consistent with the
theory and does not prove it.

Two consequences worth keeping:

- **Do not add `submodules: true` to the checkout in `deploy.yml`.** Nothing in
  `_site` comes from `.advocate-engine`, so it would buy nothing and might
  import the failure.
- **Recreating the project is a cheap first move** if this happens again. It is
  what actually cleared it, before anybody proved why.

### Where it is served, and why the domain still says Wix

Wix holds DNS for `fcpublicmedia.org` and the apex still serves the old Wix
site. The new site is reachable at:

- `fcpm.<subdomain>.workers.dev` — always, straight from Cloudflare
- **`new.fcpublicmedia.org`** — a CNAME in Wix's DNS pointing at that
  workers.dev hostname

**The CNAME is enough.** Cloudflare issues a real certificate for
`new.fcpublicmedia.org` even though it is not authoritative for the zone, so
this needs no zone transfer, no nameserver change, and no move of the domain
registration. That is worth stating plainly because the opposite is easy to
assume and would turn a DNS record into a migration.

So **"get Cloudflare serving" and "put the new site on the real domain" are
separate**, and only the second is a cutover: it is the day `www` and the apex
stop pointing at Wix.

### Preview URLs

The non-production branch deploy command is `npx wrangler versions upload`,
which uploads a version and prints its URL without promoting it to production.
That is where per-branch previews come from, and it is a reason to prefer the
git connection over the Actions path.

The Actions fallback does not do this — it publishes to production or nothing,
which is the right shape for something you invoke by hand when the usual path
is down.

### Why `wrangler deploy` and not `wrangler pages deploy`

Because this is a Worker with static assets, not a classic Pages project.
`wrangler pages deploy` does not publish to the same place: it would create a
**second** site, at its own address, with the custom domain still pointing at
the first. Two live copies of one website is the failure to avoid, not a step
on the way to anything.

The secret and variable are named `…_PAGES_…` because that is what the static
host is called in conversation. The names are ours; the product underneath is
Workers.

### Why wrangler.jsonc has to be committed

`wrangler deploy` looks for a config file. If it does not find one it runs
auto-configuration: it inspects the repository, decides what kind of project
this is, and **re-runs the build command through npx**. For a Ruby project
that produces `npx bundle exec jekyll build`, which fails with:

```
npm error could not determine executable to run
```

The Jekyll build has already succeeded at that point. The failure is wrangler
guessing, not the build. Committing `wrangler.jsonc` skips the guess.

### Notes

- **`bundle exec` is deliberate.** It guarantees the bundled Jekyll rather
  than whatever happens to be on `PATH`.
- **`_site` appears twice** — in the workflow and in `wrangler.jsonc` under
  `assets.directory`. Both need it. It is Jekyll's default and is not
  overridden in `_config.yml`.
- **`.ruby-version` pins Ruby 3.2.2**, and `.tool-versions` says the same for
  asdf. CI reads `.ruby-version`. Do not delete either.
- **`Gemfile.lock` is intentionally not committed.** A lock file resolved on a
  different platform is a common cause of `bundle install` failures on hosted
  builders. Jekyll is the only direct dependency.
- **The broker deploys separately**, from `.github/workflows/broker.yml`, with
  its own token — `CLOUDFLARE_API_TOKEN`, not the one above. The reasoning is
  in `.github/workflows/broker.yml`'s header: a GitHub secret is readable by
  GitHub Actions and by nothing else, so the workflow is the bridge that pushes
  it into Cloudflare's separate store.

### If you are on classic Pages instead

Same build command and output directory, no deploy command, and
`wrangler.jsonc` is ignored. Both flows serve `_redirects` and `_headers`
from the output, so the redirect handling below applies either way.

### Redirects and headers

Cloudflare Pages reads `_redirects` and `_headers` from the root of the
published output, and Azure reads `staticwebapp.config.json` from there. Their
sources are `site/_redirects`, `site/_headers` and `site/staticwebapp.config.json`
— the site directory is the build root, so all three land where the hosts look.
**All three are generated from `site/_data/redirects.yml`** at build time, so the
hosts cannot drift apart — add a redirect once and both get it.

The 20 legacy Wix URLs therefore keep working on either host, which matters:
those are the links currently indexed by Google and sitting in other people's
bookmarks.

## Deploying to Azure Static Web Apps

`.github/workflows/deploy.yml` builds with Jekyll and deploys to Azure Static
Web Apps on every push to `main`. Pull requests get their own preview URL,
which means the board can look at a change before it goes live — something Wix
has never offered.

One secret is required: `AZURE_STATIC_WEB_APPS_API_TOKEN`, from the Static Web
App resource in the Azure portal.

The free tier covers the static hosting, the managed functions, the auth, and a
custom domain with a certificate.

### Cloudflare or Azure?

Both, for now, and that is not indecision.

**Cloudflare Pages** is the demo host: it attaches to the domain in minutes
and needs no Azure setup. It serves static files, which is all this site
currently is.

**Azure Static Web Apps** is where this goes if members-only pages are
wanted, because it bundles static hosting, Entra ID sign-in, and a small
serverless API into one free resource inside the Microsoft 365 tenant the
organization already has. Cloudflare Pages can do auth and functions too, but
not with Entra sitting right there.

Nothing about the site favours one over the other — that is the point of it
being static files. `_site/` deploys anywhere, both hosts build from the same
command, and the redirect list feeds both. Switching later is a DNS change,
not a rewrite.

---
