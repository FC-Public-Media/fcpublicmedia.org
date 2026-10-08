# production: the crew, its one service, and the page at its door

**Status, 2026-10-07: the supervisor is built, not installed.** Its menus
(`residency.yml` in `troves/pools`, `troves/kiosk-screen` and here), its order
(`services`), the supervisor (`../crew.py`), the episode supervisor
(`troves/pools/episodes.py`) and `fcpm crew` are in. Nothing runs it yet: the
install (the task, and whether it starts with the machine or at sign-in) and
the door are next, each its own change.
Production is a crew (`../README.md`): the recordings after they land, and
the door where members meet them. Editing bay 1 (`EDIT2`) is the first to put
it on. Like station-node's one service on its Mac: one supervisor, installed
and always ready, running what the residencies offer and what production has
ordered from them. Its face is a page on the studio's LAN, built as a
member's way in, not as a console.

## The contract

What any machine wearing production owes, so a peer can step in beside it:

- **It looks after** the pools, their transcription, the episodes and their
  release, and the door.
- **It serves** the lines in `services` below, each from a residency's menu,
  each where its contract says (the door on 8080, the pools under it).
- **It stays in the building.** LAN only, nothing to Cloudflare, no grants to
  anyone outside. `fcpm` tends it.
- **It says what is true.** Status is asked live; nothing it shows was written
  down at start.

## What Autumn asked for

- **One service, never one per thing.** Station-node went to twenty launchd
  jobs and back to one ("One runnable service. One."). Here too: a single
  supervisor, and everything else is a line it runs.
- **Installed and ready, not startup clutter.** It is up before anyone signs
  in, takes no time at anyone's logon, puts nothing in the Startup apps list,
  and opens no window. People sit down to this machine every week; they
  should not see it.
- **The door is always up and visible**, even when it is backed by nothing
  running yet, or by a show that is not there.
- **No grants.** Everything it serves stays here. Nobody outside needs
  permission for anything; `fcpm` (the watcher) is enough to tend it.
- **Not station-node's design sense.** Their board is a technical record of
  everything. This page is a member onboarding experience: the intranet,
  LAN only, showing what is on the local disk. Like a terminal, like a kiosk:
  simple workflows over sophisticated things.

## What it borrows from station-node, and what it leaves

| borrowed | left behind |
|---|---|
| one supervisor that runs lines, `keep` or `every N` | twenty jobs, and two dispatchers that could run the same seats twice |
| residencies: a repository's `residency.yml` says what it **wants** (storage) and what it **serves** (a menu) | signed holder apps for OS grants (a macOS problem; Windows needs none for loopback and LAN) |
| the menu is not a startup script: declaring starts nothing; ordering does | a `status.json` written at start, which after a crash "is a lie told confidently" |
| status asked live: is the process there, does the port answer | a board that shows every internal at once |
| "it is not a web server and must not become one" | the console as the front page |

## The service

- **One scheduled task, named for the crew ("production")**, triggered **at startup**, run whether
  anyone is signed in or not, hidden, with no window. A startup task is not a
  logon item: it is not in Startup apps and costs nobody's sign-in. It also
  answers kiosk's gotcha that a power cut leaves its door down until someone
  logs on. Installed by `fcpm install` (elevated, hers alone, like every
  install).
- **It runs one supervisor** (`bin/production`, Python from the bay's own
  venv, never PATH: the lesson of station-node's launchd PATH and kiosk's
  firewall prompting per interpreter). Its children get no console (the pool's
  headless-console lesson, `pool-server-no-console`): output goes to files
  under `%LOCALAPPDATA%\editing-bay-1\`.
- **The pool task folds into it.** Today's per-minute pool (the Remote Control
  server, held off; the roller screen) become two of its lines. One task, not two.

## What it runs: residencies, then the order

1. **The menu.** Every residency it holds: `troves/*/residency.yml` in this
   repository, and the mounted repositories' own (`enhance` has one; it wants
   storage and serves nothing yet). Each `serves:` entry says what it is for,
   its kind (`listener`, `periodic`), how it starts, and what stops working
   without it.
2. **The order.** `services`, beside this file: one line per item production orders
   from the menu, in station-node's shape (`name when command`), and nothing
   that is not on a menu. Editing it is how a line starts or stops; the
   supervisor follows within seconds. There is no `enabled:` anywhere else to
   disagree with it.

First lines it would carry:

| line | from | kind | what it is |
|---|---|---|---|
| `door` | this crew | keep | the page below, on the LAN |
| `pools` | `troves/pools` | keep | the timeline, served without its window having to be open; the door links to it |
| `episodes` | `troves/pools` | every 5m | the supervisor of released episodes: runs each one's show pipeline (whisper now; Audition's steps once its panel proves out). Held episodes are left alone |
| `screen` | `troves/kiosk-screen` | every 1m | the roller TV's page, as the pool keeps it today |
| `remote-control` | this crew | keep, off | the root's Remote Control server, held off as Autumn set it (2026-10-07) |

## The door: the page at production

**Served on the studio LAN only**, on port 8080 like station-node's, from the
local disk. Never sent to Cloudflare, never public. It refuses anything that
does not come from the LAN, and its address is the one thing a person needs.
(The bay's network category is Public on purpose; letting the LAN in takes
one inbound firewall rule for this port, scoped to the local subnet. That is
part of the elevated install, and Autumn's to decide.)

It is built for someone who walked into the studio, not for us:

- **It starts with the person, not the machine.** "I recorded tonight." "I want
  my recordings." "I am here for a show." Each is a short path through what is
  sophisticated underneath (the pools, transcription, the show's pipeline,
  release), in as few steps and words as the timeline taught us: glyphs,
  colour and state, words in tooltips.
- **It is always up and always says something true.** When a show is there,
  it shows that show's nights and episodes, held and released. When nothing
  is running, it says so plainly, and what would bring it back. Its state is
  asked live every time, never read from a file written earlier.
- **The machinery is one level down.** The lines, their logs, what each
  residency offers: there, for whoever tends it, behind the member's view and
  never in front of it.
- **Kiosk-like.** It works the same on the roller TV, a phone or laptop on the
  studio LAN, and the desk.

## Open, for Autumn

- **The first workflow** to build the page around. The proposal's guess:
  *I recorded tonight* (find the night, name it for a show, release the
  episode), since every piece of it exists on the timeline already.
- **Which account it runs as** at startup with nobody signed in: this user
  with a stored credential (it can then reach the depot's shares), or without
  one (local disk and the Drobo only).
- **Whether the pools page moves under the door** (`/pools/`) or keeps its own
  port and window. The proposal: under the door, so there is one address.
