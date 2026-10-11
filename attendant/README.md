# Attendants

An attendant is a seat that can do on a studio page exactly what a person at that page can do, and nothing else. No attendant runs yet; recipes are followed by hand. ("Operator" is the person who runs a node, so it is not this seat's name.)

| seat | works on | a person is | its authority |
|---|---|---|---|
| advocate ([`docs/advocate.md`](../docs/advocate.md)) | background branches, research | not there | its seat's goals, its own branch |
| dev | thaws and grants | with it | the thaw and the grant |
| attendant | known jobs on one page | at the page | the page's own controls; no console, no Remote Control, no worktree |

It finds controls by role and accessible name (button "Files", not a selector), as assistive technology does. A control it cannot find by name is a bug for screen-reader and switch users too, and voice control uses the same lookup.

## Recipes

A recipe is one known job on one page: `page` (module or route), `shown on` (instruments), `before`, `steps` (role and accessible name, each with the visible result that proves it) and `done` (a check a person can make by looking). "It worked" is never a claim about state the person cannot see. Steps run as written under Playwright's `getByRole(role, {name})`.

A step that fails because the page lacks what the recipe says is a bug, listed in [`docs/OPEN.md`](../docs/OPEN.md). A surprise about the environment is a gotcha (`machines/kiosk-1/gotcha`). A stale recipe is fixed in the recipe.

## Pause the wall on a module

**Page:** the wall, built by `machines/kiosk-1/door.py` (`wall_files`, `write_wall`) from `wall:` in `machines/kiosk-1/node.yml`; modules Studio, Files, Classes. **Shown on** roller-tv from `\\10.209.1.1\DIGISTATION\.wall\index.html`.

**Before:** the yellow check-in header; under it, an `aria-hidden` timer; one module on the stage, turning every 45 s; the bar, navigation "Wall": "FCPM" and the module's name, a button per module, one round pause button.

1. Find what is showing: its button has `aria-current="true"` and the frame is named for the module. (Edge's DevTools accessibility tree omits `aria-current`; read the attribute.)
2. Press button "Files": the bar reads "FCPM Files", the frame is named "Files", the address ends `#files`, the timer restarts.
3. Press "Pause": the button is now "Keep paused", a ring counts down from 90 s, the timer turns thick and yellow.
4. Wait a minute: nothing turns or reloads, and the timer stays put.
5. Press "Keep paused": it is now "Play" and stays paused past 90 s; a module button switches module and stays kept. "Play" returns it to "Pause".
6. Press "Pause" and leave it: after 90 s it reads "Pause", and within 45 s the next module comes up with the bar and frame name.
7. Go Back (Alt+Left): the lit button, the bar and the frame still agree.
8. When a class is soon or on (force it with `?at=<ISO time>`): no module buttons, no pause, no timer; the bar reads "FCPM Classes", a heading names the class under "Starting soon" or "Happening now", with the room and time, and in its first 45 minutes "Join until …".

**Done:** the module asked for stays while it is read, the bar names it, and the wall carries on alone. All eight steps pass on roller-tv, from a wall editing bay 1 rendered itself (it cannot reach the depot share).
