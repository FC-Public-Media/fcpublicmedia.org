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

## Health, in three kinds

### 1. Things that decay on a clock

The category with the fewest moving parts and the most value, because nothing
here fails loudly. It just goes quietly wrong one day.

- **The Slack invite** in `_data/community.yml` expires every thirty days. The
  file says so, in a comment, and says no CI is regenerating it. It is the
  primary channel on the community page.
- **Claim signing keys.** `_data/identity.yml` currently holds none, so this is
  future rather than live — but the rotation rule is already written down and
  it has a trap in it: deleting a key invalidates links already sitting in
  people's inboxes. Old keys must outlive their claims.
- **Third-party embeds and their tokens.** Booqable's snippet, the Cablecast
  player, the newsletter link. None expire today. Any of them could.
- **The redirect map.** `_data/redirects.yml` describes an address space that
  belongs to a Wix site FCPM is leaving. It is correct now and will not stay
  correct forever.

### 2. Whether the people we depend on are still there

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

### 3. Whether the site is still telling the truth

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
