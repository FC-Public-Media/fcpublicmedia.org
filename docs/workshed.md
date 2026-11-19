# The workshed

Where a person sits down to work on something: a worktree each, its site built whole and served on its own
port, on this computer. Built: `~/code/workshed`, `fcpm workshed`, the Helm's `/workshed/`, a preview by
jekyll-enough, a shed kept to its origin branches, and searching a shed (the Helm's `/library/`). Not built:
the loudspeaker's lines for it, and a shed that follows a pin ([Not yet](#not-yet)).

## The place

`~/code/workshed/<shed>/<repo>@<branch>`: a worktree of `~/code/refs/<repo>`, kept for as long as someone works
in it; a branch's slash is a `~` in the folder's name (`fcpublicmedia.org@retain~studies`). A shed is a group with a plain name; `dev` is the one used unless another is named. A branch is named
for what it is for, in the words of whoever asked: `meet-photos`, `christmas`, `spring-classes`.

It is not `work/`. `work/` is a session's: one session each, cut from main, never reused. The workshed is a
person's: it lasts, it is reused, and a session that helps there works in the worktree it is shown. Nothing
removes a worktree with changes in it.

| file | |
|---|---|
| `workshed.log` | one line for each thing done: made, given a port, started, stopped, removed. Tail it to follow along |
| `ports.json` | each worktree's port, 4100 and up, given the first time and kept |

What each server says (its builds, its pages) is under `%LOCALAPPDATA%\editing-bay-1\workshed\`.

Where the machine has a library, the workshed writes in its grant book ([library.md](library.md#the-grant-book)),
seat `workshed`: a worktree made is a grant spent at once, and a served one is a grant its server's own process
holds, released on stop or lapsed when the process ends. The `library` and `workshed` consoles show both
([consoles.md](consoles.md)). No library is made to hold one.

## Doing it

| | |
|---|---|
| `fcpm workshed` | every worktree: up or stopped, its port, what its branch changes (pages by URL) |
| `fcpm workshed new BRANCH [--shed S] [--repo R] [--from REV]` | a worktree for BRANCH: following `origin/BRANCH` if it is there, else new from `origin/main`, or from REV (an origin's pin). R may be `<owner>/<repo>`, as `fcpm places` lists it |
| `fcpm workshed start NAME` / `stop NAME` | its server, in the background. `serve NAME` keeps it in the window |
| `fcpm workshed check [NAME]` | each thing it needs, a line each, `ok` or `WRONG` with what to do; exits 1 if any is wrong |
| `fcpm workshed log [NAME]` | the workshed's log, or that worktree's server's |
| `fcpm workshed remove NAME` | the worktree goes; its branch stays. Never with changes |
| `fcpm workshed follow [SHED]` | each clean worktree brought up to its origin branch, fast-forward only; one with changes is left as it is |
| `fcpm workshed search SHED [WORDS]` | everything in SHED's worktrees holding every word, in any order ([Search](#search)) |

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

## Search

A shed is searchable as it stands. Whatever worktrees are in it are what a search reads, every text file in
them (Markdown, YAML, JSON, TSV, CSV, text; nothing over half a megabyte), where it is: no index to keep, no
list of what counts. Putting a worktree in a shed is how something becomes searchable, and someone working
in the shed can see everything else in it, which is the point when cross-referencing. You pick a shed, not a
branch; a shed is a short list, the branches are too many.

The words come in any order, and a file is a hit when every one of them is in its path or its text: a word
where a word starts (`park` finds parks), a number whole (`14` is not `1478`), a quoted phrase as written. A
fact leads to the next: `route 14 park` gives Route 14 and every park near it. A file named `README.md` or
`facts.yml` stands for its folder. Hits come as a list, those whose name holds the words first, each with
the lines that matched, a list's item with its key (`routes near: Route 14`). It is fast because it is
small and kept in memory by the Helm between asks (the library shed: about 600 files in under 100 ms), so ask
as often as you like.

The Helm's `/library/` is the same search for anyone: a shed, the words, the list. Reading a hit shows the
file with every fact a search of its own words and every address a link out. `/library/search?shed=&q=`
answers the same as JSON. The `library` shed on digitization holds `library` (the city) and
`retain/studies`, and the crew's `shed` line keeps them to origin.local's branches every 5 minutes.

Searching is not reading what a holding says: a shed holds what was put in it to be read. A shed with
grants of its own is a later thought; nothing here hides one shed from another.

## Not yet

- **The loudspeaker.** The workshed's log is the stream for now. Its lines belong on the loudspeaker
  (`fcpm hear`), and the loudspeaker runs on digitization only, on Linux.
- **A shed that follows a pin.** `fcpm workshed follow` keeps a worktree to its origin branch. One made at an
  origin's pin, from what `fcpm places` lists ([consoles.md](consoles.md#places)), is not moved when the pin
  moves, and no console says so.
- **jekyll-enough from the origin.** It is in `refs/` today, and not yet among the origin's pins.
