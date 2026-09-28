# Screens at rest: one dim mode for every studio screen

Status: **a plan, 2026-09-27.** Nothing is built. Autumn's brief, drafted on
editing bay 1 (which holds the pen) with the media node's session (`kiosk`),
which answered for the door and for kiosk-1's panels.

## What Autumn asked for

> Every page we put up on a screen runs the exact same screensaver: fall to
> dim. Any orientation. The little animated view the kiosk made, the three
> squares where the lit one changes over time, is the screensaver, so that
> it becomes canonical. At idle the page draws really dark, something like
> 10% over pure black; normally the page body is as it is.
>
> Not an aggressive idle timer to fight. Idle is scheduled: there are times a
> screen is allowed to be idle and times it is not. By default a screen is
> awake while a host is on, and for an hour before, and it can drop out of
> alert as soon as the host time ends. All the screens can follow that for
> now. We iterate from there.
>
> Nobody switches monitors off. The welcome kiosk is useful because it is on.
> The roller TV can be turned off. A monitor that is attached but off is not
> an emergency.

(Paraphrased from speech, 2026-09-27. Her words win where this differs.)

## The shape

The same three parties as a class on now (`KIOSK.md`, *The class on now*),
for the same reason: the schedule is known days ahead, and every screen
already has a clock.

| | owes | never |
|---|---|---|
| **the door** (`door.py`) | the **awake windows** for the next week | a verdict on whether a screen is awake now |
| **`dim.js`**, one file | the verdict, from the page's own clock, and the dim | a timer that fights the person at the screen |
| **the page** | nothing, since `page()` includes it. It may *hold* the screen awake | its own rule for "awake" |

### One copy: `brand/idle/dim.js` and `dim.css`

- The three squares come **out of** `brand/idle/index.html` into these files.
  The idle screen then uses them too, so there is one mark.
- **`page()` in `door.py` inlines both, once.** Every door page goes through
  `page()`: the kiosk panels, the depot, the wall shell and its modules, and
  class mode. So every screen gets the same dim, and nobody has to remember to
  include it.
- **Inline, not `<script src>`**, because the wall is copied onto the depot's
  share and read over `file://`.
- **The roller** gets it without a change: bay 1's local render
  (`troves/kiosk-screen/render.py`) calls `wall_files()`, which goes through
  `page()`.

### Awake windows

- **Sources:**
  - rota shifts (`kiosk/rota.yml`, the same source `on_now()` reads);
  - bookings (`bookings:` in `node.yml`; only `sample` today);
  - class sessions (a class `soon`, `late` or `now` by `pickSession`).
- **Rule:** each one from **60 minutes before its start to its end**, merged
  where they overlap. No grace period after the end. The door computes
  them for the next 7 days, in local ISO time.
- **Three deliveries, because pages reload at different speeds:**
  1. **Baked into every page** as JSON. This is the fallback.
  2. **An `awake` field in the polled data:** `/kiosk/now` (already polled
     every 60 s by `NOW_JS`) and `/depot/now` (polled every 10 s). This is
     the part that matters. The door's own pages reload only when the commit
     changes (`POLL` on `/revision`), which can be days, so a bake alone would
     go stale overnight.
  3. **Baked into the wall's files**, which are rewritten every 60 s. The
     shell reloads about every 10 minutes, at a turn.
- **A stale page stays honest.** Windows are absolute times, so the page
  compares its own clock to the latest list it has. If the list runs out, the
  page stays **awake**: failing awake is the safe side for a welcome screen.

### Dim, drawn

- **Awake:** the page as it is, with nothing drawn over it.
- **Dim:** a layer of pure black over the page, the page showing through at
  about **10%**, and the three squares centred on the black, stepping on
  brand/idle's 4 s beat. Sized in `vmin`, so portrait or landscape makes no
  difference.
- **Fade** into dim slowly (tens of seconds), and **wake quickly** (under a
  second). **Reduced motion:** no fade, and the mark stops on the middle
  square, as brand/idle already promises.
- **The page itself.** Not the backlight: kiosk-1 has no DDC/CI tooling and
  no administrator, so brightness and panel power cannot be controlled from
  there.

### What wakes it

Outside a window:

- **A pointer or a touch** wakes it for **5 minutes to start** (Autumn's to
  tune), then it falls back to the schedule. A wake never shortens a window.
- **The first touch only wakes.** The layer catches it and swallows it, so
  it never also presses the button underneath.
- **The page can hold it awake:**
  - a class takeover (`pickSession` not null) on the wall and the desk. That
    check already runs every 15 s on the client;
  - the wall's **Hold / Keep paused** pressed, because somebody is there.
- **A check-in does not wake it.** It happens on the visitor's phone, and
  the door never sees one. The schedule has to cover it.
- **Proofs:** `?at=` already exists on the wall and class mode, and `dim.js`
  reads the same one, so one query shows a screen at 4 AM. `?awake` and `?dim`
  pin either state for a look.

### Designing around what the door already does

From the media node, 2026-09-27:

| | what happens under dim |
|---|---|
| the wall's turn and timer | **paused while dim**, through the same stopped path Hold and a takeover use, so a dim wall does not churn iframes |
| the ~10 min shell reload | happens only at the end of a turn (#155). While the turn is paused it waits until wake, which is fine |
| self-healing pages (#168, open) | still reload if an `<img>` failed. Harmless under dim |
| screen supervision (#168, open) | raises and relaunches kiosk windows every 30 s. It does not touch page state, and a relaunched page works out dim again from the schedule |

## Monitors: no power control, and "off" is not an emergency

- **kiosk-1:** "Turn off display after" is *Never* on AC, so Windows never
  sleeps those panels. A panel that is off had its power button pressed.
  Both Dells are on **DisplayPort** (`VideoOutputTechnology` 10), and a
  DisplayPort monitor switched off usually drops hot-plug, so Windows
  **removes** it. Its windows pile onto the other panel (the 2026-09-26
  incident). #168 relaunches each panel's kiosk in place when its monitor
  comes back, and does nothing while it is missing. So "attached but off",
  on these, means *missing for a while*, and the door recovers on its own.
- **Editing bay 1 and the roller:** the Vizio also reads as **DisplayPort**
  (10), so switching it off will most likely look the same.
  `troves/kiosk-screen` already treats a missing screen as *nothing shown*
  and puts the page back when it returns. Not yet followed on the TV.
- **Bay 1 sleeps its displays after 2 hours** idle on AC (`powercfg`, read
  2026-09-27). That would blacken the roller whatever the page does. The
  bay's display settings are not ours (`machines/editing-bay-1/PROFILE.md`),
  so this is Autumn's call: leave it, or keep the display awake from the
  trove while it drives the roller (a per-process request, not a settings
  change).

## Open, for Autumn

1. **How dark.** Is 10% the page's opacity over black? That is the same as a
   90% black layer.
2. **Should the mark be alone** in dim, or keep the clock and one line under
   it (who is on next, the Wi-Fi), the way brand/idle's slot does?
3. **How long a touch keeps it awake** (5 minutes to start).
4. **Bookings and classes as windows.** The media node proposes counting both,
   not only rota shifts.
5. **Burn-in.** The mark sits in one place all night: should it drift a
   little each hour?
6. **Bay 1's two-hour display sleep** while it drives the roller (above).

## Steps, once agreed

1. `brand/idle/dim.js` and `dim.css`: the mark lifted out of
   `brand/idle/index.html`, the verdict, the layer, the swallowed first
   touch, `?at=` / `?awake` / `?dim`. The idle screen uses them.
2. `door.py`: an `awake_windows(now)` beside `on_now()` (rota, bookings,
   classes, 60 min lead, merged, 7 days); `page()` inlines `dim.*` and bakes
   the windows; an `awake` field in `/kiosk/now` and `/depot/now`.
3. The wall: pause the turn while dim; Hold and a class takeover hold it
   awake.
4. An attendant recipe (`attendant/`), findable by role and name like the
   wall's: dim at `?at=` 4 AM, wake by a touch that presses nothing, back to
   dim, awake inside a window, awake during a takeover.
5. Bay 1: follow it on the roller from the local render; the TV switched off
   and back on.
