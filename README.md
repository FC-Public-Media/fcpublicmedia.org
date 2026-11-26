# refs

A branch of FCPM's library, never merged into `main`: the references a machine keeps beside its work, the
same list for every machine. Each is a submodule in a folder named for its owner and repository, pinned at
its `main` on the LAN's origin (origin.local) when this branch last moved. The URLs are relative
(`../../<owner>/<repo>`), so each comes from wherever this branch was cloned.

    git clone -b refs fcpm-origin:/srv/origin/FC-Public-Media/fcpublicmedia.org refs
    git -C refs submodule update --init FC-Public-Media/pools

A reference joins by a commit here; a pin moves the same way.
