# Instruments

**Every screen that shows a studio page is an instrument.** Autumn, 2026-09-25,
about the rolling TV in the control-room opening:

> the kiosk tv is an "instrument" by the building nomenclature, something that
> can be taken away from us without our ability to bring back.

and then of all of them:

> i think's reasonable for us to treat all kiosk screens as instruments in this
> sense. even media-node has 2 monitors for different pages, and it makes sense
> to treat them this way.

Status: draft. Nothing reads this directory yet. It records what the screens
are before anything is built to drive them from here.

## What an instrument is, here

The word is station-node's (`docs/instruments.md` there): *hardware the crew
plays, through gear*. The parts of that definition that fit a screen fit it
exactly:

- **Presence is discovered, never declared.** A screen is asked of the display
  stack every time: which monitor, by what it reports about itself, not by
  the number Windows gives it. "Monitor 1" in Settings, `\\.\DISPLAY3` and the
  order a cable was plugged in are all facts about one host on one day.
- **Where it lives is a placement, not a property.** The rolling TV is driven
  by whichever host it is plugged into. Today that is editing bay 1.
- **It is played through gear.** A browser, in kiosk mode, with a profile of its
  own.

## How a screen is matched

Agreed 2026-09-26. Autumn's aim: **rearranging panels must never create a
maintenance task.**

1. **A page follows its panel, not the spot on the wall.** A screen is matched
   on the EDID maker and product code (`DEL` + `DEL404D`). Moving a panel,
   swapping its cable or changing ports keeps each page on the same physical
   panel. No serials: the model is enough, and the rolling TV's serial is a
   filler value anyway.
2. **When two connected panels are the same model, position decides**, in the
   Windows desktop's order.
3. **An unknown panel takes whichever page has no screen yet**, with no config
   edit. That covers a third panel arriving or a replacement.
4. **Swapping two pages is one action**, a command or a button on the door's
   page, and never a config edit. Autumn has her own plan for fixing panels
   that end up in the wrong spot. This leaves room for it and does not design it.

**The connector is not part of a match.** A `link:` field was drafted on
2026-09-25. Rule 1 rules it out, because changing ports must not move a page.

**Rule 3 needs a boundary on a shared host.** On a bay, an unknown panel may
be a person's desk monitor. Editing bay 1 has two HP E273s that people work
at. Rule 3 applies only to panels a host has set aside for its screens. Which
panels those are is still open, and this page doesn't settle it.

The part that does not fit is **produces files**. A RØDECaster is an input;
a screen is an output. That is a deliberate widening of the word, and
station-node's page should be amended to say so rather than stretched quietly.

And the property that makes it an instrument rather than a resource, which is
Autumn's: **it can be taken away, and we cannot bring it back.** The building
owns the TV. The bays are production machines that other people use every week,
and FCPM often only provides the GPU for granted work. So nothing declared here
may assume the screen stays, and nothing driving it may touch configuration it
did not create.

## An instrument is kept with its show

Each screen gets a folder, and the folder holds two files:

| | |
|---|---|
| `instrument.yml` | the hardware: what it reports, how it is matched, where it faces, what input it gets, and who can take it away |
| `show.yml` | **the page, treated as config**: the one route it opens, which modules it shows and how (in rotation, or as thumbnails that stay up), and the scale it is drawn at |

They are kept together on purpose. What a screen shows is chosen for that
screen: its size, its orientation, its distance from the people reading it, and
whether anybody can touch it. A show written for a touch panel at a desk is
wrong for a 55-inch set on its side, seen through a window.

**Shows reference modules; they do not copy them.** The studio map, the depot's
files and the welcome panels are pages the door already builds
(`machines/kiosk-1/door.py`, *THE WALL*). A show names them, and every screen that
uses one gets the same one.

## Roles bind screens to shows, and any host may fill a role

A **role** is a streamlined crew profile for what a machine is doing at a
station: *kiosk*, *roller-TV driver*, *digitization main view*. The role says
which show goes on which instrument. The host's own profile in `machines/` says
how to do that on that platform:

| platform | how a show is put on a screen |
|---|---|
| Windows | `msedge --kiosk --edge-kiosk-type=fullscreen`, a `--user-data-dir` of its own under `%LOCALAPPDATA%`, placed at the screen's rect. `launch_screen` in `door.py` already does it |
| macOS | not written yet |
| Linux | not written yet |

So a host can pretend to fill a role. Station-node, a Mac, could play the kiosk
on its primary display while its big secondary is the digitization main view,
and neither the shows nor the instruments would change.

**The isolated profile is not optional.** On a shared machine it is what keeps a
screen from touching anybody's own browser: a plain `--new-window` is handed to
whatever Edge is already open, restores its session, and lands in someone's
profile (2026-09-24, kiosk-1). A kiosk-mode instance with its own profile folder
is InPrivate and keeps nothing between starts.

## The screens

| instrument | a folder yet | where | show |
|---|---|---|---|
| `roller-tv` | yes | the control-room opening, on a rolling stand; driven by editing bay 1 | the wall, for a pointer, not a finger |
| kiosk-1 Dell P2213 | no | media node, portrait 1050×1680. DEL / DELF043 | Check-in, `/kiosk/` |
| kiosk-1 Dell P2210 | no | media node, portrait 1050×1680. DEL / DEL404D. The one with the speaker bar and USB hub | Files, `/depot/` |
| kiosk-1 third | no | media node, waiting on a DVI adapter | none yet |
| editing bay 2's third monitor | no | faces out like a kiosk display | not named, nothing decided |

kiosk-1's two panels were read by the media node on 2026-09-25 and confirmed
physically on 2026-09-26. They are different models, so the model alone tells
them apart. Today Windows has the P2213 as `DISPLAY1`, primary, and the P2210
as `DISPLAY2`, to its left. Under rule 1 that is incidental. Their labels
say Rev A00 and Rev A04. That is a hardware revision, EDID does not report
it, and it can't be matched on. If the third panel is another P2210 or
P2213, rule 2 applies.

kiosk-1's screens are described today by the `screens:` block in
`machines/kiosk-1/node.yml`, and the rolling TV by its `wall:` block. **Those
blocks keep working until this directory is read by something.** When it is,
they become consumers of it: the door still renders, and this directory says
what is on each screen.

## Open

- **A home for the rendered pages that every driver can reach.** The wall is
  written to `\\10.209.1.1\DIGISTATION\.wall\`, and editing bay 1 is on neither
  network that reaches the depot. Its wired network is the building's, and the
  guest Wi-Fi looks isolated from the depot's LAN: pings and SMB forced out
  through it get nothing (2026-09-25). Either the bay joins, or it renders the show
  from its own checkout. The `.js` transport in `docs/KIOSK.md` already works
  from `file://` with no share.
- **Which panels a shared host sets aside** for its screens, so that rule 3
  never takes a desk monitor (see *How a screen is matched*).
- **Watching a screen nobody can see.** The TV often faces away from the control
  room. A view of what it is showing, perhaps through OBS, on a screen that
  *can* be seen, is wanted. OBS on the bays is other people's configuration and
  is not ours to change, so whatever does this brings its own scene collection
  and profile or does not use OBS.
- **The word, upstream.** Station-node's `docs/instruments.md` says an instrument
  produces files. An amendment there, or a note here that FCPM uses the word
  more widely, has to be settled with that node. One way to put it: an
  instrument has a direction. A *source* produces files and is caught and armed;
  a *sink* is shown things, checked and locked. `kind: screen` is a sink.
