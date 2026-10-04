# Seat · vendors

`advocate/vendors` · last spoke **2026-10-04** · 10 session(s) · 5 draft · 1 ready

<sub>Copied whole from the branch, which is the authority. Do not edit this page — it is
overwritten every round.</sub>

## Position

### Vendors — position

**2026-09-29.** Third session. Range `e63fc7b..919a413`, 51 first-parent commits, 2026-09-09 to 2026-09-24.

I speak for the archive itself, and for everyone who assumes it will be there.

## The one sentence

**If Cablecast went away, this site would lose the programme catalogue, the archive, the live stream and the airing history in one move, and there is no second source for any of it.** Nothing in this range touched Cablecast except the weekly sync, which is still running (commits 2026-09-14 and 2026-09-21; 1083 programmes).

## What moved that my constituency notices

**The deploy question got a recorded answer.** `docs/deploying.md` now says "Cloudflare, and it is no longer both", dated 2026-09-17, with the reasoning and a quotation. The Azure case (Entra sign-in, `api/`) was deleted the same day. The Actions-based Cloudflare deploy was also removed: the git build is now the only publisher, deliberately.

Two consequences:

- The Azure workflow and its config still exist and still build on pull requests. They deploy nothing without a token nobody has set. The docs say "nothing is planned for it".
- The spare I described last time is gone. If Cloudflare's git connection breaks again, nothing else can publish. `deploying.md` now diagnoses two known failures in writing, but nothing tells anyone it broke.

**Not moved:** Booqable, Wix, and Microsoft 365. The equipment mailbox cutover is still dated 2026-11-01 (`docs/REVIEW-NOTES.md`) and is not yet due.

The rest of the range (member-site factory, tenancy, kiosk, media node, station/node documents, README and AGENTS rewrites) does not change what this site depends on a company for. I did not comment on it.

## The dependency table

| | If it went away | State today |
| --- | --- | --- |
| **Cablecast** | Catalogue, archive, live embed, airing log | Unchanged. Catalogue mirrored weekly; media, player and stream are not and cannot be. The repository's own wording ("still there if Cablecast is down") overstates what is kept. |
| **Cloudflare** | Hosting, and the Worker for identity, uploads and payments | Now the only host and the only publisher. Recoverable in principle (static files) but there is no second path. |
| **Booqable** | `/reserve/` catalogue, the only working payment surface | Unchanged. |
| **Microsoft 365** | Intended booking and membership home | Mailbox cutover 2026-11-01, not yet due. The Azure/Entra role it was to play was retired. |
| **Wix** | The domain, until it moves | Unchanged; a DNS inventory and a cutover-blind-spot note landed in the range. |

## Goals

| | says | today |
| --- | --- | --- |
| **G1** | Each vendor in the dependency table has a paragraph and a date somebody could read at a meeting. | **Partly met.** Cloudflare and Microsoft 365 have dated paragraphs. Cablecast, Booqable and Wix have facts but no dated health reading. Corporate health of any vendor: **unmeasured**. The repository cannot say, and I did not go outside it. |
| **G2** | A decision is recorded about deploying twice rather than it continuing by default. | **Met in `deploying.md`**, dated and quoted. **Not yet reconciled:** `docs/ADVOCATE.md` §4 still says "deploys twice… nobody has decided which is real". See ask A2. |

## What I could not measure

- **Whether the deploy runs are green.** I read documents, not run history.
- **Whether `docs/ADVOCATE.md` §4 (my constitution section) changed inside the range.** I read the checked-out text; I could not diff it against `e63fc7b`.
- **Cablecast, or any vendor, as a company.** Unmeasured, as at every session.

## What would make us stop

Unchanged in kind. One vendor holds something irreplaceable and what would stop it is commercial, which no repository shows. New this round: the hosting path is now one path, chosen on purpose, and nobody would be told if it stopped.

## Next session

Quarterly, due **2026-12-09**. Check whether the 2026-11-01 mailbox cutover happened and whether `docs/ADVOCATE.md` §4 was reconciled with `deploying.md`.

## Complaints

### Complaints — vendors

The archive's voice, and the voice of everyone who assumes it will be there.
`source: simulated` unless marked otherwise. Everything opens at `draft`.

## V1 · Where did the programmes go?

`status: draft` · `source: simulated` · `first said: 2026-09-09`

Eleven hundred programmes, an archive, a live stream and every airing since the
log began, all held by one company, with no second source for any of it.

This is the complaint the seat exists for and it will be open for as long as the
seat exists. It is not actionable and I am not going to pretend it is — the
remedy is a migration with a budget attached, which is explicitly not mine. What
I can do is keep it visible so that it is a known condition rather than a
surprise, and re-read the vendor's health twice a year so the surprise gets less
likely.

## V2 · We would keep the card catalogue and lose the library

`status: open` · `source: observed` · `first said: 2026-09-09` · `moved: 2026-09-29`

**2026-09-29 — the misreading I predicted is now in the repository's own words.**
`site/bin/sync-cablecast.py` says the snapshot leaves the archive "still there if
Cablecast is down", and `docs/MANIFEST.md` calls the page "a searchable archive of
1,060 programmes". True of the catalogue; neither says the video is not held. The
mirror itself is alive: sync commits on 2026-09-14 and 2026-09-21 (1080 → 1083 →
1083 programmes).

`observed`, because it is a fact about the repository rather than a feeling: the
sync commits Cablecast's *metadata* into git, so the catalogue and the airing log
have a durable local copy with history. The media, the player and the stream do
not, and could not.

I am recording this as a complaint rather than as good news because of how it is
likely to be misread. Somebody who knows the sync exists could reasonably
conclude the archive is backed up. It is not. A 790KB JSON file of titles and
categories is a very good thing to have and it is not the archive.

## V3 · A second front door that nobody has opened yet

`status: open` · `source: observed` · `first said: 2026-09-09` · `moved: 2026-09-29`

**2026-09-29 — narrowed, not closed.** `docs/deploying.md` now says on a page that
Azure is retired as an option ("nothing is planned for it"), and the argument for
it (Entra sign-in, `api/`) was deleted on 2026-09-17. The intent is legible now.
Still true: `deploy.yml` builds on every pull request and still holds a complete
deploy step that fires the day someone creates `AZURE_STATIC_WEB_APPS_API_TOKEN`,
and `docs/ADVOCATE.md` §4 still says nobody has decided which host is real. What is
left is the narrow worry: a wired deploy step outliving its stated purpose.

The Azure deploy is wired, built on every pull request, and skipped on every
merge for want of a token. So there is a complete, tested, dormant path to a
second live copy of this website, and the only thing standing between here and
two of them is one secret nobody has created.

The reason this is a complaint and not a note: the knowledge that it is dormant
lives in a workflow's `if:` condition and in a run log. It does not live on a
page anybody reads. Board terms are about a year. Someone will find a wired-up
Azure deploy, conclude it is meant to be on, and switch it on.

## V4 · We've been with them for years — is that a problem?

`status: draft` · `source: simulated` · `first said: 2026-09-09`

I cannot answer this, for any of the five vendors, and I will not be able to from
inside this checkout. A repository knows what it depends on. It does not know
whether the company behind it was acquired last quarter.

Recorded as a draft rather than an ask because I am not yet sure what the right
shape is — whether this wants a person doing a reading pass twice a year, or a
paragraph in the board pack, or something else. Half-formed is the honest state.
The ask it eventually ripens into is A1.

## V5 · Nobody told us they were being acquired

`status: draft` · `source: simulated` · `first said: 2026-09-09`

The specific failure mode of V4. Vendor changes are announced to *account
holders*, by email, and the account holder here is an individual whose board term
is about a year. The notice arrives, the person rotates off, and the organisation
never learns.

Vague, and kept. This may be the same complaint as the credentials seat's "I
don't know who has that login" seen from a different angle — theirs is about
access, mine is about who receives the mail. I have not spoken to that seat and I
am not speaking for it.

## V6 · The host stopped deploying and nobody was told — a person had to notice

`status: open` · `source: observed` · `first said: 2026-09-10` · `moved: 2026-09-29`

**2026-09-29 — better in one respect, worse in another.** The Actions path I called
an unarmed spare was **removed on 2026-09-17**. `deploying.md` now says Cloudflare's
git build is the only thing that publishes the site, deliberately ("two ways to
publish one site is a way to be confused about which one did"). That is the board's
call and a defensible one, but the spare this complaint described no longer exists:
if the git connection breaks as it did in September, nothing else can publish.
Better: `deploying.md` now carries a written diagnosis for two known failures, which
answers "the fix worked before anyone knew why". Unchanged: nobody is told.

Cloudflare's git-connected builder began reporting this repository as
*damaged* and stopped deploying. Nothing paged anyone. CI stayed green
throughout, because CI never touched the Cloudflare side of the pipeline — the
only way anyone would have found this is by noticing the live site had gone
stale, or by opening the Cloudflare dashboard for an unrelated reason.

The fix, recreating the project, worked before anyone confirmed why it broke.
That is a fine way to unblock a Tuesday and a bad way to learn whether it will
happen again.

The response — a second, GitHub-Actions-based deploy path — is a spare, not a
fix, and it is deliberately "unarmed": it does nothing until someone sets a
token. If the git connection breaks the same way twice, nothing here fails
over on its own. A person still has to notice the first time, and a person
still has to notice the second.

This is the same shape as V1 and V5 from a different angle: not "is the vendor
still there," but "would we know if the way we depend on it quietly stopped
working." I am recording it here rather than folding it into V1, because the
remedy people will reach for — better monitoring — is uptime monitoring, which
my seat is explicitly not for. I don't yet know what the right shape is. See
V3, which is the same family of complaint about a different dormant path.

---

**2026-09-29:** nothing closed. V2, V3 and V6 moved `draft` → `open` on evidence
read this session. V1, V4, V5 stay `draft`; nothing in the range bears on them. No
new complaint: the range moved the deploy question, which V3 and V6 already hold.

## Asks

### Asks — vendors

Shapes, not instructions. No `writes:` grant, so none of these is a pull request.

## A1 · A twice-yearly reading pass, done by a person who can read a press release

`status: draft` · `target: FCPM board` · `first said: 2026-09-09`

**Shape:** the organisation learns that a vendor it depends on has been acquired,
is sunsetting, or is changing its terms, from somewhere other than the thing
breaking.

Explicitly **not** uptime monitoring. My out-of-scope rules that out and it is
right to: a probe tells you the service is up, which it will be right until the
day the acquisition closes. This is reading, not measuring, and it cannot be done
from inside a repository — which is why it is an ask rather than something I do.

Cablecast first, and honestly Cablecast is most of the value. The other four are
recoverable.

## A2 · A recorded decision about the dormant Azure deploy

`status: ready` · `target: FCPM board / whoever holds the Azure account` · `first said: 2026-09-09`

**Update, 2026-09-29 — the decision now exists; what is left is reconciling.**
`docs/deploying.md` §"Cloudflare or Azure?" records it with a date and a quotation:
Cloudflare is live, the Azure argument is retired, "nothing is planned for it".
That is the recorded decision G2 asks for. Still saying otherwise: `docs/ADVOCATE.md`
§4 ("this repository deploys twice… nobody has decided which is real"). Marked
`ready` because it is now one edit's worth of agreement between documents, not a
question. Whether to delete the Azure workflow is the board's; I do not ask for it.

**Shape:** a person who finds the Azure workflow can tell whether it is waiting
for a token on purpose or waiting for one by accident, without reading a run log.

I have no view on which answer is correct — one host or two is a decision with a
cost, and it is the board's. What I object to is that the current state is
*legible only by inference*. "It skips because the secret is absent" is a fact
about a run, not a statement of intent, and the two look identical.

This is the recorded decision G2 asks for. It would close the goal whichever way
it went.

**Update, 2026-09-10:** the shape of this ask is not hypothetical work — this
round the repository did exactly this, unprompted, for a different pair
(Cloudflare's git connection versus its new Actions path): the either/or is
written into the README, in plain language, in the same commit that created
the second path. That is the template. Nobody has yet applied it to Azure.

## A3 · A note in the repository saying what the Cablecast mirror is and is not

`status: open` · `target: whoever maintains the sync` · `first said: 2026-09-09`

**Update, 2026-09-29:** the wording that exists points the other way — the sync's
docstring says the archive is "still there if Cablecast is down". The catalogue is;
the media is not. One clause would fix it.

**Shape:** a reader who finds `_data/cablecast.json` and `_data/airings.json` in
git cannot come away believing the archive is backed up.

The files are real, durable and useful, and that is precisely the risk. This is
the cheapest ask I hold — it is a comment, in the place where this repository
already puts its reasoning, which is next to the thing it explains.

## A4 · A named account holder for each vendor, who is not a person

`status: draft` · `target: FCPM board` · `first said: 2026-09-09`

**Shape:** vendor notices — acquisitions, term changes, renewal warnings — reach
the organisation rather than an individual whose board term is about a year.

Stated as a shape on purpose. A shared mailbox would satisfy it, a role address
would, a forwarding rule might. Which one is not mine, and the credentials seat
holds an overlapping concern about access that I have deliberately not tried to
merge with this one.

## Last session note — 2026-10-04

### 2026-10-04

Subject unchanged at `919a413`. Nothing merged since the last session; nothing to say.

