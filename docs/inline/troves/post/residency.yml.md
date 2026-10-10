# `troves/post/residency.yml`

Moved out of the file. Unreviewed.

## 1

Above `resident: post`

residency.yml -- what the post trove offers a crew that holds it.

A MENU, NOT A STARTUP SCRIPT. Nothing here runs because it is written down;
a crew orders from it (crews/<crew>/services). {python} is the
crew's Python (uv, 3.12, with pyyaml); paths are from the repository's root.

The seam: admission is the only way in. Whoever releases a take (the pools
page for production; capture's ledger for digitization) writes a release and
admits it; post doesn't care who. The steps a machine does are its crew's
(crews/<crew>/post.yml); where the partition is, the hardware's
(machines/<profile>/post.yml).
