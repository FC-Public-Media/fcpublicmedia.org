# The FCPM library

**This branch is the library. It is not a version of the website.**

`main` holds the site. This holds what FCPM keeps — and it is a branch rather
than a folder on `main` on purpose, so that pins, holdings and correspondence
move in a place nobody pulls in order to get something else.

    git fetch origin library
    git checkout library

## The categories are advertisements

Three folders, all empty. That is deliberate and it is the point: an empty
`trade/` says *this library does this, and currently puts nothing forward under
it*, which is a different statement from the folder being absent.

| | |
|---|---|
| `library/trade/` | **member sites.** Each is its own repository, pinned here as a submodule — see `docs/TENANCY.md` on `main` |
| `library/city/` | what is true about Fort Collins that somebody else would have to re-derive |
| `library/voices/` | the community's own, kept so it outlives whoever published it |

Those three are reserved words in the library engine's vocabulary, and they are
the three FCPM said it would hold. `media` and `library` are reserved too and
are not claimed here.

## Why there is a site directory on a branch that is not a site

Because Cloudflare builds **every** branch. The non-production branch deploy
command is set, so a branch with nothing to build does not sit quietly — it goes
red, and stays red, and teaches everyone to ignore a red light.

So this branch carries the smallest thing that builds: a config, a Gemfile, a
Ruby pin, and one page. The build is green in a couple of seconds and the
preview URL shows a page that says what this branch is.

**This is worth knowing upstream.** `library.anecdote.channel` has a petition
proposing a one-line `PLACE` file so a build can exit 0 and print what it
skipped. `PLACE` is here, and on this host **it is not sufficient on its own** —
the build command lives in a dashboard and does not consult it. A place-branch on
a host that builds every branch has to be buildable, or the host has to be told
which branches to skip. That is a second requirement the petition does not name.

## Nothing is mounted

No `.advocate-engine`, no submodules. The engines run on `main`.
