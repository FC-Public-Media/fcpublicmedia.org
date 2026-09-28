# Screens at rest: one dim mode for every studio screen

Status: **a plan, 2026-09-27.** Nothing is built. Autumn's brief, drafted on
editing bay 1 with the media node's session (`kiosk`) asked for its notes.
Where the media node has not answered yet, this page says so.

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
| **a builder** (the door, `build-kiosk.py`, bay 1's `render.py`) | the **awake windows** for the next week, baked into the page | a verdict on whether it is awake now |
| **`rest.js`**, one file | the verdict, from the page's own clock, and the dim | a timer that fights the person at the screen |
| **the page** | nothing but including `rest.js`. It may *hold* the screen awake (a check-in on, a class on) | its own rule for "awake" |

### Awake windows

- **Source:** who is on. Today that is `kiosk/rota.yml` shifts, through the
  door's `occurrences()` (the same source `on_now()` reads). Later, the
  calendars that go in front of the rota.
- **Rule:** each shift, from **60 minutes before its start to its end**.
  Overlapping windows merge. No grace period after the end.
- **Written as** a list of `[start, end]` in local ISO time for the next 8
  days, the horizon `occurrences()` already uses. The door writes it into
  every page it builds. For a `file://` page it writes a small
  `awake.js` loaded by `<script src>`, because `fetch` is refused there
  (`KIOSK.md`, the `file://` table).
- **A stale page stays honest.** Windows are absolute times, so a page that
  has not reloaded in a day still dims and wakes on time. If the list runs
  out, the page stays **awake**. Failing awake is the safe side for a
  welcome screen.

### Rest mode (the dim)

- **Awake:** the page as it is, and nothing drawn over it.
- **At rest:** a layer of pure black over the page, the page showing through
  at about **10%**, and brand/idle's **three squares** centred on the black,
  stepping on its 4 s beat. The squares are sized in `vmin`, so portrait or
  landscape makes no difference.
- **Fade** into rest slowly (tens of seconds), and **wake quickly** (under a
  second). A screen should never look like it is flickering.
- **Reduced motion:** no fade, and the mark stops on the middle square,
  which brand/idle already promises.
- **The page keeps running underneath.** Rotation, reloads and polling carry
  on, so waking shows the current page, not a stale one.

### Waking outside a window

This is not a timer to fight. Outside a window:

- **A touch, a click, or the pointer moving** wakes the screen for a short
  while, **5 minutes to start**, which is Autumn's to tune. Then it falls back
  to rest. A wake never shortens a scheduled window.
- **The page can hold it awake** while something matters. Examples: a
  check-in in progress on the welcome panel, or a class takeover (`soon`,
  `late`, `now`) on the wall or class mode. A class is on the calendar
  anyway, so this is a backstop.
- **Overrides for proofs:** `?at=` already exists on the wall and class mode;
  `rest.js` reads the same `?at=`, so one query shows a screen at 4 AM. `?awake`
  and `?rest` pin either state for a look.

### Where the one copy lives

- **`brand/rest/rest.js`**, with its CSS injected by the script itself, so a
  page needs one line to use it. The mark's shape and beat are taken from
  `brand/idle/index.html`, so there is one brand. The idle screen could then use
  `rest.js` too, instead of carrying a copy.
- **Included by:** `door.py`'s `page()` (every door page: `/kiosk/`,
  `/depot/`, `/board/`), the wall shell and its modules (a module sits in an
  iframe, so only the shell dims), class mode, and anything
  `build-kiosk.py` writes.
- **The roller:** bay 1 renders the wall with `door.py`, so it gets `rest.js`
  and the windows for free (`troves/kiosk-screen`).

### What is not in scope

- **No monitor power.** No DPMS, no switching panels off, no `fcpm screen off`
  on a schedule. The roller can be switched off by hand, and a person can
  still do that.
- **Attached but off is not an error.** Windows keeps an off monitor in the
  display stack, so the door's `screens` supervision and bay 1's
  `kiosk-screen` keep a browser on it as usual. Nothing alarms.

## Open, for Autumn

1. **How dark.** Is 10% the page's opacity over black? Or should it be the
   black layer at 90%? These are the same thing, drawn two ways.
2. **Should the mark stay alone** at rest, or should it keep the clock and one line
   under it (who is on next, the Wi-Fi) the way brand/idle's slot does?
3. **How long a touch keeps it awake** outside a window (5 minutes to start).
4. **Bookings as windows.** Is a booked member session a "live host session"
   too, or only rota shifts for now?
5. **Burn-in.** A mark that sits in one place for the whole night: should it
   drift a little each hour?

## Open, for the media node

(Asked 2026-09-27 over Remote Control; to be filled in from its answer.)

- Where `rest.js` should sit so the door, the wall's files and `file://`
  pages share it, and how `page()` and the wall shell include it.
- Whether anything the door already does (the 10-minute reload, polling,
  `screens` supervision) conflicts with a black layer.
- What the two Dells do when they are switched off at the panel, and what
  "attached but off" looks like to the display stack on kiosk-1.

## Steps, once agreed

1. `brand/rest/rest.js`: the verdict, the layer, the mark, `?at=` / `?awake` / `?rest`.
2. The door writes the awake windows (`awake_windows(now)` beside `on_now`) into
   `page()`, the wall shell and `awake.js`.
3. Pages hold it awake where they must (check-in, class takeover).
4. brand/idle uses `rest.js`'s mark instead of its own copy.
5. An attendant recipe (`attendant/`), findable by role and name like the wall's:
   rest at `?at=` 4 AM, wake by pointer, back to rest, awake inside a window.
