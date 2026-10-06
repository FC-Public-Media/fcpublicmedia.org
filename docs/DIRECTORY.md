# The directory: Atlas, and the Tell that registers to it

Recorded 2026-10-05 from Autumn's briefing on the media node (kiosk). It mounts
two engines, `.atlas-engine` and `.tell-engine`, and makes this repository both
the Atlas and the first Tell listed in it. Nothing is published yet. What exists
is the self-registration, which is the part she asked to be sure of:

> we are reducing all of what we're talking about to just making sure that we
> can do this self-registration locally, because that's all it's going to take.

## What it is for

> us having a directory of member sites is already, like, in motion. We don't
> publish it as a directory, but that is the proximate goal.

`sites.yml` knows our member sites, and `site/_shows/` and `site/_podcasts/` know
the shows. *"How those get listed is actually a totally different concern."*
Atlas is that concern: it provides the portal for discovery, and what it shows
is the Tell's content.

## The shape

```
member site ──▶ its data pile ──registers to──▶ our Tell ──registers to──▶ our Atlas
                (private, FCPM's org)            tell.yml                    atlas.yml
                                                 keys/tell.fpr               _data/tells.yml
```

Here the Tell and the Atlas *"are one and the same, they just need that
self-registration"*. The engines name this case: tell's README calls it **being
your own Atlas**. Registration is self-consent, and it is still consent.

- **A Tell fronts data piles.** It is an inbox system. A pile can be attached to
  several Tells, and piles can address each other or post where anyone who can
  address the Tell can see it. Deliveries to a pile are `age`-encrypted, which
  makes it *"provable when we were delivering it"*.
- **The starting posture is notification.** *"Just because I say notification
  doesn't mean it's actually going to anybody."* The enhancement queue on this
  node is the first thing that has notifications to give.
- **Delivery is settlement.** *"The delivery to the data pile we have access to
  is one and the same with completion."* Whether the member has looked yet is a
  separate question.
- **Atlas keeps the history, for now.** The Tell is *"ephemeral and transient"*.
  The posture between the two is not decided, but *"it's fair if we say that the
  Atlas component does the stockpiling for now."*
- **Antidote matches constitutions; Atlas only enforces its own**, when it lets
  a Tell register. That judgement is a human operator's today: *"An agent means
  either one of us."* Its failure mode is us.

## The data piles

> the data piles … are necessarily going to be our multi-tenant private
> repositories that we keep on FC Public Media, the org, on GitHub.

They can be mounted here, and we have the authority to speak for them. A member
reads theirs by authorizing a passkey at `<show-name>.you.fcpublicmedia.org`
([`MEMBER-SHOWS.md`](MEMBER-SHOWS.md)).

**Not decided:** whether a member's pile is a branch on their site's repository
or part of its base. She leans towards branches because they keep things clean
for members. Branches also mean a member's Cloudflare git connection has to
nominate which branches it builds, because ours will not build. *"We can make it
fail more gracefully, but the point is that like they should be aware."*

## What is mounted, and where its data lives

The engines read their data from the directory they are run in, which is the
repository root. So the root holds it, beside `advocate.yml`:

| | |
|---|---|
| `tell.yml` | who our Tell is: `id`, `name`, `url`, `scope`, `reports` |
| `atlas.yml` | who our Atlas is. Only peering with another Atlas reads it |
| `keys/tell.{pub,signers,fpr}` | the Tell's public signer. A pile pins `tell.fpr` |
| `_data/tells.yml` | the Tells our Atlas lists. Registration appends to it, and fails if `_data/` is missing |

The build root is `site/`, so none of this is published by the site.

`_data/piles.yml` will mean **tell's** registry, the piles that register to our
Tell. Atlas uses the same name for piles that place coarse public maps on it.
We do not do that, and the collision has to be settled before we do.

## The signer

Minted 2026-10-05 on kiosk with `door.py tell mint`. Its fingerprint is in
`keys/tell.fpr`. The private half is in Windows Credential Manager on that
machine (`fcpm-tell-signer`), and nowhere else. `door.py tell register` writes it
to a temporary file for the one signing call. Losing it means minting again, and
every pile that pinned the old fingerprint pins the new one. No pile has pinned
it yet.

Not minted, because nothing here needs them yet:

- `TELL_SEED_IDENTITY` (`age`). Delivery needs it, and `age` is not on kiosk.
- `TELL_QR_SECRET`. It is for polls, and polls are not our posture.
- An Atlas signer. Only peering with another Atlas uses it.

## Registering

```
door.py tell            what is published, and whether this machine holds the key
door.py tell register   .tell-engine/bin/register pr, against this repository
```

`register` clones `main`, so it runs once `_data/tells.yml` is there. It opens a
PR here on `tell/fort-collins/fcpublicmedia`. The branch name
is the claim, the commit is signed with the Tell's key, and the PR appends our
entry to `_data/tells.yml`. **Merging it is the Atlas's consent.** Checking the
signature against `keys/tell.fpr` is manual at every tier, as the Atlas's own
`docs/lifecycle.md` says.

## Recorded, not built

- **The runner.** A pile kept on a thumb drive and synced later. That would let
  us carry, say, directory reports to City Hall and prove that what arrived is
  what left. This is [`TENANCY.md`](TENANCY.md)'s *Runner mode* with a payload.
- **Tags.** Listings will need them.
- **Rendering the directory.** Atlas ships `tells.md` and `directory.html`. The
  `meet` page already wants a curated view of `site/_data/member_sites.json`
  ([`TENANCY.md`](TENANCY.md), *And the listing has a consumer already*).
- **Batteries for members.** Basic tooling for adding member sites may belong in
  the tell engine itself.
- **The data-pile engine.** station-node mounts it at `.data-pile`. It is not
  mounted here.

## Open

| | |
|---|---|
| scope | `fort-collins`, chosen for this PR. The engines' reference Tell and Atlas both say `colorado`. Changing it renames the registration branch, which is cheap until somebody pins |
| `url` | the Tell serves feeds at `piles/<id>/feed/*`. The site's build root is `site/`, so a feed at the root would not be served. Where they go is decided when the first pile registers |
| pile layout | a branch on the member site, or part of its base |
| Tell vs Atlas | which one stockpiles. Atlas, for now |
