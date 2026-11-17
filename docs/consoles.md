# Consoles and places

What a helm holds up to be read: consoles, a screen each, and places, an origin branch's repositories as a
listing. Built: `fcpm consoles`, `fcpm places`, the helm's `/consoles` and `/places`, production's beat. Not built:
a console for who is connected, and a golem asking for any of it ([Not yet](#not-yet)).

## A console

A console is one screen of plain text, 80 by 24, that something keeps written so that nobody has to go and look.
It is for reading, never for typing into. The same thing is always on the same line, so a console that looks
different is different, and that is the signal. It is never a log that grows: what does not fit is counted on its
last line, and a log stays a log.

- **Its first line** says what it is, where, when it was written and until when it is fresh.
- **Written whole, replaced by rename.** A reader gets the whole page, the old one or the new one, never half,
  and never waits on the script that writes it. No lock to get stuck.
- **Each on its own beat**, in its own thread, so a slow one never holds another up. A composer that fails writes
  a page saying so.
- **Reading never writes**, unless the page is missing or three beats stale (no helm keeping it), and then once.

It is Fighter's idea of a console ([intuition](https://github.com/DiscoveryWritten/editor-notes/blob/main/notes/intuition.md),
[the console](https://github.com/DiscoveryWritten/editor-notes/blob/main/notes/the-console.md)), held up by a
helm: `~/code/consoles/CONSOLES` is the list Fighter's console tabs read, `name<TAB>path<TAB>helm`.

| console | beat | says |
|---|---|---|
| `helm` | 10 s | the jobs this machine wears, whether its door answers, the revision, the wizards only it applies, and each peer helm in `helms.yml`: answering, not answering, or no address yet |
| `workshed` | 5 s | whether sites can be built here, and each worktree: its port or stopped, its changed pages, and how far it is from main ([workshed.md](workshed.md)) |
| `library` | 60 s | the library's own console: who is at work, jobs, the hour's grants, the inbox, the x-rays ([library.md](library.md#the-console)) |
| `constitution` | 300 s | each job's `machines/<job>/CONSTITUTION.md` with its history, or that it has none yet. A blank constitution is not good metadata, so its absence is shown, not left off |

**Keeping the beat** is the helm's: `consoles` in its `FCPM_DOOR_WATCH` (production's, in `production.yml`). A
session starts no service, so `fcpm consoles beat` is only for trying it.

## Places

`fcpm places [BRANCH]` lists the repositories an origin branch pins, in the format Fighter's location providers
print (`@modes`, `# owner`, then `name<TAB>path<TAB>detail`). An origin branch is known by its shape: every folder
holds only submodules at `<owner>/<repo>`, and files are only at the top. `origin` is the first. It reads the
branch as `fcpm pull` last fetched it and asks nothing of the network.

Each repository's place is, in order:

1. **Its worktree** in the shed named for the branch (`~/code/workshed/origin/...`).
2. **Its mirror** in `refs/`, read only. The detail says so, and says if the pin is not fetched there.
3. **Nothing: offered.** It is pinned but not mirrored here (`refs.wanted`, then `fcpm pull`).

A worktree at the pin is asked for in words the listing gives:
`fcpm workshed new BRANCH --shed origin --repo <owner>/<repo> --from <pin>`. It is a grant in the library's book,
spent once the worktree exists, and serving it is a grant its server holds until it stops ([workshed.md](workshed.md)).
For Fighter, a provider is one line: `ssh <bay> fcpm places`, or the helm's `/places`.

## The helm's addresses

Plain text, for reading: a table of contents, not an API.

| | |
|---|---|
| `/consoles` | the list, with this helm's addresses where the paths are |
| `/consoles/<name>` | one console, as last written |
| `/places`, `/places/<branch>` | the listing |

The board lists both under Consoles.

## Not yet

- **Who is connected:** a console of live sessions once anything can arrive (an SSH tether, a golem).
- **A golem asking.** By [helm.md](https://github.com/DiscoveryWritten/editor-notes/blob/main/notes/helm.md), a golem
  arrives by a reply only the bay's own helm holds, and the bay starts it because its job orders a `golem` line;
  the SSH session is only the tether. Neither is built.
- **The constitution itself.** No job has one yet.
- **A console that knows who reads it**, so a reader that stops goes dark.
