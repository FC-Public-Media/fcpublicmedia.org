# Put a module on the wall

    page:     the wall: the shell and its modules, built by door.py (write_wall)
    shown on: roller-tv, from \\10.209.1.1\DIGISTATION\.wall\index.html
    modules:  from the `wall:` block in machines/kiosk-1/node.yml; today
              Studio (page kiosk) and Files (page depot)

The job: somebody at the rolling TV wants to see the other module. With a
pointer they press its button. An attendant does it by name.

Status: written 2026-09-26 against `door.py` on `main`. **Not yet followed on
the wall.** Steps 2 and 5 are expected to fail; see [`BUGS.md`](BUGS.md).

## Before

The wall is open. The frame fills the screen, and a row of buttons runs along
the bottom. One button is lit (signal colour) and the others are dark.

## Steps

1. **Find the rail.** Buttons named **Studio** and **Files**, in that order,
   and nothing else in the row.
   *You see:* the two buttons along the bottom edge. The lit one has
   `aria-current="true"` and the other has `"false"`.

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

## Done

The module the person asked for is in the frame, its button is the only lit
one, and a reload keeps it there.

## As a test

    await page.getByRole('button', { name: 'Files' }).click();
    await expect(page.getByRole('button', { name: 'Files' }))
      .toHaveAttribute('aria-current', 'true');
    await expect(page).toHaveURL(/#files$/);

Not in `site/tests/` yet: that suite runs against the built site, and the wall
is not in it. The wall is door output (see *A local copy of each page* in
[`README.md`](README.md)).
