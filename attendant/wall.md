# Pause the wall on a module

    page:     the wall: a check-in header over a stage that turns by itself,
              built by door.py (wall_files, write_wall)
    shown on: roller-tv, from \\10.209.1.1\DIGISTATION\.wall\index.html
    modules:  from the `wall:` block in machines/kiosk-1/node.yml; today
              Studio (page kiosk), Files (page depot), Classes (page classes)

The job: somebody at the rolling TV wants to read one module without it
turning away. With a pointer they press its button and then Pause. An
attendant does it by name. While a class is soon or on, the wall shows that
class instead, and the job is to find what it says.

Status: **followed 2026-09-26 on roller-tv**, by an agent on editing bay 1,
against #138, #140, #142 and #152, last at `8cb5e66`. All steps pass. See
*How it was followed*.

## Before

The wall is open. Across the top is the yellow check-in header: the code
printed straight on the yellow, *Check in* and "Don't Just View It. / Do
It.", and the header's one crooked edge at the bottom. Just under that edge,
on the right, is the timer: a thin red line fills, a red knob takes off to
the right, there is a short breath, and the next module comes up. One module
fills the stage, and it changes by itself every 45 seconds. The timer is
decoration (`aria-hidden`): nothing here is found through it.
Along the bottom is the bar: **FCPM** and the module's name, a button for
each module, and one round button that pauses. It has no text, and a
name for each of its three states: **Pause** (a pause glyph), **Keep
paused** (a ring counting down 90 seconds) and **Play** (a full ring and a
play glyph).

## Steps

1. **Find what is showing.** The navigation named **Wall** holds a button per
   module (**Studio**, **Files**, **Classes**) and **Pause**.
   *You see:* "FCPM Studio" (or whichever is up). That module's button is
   lit, with `aria-current="true"`, and the frame is named for the module:
   "Studio".
   *Over Edge's DevTools protocol:* its accessibility tree does not report
   `aria-current`, so read the attribute. Screen readers get it from the
   platform API; this is a limit of the tool, not of the page.

2. **Press button "Files".**
   *You see:* Files lights, the bar reads "FCPM Files", the frame is named
   "Files" and lists the studio drive ("On the studio drive · N
   partitions"), the address ends in `#files`, and the timer starts again.

3. **Press button "Pause".**
   *You see:* the button is now named **Keep paused**. A ring drains around
   it with the seconds left, from 90, and the timer turns thicker and yellow.

4. **Stay for a minute.**
   *You see:* Files stays. Nothing turns, nothing reloads, the timer stops
   where it was, and the seconds count down.

5. **Keep it: press button "Keep paused".**
   *You see:* the button is now named **Play**: a full ring and a play
   glyph. It stays paused past the 90 seconds, for as long as it is left.
   Pressing a module button while it is kept switches the module and stays
   kept. **Press "Play"** and it is **Pause** again, and the timer is thin,
   red and moving.

6. **Press "Pause" and leave it.** It lets go by itself after a minute and
   a half.
   *You see:* the button is named **Pause** again, and the ring is gone.
   Within 45 seconds the next module comes up; its button lights, and the
   bar and the frame's name change with it.

7. **Go Back** (a mouse's Back button, or Alt+Left).
   *You see:* the lit button, the bar and the frame still agree.

8. **When a class is soon or on**, the stage shows the class instead of a
   module. The bar's buttons are gone, the pause button included, and so
   is the timer.
   *You see:* the bar reads "FCPM Classes", and a heading has the class's
   name, with "Starting soon" or "Happening now" above it. Below it are the
   room and "Starts …" or "Until …". In the class's first 45 minutes there
   is also a pill, "Join until …", and "Check in with the code above."

## Done

The module the person asked for stays up while they read it, the bar says
which one it is, and when they walk away the wall carries on by itself.

## How it was followed

2026-09-26, `door.py` at `a7e2283` (#138), again at `e8d44d1` and `cf4249f`
(#140) after the kiosk session's fixes, at `2a5625f` after #142 (the
one-shape header, the red take-off, Files as a list), at `0f7a13a` during
#152, and at `8cb5e66` at the end of it (the bar reads "FCPM" and the module,
Hold became one button with three named states, Pause, Keep paused and
Play, and the timer is thin, and yellow while paused). The kiosk session's
later change to the ten-minute reload (`4f5f608`, landing it at the end of a
turn) came after #152 merged and was not followed: no step waits ten
minutes. (#140's `door.py` is
the one followed, as `3e1fc2e`, before it was re-landed.) Editing bay 1
cannot reach the depot share, so it rendered the wall itself: `wall_files()` under a
uv-managed Python 3.12 with `pyyaml`, with `classes: sample` forced on for the
render only, written to `%LOCALAPPDATA%\editing-bay-1\wall\`, and opened on
the roller from `file://` the way `launch_screen` opens a screen (Edge,
`--kiosk`, fullscreen, a profile of its own), plus a DevTools port on
localhost. Each step found its control with `Accessibility.queryAXTree` by
role and name, and checked the result against the accessibility tree, the
frame tree and the DOM. Files is empty because the render has no depot.
At `2a5625f` the frame's opacity was sampled every 2.5 s through a turn: 1 the
whole time, and fully bright on the Vizio. The dimness the kiosk session saw
was its headless screenshots, not the page.

Step 8 used the page's own `?at=`: `index.html?at=2026-09-27T17:00:00-06:00`
(soon), `T18:10` (late: the join pill) and `T19:00` (on). The sample classes
are dated from the day of the render, so pick an `at` from the Classes
module's first entry.

| step | result |
|---|---|
| 1 | passes: nav "Wall", buttons Studio, Files, Classes, Pause; frame "Studio"; the timer is `aria-hidden` |
| 2 | passes: "FCPM Files" |
| 3 | passes: renamed "Keep paused"; the ring reads 90; the timer gets `held` |
| 4 | passes: no turn in 60 s; the timer did not move; 30 s left |
| 5 | passes: renamed "Play"; still kept at 101 s; pressing Classes switched and stayed kept; "Play" returned to "Pause" |
| 6 | passes: "Keep paused" with 7 s left at 85 s, "Pause" by 91 s, then turned to Files |
| 7 | passes: pressing modules and the pause button adds no history; after Back the bar, the lit button and the frame agreed |
| 8 | passes at soon, late and on: "FCPM Classes", no buttons and no timer, no module frame left in the accessibility tree |

The three bugs the previous wall had (the frame always called "Module", an
unannounced reload every minute, and Back desyncing the rail from the frame)
are gone with #138, and gone from [`BUGS.md`](BUGS.md).

## As a test

    await page.getByRole('button', { name: 'Files' }).click();
    await expect(page.frameLocator('iframe[title="Files"]').locator('body')).toBeVisible();
    await page.getByRole('button', { name: 'Pause' }).click();
    await page.getByRole('button', { name: 'Keep paused' }).click();
    await expect(page.getByRole('button', { name: 'Play' })).toBeVisible();
    await page.getByRole('button', { name: 'Play' }).click();
    await expect(page.getByRole('button', { name: 'Pause' })).toBeVisible();

Not in `site/tests/` yet: that suite runs against the built site, and the wall
is door output.
