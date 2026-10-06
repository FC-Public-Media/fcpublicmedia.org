# Screens at rest: one dim mode for every studio screen

Status: **agreed, 2026-09-27; not built.** Autumn's brief and her answers,
drafted on editing bay 1 (which holds the pen) with the media node's session
(`kiosk`), which answered for the door and for kiosk-1's panels.

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

And her answers to the plan's questions, the same day:

> Very, very dim. If it's on, nobody's here. The point is not to turn the
> kiosk machine's monitors off; the roller TV is what it is. Try 10% the way
> I said it.
>
> The animated page the way it is. It doesn't need to show anything. It's an
> excuse not to have the screen off: nobody would see it, but if they did,
> they'd know it was working. We're free to be stylistic with the three
> squares, like split clock silliness: the middle square ticks the seconds,
> the top one has the hour hand, the bottom one the minute hand. Be weird.
>
> There won't be touches, but treating touch and the mouse together is right.
> Five minutes is ridiculously short: an hour. I'm not putting an audience
> through the screen dimming every five minutes because the schedule doesn't
> know they're here.
>
> Bookings are necessarily a subset of the host schedule, so they're covered.
> Classes are what we add.
>
> Against burn-in, the squares can glide around like perpetual-motion hockey
> discs, calmly. That would be funny.
>
> A visitor checking in during off time isn't legitimate: the door is locked,
> which is why a host is here. The space is small; ten short paces in and you
> see all three rooms. The host schedule covers it.

(Both paraphrased from speech, 2026-09-27. Her words win where this differs.)

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
  - rota shifts, the host schedule (`kiosk/rota.yml`, the same source
    `on_now()` reads);
  - class sessions (a class `soon`, `late` or `now` by `pickSession`).
  - **Not bookings.** A booking is always inside host hours, because the
    host is who lets the member in. So the rota already covers every booking
    (Autumn, 2026-09-27).
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
- **Dim:** very, very dim. Pure black, with the page showing through at
  **10%**, and over it the three squares, as the idle screen draws them. The
  squares show nothing but the fact that the screen is working. Sized in
  `vmin`, so portrait or landscape makes no difference.
- **The squares are allowed to be weird.** The idle screen's walk of the lit
  square stays. On top of it, a split clock: the **top** square carries an
  hour hand, the **bottom** one a minute hand, and the **middle** one ticks
  the seconds. The hands are thin marks inside each square, in the soft
  grey.
- **They glide, against burn-in.** The column of three drifts slowly
  across the black, like a perpetual-motion hockey disc: a straight line at
  a calm, constant speed, and a bounce off each edge of the screen. The
  pixels it lights are never the same for long.
- **In step, on every screen of one computer** (Autumn, 2026-10-05). The
  column's place and its lit square are read off the clock rather than kept
  from frame to frame, so kiosk-1's panels show the same thing at the same
  moment. They need no messages for that, which is as well: each panel is
  a browser profile of its own, and tabs in different profiles can't talk.
- **Fade** into dim slowly (tens of seconds), and **wake quickly** (under a
  second). **Reduced motion:** no fade, no glide, and the lit square stops on
  the middle one, as brand/idle already promises. The column then moves to a
  new resting place once an hour instead of gliding, so burn-in is still
  kept away.
- **The page itself.** Not the backlight: kiosk-1 has no DDC/CI tooling and
  no administrator, so brightness and panel power cannot be controlled from
  there.

### What wakes it

Outside a window:

- **A pointer or a touch** wakes it for **an hour**, and each later touch or
  movement starts that hour again. Then it falls back to the schedule. A room
  with people in it should not watch the screen dim because the schedule
  didn't know they were there. A wake never shortens a window. (None of these
  screens is touched today, but a touch and the mouse count the same.)
- **The first touch only wakes.** The layer catches it and swallows it, so
  it never also presses the button underneath.
- **The page can hold it awake:**
  - a class takeover (`pickSession` not null) on the wall and the desk. That
    check already runs every 15 s on the client;
  - the wall's **Hold / Keep paused** pressed, because somebody is there.
- **A check-in does not wake it,** and doesn't need to. It happens on the
  visitor's phone, so the door never sees one. And a check-in outside host
  hours isn't legitimate anyway: the door is locked, and a host is why anybody
  is inside. The host schedule covers it.
- **Proofs:** `?at=` already exists on the wall and class mode, and `dim.js`
  reads the same one, so one query shows a screen at 4 AM. `?awake` and `?dim`
  pin either state for a look.

### The contract between the door and `dim.js`

Set by the media node on branch `screens-awake-windows`, and accepted for
`dim.js` on 2026-09-27:

| | |
|---|---|
| `window.FCPM_AWAKE` | `[[startMs, endMs], ...]`, epoch ms, merged. `page()` bakes it into `<head>` before any body script |
| `window.fcpmAwake(list)` | called by the kiosk page (every 60 s) and the depot page (every 10 s) with fresh windows. It replaces `FCPM_AWAKE` and dispatches `fcpm:awake` on `window` |
| `<html class="fcpm-awake">` | awake whatever the schedule. The wall sets it while held and during a class takeover; the desk sets it during a takeover |
| `window.FCPMDim.isDim()` | the wall asks every frame and stops its turn while it is true |
| `window !== window.top` | `dim.js` does nothing, so a module's iframe draws no second layer |
| no list, an empty list, or past its last end | **awake** |

A touch inside a module's iframe while the screen is awake does not reach the
shell, so it does not restart the hour. While dim, the layer sits above the
iframes and catches the touch itself.

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
- **Editing bay 1 and the roller:** the Vizio reads as **DisplayPort** (10)
  because it is on an HDMI-to-DisplayPort adapter; the studio has no native
  HDMI-to-DisplayPort cable. On 2026-09-27 Autumn moved its cable between
  ports while testing. The roller dropped out and came back 1 px lower, and
  our Edge was gone. One `keep` launched it again in place. Once #170 merges,
  the pool's pass does that within five minutes. The long HDMI cables with
  blue insides have never worked here, possibly because they need more
  power. Suspect them first.
- **Bay 1 sleeps its displays after 2 hours** idle on AC (`powercfg`, read
  2026-09-27). **Left as it is:** "the roller TV is what it is." The page
  dims on schedule, and the bay may blank the TV on top of that. Neither is
  an emergency.

## Decided (Autumn, 2026-09-27)

1. **How dark:** 10% the way she said it: the page at 10% over pure black.
2. **Dim is the animated squares alone,** with no text. They can be weird:
   a split clock across the three squares.
3. **A touch or the mouse keeps it awake for an hour,** restarted by each
   later touch or movement. Not five minutes.
4. **Windows are host shifts plus classes.** Bookings are inside host hours
   by definition.
5. **Burn-in:** the squares glide calmly and bounce off the edges.
6. **Bay 1's display sleep is left alone.**

## Steps

Who builds what (agreed 2026-09-27): **bay 1** does steps 1, 4 and 5. **The
media node** does steps 2 and 3, on top of step 1 once it lands, so only one
session writes `dim.js`.

1. `brand/idle/dim.js` and `dim.css`: the mark lifted out of
   `brand/idle/index.html`, the split clock, the glide, the verdict, the
   layer at 10%, the hour-long wake with the first touch swallowed, and
   `?at=` / `?awake` / `?dim`. The idle screen uses them.
2. `door.py`: an `awake_windows(now)` beside `on_now()` (rota shifts and
   classes, 60 min lead, merged, 7 days); `page()` inlines `dim.*` and bakes
   the windows; an `awake` field in `/kiosk/now` and `/depot/now`.
3. The wall: pause the turn while dim; Hold and a class takeover hold it
   awake.
4. An attendant recipe (`attendant/`), findable by role and name like the
   wall's: dim at `?at=` 4 AM, wake by a touch that presses nothing, back to
   dim, awake inside a window, awake during a takeover.
5. Bay 1: follow it on the roller from the local render; the TV switched off
   and back on.
