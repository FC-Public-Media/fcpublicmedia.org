# Everything written down

The root README is empty on purpose. It was 68 KB, it was the first thing a
visitor saw, and it was the last place anybody wanted to edit — so it had become
the only home for a lot of this while also being unreadable. One of those two
jobs had to go somewhere else, and it was easier to move the reference material
than to move the front door.

A short README will come back when the shape stops moving. Writing one now would
describe a repository that is being rebuilt underneath it.

---

## Start here if you just arrived

[`OPEN.md`](OPEN.md) — what is true right now and will not announce itself. Stale
pins, a branch nobody is watching, a seat's own finding nobody actioned.

## What this repository is

| | |
|---|---|
| [`NODE.md`](NODE.md) | **the repository.** What is at the root, what is in `site/`, what `site/_data` may reach into, and what a second site in a cluster would need |
| [`STATION.md`](STATION.md) | **the station.** The machines, the crews, the public-repository rule, and which engines arrive in what order |
| [`TENANCY.md`](TENANCY.md) | **the tenancy.** Other people's sites published from here — the factory, ejection, and what a member site is owed |
| [`DESIGN-NOTES.md`](DESIGN-NOTES.md) | **the services.** Work taken far enough to be resumed and deliberately not built — the digitization station, workstation sign-in, member scheduling |

## How to work on it

| | |
|---|---|
| [`running-it.md`](running-it.md) | build it locally, what the tree holds, how to add a page, how the tests run |
| [`deploying.md`](deploying.md) | Cloudflare is the live path; Azure is the one that came first |
| [`payments.md`](payments.md) | the five transactions, who processes each, and the rules about keys |
| [`identity.md`](identity.md) | who somebody is, how they prove it, and what happens at the door |
| [`programming.md`](programming.md) | Cablecast, the schedule, class mode, and what the homepage features |
| [`member-sites.md`](member-sites.md) | what a member's repository holds, what we supply, publishing states, and ejecting |
| [`MEMBER-SHOWS.md`](MEMBER-SHOWS.md) | the plan: a passkey on `you.`, a sub-subdomain per show, wizard steps as pull requests, publishing to trade, bookings and recordings coming home, and a test per stage |
| [`HOLDING-A-BUBBLE.md`](HOLDING-A-BUBBLE.md) | the same plan from the member's phone: what the README owes them before they sign, where membership sign-up goes wrong from their side, and the rails that meet there |
| [`known-issues.md`](known-issues.md) | things that are wrong and known to be wrong |

Standing orders for anyone working here — human or agent — are in
[`../AGENTS.md`](../AGENTS.md), at the root, because that is where they are
looked for.

## What people have said, and what is owed

| | |
|---|---|
| [`REVIEW-NOTES.md`](REVIEW-NOTES.md) | feedback, close to verbatim, with the file each note lands in. **Unratified board feedback — this is the document most worth not publishing** |
| [`CONTENT-TODO.md`](CONTENT-TODO.md) | copy the site still needs, most of it locked inside Wix widgets |
| [`PAYMENTS-CHECKLIST.md`](PAYMENTS-CHECKLIST.md) | what has to be true before anybody can be charged |
| [`RESERVE-DESIGN.md`](RESERVE-DESIGN.md) | turning `/reserve/` from a list of rooms into a list of hosts |
| [`REDIRECTS.md`](REDIRECTS.md) | the old Wix address space, generated from their sitemaps rather than typed |
| [`MANIFEST.md`](MANIFEST.md) | what the site claims to be |
| [`ADVOCATE.md`](ADVOCATE.md) | the constitution the advocate seats answer to. `../advocate.yml` declares them |

---

## None of this is published

`_config.yml` sets `source: site`, so Jekyll never looks at the repository root
or at this directory. That is structural, not a rule anybody has to remember:
these files have no public URL because the build cannot see them.

It used to be a rule anybody had to remember, and it failed three times —
MANIFEST, REDIRECTS and RESERVE-DESIGN each reached a public URL by being left
off an `exclude:` list. So: **a new internal document goes here or at the root.
Never in `site/`.**
