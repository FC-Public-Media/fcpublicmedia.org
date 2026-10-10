# Open

Everything not built, not decided, or known wrong. One line each; the file named is where it lands.
Plans that once had their own docs are here in a few lines; git history has the long versions.

## Broken now

- `propose-shows.yml` runs `git diff --quiet` after writing an untracked stub, so no show PR ever opens. .github/workflows/propose-shows.yml
- `crews/crew.ps1` looks for `machines\crews\`; `fcpm crew status|install|uninstall` stop at "no crew". crews/crew.ps1
- `crews/production/residency.yml` does not parse in PyYAML (`\s` in a double-quoted string). crews/production/residency.yml
- `machines/editing-bay-1/gear.yml` is not valid YAML (gh-stack `for:`); check.ps1 reads it by regex, so it still works.
- `bin/runnables` is `#!/bin/sh` but needs bash, and `compile` fails under BWK awk (macOS); Git Bash is fine. bin/runnables
- `cablecast.json` `fetched` is always null: the workflow never sets `SYNC_STAMP`. .github/workflows/sync-cablecast.yml
- Expired `featured.yml` items stay live: the weekly sync dispatches `deploy.yml`, which builds Azure only. .github/workflows/sync-cablecast.yml
- Show pages gather episodes by `match.prefixes` only; `match.producers` is ignored. site/_layouts/show.html
- `site/bin/redirect-report.py` still writes `docs/REDIRECTS.md`; point it elsewhere or retire it with Wix.
- `/check-in/` on a shared browser prefills the last visitor's name and email (`fcpm.profile`); `dropStore` exists. site/assets/js/checkin.js
- `machines/fcpm`'s proof is at blob fb3c96fd4d53; the file is now 73525b1cfe77, so its verbs are unproven. machines/editing-bay-1/bay/runnables.proven
- `machines/fcpm`, `obs.ps1` and `obs-portable.ps1` still link `machines/README.md` and `machines/BAY.md` (kept as signposts) until each is next re-proven.
- `--paper-sunk` (used by `.code-block`) is never defined. site/assets/css/site.css
- Page copy: `/contact/` cites a deleted `/api`; `/donate/` says it is not in the nav, and it is. site/contact.md, site/donate.md
- Unused: `_includes/community.html`, `countdown.html`, `checkin-card.html`; `watch.yml` `live_url`, `live_provider`, `categories`.
- `pools.py`'s fallback usage omits `timeline`; `pool.ps1`'s usage omits `install|uninstall`.
- `crew.py`, `crew.ps1` and `episodes.py` hard-code the `editing-bay-1` profile instead of the machine's.
- `recorder/gear.yml` names the profile `fcpm-recorder`; `obs.ps1` uses `FCPM Recorder`. troves/recorder/gear.yml
- `door.py`'s route table omits `/preview/`, `/helo/*`, `/input`, `/heard`, `/wall/`; nothing calls `m365-token.ps1`.
- kiosk-1's `code/AGENTS.md` names `docs/CAPTURE.md`, which is not in this repository.
- `member-site-core/feed.xml` names `script/sync-feeds.py`; `site-template/` points at a README that does not exist.
- `machines/crew.yml` says there is no supervisor or pool; editing bay 1 runs both.

## Pins and watching

- `.advocate-engine` is 5 commits behind `origin/main` (pinned 4635cfc1); bumping it is its owner's PR.
- station-node's library pin for this repository is 508 commits behind `main`; harmless while station-thaw checks out `main`.
- `origin/library` has no PR and no owner. Cloudflare builds every branch, so it must stay buildable until that stops.
- After any change of publisher, a legacy Wix URL must 301 to `/reserve/` with no `x-wix-request-id`; nobody owns the check. site/_redirects
- Anything running wrangler on a payload needs `site/wrangler.jsonc` beside it.
- Something moving into `site/` gets an assertion in `site/bin/test_nothing_internal_is_published.py`, not an `exclude:`.
- How long `/README.md` was public before #81 is unknown.
- The Slack invite in `community.yml` expires every 30 days; nothing regenerates it. Slack or Teams is unsettled.
- 2026-11-01: set `org.equipment_email` to equipment@fcpublicmedia.org. site/_data/org.yml
- Every class in `classes.yml` is past and `calendar.json` is empty; `/meet/` and "Coming up" render empty.

## Site content

- Missing copy: `/donate` (amounts, recurring, the case, the processor), `/bulletin-board`, the eight podcasts, the verbatim DEI statement from Wix, the `/submit` agreement, `/teach` application questions, an `/about/` history (render `org.mission`).
- Membership tier benefits, nonprofit production pricing and drop-in prices (`TODO`, and whether members attend free) await the board.
- Financials (EIN, 990, annual report) are a board decision; published ones go in `governance.yml` `documents`.
- Retired Wix shows redirect to `/podcasts/`; Wix `/equipment` has no redirect or decision. site/_data/redirects.yml
- A real logo: CSS called the mark a placeholder; brand/README.md documents a plate.
- Board roster is empty, so office hours cannot appear. site/_data/board.yml
- Photos waiting on files: mission band, each space, top of `/reserve/`, a class in progress, board headshots.
- Ask: one picture of instruction, or one per instructor (no `instructor` field). site/_data/classes.yml
- Someone has to enter community events as a standing job. site/_data/community.yml
- `page` layout prints no `<h1>`; accessibility audits flag it. site/_layouts/page.html
- Check `/watch/` renders `## Podcasts` as a heading (a trimming Liquid comment precedes it). site/watch.md

## Board review

- BLOCKING: the Equipment Terms and Conditions that shipped copy names do not exist. site/reserve.md
- Confirm the card is kept for late fees and incidentals, not as collateral. site/reserve.md
- "Check out production equipment" reads as self-serve; the page says equipment is arranged by email. site/_data/facilities.yml
- A video or slideshow of the spaces where the floor plan was; waits on footage. site/reserve.md

## Deploy and domain

- Ruby 3.2.2 is end of life; 3.3 or 3.4 is a one-line change. site/.ruby-version
- The live Worker is in a personal Cloudflare account, not FCPM's; moving it and making `new` a Custom Domain is undecided.
- Nameservers to Cloudflare (apex kept on Wix by pointing), then the www and apex cutover: not scheduled. docs/site.md#domain-and-dns
- Member subdomains need the zone on Cloudflare, a wildcard and a hostname-to-folder Worker (one Worker with `run_worker_first`, or a second). site/wrangler.jsonc
- Member builds set no `baseurl`, so `/member-sites/<name>/` on www breaks.
- Org secrets `CLOUDFLARE_PAGES_*` and `CLOUDFLARE_ACCOUNT_ID` are unused here.
- Rule out two Cloudflare projects building this repository; check whether the "damaged repository" failure is the advocate pin under a shallow clone.
- `_headers` sends no HSTS; `staticwebapp.config.json` does.
- Build-less deploys, and Workers relaying registration, class sign-up and reservations to Microsoft 365: planned.
- Whether Cloudflare stops building at all (the station builds instead) is direction, not done.

## Programming and classes

- Cablecast hygiene: 461 programs uncategorized, 746 without VOD, none captioned, filename debris in titles; `LOCAL_PREFIXES` is a guess. site/bin/sync-cablecast.py
- The calendar source is undecided: a published ICS (what `sync-calendar.py` does; no workflow runs it) or Microsoft Graph (scope `Calendars.Read` with an access policy; workload identity, not a secret).
- `sync-calendar.py` ignores `STATUS`, so cancelled events show.
- Check-ins and RSVPs stay on the visitor's phone until retention and access rules exist; the paper log stays. Flagging a check-in without a booking needs the calendar.
- Cloudflare Access for verified email at check-in: free to 50 users, then about $7 per user per month.
- Retired podcasts: own entries or one archive listing. site/podcasts.md
- The artificially pipeline's Audition steps wait on its panel proving out. site/_shows/artificially.md
- Class mode: grade the lit hour pill; take class and presenter from the calendar; an admin or teacher view; an attendant recipe.
- Instruments: nothing reads `instruments/` yet; which panels a shared host sets aside; swapping two pages in one action; macOS and Linux drivers; whether an instrument can be a sink (with station-node).
- A view of what the roller TV shows when it faces away; bay OBS is not ours to change.

## Members

- Ejection owes the core as a commit to the member's repository; no tool writes it. bin/build-sites.py
- A generated tier (a site from show data for shows without a repository): how `sites.yml` names it, never confusable with `scaffold`.
- `_shows/` and `_podcasts/` as one collection moves live URLs.
- `/meet/` to render `member_sites.json` once it has entries; nothing reports stale tenant pins.
- Undecided: which observation a tenant may switch off; per-tenant build days; staying listed while private (a GitHub App reading the feed); runner mode on bay machines.
- Members are not told that a feed taken down reads as an outage; withdrawal is an act on FCPM's list.
- `member-site-core/` is a provisional name; proposed as an engine. Is anecdote.channel only the default hosting namespace?
- The member-facing README for a member repository is Autumn's to write. site-template/
- Hosting: nothing deploys tenants. Default is Autumn's Cloudflare under anecdote.channel, FCPM's once a member buys a domain; the deployer chooses the account per tenant and cannot fire twice.
- Intermediates (decided, not built): members send signed built HTML instead of being composed here; signing waits on a key ceremony (`identity.yml` `keys: []`); input outside parameters shows uninterpreted. docs/station.md#intermediates
- Member shows: a passkey on `you.fcpublicmedia.org`, one `<show>.you.` per show, wizard steps as PRs replayed and never run, bookings with a nonce, recordings home as expiring passkey links, each stage proven by a test on the media node.
- Holding a bubble: its README says who sent it, what it holds, where it goes, what it costs, what is final and how to leave; membership as You passkey, application, Stripe Checkout carrying only the application digest.
- Library: move it from the `library` branch to `library/` on main; mount `.you-engine`; wizards in `wizards/<label>/`, shown on a studio screen as a QR bottle and returned as a passkey-signed PR; class materials sealed per session.
- Directory: `_data/tells.yml` is empty (our Tell's registration is not merged); scope `fort-collins` vs the engines' `colorado`; the Tell's feed `url`; piles as member branches; the Atlas–Tell split.
- Escalation 9605: the board's decisions on what public media offers under the library's categories.

## Payments and identity

- Payments are not switched on; what remains is the status table. docs/payments.md#before-charging
- `/membership/` publishes "TODO" under three tiers (`tier.summary` renders unconditionally). site/_data/membership.yml
- Nothing reads `stripe.live` or `stripe.publishable_key`; the buy button that should does not exist. site/_data/payments.yml
- `membership.note` (public copy) still describes Entra ID sign-in and a README section that is gone. site/_data/providers.yml
- No provider for `tickets`, `donate` or `submit`; booking moves to Microsoft 365 (`booking.subdomain` unset). site/_data/providers.yml
- Form posts have no receiver: an `/api` relay through Graph, or a hosted form service. site/_data/forms.yml
- A build-time Booqable catalog would need a read-only `BOOQABLE_TOKEN`; not wanted yet.
- The first live `reprice-subscriptions.py --apply` runs against a Stripe sandbox with a test clock.
- The membership record (email, paid-through date) is unbuilt: a SharePoint list written only by the payment webhook.
- The claim signing key is not minted and its custody is undecided (`keys: []`, `CLAIM_KEYS` `[]`), so `/bind` refuses every enrolment. site/_data/identity.yml
- `/upload/` posts to the broker's base URL, which has no such route. site/assets/js/upload.js
- `write_mode` in `authorize.yml` is rendered but read by nothing. site/_data/authorize.yml
- Upload destination: bucket, `R2_MAX_BYTES`, retention; Dropbox stays the fallback. site/_data/upload.yml
- The broker has no rate limit on `/challenge`, and challenges are not strictly single-use (KV read-then-delete). worker/src/
- Check-ins leaving the device (worker, GitHub App, private repo, SharePoint) is proposed; it waits on the board's retention, readers and privacy notice.
- The pass is to hold several cards per device, and a check-in to record which.
- Confirm the venue coordinates and the QR's final URL (`new.` vs `www`) before printing. site/_data/checkin.yml
- `/reserve/` as a list of hosts booked by shift from one shared M365 calendar, through the Worker, working without JavaScript; open: how hosts are marked, the activity vocabulary, single-use claim links, what a host is called. site/_data/hosts.yml

## Station and machines

- Which station services move from station-node to FCPM machines, and in what order.
- Ablative: bring it, split its observation for both nodes, or re-home its concerns. Nothing filed.
- `.library-engine`'s residency asks are unanswered; `.journal-engine` wanted at the root (its own PR); `.proofing-engine` wanted, not mounted.
- What the library holds under `trade`, `city` and `voices` is the board's.
- Front door: a passive landing page per machine on `.local` where a visitor makes a passkey and gets a grant.
- Putting a profile on should be a signed commit; admission a passkey-signed request with KEYHOLDERS, not a merge.
- Machines pull from a LAN origin (thin-client is the likely host) once they can reach it.
- digitization: names not applied; SSH door and keys wait on passkeys; intake polls until a webhook.
- editing-bay-2: names unfilled, and it may be the machine that is now kiosk-1.
- editing bay 1: depot only over opt-in Wi-Fi; `.ps1` under `-ExecutionPolicy Bypass`; capture for digitization waits on HDCP and a home for masters.
- `code/bin/refs` has two copies that differ; it belongs where both machines read it.
- Runnables: a canonical door.py form; a door restart verb; claims for bay 1's `refs` and `pool.ps1`.
- The pool restarts the `production` supervisor too. machines/editing-bay-1/code/bin/pool.ps1
- The default `gear.yml` claude-code winget id is unconfirmed.

## Crews and services

- The crew install has never run to completion; it needs an administrator.
- The supervisor is Windows-only; a Linux host needs a unit, a lock, display detection and process-group kill. crews/crew.py
- Machines do not yet say which crews they `wear`; the `kiosk` crew has no folder; digitization has no `services` order.
- Production's door is not built; its first workflow and whether `/pools/` moves under it are undecided. docs/services.md
- The welcome before sign-in at the bays is an experiment. docs/services.md#workstation-sign-in
- Digitization: bay 1's answers as tank host and screen; the Debian member has no capture verb or drive; capture splitting on silence vs one file per session; recording input and start time; a name for the scratch share; the Integra, VCR, multichannel interface and compressors; RØDECaster multitrack.
- Instanced configurations for gear several crews use (ATEM, OBS).
- Member scheduling: ask Cablecast about a draft `runStatus`, and how staff's tool creates shows. docs/services.md#member-scheduling
- Depot volume identity (a marker per partition) is not built. docs/services.md#depot-index
- Mailing a site's owner when a device is added: not built. worker/
- `advocate.yml` puts the journal out of scope; the later decision wants it at the root. A seat naming what it reads (to wake on station-node) is proposed upstream.
- Attendants: nothing wakes one on an `attendant` channel; recipes are followed by hand; the wall recipe is not in `site/tests/`, misses its reload, and says `page depot` where node.yml has `drive`.
- `.contact-sheets-engine` deletes the previous sheet before montage runs; it has no library address.

## Kiosk

- Placeholder wording: the greeting, where the Wi-Fi card hangs, whom to ask; the desk page reads `node.yml` `wording:`, which belongs in `kiosk/content.yml`. kiosk/content.yml
- The rota's `crew:` tags are Autumn's to give. kiosk/rota.yml
- Bookings: Microsoft 365 calendars replace `bookings: sample`; Bookings is ruled out for intake; a second desk monitor for today's bookings waits on its API.
- `brand/idle`'s `#slot` is not wired to `welcome.js`. brand/idle/index.html
- Dim: an attendant recipe; on the roller with the TV switched off and on, unconfirmed.
- The Dropbox queue is off (no app key, no staff folder). machines/kiosk-1/node.yml
- Camera replies with a passkey signature are refused until devices can be checked; the HELO preview waits on an RTSP player. machines/kiosk-1/door.py
- kiosk-1's third panel waits on a DVI adapter; editing bay 2's outward monitor has no show.
- Asked of IT: automatic sign-in, inbound TCP 8080. `kiosk-1` is a placeholder name. machines/kiosk-1/PROFILE.md

## Troves

- game-intake is not submoduled under station-node's `library/FCPM/`.
- Pools: squares as units enhanced together; the Buffalo as a pool; one file saying which machine holds each pool; rows per host from bookings; promotion to a final timeline; groups written to a show's repository; Audition and other transcription engines.
- Post: delivery and eviction from `E:` are not designed.
- Recorder: OBS for digitization waits on capture hardware and HDCP; silence splitting needs another payload; the first schematic is unwritten.
- TI-89: next `link.py` verbs; OS installs through TiLP; a screen instrument; later VMs from the ROM, a hub on the media node, a kiosk menu, a cordless relay.
- Ki Pro: tape digitizing and a start/stop verb are a person's decision; trace DL32R 13/14 and its HDMI feed.
- Camera: test the console attached, ATEM resets of USB presets, unnamed properties `D007`–`D00A`; presets are drafts.
- EdgeRouter X: joining the studio network, a preparation script, firmware.
- PTZ: read each camera on arrival; how a show holds one; the board's policy on behind-the-scenes recording and a 24-hour stream.
- Nest Cam: which app still sets it up was never checked.
