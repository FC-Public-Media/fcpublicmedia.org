# FCPM editing bay 2: the project

Editing bay 2, `BAY2` to Windows (11 Home, user `fcpme`), is bay 1's twin and works as bay 1 does:

@../../production/code/AGENTS.md

What is bay 2's own:

- Bay 1's machine is not here: `BAY1`, `fcpub`, its drives, the rolling TV, its OBS, its workshed.
- The pool's task is `editing-bay-2 pool`; its log `%LOCALAPPDATA%\editing-bay-2\pool.log`.
- The crew is `editing-bay-2`: `follow` brings this checkout to the origin's main every 5 minutes.
- No address on Helm (10.209.1.0/24) yet.

## Orientation: Bay 2 (user "fcpme", device "BAY2")

`C:\Users\fcpme\code` is our root.
`C:\Users\fcpme\code\fcpublicmedia.org` is what this bay runs, from the origin's main; sessions start there.
`refs\` is a cold shed: references, for worktree sources, or study (the library's `refs` branch lists them).
`work\` is worktrees and standalone clones.
