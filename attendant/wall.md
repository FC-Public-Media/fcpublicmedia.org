# Put a module on the wall

    page:     the wall: the shell and its modules, built by door.py (write_wall)
    shown on: roller-tv, from \\10.209.1.1\DIGISTATION\.wall\index.html
    modules:  from the `wall:` block in machines/kiosk-1/node.yml; today
              Studio (page kiosk) and Files (page depot)

The job: somebody at the rolling TV wants to see the other module. With a
pointer they press its button. An attendant does it by name.

Status: **followed 2026-09-26 on roller-tv**, by an agent on editing bay 1.
Steps 2, 5 and 7 fail; see [`BUGS.md`](BUGS.md). See *How it was followed*
below.

## Before

The wall is open. The frame fills the screen, and a row of buttons runs along
the bottom. One button is lit (signal colour) and the others are dark.

## Steps

1. **Find the rail.** Buttons named **Studio** and **Files**, in that order,
   and nothing else in the row.
   *You see:* the two buttons along the bottom edge. The lit one has
   `aria-current="true"` and the other has `"false"`.
   *Following it over Edge's DevTools protocol:* its accessibility tree does
   not report `aria-current` (it is not one of the properties it exposes), so
   read the attribute. Screen readers get it from the platform API; this is a
   limit of the tool, not of the page.

2. **Check that the frame says what it is showing.** The frame (role
   `iframe`/document) is named for the lit module.
   *You see:* a screen reader or the accessibility tree gives the frame a name
   that includes the lit button's label.

3. **Press button "Files".**
   *You see:* Files lights and Studio goes dark. The frame shows the depot:
   what is on the studio drive. The address ends in `#files`.

4. **Reload the page.**
   *You see:* the same thing as step 3. The wall remembers the module after
   the `#`, and there is no history entry to go Back to.

5. **Stay on it for two minutes.**
   *You see:* the depot page stays where you left it, or tells you before it
   refreshes and lets you stop it.

6. **Press button "Studio".**
   *You see:* Studio lights. The frame shows the welcome screen: the
   check-in code, the Wi-Fi codes and who is on. The address ends in `#studio`.

7. **Go Back** (a mouse's Back button, or Alt+Left).
   *You see:* nothing changes, or whatever changes, the lit button and the
   frame still agree.

## Done

The module the person asked for is in the frame, its button is the only lit
one, and a reload keeps it there.

## How it was followed

2026-09-26, `door.py` at `1384224`. Editing bay 1 cannot reach the depot
share the wall is normally written to, so it rendered the wall itself:
`wall_files()` under a uv-managed Python 3.12 with `pyyaml`, written to
`%LOCALAPPDATA%\editing-bay-1\wall\`, and opened on the roller from
`file://` the way `launch_screen` opens a screen (Edge, `--kiosk`,
fullscreen, a profile of its own), plus a DevTools port on localhost. Each
step found its button with `Accessibility.queryAXTree` by role and name and
checked the result from the frame tree and the DOM. The rail and the frame
are the real ones. The module data is thin: no depot, and no calendars.

| step | result |
|---|---|
| 1 | passes |
| 2 | **fails**: the frame is named `Module` |
| 3 | passes: Files current, `files.html` in the frame, `#files` |
| 4 | passes |
| 5 | **fails**: the frame reloaded at 58 s and 118 s, unannounced |
| 6 | passes |
| 7 | **fails**: after Back the frame shows Studio and the rail still lights Files |

## As a test

    await page.getByRole('button', { name: 'Files' }).click();
    await expect(page.getByRole('button', { name: 'Files' }))
      .toHaveAttribute('aria-current', 'true');
    await expect(page).toHaveURL(/#files$/);

Not in `site/tests/` yet: that suite runs against the built site, and the wall
is not in it. The wall is door output (see *A local copy of each page* in
[`README.md`](README.md)).
