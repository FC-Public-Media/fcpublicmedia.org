# origin

A branch of FCPM's library, never merged into `main`: the origin. Every repository FCPM keeps, as a
submodule in a folder named for its owner and repository (`FC-Public-Media/pools`,
`FCCN-ANTIBODY/tell.anecdote.channel`), so two projects with one name never collide. Each is pinned at
its `main` on the LAN's origin (origin.local) when this branch last moved.

The URLs are relative (`../../<owner>/<repo>`), so a submodule comes from wherever this branch was
cloned: from origin.local, everything comes from origin.local, LAN-born repositories included
(`brand`, `broadcast`); from GitHub, everything GitHub has.

    git clone -b origin fcpm-origin:/srv/origin/FC-Public-Media/fcpublicmedia.org origin
    git -C origin submodule update --init FC-Public-Media/pools

A repository joins by a commit here; a pin moves the same way. See `docs/library.md` on `main`.
