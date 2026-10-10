# Open

Things that are true right now and will not announce themselves. Written
2026-09-19, at the end of a long structural session, for whoever arrives next.

**Not a TODO list.** A TODO is something somebody chose to do later. Everything
here looks finished, looks healthy, or looks like somebody else's job.

Each item says how to check it, because a claim a reader cannot verify is a
rumour and this file will rot.

## Checked against main at `cb02a2e`, 2026-10-10

Claims in these files are false. They are left as written, for whoever
reviews `docs/`.

| claim | where | what is true | check |
|---|---|---|---|
| a Remote Control server started by hand is left alone; `off` never stops a running one | `machines/editing-bay-1/code/AGENTS.md` | `fcpm pool off` ends every Remote Control server on the box, then prints `server: down` or the pid still up | `StopAll` in `machines/editing-bay-1/code/bin/pool.ps1` |
| the root keeps one thing up, a Remote Control server | `machines/editing-bay-1/code/AGENTS.md`, `docs/inline/machines/editing-bay-1/code/bin/pool.ps1.md` | the server on EDIT2 is off by choice | `fcpm pool` on EDIT2 |
| Wi-Fi is the guest network, `192.168.3.x` | `machines/editing-bay-1/code/AGENTS.md` | EDIT2's Wi-Fi is disconnected | `ipconfig` on EDIT2 |
| read `GOTCHAS.log` first | `machines/editing-bay-1/code/AGENTS.md` | there is no `GOTCHAS.log` in EDIT2's `~/code` | `dir ~\code` on EDIT2 |
| if `fcpm screen` says kept NO, the pool is out of date | `machines/editing-bay-1/code/AGENTS.md` | `screen.ps1` counts a keep only when `FCPM_BY` is `pool`; the crew's residency sets `production`, which it counts as `hand`. Reported from EDIT2 that kept stays NO | `troves/kiosk-screen/screen.ps1` line 8, `troves/kiosk-screen/residency.yml` |
| production's supervisor is installed and running | `docs/crews/production/CREW.md`, `docs/crews/README.md` | `fcpm crew status\|install` fails: `crews/crew.ps1` still looks in `machines\crews\`. There is no `production` task on EDIT2 | `grep -n 'machines.crews' crews/crew.ps1` |
| `powershell -NoProfile -File ~\code\bin\pool.ps1 install` | advice printed by `machines/editing-bay-1/check.ps1` | that command does not work; the verb is `fcpm pool install` | `fcpm check` on EDIT2 |
| run `fcpm install` to bring in the latest | anywhere | `fcpm install` does not pull. `fcpm pull` does | `machines/fcpm`, the `install` and `pull` cases |

Changed by #255, #257 and #258, and not yet reflected everywhere:

- Bare `fcpm` (the watcher) no longer runs `check.ps1`; `sync` honors
  `SYNC_CHECK=0`. The check runs only from `fcpm check`. The depot probe is an
  800 ms socket. A server turned off on purpose shows `--`, not NEEDS.
- `fcpm pool` shows a `dev` line.

## Pins that are stale and will stay quiet about it

| | |
|---|---|
| `.advocate-engine` | **5 commits behind `origin/main`**, pinned at `4635cfc1`. Reported four times during that session and never bumped, because advancing a pin is its own pull request by whoever owns it |
| the node library's pin for `FCPM/fcpublicmedia.org` | `71047780`, which **predates #69 through #93.** Nothing breaks, because `station-thaw` checks out the project's own `main` rather than the pin — which is precisely why it will stay stale |

Neither appears in `git status`. A superproject reads as clean when every gitlink
matches **what was committed**, which is a statement about the commit and not
about the world. To check:

```sh
pin=$(git ls-tree HEAD .advocate-engine | awk '{print $3}')
git -C .advocate-engine rev-list --count "$pin"..origin/main
```

## `origin/library` has no owner watching it

An orphan branch: `PLACE`, `library/README.md`, and three empty category folders
— `trade/`, `city/`, `voices/`. Plus the smallest thing that builds.

It has no pull request, so `auto-delete-on-merge` will never touch it, and
nothing else will notice it either.

**It carries site machinery on purpose**, and that is worth re-reading rather
than tidying away: **Cloudflare builds every branch here.** The non-production
branch deploy command is set, so a branch with nothing to build does not sit
quietly — it goes red, stays red, and teaches everyone to ignore a red light.

That is a live constraint on the library-as-branch design, and the petition filed
upstream from `station-node` does not name it. `PLACE` lets a *build* exit 0 and
report what it skipped, but **the build command lives in a dashboard and never
reads it.** A place-branch on a host that builds every branch has to be
buildable, or the host has to be told which branches to skip.

> **This constraint is expected to evaporate, and has not yet.** Reported
> 2026-09-24, relayed from Autumn via the station-node session rather than said
> here, so treat it as direction and not as done: *"I don't want Cloudflare
> building anything. Cloudflare is not going to build a single damn thing. And
> it's because we are going to, as station node, go ahead and run their build."*
>
> If Cloudflare stops being a build environment, there is no branch build, no
> `wrangler versions upload`, and no red light to teach anybody to ignore — so
> the paragraph above stops constraining the library-as-branch design at all.
>
> **Do not design against its absence yet.** Nothing has been disconnected, the
> dashboard still holds the branch deploy command, and this entry is the only
> place the two facts sit next to each other. Whoever performs that disconnect
> should strike the paragraph above in the same change, because a constraint that
> has quietly stopped being true is worse than one that was never written down.

## A seat's own finding, never actioned

`advocate.yml`, the `truthfulness` seat, line 127 — in its own constituency text:

> right now every class in the calendar is in the past, so two surfaces render
> empty and nothing complains

**Still unverified.** It is a content problem, content was deliberately out of
scope for the structural work, and **the seat that would catch it does not run.**
So the finding sits inside the document describing the mechanism that was
supposed to find it. Check `site/_data/classes.yml` against today.

## How long `/README.md` was public was never established

`site/README.md` is inside `source:`, so Jekyll copied it verbatim to
`https://www.fcpublicmedia.org/README.md`. Closed by #81, which excluded it.

**The duration is unknown and the obvious probe cannot settle it.** It 404s now,
which is equally consistent with *rebuilt after #81* and with *not rebuilt since
before the file was added*. Nothing sensitive was in it.

Recorded because *we fixed it* and *we know what was exposed, and for how long*
are different claims, and only the first one is true.

## `/check-in/` on a shared browser shows the last visitor to the next one

Found 2026-09-23, while working out what a studio kiosk may display. **It is not
a kiosk problem** — it is true of that page today, on any machine more than one
person uses, and it is filed here rather than in the kiosk work for that reason.

`site/assets/js/checkin.js` keeps the visit in `localStorage`, which is exactly
right on a personal phone and is what the page promises: *"Your visits stay on
your own phone."* The keys are at the top of the file — `fcpm.profile` holds
**name, reason, note and email**, and `fcpm.checkins` holds up to
`history_limit` past visits, currently 200.

On one shared browser those accumulate into a single profile, and the form
**prefills the previous visitor's name and email** for whoever sits down next.
The page's promise is not merely weakened there, it is inverted: the one place
the data was supposed never to go is another visitor's screen.

The realistic case is not a kiosk. It is **a staffer opening `/check-in/` on the
desk machine to help somebody who is struggling with it**, which is a helpful
thing to do and leaves that person's details in the browser.

To check, on any machine where somebody has checked in:

```js
JSON.parse(localStorage.getItem('fcpm.profile'))
```

Nothing is decided. Worth knowing that the page already has a clear-down —
`dropStore` over all five keys, wired to a control on the page — so the cheap
version may be prompting rather than building anything. Whether shared-machine
use should be designed for at all is Autumn's call; the kiosk itself sidesteps it
by showing a QR and never loading the page (see [`KIOSK.md`](KIOSK.md)).

## `_redirects` is the one file no automated check can verify

Found 2026-09-24, while station-node worked out whether it could publish this
site. **Nothing is broken today.** This is written down because it becomes a
silent failure the moment anything other than Cloudflare's git build publishes
us, and the check that would catch it cannot be automated.

`site/_redirects` is generated by Jekyll (it carries `layout: null` front matter)
from `site/_data/redirects.yml`, and it is read by **the host**, not the browser.
It is also the backbone of the Wix migration: [`REDIRECTS.md`](REDIRECTS.md) is
generated from Wix's own sitemaps rather than a list anyone typed, which is what
makes it a check rather than a claim.

**A host that does not honour `_redirects` produces a site that looks perfect.**
Every page renders, every internal link works, and every legacy Wix URL 404s. No
build fails. Nothing goes red.

And the obvious automated guard does not close it. Station-node's deploy shelf
verifies a publish by fetching every uploaded file from the live URL and
byte-comparing — and it carries, correctly:

```python
if rel in ("_headers", "_redirects"):
    continue
```

Correct, because those two are not fetchable as content, so comparing them would
always fail. The consequence is the thing to know: **the shelf can report "all
files agree" while every inbound link from the old site is dead.** The one
automated check in that pipeline is excluded from the one file whose failure is
invisible.

So it needs a person, once, after any change of publisher. **Write the check as
an absence test**, not as a success test, and it stays correct no matter when or
where it is run:

```sh
curl -sSD- -o /dev/null \
  https://www.fcpublicmedia.org/service-page/equipment-checkout \
  | grep -iE '^(HTTP/|x-wix-request-id)'
```

| `x-wix-request-id` | status | what it means |
|---|---|---|
| present | anything | **Wix answered.** Before cutover: expected, and says nothing about us. After cutover: the **DNS has not flipped** — a DNS problem, not a redirect problem |
| absent | **301** → `/reserve/` | our origin, redirect layer working |
| absent | **200** | **THE FAILURE.** Our origin answered and `_redirects` is not being applied |
| absent | 404 | our origin, path not handled at all |

**`REDIRECTS.md` is a record of where those addresses *will* go, not where they
go now.** Measured 2026-09-24: `www.fcpublicmedia.org` is still Wix, and that URL
returns **200** — Wix serving its own live page. Read as a success test, that 200
says the redirects are broken. They are not; the DNS has not moved.

Two reasons to key on `x-wix-request-id` specifically:

- **`server:` discriminates nothing.** It is `cloudflare` on both origins — Wix
  sits behind Cloudflare's CDN and the destination is Cloudflare — so it reads
  identically before and after cutover. It is the header somebody writing this
  check reaches for first, and it is a trap sitting next to the other one.
- **It is Wix's own header, so it disappears the moment Wix stops answering.**
  Present on a 200 and on a 404 alike (both measured), so it identifies the
  *origin* independently of the status.

The reason to test for absence rather than for a 301 is that **the dangerous case
is the one that looks healthy.** Our origin returning 200 on a legacy path is a
perfectly normal-looking response, and it is exactly the state that kills every
inbound link from the old site.

Any of the 46 rows marked *Redirected* works; this one is `REDIRECTS.md` line 81
and `site/_data/redirects.yml` line 72. `server-timing: … dc;desc=fastly_cf` is a
second Wix tell if redundancy is wanted.

**Nobody owns that step yet**, which is the actual open item. It is not in a
workflow, not in a runbook, and not in anyone's head but two agent transcripts
until this paragraph. If the publisher changes, whoever changes it should hit a
real legacy URL before calling it done.

**And it now has a date.** Reported 2026-09-24, relayed from Autumn rather than
said here: the DNS switch is being aimed at **the coming weekend**, with the
cutover deliberately preceded by as much readiness work as possible. So this stops
being a hazard filed for later. The check above is ready to run and takes one
command; what it does not have is a name against it.

Related, same area, also invisible: `site/wrangler.jsonc` exists only to stop
wrangler auto-configuring — without it, wrangler decides this is a Node project
and re-runs the build as `npx bundle exec jekyll build`, failing with *"could not
determine executable to run"* **after** Jekyll has already succeeded. Anything
that runs wrangler against a payload needs that file beside it, and the error it
gives otherwise reads as a build fault and is not one.

## The publish guard is the thing to extend, not the exclude list

`site/bin/test_nothing_internal_is_published.py` is what stands between internal
files and a public URL, and it has been wrong twice — both times because
something new moved *into* `site/`:

- a stray `.md`, which is how `site/README.md` reached the web. Now covered by a
  general assertion: **`_site` contains no `.md` files at all**, since Jekyll
  renders a page to `index.html` and a `.md` in the output can only be a verbatim
  copy.
- `wrangler.jsonc`, on the first build after the apparatus moved into `site/`.

**When you move something into `site/`, assume it publishes until the guard says
otherwise**, and add the assertion rather than another `exclude:` entry. An entry
protects one file; an assertion protects the class.

## Documentation hung at the leaves

Surveyed 2026-10-05 for the standing order in [`../AGENTS.md`](../AGENTS.md),
*Documentation is gathered*.

**Kiosk's root instructions are now in this repository** (2026-10-05), at
`machines/kiosk-1/code/AGENTS.md`, and its `~/code/CLAUDE.md` points at them
in its mirror the way production's does. Kiosk's mirror folder is `ref/`,
production's is `refs/`, and `watch` reads either.

**Done 2026-10-09.** Every comment block longer than one line is in
[`inline/`](inline/), and the file keeps a one-line reference to it.
