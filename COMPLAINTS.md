# Complaints — vendors

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

`status: draft` · `source: observed` · `first said: 2026-09-09`

`observed`, because it is a fact about the repository rather than a feeling: the
sync commits Cablecast's *metadata* into git, so the catalogue and the airing log
have a durable local copy with history. The media, the player and the stream do
not, and could not.

I am recording this as a complaint rather than as good news because of how it is
likely to be misread. Somebody who knows the sync exists could reasonably
conclude the archive is backed up. It is not. A 790KB JSON file of titles and
categories is a very good thing to have and it is not the archive.

## V3 · A second front door that nobody has opened yet

`status: draft` · `source: observed` · `first said: 2026-09-09`

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

`status: draft` · `source: observed` · `first said: 2026-09-10`

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

**Nothing closed this session.** Nothing genuinely resolved or went stale —
V1–V5 are all still true as stated. One new draft, V6.
