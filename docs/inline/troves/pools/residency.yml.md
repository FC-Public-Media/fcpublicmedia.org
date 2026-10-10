# `troves/pools/residency.yml`

Moved out of the file. Unreviewed.

## 1

Above `resident: pools`

residency.yml -- what the pools trove offers a crew that holds it.

A MENU, NOT A STARTUP SCRIPT (station-node's rule, kept). Nothing here runs
because it is written down; a crew orders from it (crews/<crew>/
services) and its supervisor runs what was ordered. Status is asked live:
`alive:` says how (a port that answers, a process that is there).

{python} is the crew's Python (uv, 3.12, with pyyaml), and paths are from
the repository's root.
