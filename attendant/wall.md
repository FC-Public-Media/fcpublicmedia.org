# Hold the wall on a module

    page:     the wall: a check-in header over a stage that turns by itself,
              built by door.py (wall_files, write_wall)
    shown on: roller-tv, from \\10.209.1.1\DIGISTATION\.wall\index.html
    modules:  from the `wall:` block in machines/kiosk-1/node.yml; today
              Studio (page kiosk), Files (page depot), Classes (page classes)

The job: somebody at the rolling TV wants to read one module without it
turning away. With a pointer they press its button and then Hold. An
attendant does it by name. While a class is soon or on, the wall shows that
class instead, and the job is to find what it says.

Status: **followed 2026-09-26 on roller-tv**, by an agent on editing bay 1,
against #138, #140, #142 and #152, last at `0f7a13a`. All steps pass. See
*How it was followed*.

## Before

The wall is open. Across the top is the yellow check-in header: the code
printed straight on the yellow, *Check in* and "Don't Just View It. / Do
It.", and the header's one crooked edge at the bottom. Just under that edge,
on the right, is the timer: a thin red line fills, a red knob takes off to
the right, there is a short breath, and the next module comes up. One module
fills the stage, and it changes by itself every 45 seconds. The timer is
decoration (`aria-hidden`): nothing here is found through it.
Along the bottom is the bar: **FCPM**, a button for each module, and
**Hold**.

## Steps

1. **Find what is showing.** The navigation named **Wall** holds a button per
   module (**Studio**, **Files**, **Classes**) and **Hold**.
   *You see:* that module's button is lit, with `aria-current="true"`, and
   the frame is named for the module: "Studio". Nothing else on the wall
   names it: the lit button is the answer.
   *Over Edge's DevTools protocol:* its accessibility tree does not report
   `aria-current`, so read the attribute. Screen readers get it from the
   platform API; this is a limit of the tool, not of the page.

2. **Press button "Files".**
   *You see:* Files lights, the frame is named "Files" and lists the studio
   drive ("On the studio drive · N partitions"), the address ends in
   `#files`, and the timer starts again.

3. **Press button "Hold".**
   *You see:* the button gets a yellow outline and `aria-pressed="true"`,
   and keeps its name, "Hold". The bar reads "FCPM · held 3:00", and the
   timer turns thicker and yellow.

4. **Stay for a minute.**
   *You see:* Files stays. Nothing turns, nothing reloads, the timer stops
   where it was, and the countdown runs down.

5. **Let go early: press button "Hold" again.**
   *You see:* `aria-pressed="false"`, the outline goes, the bar reads "FCPM"
   again, and the timer is thin and red and moving.

6. **Press "Hold" once more and leave it held.** It lets go by itself after
   three minutes.
   *You see:* `aria-pressed="false"` and no countdown. Within 45 seconds
   the next module comes up; its button lights and the frame's name changes
   with it.

7. **Go Back** (a mouse's Back button, or Alt+Left).
   *You see:* the lit button and the frame still agree.

8. **When a class is soon or on**, the stage shows the class instead of a
   module. The bar's buttons are gone, Hold included, and so is the timer.
   *You see:* a heading with the class's name, and above it "Starting soon"
   or "Happening now". Below it are the room and "Starts …" or "Until …". In
   the class's first 45 minutes there is also a pill, "Join until …", and
   "Check in with the code above."

## Done

The module the person asked for stays up while they read it, the bar says
which one it is, and when they walk away the wall carries on by itself.

## How it was followed

2026-09-26, `door.py` at `a7e2283` (#138), again at `e8d44d1` and `cf4249f`
(#140) after the kiosk session's fixes, at `2a5625f` after #142 (the
one-shape header, the red take-off, Files as a list), and at `0f7a13a` after
#152 (the bar says "FCPM" instead of "Showing …", and the timer is thin, and
yellow while held). (#140's `door.py` is
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
| 1 | passes: nav "Wall", four buttons, frame "Studio"; the timer is `aria-hidden` |
| 2 | passes |
| 3 | passes: still named "Hold"; "FCPM · held 3:00"; the timer gets `held` |
| 4 | passes: no turn in 65 s; the timer did not move in 60 s |
| 5 | passes at `cf4249f` (#140). At `e8d44d1` it failed: the countdown was the button's name |
| 6 | passes at `a7e2283`, `cf4249f` (#140), `2a5625f` and `0f7a13a` (#152): still held at 175 s, released by 191 s, countdown gone, the timer thin and moving again, then turned |
| 7 | passes: pressing modules and turning add no history; Back reloaded the wall, and bar and frame agreed |
| 8 | passes at soon, late and on: no buttons and no timer, and no module frame left in the accessibility tree |

The three bugs the previous wall had (the frame always called "Module", an
unannounced reload every minute, and Back desyncing the rail from the frame)
are gone with #138, and gone from [`BUGS.md`](BUGS.md).

## As a test

    await page.getByRole('button', { name: 'Files' }).click();
    await expect(page.frameLocator('iframe[title="Files"]').locator('body')).toBeVisible();
    await page.getByRole('button', { name: 'Hold' }).click();
    await expect(page.getByRole('button', { name: 'Hold' }))
      .toHaveAttribute('aria-pressed', 'true');

Not in `site/tests/` yet: that suite runs against the built site, and the wall
is door output.
