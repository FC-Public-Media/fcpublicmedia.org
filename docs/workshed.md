# The workshed

Where a person sits down to work on something: a worktree each, its site built whole and served on its own
port, on this computer. Built: `~/code/workshed`, `fcpm workshed`, the Helm's `/workshed/`, a preview by
jekyll-enough. Not built: the loudspeaker's lines for it, and a shed filled from an origin branch
([Not yet](#not-yet)).

## The place

`~/code/workshed/<shed>/<repo>@<branch>`: a worktree of `~/code/refs/<repo>`, kept for as long as someone works
in it. A shed is a group with a plain name; `dev` is the one used unless another is named. A branch is named
for what it is for, in the words of whoever asked: `meet-photos`, `christmas`, `spring-classes`.

It is not `work/`. `work/` is a session's: one session each, cut from main, never reused. The workshed is a
person's: it lasts, it is reused, and a session that helps there works in the worktree it is shown. Nothing
removes a worktree with changes in it.

| file | |
|---|---|
| `workshed.log` | one line for each thing done: made, given a port, started, stopped, removed. Tail it to follow along |
| `ports.json` | each worktree's port, 4100 and up, given the first time and kept |

What each server says (its builds, its pages) is under `%LOCALAPPDATA%\editing-bay-1\workshed\`.

## Doing it

| | |
|---|---|
| `fcpm workshed` | every worktree: up or stopped, its port, what its branch changes (pages by URL) |
| `fcpm workshed new BRANCH [--shed S] [--repo R]` | a worktree for BRANCH: following `origin/BRANCH` if it is there, else new from `origin/main` |
| `fcpm workshed start NAME` / `stop NAME` | its server, in the background. `serve NAME` keeps it in the window |
| `fcpm workshed check [NAME]` | each thing it needs, a line each, `ok` or `WRONG` with what to do; exits 1 if any is wrong |
| `fcpm workshed log [NAME]` | the workshed's log, or that worktree's server's |
| `fcpm workshed remove NAME` | the worktree goes; its branch stays. Never with changes |

NAME is `<shed>/<repo>@<branch>`, or the shorter `<repo>@<branch>` or `<branch>` when only one worktree has it.

**For an agent preparing a shed**, asked in words like "we want to make the site Christmassy": pick the
branch name from the words, then `fcpm workshed new christmas`, `fcpm workshed start christmas`, and
`fcpm workshed check christmas`. Each step says what it did or what is wrong. Do not build or serve by hand.

## The Helm's page

`/workshed/` on a helm (bay 1: `http://localhost:8080/workshed/`, on the board under Sites). A card per worktree:
its branch, up or stopped, Open, and every page of its site, the ones its branch changes first. Start, Stop and
"Make a worktree for it" are this computer's only, as the board's other switches: a worktree's server answers on
`localhost` and nowhere else, so its pages open here. Elsewhere the page only shows.

## How a site is built

`machines/workshed-serve.mjs` reads the worktree's `site/` (or its top, if `_config.yml` is there) and builds
the **whole** site with [jekyll-enough](https://github.com/FCCN-ANTIBODY/jekyll-enough), in memory, in well
under a second, and again on every save. Never one page alone: the header, the footer and the menus read
`_data` and every page, and a part would leave them wrong. "Per page" is only where you open it.

- A port each, because the site's service worker and passkeys belong to an origin (`localhost:4101` is not
  `localhost:4102`), and because the site's links start at `/`.
- jekyll-enough is found from the code root: `FCPM_JEKYLL_ENOUGH`, then `~/code/origin/FCCN-ANTIBODY/jekyll-enough`
  (once the origin lives at the root), then `~/code/refs/jekyll-enough`. Node is the bay's
  (`machines/production/bay/node-*.yml`). `fcpm workshed check` says which it found.
- A server reads jekyll-enough once, when it starts: after `fcpm pull` brings a new one, stop and start.
- What jekyll-enough cannot do is named, never skipped: the card says "Not built as the real site would be"
  with each gap. Against the live site, page by page (2026-11-16), what is left is cosmetic: headings get no
  `id` (so a `#anchor` link does not scroll), quotes stay straight, `markdown="1"` stays on its tag, list
  items are not on lines of their own, and dates show in UTC (the same moment).
- Nothing here deploys. A worktree's branch is pushed and merged like any other ([site.md](site.md#deploy)).

## Not yet

- **The loudspeaker.** The workshed's log is the stream for now. Its lines belong on the loudspeaker
  (`fcpm hear`), and the loudspeaker runs on digitization only, on Linux.
- **A shed from an origin branch.** The `origin` branch pins every repository by `owner/repo`. A shed per
  origin branch, its worktrees following what moved there, and a loudspeaker line when a pin moves, are the
  next step; worktrees here are not tied to `refs/` beyond being made from it.
- **jekyll-enough from the origin.** It is in `refs/` today, and not yet among the origin's pins.
