# `crews/crew.py`

Moved out of the file. Unreviewed.

## 1

Above `import ctypes`

A crew (docs/crews/README.md) orders from menus: its `services` file names,
line by line, a service some residency serves (`residency.yml`, `serves:`).
This runs those lines and nothing else. A `keep` line is kept up, coming back
after 5s, doubling to 5m, the wait reset once it has stayed up 10m. An `every`
line runs on its interval, never two at once. A `desktop` service runs only
while this process has someone's desktop to put it on. The file is read again
whenever it changes: a new line starts, a removed one stops being kept (and is
stopped, if this started it).

Nothing here remembers. Whether a line is up is asked each time, the way its
residency says (`alive:` a port that answers, or a process that is there);
something already serving it (a `fcpm pools` window, say) counts, and is left
alone. A file written at start would be a record of an intention, and after a
crash a lie told confidently (station-node's bin/services).

Children get no console and no window: output goes to a log per line, under
%LOCALAPPDATA%\<profile>\crew\ (the pool's lesson: a headless console killed
what it started). One supervisor per crew per machine (a named mutex).

## 2

Above `f = HERE / crew / "services"`

The crew's lines: name, when, the service from its residency. A line
that names nothing on a menu is reported, never run.

## 3

Above `a = svc.get("alive") or {}`

Whether the service is up, by its residency's own test. None: it has
none (a periodic service is not up or down; it ran, or it did not).

## 4

Above `sid = ctypes.c_ulong()`

Whether this process is in someone's session (not session 0, where a
task started with the machine and nobody signed in runs).

## 5

Above `if not has_desktop():`

One pass of the crew's desktop lines, in someone's session: what the
supervisor started with the machine cannot do, having no desktop (Windows
keeps session 0 apart). The sign-in task runs this every minute; a line is
run when its interval has passed since it last wrote its log.
