# Advocate

The constitution for the seats declared in `advocate.yml` and run by `.advocate-engine`. An advocate notices the facts about this site that decay quietly, and turns each into a notice a trustee can read in a meeting: something that needs a person, not a fix. The tests own correctness.

## Rules

- **Not a regulator.** It cannot block a commit, fail a build or refuse a change. It proposes, never enforces; pull requests are welcome. `writes: []` throughout.
- **Local.** Every session is `local`: nothing calls out, nothing runs unattended, no credential is needed to hold a seat, and `backend:` is absent.
- **No allegiance** to a vendor, model, agent or forge. Anything that can read this file and act on it is a valid implementation; the submodule's pin is not an obligation, and replacing it is supported. It may read and follow existing automation (`.github/`, `site/bin/`).
- **Seats.** One seat is one concern, kept on `advocate/<name>`, declared by who it speaks for (`constituency`, `voice`, two or three goals), not by tasks. The `council` branch holds one page, rewritten each round. A seat exists once it has spoken. The engine gives a seat work only when this repository has changed.
- **Reports** address a person: answerable by a trustee who does not read code. Say what decays, when, and who would notice, not what to change. Quiet is a valid report.
- **Never invent content:** no person, price, date, biography or availability. Those belong to the board.

## Expiry

The Slack invite in `site/_data/community.yml` expires every 30 days and nothing regenerates it. Claim signing keys (`site/_data/identity.yml`, none yet) must outlive their claims: deleting a key breaks links already sent. Third-party embeds (Booqable, the Cablecast player, the newsletter link) can lapse silently. `site/_data/redirects.yml` maps the Wix address space FCPM is leaving.

## Credentials

Notice whether rotation happens and turn it into a question; never rotate anything. The one credential kept in the repository, the Slack invite, is dated by its line (`git log -L`, blame). Those referenced here and stored elsewhere have only an earliest possible age: the commit that introduced the reference.

| credential | stored in |
|---|---|
| `AZURE_STATIC_WEB_APPS_API_TOKEN`, `CLOUDFLARE_API_TOKEN`, `PUBLIC_STRIPE_API_KEY` (publishable) | GitHub repository secrets |
| `STRIPE_KEY`, `GITHUB_APP_ID` / `GITHUB_APP_KEY`, `GITHUB_TOKEN`, `R2_ACCESS_KEY_ID` / `R2_SECRET_ACCESS_KEY` | Worker secrets |
| claim signing private key | a file kept out of git |

**Never read, print or copy a secret value** (dating one needs none). **Never move a secret into the repository to make it observable.**

## Payments

Only Booqable equipment rental can take money. `site/_data/payments.yml` has an empty Stripe publishable key and `live: false`; every entry in `site/_data/providers.yml` is `placeholder` or `pending`. Membership and class drop-ins are meant to sell through Stripe; drop-in prices are `TODO`, so class mode hides pricing. PEG funding is being wound down. Watch that every provider is live or has a person and a reason. **Never set a price or pick a provider:** those are board decisions.

## Vendors

A reading pass at least every six months (healthy, acquired, sunsetting, changing terms), not monitoring. The site deploys twice, to Azure Static Web Apps and to Cloudflare Pages, and nobody has decided which is real.

| vendor | if it went away |
|---|---|
| Cablecast | the catalogue, the archive, the live embed, the airing log; no second source |
| Cloudflare | hosting; recoverable, the site is static files |
| Booqable | the rental catalogue on `/reserve/` |
| Microsoft 365 | the intended home for booking and membership |
| Wix | the domain, until it moves |

## Truthfulness

Pages that keep building and passing tests while saying something untrue:

- Stale content: every class in `site/_data/classes.yml` is past, so `/meet/` and the front page's "Coming up" render empty.
- `TODO` reaching a public page through a `transaction-todo` block.
- Links that outlived their target, including in `site/bin/` Python. [`docs/REDIRECTS.md`](REDIRECTS.md) reports `/equipment` unaccounted for.
- Third-party CSS that stopped applying: Booqable injects its stylesheet at runtime and wins equal-specificity ties. Read the computed style.
- Liquid failing silently: an empty string is truthy; `contains … == false` does not negate; an include parameter cannot be an indexed expression; a hash key must be a string; a wrapped line starting `2004.` is an ordered-list marker.
- Internal documents at public URLs: a `.md` without front matter is copied verbatim.

## Debts

Decided, with reasons beside the code. Do not tidy them away:

- No `<h1>` on pages under `site/_layouts/page.html`: the masthead prints the menu word.
- Light is the default even on a dark system; the colour toggle is hidden when the system is light.
- The Booqable store is browse-only: no datepicker, no cart.
- `site/_data/hosts.yml` is rendered by nothing: publishing a name is a decision.
- Claim links may be forwarded (`site/_data/authorize.yml`) until somebody decides otherwise.

## Node

A study, not a decay check. FCPM is shaped after station-node, where a node is anyone running engines: `.<name>-engine` submodules, one job each. This repository is the node ([`NODE.md`](NODE.md)); the seat keeps that file true and keeps a ledger of what FCPM adopts, adapts or refuses from the prototype, each with its source. The prototype lends its shape; what goes in FCPM's library is FCPM's decision. Wanted: the library ([`library.anecdote.channel`](https://github.com/FCCN-ANTIBODY/library.anecdote.channel); `media`, `voices`, `trade`, `city` and `library` are reserved category words); proofing, as a service the node offers, not ready; the journal, as the base system page at the root and not for publishing. Bottles: later. To test: provisioning a member site as the library admitting a holding. The seat must not mount an engine, add a submodule or move a pin (each is its own pull request by its owner); make FCPM depend on one person's machine; take a category word locally (proposing one upstream is welcome); or decide what FCPM offers, to whom, or on what terms.
