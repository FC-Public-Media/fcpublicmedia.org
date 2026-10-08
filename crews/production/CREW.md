# production: the crew, its one service, and the page at its door

**Status, 2026-10-07: built; installed by `fcpm crew install`.** Its menus
(`residency.yml` in `troves/pools`, `troves/kiosk-screen` and here), its order
(`services`), the supervisor (`../crew.py`), its task (`../crew.ps1`), the
episode supervisor (`troves/pools/episodes.py`) and `fcpm crew` are in. It
starts with the computer (Autumn, 2026-10-07: a welcome screen before anyone
signs in is the experiment it makes room for). The door is next.
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
- **The pool task is its desktop half.** A task started with the computer has
  no desktop (Windows keeps session 0 apart), so it cannot put the rolling TV's
  page on a screen. The pool's every-minute task, in the signed-in session,
  runs the crew's `desktop` lines from the same order (`crew.py desktop`). One
  crew, one order, one supervisor program; two tasks only because Windows
  keeps desktops apart.
- **As whom.** This machine's user, with no stored password (S4U): the local
  disks and the Drobo, not network shares or Credential Manager secrets. The
  depot is out of reach from this bay anyway; when it is not, a stored
  credential is the change.

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

## Later: the welcome, and a space of your own (a hook, not a plan)

Autumn, 2026-10-07. Why production starts with the computer, before anyone
signs in. Nothing is built for this, and nobody gains anything from it yet;
it is the hook to think with.

- **The problem.** Everyone at a bay uses the same Windows account and the
  same browser profiles, so being signed out is something you have to
  remember. Staff may get Microsoft 365 sign-in, each in their own space, one
  day. Guests will not have that.
- **The scrappy equivalent.** A welcome before sign-in offers a check-in code,
  like the studio's other QR codes, but for saying who you are. Identifying
  yourself is the grant: from then, on this machine, for this sitting,
  production knows who is here.
- **What it could give.** A space bound to you whether or not you sign in to
  any browser: your page at the door (your nights, your episodes), a browser
  profile that is yours rather than the bay's. Put away when the sitting ends.
- **What Windows allows.** Before sign-in, only the lock screen shows, and no
  program draws on it. A lock-screen picture with a fresh code (the
  machine-wide setting is meant for business editions, and this is Home), a
  welcome account that signs itself in, or the code somewhere else (the
  rolling TV): each is an experiment, not a decision.
- **What it leans on.** The member's pass (`/check-in/`, `docs/identity.md`),
  and a phone that can reach the door: the guest Wi-Fi cannot reach the LAN.

## Open, for Autumn

- **The first workflow** to build the page around. The proposal's guess:
  *I recorded tonight* (find the night, name it for a show, release the
  episode), since every piece of it exists on the timeline already.
- **Whether the pools page moves under the door** (`/pools/`) or keeps its own
  port and window. The proposal: under the door, so there is one address.
