# The workshed

Where a person sits down to work on something: a worktree each, its site built whole and served on its own
port, on this computer. Built: `~/code/workshed`, `fcpm workshed`, the Helm's `/workshed/`, a preview by
jekyll-enough, a shed kept to its origin branches, and searching a shed (the Helm's `/library/`). Not built:
the loudspeaker's lines for it, and a shed that follows a pin ([Not yet](#not-yet)).

## The place

`~/code/workshed/<shed>/<repo>@<branch>`: a worktree of `~/code/refs/<repo>`, kept for as long as someone works
in it; a branch's slash is a `~` in the folder's name (`fcpublicmedia.org@retain~studies`). A shed is a group with a plain name; `dev` is the one used unless another is named. A branch is named
for what it is for, in the words of whoever asked: `meet-photos`, `christmas`, `spring-classes`.

A shed can be anywhere, as a library holding can: any folder of `<repo>@<branch>` worktrees, bound by name in
`machines/<job>/workshed.yml` (`sheds: {work: work}`; a relative folder is from `~/code`). Bay 1 binds `work`
to `~/code/work`, where sessions make theirs (`bin/refs work`), so a session's worktree is started, shown and
searched like any other: `fcpm workshed start meet-says-more`. A bound name wins over a folder of the same name
here. `follow` moves only a worktree following its own branch on the origin; a session's, cut from main and
following it, is left as it is. Nothing removes a worktree with changes in it.

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
| `fcpm workshed search WHERE [WORDS]` | everything in WHERE holding every word, in any order: a shed's name, `branch:REPO@BRANCH` or `every:REPO` ([Search](#search)) |
| `fcpm workshed wheres` | what a search can be kept to |

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
in the shed can see everything else in it, which is the point when cross-referencing.

A search can also be kept to one branch, or every branch, of a repository whose mirror in `refs/` follows the
LAN's origin, read straight from git's objects with no checkout. That is for when you don't know where
something is: a shed only finds what someone checked out. Picking a place is a blinder, so what is not from
there is not sifted at all. Content git already holds once is read once, so every branch of fcpublicmedia.org
(113, about 2,000 distinct files) is as quick as a shed after the first ask. The same file on several branches is
one hit saying how many others hold it; a file that differs between branches is a hit per version.

Most of what is searched is **things**: a folder holding `.scopes` files ([Scopes](#scopes)). The words come
in any order, and a thing is a hit when its lines, together, say every one of them, where words side by side
in the ask are side by side in one line: `park route 14` is a thing with a `park` line and a `route.14` line,
the Venn of two facts. A word matches a whole word, and a number never stands alone when more was asked, so
`park 14` finds no park. Any other text file is a hit when every word is in its path or its text (a word where
a word starts, a number whole); a file named `README.md` stands for its folder. Hits come as a list, things
first, those whose own line opens with the ask (Route 14 for `route 14`) before those that only mention it,
each with the lines that said it. It is kept in memory by the Helm between asks (the city with its layers:
about 1,300 files in a little over 100 ms), so ask as often as you like.

The Helm's `/library/` is the same search for anyone: where to look (the worksheds, then each repository's
branches, `every branch` first), the words, the list. Reading a thing shows every
reader's lines under its file's name, then what it wears; each line is a search of its last two parts
(`route.14` asks `route 14`), and an address goes there. `/library/search?where=&q=`
answers the same as JSON (`where` is `shed:NAME`, `branch:REPO@BRANCH` or `every:REPO`; `fcpm workshed wheres`
lists them). The `library` shed on digitization holds `library` (the city) and
`retain/studies`, and the crew's `shed` line keeps them to origin.local's branches every 5 minutes, fetching every mirror too.

### Scopes

Metadata is flat: a line is a dotted scope, the value a part like any other, and there is no nesting, no `=`,
and no join. `park.lee-martinez-community-park.near.route.14`. A key repeats for each value (`near.route.5`,
`near.route.14`), structure is more dots, and long chains without peers are fine. A literal dot in a part is
`..` (`acres.89..56`); that is the only sequence with a meaning. `machines/scopes.py` reads and writes them.

A folder holding `.scopes` files is a thing, and its lines are all of them together. Each file is one reader's:
a reader writes only its own (`city.scopes`, `districts.scopes`, `osm.scopes`) and never another's, so a reader
can be dropped and read again, and two that disagree both stand, for the weirdness to show. A `WORN.scopes` is
worn by everything below its folder: what the branch, or part of it, is outright (`city.fort-collins`), said
once in the branch itself and never plastered on every thing. The roots are anecdote's top words: `city` for
public documents and the city governing, `land` for what was there before it, `trade` for an organization's
own. The study is `flat-scopes/` on `retain/studies`.

Searching is not reading what a holding says: a shed holds what was put in it to be read. A shed with
grants of its own is a later thought; nothing here hides one shed from another.

## Not yet

- **The loudspeaker.** The workshed's log is the stream for now. Its lines belong on the loudspeaker
  (`fcpm hear`), and the loudspeaker runs on digitization only, on Linux.
- **A shed that follows a pin.** `fcpm workshed follow` keeps a worktree to its origin branch. One made at an
  origin's pin, from what `fcpm places` lists ([consoles.md](consoles.md#places)), is not moved when the pin
  moves, and no console says so.
- **jekyll-enough from the origin.** It is in `refs/` today, and not yet among the origin's pins.
