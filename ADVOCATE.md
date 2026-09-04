# The advocate: what health means for this site

Draft, and expected to stay draft for a while. This is the spec
`.advocate-engine` would implement for *this* repository.

## Why this exists

Board terms are about a year. Nobody who built this will be here indefinitely,
and the people who inherit it will not have watched it being made. Almost
everything in this repository is explained in a comment next to the thing it
explains — which works beautifully for whoever is already reading that file,
and not at all for whoever does not know the file exists.

So the point is **not** to catch bugs. The tests do that. The point is that a
small set of facts about this site decay on their own, quietly, and the person
who would have noticed has rotated off the board.

The output is therefore **notices a trustee can read in a meeting** — not a log,
not a dashboard, not a red X in a pipeline nobody opens. Something like:

> *The Slack invite on the community page expires every thirty days and was
> last regenerated in June. Anyone clicking it today gets an error. Who owns
> regenerating it?*

That is a board agenda item. It needs a person, not a fix.

## What this is not

- **Not a regulator.** It cannot block a commit, fail a build, or refuse a
  change. It is not a pre-commit hook and it has no veto. It shows up to
  understand where things are going and to say something useful about it.
- **Not a pipeline.** Nothing runs on its own today. It is local by default,
  and that is the intended resting state, not a limitation to be engineered
  away.
- **Not owed to any particular vendor or agent.** FCPM has no allegiance to a
  specific model, product or company. Anything that can read this file and act
  on it is a valid implementation. The submodule is a working default — a
  toolbox left in the corner with batteries included — and there is no
  obligation to follow its pin. Replacing the implementation entirely is a
  supported outcome.
- **Not GitHub-shaped.** Today the work arrives as pull requests because that
  is what exists. The intended direction is local checkouts on ordinary
  devices, so somebody can draft a change from a phone and have it transmitted
  as a proposal. Nothing in this spec should assume a particular forge.

An advocate may also read whatever automation already exists here — the
workflows in `.github/`, the scripts in `script/` — and follow those rather
than reinvent them. Belt and suspenders. Several routes to the same outcome is
the point, not duplication to be cleaned up.

## Health, in five kinds

### 1. Things that decay on a clock

The category with the fewest moving parts and the most value, because nothing
here fails loudly. It just goes quietly wrong one day.

Credentials are the biggest instance of this and have their own section below.
What is left here is everything else that has a shelf life:

- **The Slack invite** in `_data/community.yml`. It is the primary channel on
  the community page, it expires every thirty days, the file says so in a
  comment, and it says no CI is regenerating it. It is also the one credential
  in this project whose age is fully readable from the git history — see below.
- **Claim signing keys.** `_data/identity.yml` holds none today, so this is
  future rather than live. The rotation rule is already written down and has a
  trap in it: deleting a key invalidates links already sitting in people's
  inboxes, so old keys must outlive their claims.
- **Third-party embeds.** Booqable's snippet, the Cablecast player, the
  newsletter link. None expire today. Any of them could, and none would
  announce it.
- **The redirect map.** `_data/redirects.yml` describes an address space
  belonging to a Wix site FCPM is leaving. Correct now; will not stay correct.

### 2. Whether our credentials are being rotated

A standing concern in its own right, and deliberately **not** something to
solve here. Nobody is asking the advocate to rotate anything. The job is to
notice, periodically, that rotation is or is not happening, and to turn that
into a question somebody can answer.

This is a research task, and the repository is a better source than it looks.

**What the git history can tell you.** When a credential lives in the repo,
the last time its line changed *is* the last time it was rotated. `git log -L`
or a blame on that line dates it exactly. The Slack invite in
`_data/community.yml` is the worked example: it expires every thirty days, so
the age of that line is the answer, and the answer is almost certainly "too
old".

**What the git history cannot tell you, and this is the more important half.**
Most of what this project depends on is *referenced* here and *stored*
somewhere else — which is correct, and is exactly why nobody can see when it
was last rotated:

| Credential | Where it lives | Visible from the repo |
|---|---|---|
| `AZURE_STATIC_WEB_APPS_API_TOKEN` | GitHub repository secrets | Reference only |
| `CLOUDFLARE_API_TOKEN` | GitHub repository secrets | Reference only |
| `STRIPE_KEY` (secret half) | Worker secret | Reference only |
| `PUBLIC_STRIPE_API_KEY` | GitHub secret, publishable half | Reference only |
| `GITHUB_APP_ID` / `GITHUB_APP_KEY` | Worker secret | Reference only |
| `GITHUB_TOKEN` (the Worker's own) | Worker secret | Reference only |
| `R2_ACCESS_KEY_ID` / `R2_SECRET_ACCESS_KEY` | Worker secret | Reference only |
| Claim signing private key | A file kept out of git | Reference only |
| The Slack invite | `_data/community.yml` | **Fully datable** |

For everything marked *reference only*, the repository can still establish the
**earliest possible age** — the commit that introduced the reference — and can
say plainly that no later evidence exists. That is enough to ask the question:

> *The deploy token was wired up in March and there is no record of it being
> replaced since. Whoever holds the Cloudflare account: has it been rotated,
> and does it expire?*

**Why this matters more than it sounds.** A deploy token that quietly expires
does not announce itself. The site simply stops updating, and the person who
notices is whoever next wonders why their change never appeared — possibly
weeks later, possibly a board member who assumes the site is just wrong. The
same is true of the GitHub App key and the R2 credentials: nothing breaks
loudly, things just stop working.

**Two things the advocate must never do here.**

1. **Never read, print, or copy a secret value.** Establishing that a
   credential exists and when it was last touched requires none of them.
2. **Never move a secret into the repository to make it observable.** The
   reason these are unobservable is the reason they are safe. Trading that for
   a tidier report is the single worst outcome this document could cause.

### 3. Whether we can still be paid

Named as a concern in its own right, and the answer today is uncomfortable:
**nothing on this site can take money except Booqable equipment rental.**
`payments.yml` carries an empty Stripe publishable key with `live` false, and
all five entries in `providers.yml` are `placeholder` or `pending` — tickets,
membership, donations and program submission all still point at Wix in their
notes.

Three things are meant to sell: membership and class drop-ins through Stripe,
equipment through Booqable. Only the third is wired, and class drop-in prices
are still `TODO`, which is why class mode hides pricing rather than showing a
number nobody approved.

This matters more each year, because PEG funding is being wound down.

**Watch:** that every entry in `providers.yml` is either live or has a person
and a reason recorded against it. **Never set a price or pick a provider** —
those are board decisions, and a plausible guess at either is worse than a
blank.

### 4. Whether the people we depend on are still there

The named worry, and the reason this is not paranoia: **if Cablecast were to go
out of business, this site would lose its entire programme catalogue, its
archive, its live stream and its airing history in one move.** There is no
second source for any of it.

A research pass every six months is enough. Not monitoring — reading. Is the
vendor healthy, acquired, sunsetting, changing terms?

The current dependencies, in rough order of how much would break:

| | If it went away |
|---|---|
| **Cablecast** | The catalogue, the archive, the live embed, the airing log |
| **Cloudflare** | Hosting. Recoverable — the site is static files |
| **Booqable** | The rental catalogue on `/reserve/` |
| **Microsoft 365** | The intended home for booking and membership |
| **Wix** | The domain, until it moves |

Worth a board conversation on its own: **this repository deploys twice**, to
Azure Static Web Apps and to Cloudflare Pages, by two independent mechanisms.
Two live copies of the same site is one more than anyone needs, and nobody has
decided which is real.

Also worth surfacing, because it is org health rather than site health and it
still lands here: PEG funding is being wound down. Anything on this site that
generates revenue — memberships, rentals, hourly studio hire — gets more
important as that goes.

### 5. Whether the site is still telling the truth

Failures here are not crashes. They are pages that keep building, keep passing
the tests, and quietly say something untrue.

- **Content that has gone stale rather than wrong.** Every class in
  `_data/classes.yml` is currently in the past, so the calendar on `/meet/` and
  the "Coming up" strip on the front page both render empty and nothing
  complains. This is live today.
- **`TODO` reaching a public page.** The `transaction-todo` block is designed to
  be loud, which only works while it is rare.
- **Links that outlived their target.** Pages here get merged deliberately and
  often. `/equipment/` and `/reservations/` both disappeared inside a week, and
  a rename was missed in `script/` because the sweep covered templates, data
  and JavaScript but not Python. `REDIRECTS.md` currently reports one address
  unaccounted for: `/equipment`.
- **Third-party CSS that stopped applying.** The Booqable overrides in
  `site.css` were entirely dead for weeks while the file confidently described
  a layout the site did not have — their stylesheet is injected at runtime and
  wins every equal-specificity tie. Read the *computed* style, never the rule.
- **Liquid that fails without raising.** Each of these shipped here: an empty
  string is truthy; `contains … == false` does not negate; an include parameter
  cannot be an indexed expression; a hash key must be stringified; and a
  wrapped line beginning `2004.` is an ordered-list marker to Markdown.
- **Internal documents served at public URLs.** A `.md` without front matter is
  copied verbatim. Four were reachable before this was noticed.

## Debts that are deliberate

An advocate that tidies these away is worse than none. Each was decided, with
reasons, and the reasons are in the code next to them:

- **No `<h1>` on pages under `_layouts/page.html`.** The heading was the menu
  word repeated at a cost of 240px; the masthead prints the menu word instead.
  Accessibility will want a heading here eventually. Known, deferred, not an
  oversight.
- **Light is the default even on a dark system**, and the colour toggle is
  hidden from anyone whose system is already light.
- **The Booqable store is browse-only.** No datepicker, so no cart.
- **`_data/hosts.yml` is rendered by nothing.** Publishing a person's name is a
  decision, not a side effect of recording it.
- **Claim links forward on purpose** — see `_data/authorize.yml`.
  `RESERVE-DESIGN.md` proposes reversing that. Until somebody decides, the
  current behaviour is intended.

## Seats

The concerns above are held as seats in `advocate.yml` — the only file
`.advocate-engine` asks of this repository. One seat is one concern, kept on
`advocate/<name>`, worked in short visits by whoever turns up.

A seat is declared by **who it speaks for**, not by a list of tasks: a
`constituency`, the things that constituency actually says out loud, and two or
three goals. That is the framework's shape and it is the right one — a task
list goes stale, whereas "the treasurer who has to answer whether we can take
money" does not.

Every session is `local`. Nothing calls out, nothing runs unattended, and no
credential is needed to hold a seat. `writes: []` throughout, which is the
honest default: an advocate proposes, a person decides.

A seat exists once it has spoken. Until then it is an intention, and the
council page says so.

## How to report

- **Address a person, not a repository.** A notice should be answerable by a
  trustee who does not read code.
- **Say what decays, when, and who would notice** — not what to change.
- **Propose, never enforce.** Pull requests are welcome. Blocking is not.
- **Never invent content.** No person, price, date, biography or availability.
  Those belong to the board, and a plausible guess in any of them is worse than
  a blank.
- **Quiet is a valid report.** Nothing to raise is the expected result most of
  the time, and saying so is how the next reader knows it ran.
