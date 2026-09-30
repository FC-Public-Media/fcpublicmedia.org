# Truthfulness — position

**As of 2026-09-30.** Range `e63fc7b..919a413`: 51 first-parent commits,
2026-09-09 → 2026-09-24. Almost all of it is structure (member sites, the
factory build, machine profiles, the node, deploy, DNS) and is not mine.

I speak for the member who reads the site, believes it, and turns up.

## The one sentence

**Nothing I reported on 2026-09-10 has been fixed, and the site is being
readied to become the public one.**

The range touched none of the four files I watch — I read their current state
rather than the diff, and each is as I left it (see the table). What changed
is the stakes: `docs/OPEN.md` records that the DNS switch from Wix was aimed
at the weekend after 2026-09-24. **I cannot tell from this checkout whether
that has happened** — measured on 2026-09-24 the public host was still Wix.
If it has, every finding below is now what a member reads; if not, it is what
they will read the day it does.

## Goals

| | says | today |
| --- | --- | --- |
| **G1** | No page asserts a date, a price or an availability that is out of date. | **Not met, and older.** Both classes in `_data/classes.yml` are past — 50 and 35 days (Aug 11, Aug 26). `governance.yml` still says meetings are open with `schedule: ""`. `reserve.md` still asks a member to agree to Equipment Terms and Conditions that do not exist (`CONTENT-TODO.md` still marks it BLOCKING). The "a class is on" surfaces render empty. `OPEN.md` names the class finding as *still unverified*; it is verified, and true. |
| **G2** | Every internal link resolves, including anchors, and `REDIRECTS.md` reports nothing unaccounted for. | **Redirect half: unchanged, one address** — `/equipment`, `REDIRECTS.md:103`. **And newly qualified:** `OPEN.md` states `REDIRECTS.md` records where addresses *will* go, not where they go now, and that the one automated publish check skips `_redirects`. So the report can read clean while every legacy link is dead. **Link-and-anchor half: `unmeasured`** — still no link walk anywhere. |

## What moved that my constituency would notice

Two things, both from the maintainers' own candour in `docs/OPEN.md`, not
from a content change:

- **The check-in promise is untrue on a shared browser.** `/check-in/` and the
  kiosk say *"your visits stay on your phone."* OPEN.md records that on any
  machine more than one person uses, the form prefills the previous visitor's
  name and email. The kiosk sidesteps it (QR only); a staffer helping someone
  at the desk machine does not. New draft T8.
- **The redirect check has a blind spot with a date on it** — folded into T5,
  not a new complaint.

## What would make us stop

Unchanged: a member acts on a promise this site made — a meeting, a class, a
form to agree to, a privacy assurance — and it was not true when they read
it. They do not file a bug; they conclude something about FC Public Media.

## Next session

Monthly, due 2026-10-28. First thing: whether the cutover happened, which
decides whether "will read" becomes "reads". Then the same four files.
