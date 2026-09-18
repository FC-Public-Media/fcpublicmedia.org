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
| Path / root directory | **`site`** |
| Build output directory | `_site` |

**`site` is the build root, and that one field carries the whole arrangement.**
It is both the working directory for those commands and where wrangler starts
looking for its config — and everything either of them needs is in that
directory: `_config.yml`, `Gemfile`, `.ruby-version`, `wrangler.jsonc`.
`assets.directory` inside `wrangler.jsonc` resolves relative to the config file,
so `_site` there means `site/_site`, which is also why the output field is
`_site` rather than `site/_site`: **that field is relative to the root directory
too.**

Pointing it at `worker/` would deploy the **broker** instead of the site — that
directory is a second, complete Worker config with a `main` and no assets.

### Why it is `site` and not `/`

It was `/` until 2026-09-18, and the change was not tidiness. The repository
root is being given to the station — the front door, and whatever engine ends up
providing it — and **the station is not the website**. A root that is also a
Jekyll build root cannot be given to anything else, because Jekyll takes the
directory it is run from as the source unless told otherwise.

So the site stopped borrowing the root. `_config.yml` moved into `site/` and
dropped its `source:` line, because the source is now simply where the config
lives; the three files that are read *relative to the build root* went with it.

**`.ruby-version` is the one that would have failed quietly.** Cloudflare's
image reads it from the root directory setting, so had it stayed at the
repository root the host would have moved to their default Ruby — currently
3.4.4 — with nothing in CI noticing.

**Changing the field and merging the move have to happen together**, and the
field first. The build command does not name the config, so a build run at `/`
after the config has moved finds none, takes the repository root as its source,
and publishes something wrong while reporting success. A failed build is safe —
the last good deployment keeps serving — but a *successful wrong* build is not.

Everything else is in `wrangler.jsonc`, which is committed.

### One deploy path

**Cloudflare's git build is the only thing that publishes this site.** A second,
`workflow_dispatch`-only Action existed until 2026-09-17 and was removed: two
ways to publish one site is a way to be confused about which one did.

Nothing here now reads `CLOUDFLARE_PAGES_TOKEN`, `CLOUDFLARE_PAGES_PROJECT` or
`CLOUDFLARE_ACCOUNT_ID` — the organization secret can go once you are satisfied
no other repository in the org wants it. The broker's `CLOUDFLARE_API_TOKEN` is
a different secret and is unaffected.

One thing that workflow taught is kept in [`TENANCY.md`](TENANCY.md), where the
factory design is the thing that needs it: **safety that depends on a credential
not existing is a landmine with a note on it.**

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

**A third thing to rule out first, now that it is known.** Cloudflare's builder
detects `.tool-versions` files undocumentedly, and their presence alone can fail
a build with `error occurred while installing tools or dependencies`. This
repository carried one from 2026-09-09 until it was deleted on 2026-09-17. That
does **not** explain either failure above — neither error matches, and the
`Gemfile` failure predates the file — but it is the cheapest thing to check if a
build ever fails in the tool-detection phase, and the file is gone now, so the
variable is gone with it.

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

### The registrar is Network Solutions, not Wix

Checked by `whois fcpublicmedia.org` on 2026-09-17, because it decides what is
possible and nothing in this repository said it:

| | |
|---|---|
| Registrar | **Network Solutions, LLC** |
| Nameservers | `ns4.wixdns.net`, `ns5.wixdns.net` |
| Registered | 2014-06-19. Expires 2027-06-19 |
| Status | `clientTransferProhibited` — a **transfer lock** |

**Wix holds the DNS; it does not hold the registration.** That distinction is
the whole ballgame, because Wix *does not permit changing the nameservers of a
domain registered with Wix* — and this domain is not one. **Nameservers are
changed at Network Solutions, and can be changed today**, with no transfer and
nobody's permission.

Two things follow that are easy to get backwards:

- **Moving nameservers is not transferring the registration.** They are separate
  acts at separate companies, and only the first is needed to make Cloudflare
  authoritative for this zone.
- **`clientTransferProhibited` blocks a registrar transfer, not a nameserver
  change.** It would have to be lifted at Network Solutions before the domain
  could move to any other registrar, Cloudflare included.

And on moving the registration to **Cloudflare Registrar** specifically, which
is a thing somebody will propose: it requires the zone to already be on
Cloudflare nameservers — *"all domains on Cloudflare Registrar use Cloudflare
nameservers"* — so the nameserver move is a **prerequisite** for it, not a
consequence of it. It is also entirely optional; nothing about serving this
site, or member subdomains, needs the registration to move at all.

Keeping the apex on Wix after a nameserver move is Wix's documented **pointing**
method: the Cloudflare zone carries Wix's A and `www` records instead of Wix's
nameservers carrying everything. Wix's own caveat is worth knowing before the
flip — once a domain is connected by pointing, Wix will not help manage records
it no longer hosts.

### What Wix's nameservers actually serve, read on 2026-09-17

The plan is to move nameservers to Cloudflare and keep the apex on Wix by
**pointing** — Cloudflare becomes authoritative, and its zone carries Wix's own
records instead of Wix's nameservers carrying everything. **The whole risk of
that flip is a record that existed at Wix and does not exist at Cloudflare**,
and the ones that go missing are never the website's.

Read directly from `ns4.wixdns.net` with `dig`, because Cloudflare's import scan
cannot enumerate subdomains it was not told about:

| Name | Type | Value | Proxy |
|---|---|---|---|
| `@` | A | `185.230.63.171` | **DNS only** |
| `@` | A | `185.230.63.107` | **DNS only** |
| `@` | A | `185.230.63.186` | **DNS only** |
| `www` | CNAME | `cdn3.wixdns.net` | **DNS only** |
| `new` | CNAME | `fcpm.autumn-e2c.workers.dev` | **DNS only** — see below |
| `@` | MX 10 | `fcpublicmedia-org.mail.protection.outlook.com` | — |
| `@` | TXT | `v=spf1 include:spf.protection.outlook.com -all` | — |
| `@` | TXT | `ms15993575` | — |
| `autodiscover` | CNAME | `autodiscover.outlook.com` | **DNS only** |
| `lyncdiscover` | CNAME | `webdir.online.lync.com` | **DNS only** |
| `sip` | CNAME | `sipdir.online.lync.com` | **DNS only** |
| `enterpriseregistration` | CNAME | `enterpriseregistration.windows.net` | **DNS only** |
| `enterpriseenrollment` | CNAME | `enterpriseenrollment.manage.microsoft.com` | **DNS only** |
| `_sipfederationtls._tcp` | SRV | `100 1 5061 sipfed.online.lync.com` | — |
| `_sip._tls` | SRV | `100 1 443 sipdir.online.lync.com` | — |

No wildcard, no CAA, no `_dmarc`, and no custom DKIM selectors.

**Re-read it immediately before flipping.** This is a snapshot; the zone is
somebody else's until the nameservers move.

#### The three things that break, in order of how quietly they do it

**1. Email, and it is on Microsoft 365.** The MX, the SPF TXT and the
`ms15993575` verification record are the highest-consequence rows in that table
and they have nothing to do with the website, which is exactly why a
website-focused migration loses them. **The SPF record ends in `-all`** — a hard
fail — so losing it does not merely weaken authentication, it makes receivers
*reject* mail FCPM sends. Inbound stops if the MX goes; outbound starts bouncing
if the SPF goes.

**2. The five Microsoft service CNAMEs and the two SRV records.**
`lyncdiscover`, `sip`, `enterpriseregistration`, `enterpriseenrollment` and the
two `_sip*` SRVs are what Cloudflare's scan is least likely to find, because
nothing advertises them. Nobody notices for weeks, and then a device will not
enrol or Teams federation fails, and it is not connected to a DNS change made
last month.

**3. Proxying the Wix records.** Every row above marked **DNS only** must be the
grey cloud, not the orange one. Wix serves the apex on shared infrastructure
with its own certificates and host-based routing; putting Cloudflare's proxy in
front of it is the classic version of this mistake and it takes the public site
down rather than degrading it.

#### `new.fcpublicmedia.org` points into a personal account

`fcpm.autumn-e2c.workers.dev` is a Worker in **`autumn-e2c`**, which is not
FCPM's Cloudflare account. So the live site is served today from a Worker in a
personal account, and the CNAME is what makes that invisible.

That is the account-migration question arriving as a concrete fact rather than a
principle, and it has a specific edge: a **Workers Custom Domain requires the
zone and the Worker to be in the same account.** Once `fcpublicmedia.org` is
active in FCPM's account, `new` can either stay a plain DNS-only CNAME to the
`workers.dev` hostname — which keeps working and keeps the dependency — or
become a proper Custom Domain, which requires the Worker to live in FCPM's
account first. Decide it deliberately; do not let the flip decide it.

#### Verifying afterwards

Flip, wait for the zone to go Active, then dig every name in the table above
against Cloudflare's nameservers and diff it against the table. Answers that
differ are the work; answers that are empty are the bug.

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
- **`.ruby-version` pins Ruby 3.2.2**, and it is the only file that does.
  Cloudflare's builder reads it; so does `ruby/setup-ruby`, by name, in every
  workflow. Do not delete it, and do not add a `.tool-versions` beside it — see
  *The version pins* below for what that costs.
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

## Collapsing the config files, and what each one costs

Measured 2026-09-17, because *"I'd like to find a way to collapse some configs"*
turns out to be four separate questions with four different answers, and the
expensive one is easy to walk into by accident.

Six things sat at the repository root when this was written; five do now. What
reads each, and whether it can move:

| | read by | can it move? |
|---|---|---|
| `_config.yml` | Jekyll | **no, not for free.** See below |
| `Gemfile` | bundler, and Cloudflare's build image | **probably not.** See below |
| `.ruby-version` | `ruby/setup-ruby`, and Cloudflare's build image | **no.** It is the only pin now; see below |
| ~~`.tool-versions`~~ | ~~asdf, locally~~ | **deleted 2026-09-17.** See below |
| `wrangler.jsonc` | wrangler, from the directory it runs in | no |
| `advocate.yml` | `.advocate-engine` | untested |

### `_config.yml` cannot move without changing the host's build command

**Jekyll looks for `_config.yml` in the directory it is run from, before it has
read any `source:` setting.** It will not find one inside `source:`.

Measured, with the file moved to `site/config/_config.yml`:

- `bundle exec jekyll build` prints **`Configuration file: none`**, takes the
  *repository root* as the source, warns that the `default` layout is missing,
  and dies on a Liquid exception in `site/watch/archive.md`. It does not fail
  fast and it does not mention the config.
- `bundle exec jekyll build --config site/config/_config.yml` works, and the
  output is **byte-for-byte identical** to the build from the root.

So the move costs exactly one flag, in three places: `deploy.yml`,
`smoke.yml` — and **the Cloudflare dashboard's build command**, which is
git-connected, is what publishes the live site, and is the one field no agent
can read or set. Getting that wrong does not fail the build;
it publishes a broken site and reports success.

**Not worth it for tidiness alone.** If the build command is ever being edited
for another reason, take this with it.

### The Gemfile can move, but Cloudflare probably needs it where it is

`.bundle/config` at the root, holding `BUNDLE_GEMFILE: "site/config/Gemfile"`,
is read by bundler automatically — so `bundle exec jekyll build` keeps working
with no Gemfile at the root and no change to any command. Verified locally.

**The unverified part is the one that matters.** Nothing in this repository runs
`bundle install`; the live build works because Cloudflare's image detects a Ruby
project and installs gems itself. If that detection keys on a Gemfile at the
root directory, moving it means no gems, and `bundle exec` fails at the host
while passing everywhere else. That cannot be tested from here.

It trades one visible file for one hidden directory, so the tidiness gain is
close to zero anyway.

### The version pins: collapsed, and the fact came back the other way

**Done, 2026-09-17. `.tool-versions` is deleted; `.ruby-version` is the only
pin.** The `smoke.yml` step that checked the two agreed is gone with it, because
there is nothing left to compare.

This went the opposite way to the guess above, and the guess is left in the
history rather than quietly corrected because the reasoning is the useful part.
Two facts settled it, and neither was checkable without looking it up:

**1. Cloudflare reads `.ruby-version`, not `.tool-versions.`** Their build image
documents exactly three ways to set Ruby — the `.ruby-version` file, the
`RUBY_VERSION` environment variable, and a build variable on the dashboard — and
`.tool-versions` is not among them. Their current default is **Ruby 3.4.4**, so
deleting `.ruby-version` would not have failed the build; it would have silently
moved the host onto a different Ruby from CI and local, which is worse.

**2. `.tool-versions` is an active hazard there, undocumented.** Cloudflare's
builder *does* detect the file, and its presence alone can fail a build with
`Failed: error occurred while installing tools or dependencies` — with no way to
turn the behaviour off, and `SKIP_DEPENDENCY_INSTALL` does not help. See
[the write-up Autumn found](https://www.codejam.info/2026/02/cloudflare-workers-choke-asdf-tool-versions.html).
The published workaround is to rename it and set versions through build
variables instead; deleting it outright is the same fix with one fewer file.

So the file that had to survive was the one that was *not* named as expendable —
and removing the other one is both the collapse and the removal of a hazard.

#### Where the file came from, so it does not come back

It was not a decision made here. Autumn, 2026-09-17:

> I told my agents in my projects folder to unify tools. And so that's probably
> what happened. This repository is allowed to not listen to my personal dev
> advice. I didn't realize we hit this repo.

That generalises, and it is now a standing order in `AGENTS.md`: **guidance about
unifying tooling across a personal projects folder is not guidance about here.**
This repository is org-owned, public, and built by a host with its own opinion
about version files.

Which is her own machine's rule read the other way round — its toolkit note says
divergence is allowed and belongs written down *in the diverging project*, never
by editing the shared list. This is that, written down.

#### What it cost, and the thing that pays for it

asdf does not read `.ruby-version` unless `legacy_version_file = yes` is set in
`~/.asdfrc`, which is per-user and off by default. Without something in the way,
a contributor at the repository root would get whatever Ruby their shell hands
them and find out from a confusing Jekyll error — the exact failure the deleted
`smoke.yml` step existed to catch.

**The `Gemfile` now carries `ruby ">= 3.2"`.** A floor, not a second pin, so
bumping `.ruby-version` stays a one-file change. Measured on this machine with
the Ruby macOS ships:

```
$ /usr/bin/bundle check
Your Ruby version is 2.6.10, but your Gemfile specified >= 3.2
```

One line, names the version, refuses before Jekyll is reached. That is a better
guard than the CI step it replaces, because it fires where the mistake is made
rather than after a push.

`docs/running-it.md` has the `~/.asdfrc` line for anyone who wants asdf to keep
selecting Ruby automatically.

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

**Cloudflare**, and it is no longer both.

**Cloudflare** is the live host. It attaches to the domain in minutes, serves
static files, and — the part that settled it — `worker/` is already a Worker
there. Autumn, 2026-09-17: *"that's the one I wanna keep around, because that's
for Cloudflare. I think I made us a Pages site, but I wanna use a Worker. And so
it's still in the cards."* Identity, uploads and payments all go through that
Worker.

**Azure Static Web Apps** used to be the answer to *"where does this go if
members-only pages are wanted"*, because it bundles static hosting, Entra ID
sign-in and a small serverless API into one free resource inside the Microsoft
365 tenant FCPM already has. **That argument is retired.** The sign-in it was
offering is the one deleted on 2026-09-17 along with `api/` — see
[`identity.md`](identity.md) — so what is left of the Azure path is a static
host with no advantage over the one already serving the site.

The workflow and the config are still here and still build, and they are cheap
to keep: `deploy.yml` gates every pull request, and it deploys nothing without a
token nobody has set. But nothing is planned for it.

Nothing about the *site* favours one host over the other — that is the point of
it being static files. `_site/` deploys anywhere, both hosts build from the same
command, and the redirect list feeds both. Switching is still a DNS change, not
a rewrite. What has changed is that there is no longer a reason to switch.

---
