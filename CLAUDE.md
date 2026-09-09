# Standing orders

Rules that hold across sessions, for anyone — human or agent — working in this
repository. They are here rather than in a commit message because they are the
kind of thing that gets re-derived wrongly by whoever shows up next.

Not a style guide. See [DESIGN-NOTES.md](DESIGN-NOTES.md) for how the site is
built and [CONTENT-TODO.md](CONTENT-TODO.md) for what it still needs.

---

## Wix is a READ-ONLY interface. Always. No exceptions.

**Read from Wix freely. Never write to it — regardless of what permissions the
connector offers.**

The connector is authorised for our convenience, and it may well expose write
scopes. An OAuth grant is not a decision anybody made. Treat every write verb
it offers as unavailable.

Why this is a standing order and not a preference:

- **Wix is the live public site.** It is what visitors and Google see today. A
  write does not land in a staging environment — it changes what the public is
  looking at, immediately.
- **Nothing there is under version control.** No diff, no branch, no PR, no
  history, no revert. Every safeguard this repository has, Wix has none of. A
  mistake made through the connector cannot be undone by us.
- **Divergence is the specific hazard.** We are mid-migration. Wix is still the
  system of record for content nobody has moved yet — that is exactly what
  CONTENT-TODO.md is a list of. The moment both sites are being edited, they
  start disagreeing about the same fact, and the *old* one wins, because the
  old one is the one actually published.
- **Reading is the whole job anyway.** REDIRECTS.md is generated from Wix's own
  sitemaps rather than a list someone typed, which is why it is a check rather
  than a claim. That pattern only works in one direction.

**What reading is for**, concretely, and it is a lot: pulling copy that was
locked inside a Wix widget and could not be scraped; checking what a page
currently says before rewriting it here; reading the sitemaps; and — the live
errand as of September 2026 — **retrieving old photographs of the spaces**,
which Bryan believes are still up there. See REVIEW-NOTES.md, round 1.

If something genuinely has to change *on Wix* — taking a page down, fixing a
redirect at the source — **say so and stop.** A human does it in the Wix admin.
Do not do it helpfully on the way past.

---

## Bryan's wording is authoritative. Do not improve it.

When the board president's phrasing and ours differ, **his wins**, and it goes
in close to verbatim.

Our copy is over-written. It was drafted by an agent and it reads like it —
longer than it needs to be, fond of a subordinate clause, explaining things a
member already knows. His rendering of the same idea is consistently shorter
and lands harder. "At any tier of FC Public Media Membership you can reserve
both the video and podcast studios, edit with the full Adobe Creative Suite,
and check out production equipment" says more, in fewer words, than the
paragraph it replaced.

The repository already worked this out once, before anybody made it a rule.
From the top of [`_data/facilities.yml`](_data/facilities.yml):

> Copy and square footage from the board president, August 2026. His words are
> kept close to verbatim — this is the one part of the site not written by us,
> and it reads better for it.

So:

- **Do not paraphrase him into our voice.** That is the failure mode. It reads
  as tidying and it is actually reverting.
- **Do not re-expand what he shortened.** If he cut a clause, the clause was
  the problem.
- Fix an outright typo, keep his sentence.
- Where his wording changes **policy rather than prose**, that is different and
  it stops being a copy question — it goes to Autumn. The credit-card wording
  on the reserve page is the worked example: "a temporary charge as collateral"
  and "a valid credit card for late fees and incidentals" are different
  arrangements, not two ways of saying one thing. Record it, do not choose it.

This applies to his words specifically, not to all feedback. It is a judgement
about one person's ear for the copy, which has been better than ours every time
so far.

---

## Feedback is recorded before it is acted on

[REVIEW-NOTES.md](REVIEW-NOTES.md) holds what people have said about the site,
close to verbatim, with the file each note lands in. Add to it when feedback
arrives; strike an entry through when it ships.

It is excluded from the Jekyll build in `_config.yml`, along with every other
internal document. A `.md` file with no front matter is copied verbatim to a
public URL otherwise — MANIFEST, REDIRECTS and RESERVE-DESIGN each leaked that
way once. **Any new internal doc goes on that exclude list in the same commit
that creates it.**
