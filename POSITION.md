# Vendors — position

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
