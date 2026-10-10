# `troves/kiosk-screen/screen.ps1`

Moved out of the file. Unreviewed.

## 1

Above `param(`

screen.ps1 -- keep a studio page on a screen this host finds plugged in.

screen.ps1 status [INSTRUMENT]   is the screen here, is our browser on it, showing what
screen.ps1 keep   [INSTRUMENT]   one pass: put it right. What the pool's task runs
screen.ps1 off    [INSTRUMENT]   close our browser and stay off until `on`
screen.ps1 on     [INSTRUMENT]   keep it again, starting now
screen.ps1 reset  [INSTRUMENT]   close our browser and start it again
screen.ps1 class  [light|dark]   show class mode instead of the wall, until wall`n    screen.ps1 wall   [INSTRUMENT]   back to the wall

INSTRUMENT is a folder in ../../instruments/ (default roller-tv). Its
instrument.yml `match:` says what the screen reports about itself over EDID;
the screen is looked up by that, every time, never by display number
(../../instruments/README.md).

What goes on it is the wall, or class mode while a person has asked for it
(../../instruments/roller-tv/class-mode.md: the teacher's materials, written
as class.html beside the wall, with no turning). Either way, the depot's copy, which kiosk-1 writes, when the
depot answers; otherwise the wall rendered here from this checkout's door.py
(render.py, under uv). It is played the way door.py's launch_screen plays a
screen: Edge in kiosk mode, fullscreen, with a profile of its own under
%LOCALAPPDATA%\<profile>\troves\kiosk-screen\<instrument>\, so nobody's own
browser is touched and nothing is kept between starts.

- No match, nothing shown. If Windows piled our browser onto another monitor
when the screen went, it is closed; it never takes another screen.
- Our browser is the one whose command line carries our profile folder. It is
closed by asking its windows, then by its process ids. Never by name: every
Edge on this machine is msedge.exe, and the others are people's.
- Nothing here runs for long. The pool's task runs `keep` every minute, with
FCPM_BY=pool, and a person's `off` holds until their `on`. Each pass leaves
a heartbeat, and `status` reports when the pool last ran it, not a promise.

Windows PowerShell 5.1, no modules. ASCII only.

## 2

Above `[ValidateSet('pool', 'hand')] [string] $By = $(if ($env:FCPM_BY -eq 'pool') { 'pool' } else { 'hand'`

Who is running this pass: the pool, or a person (or a session acting
for one). The pool says so with FCPM_BY=pool in the environment, not
with this flag, so a pool newer than this file's copy in the mirror
still keeps the screen instead of failing on an unknown parameter.

## 3

Above `$Beat    = @{ pool = (Join-Path $Root 'kept-pool'); hand = (Join-Path $Root 'kept-hand') }`

The heartbeat: when a pass last ran, one file per who ran it. `status` reads
these rather than promising. For a week in September it said "every pool
pass" while the pool running on EDIT2 had no screens step at all.

## 4

Above `if (-not (Test-Path $Spec)) { throw "no instrument '$Instrument' ($Spec)" }`

instrument.yml's `match:` block, by line. Only `product` is needed to
find it (the EDID product code carries the maker's three letters).

## 5

Above `$names = @([Fcpm.Screen]::AdaptersFor($m['product']))`

The monitor answering to the match, or $null. More than one is also $null:
which of two identical sets is which is not ours to guess.

## 6

Above `if (-not $path -or $path -notmatch '^\\\\([^\\]+)\\') { return $false }`

A share that is not there can hold Test-Path for half a minute, so ask
its SMB port first, briefly.

## 7

Above `$uv = FindUv`

Render here every pass, so the fallback is never stale, then prefer the
depot's copy if it answers. Returns the URL, and says which.
