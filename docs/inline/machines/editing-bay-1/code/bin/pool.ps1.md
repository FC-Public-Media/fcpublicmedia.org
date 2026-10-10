# `machines/editing-bay-1/code/bin/pool.ps1`

Moved out of the file. Unreviewed.

## 1

Above `param([Parameter(Position = 0)][string]$Verb = "status",`

The root is ~/code. The pool keeps one thing up there, `claude remote-control
--no-create-session-in-dir`: a server, not a session. It opens none and
names none, and every session starts from zero at claude.ai or the phone
(Autumn, 2026-10-06). `production` names the worktree, not a session.

Earlier pools revived every session after a logon, then kept one seat
session open. Both are gone: nothing is resumed and no session is started
here. Sessions that are running are listed, and ended only with a stale
server (below).

Every pass, not once per logon: a server that dies mid-day is back within a
minute. If one is already serving ~/code, a terminal one included, the pass
leaves it alone (a second would refuse anyway).

Claude updates are when the server goes bad (2026-10-09). An update swaps
claude.exe under it, and can revoke its sign-in: it keeps running,
unregistered, and no session reaches it. So a server this pool started is
bounced when signed out, at once, and when older than the installed
claude.exe, once calm for 15 minutes, as kiosk-1's door does. Ending it ends
its sessions; nothing is revived after.

ASCII only: Windows PowerShell 5.1 reads a BOM-less script as ANSI.

## 2

Above `$ErrorActionPreference = "Continue"`

Not "Stop": under 5.1 that turns any line claude.exe writes to stderr into a
terminating error, and a call that went fine reads as a failure.

## 3

Above `$Dev = Join-Path $env:LOCALAPPDATA "fcpm\dev"`

`fcpm dev on` (Autumn, 2026-10-09): follow GitHub, so a merge reaches this
bay by itself. Shared with machines/fcpm, which flips it.

## 4

Above `@(Get-CimInstance Win32_Process -Filter "Name='claude.exe'" -ErrorAction SilentlyContinue |`

claude.exe processes running the `remote-control` subcommand. Not the
--remote-control flag, which a single session carries.

## 5

Above `$srv.CommandLine -match [regex]::Escape((Join-Path $State "server.log"))`

A server this pool started: only its own write to our server.log. One
started by hand in a terminal is left alone, stale or not.

## 6

Above `$out = @(); $todo = @($all | Where-Object { $_.ProcessId -eq $procId })`

Every process under $procId. Windows reuses pids, so a child must have
started after its parent to count as one.

## 7

Above `$since = $srv.CreationDate.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss")`

The server's sign-in was taken from it (a Claude update or a sign-in
elsewhere revokes the token, 2026-10-09): it says so in server.log and
stays running, unregistered, and no session can reach it.

## 8

Above `$below = @(Below $srv.ProcessId $all)`

What keeps a stale server from a bounce now: short reasons, none once it
has been calm for $CalmMin minutes (kiosk-1's door, 2026-10-09: sessions
don't close, so waiting for them would never end). Calm is no task
running under it and no transcript of its sessions written lately.

## 9

Above `$elsewhere = @($rows | Where-Object { $mine -notcontains $_.pid } | ForEach-Object { $_.sessionId })`

Sessions outside the server (a background job, a terminal) are not its
to wait on: their transcripts don't count.

## 10

Above `if (SignedOut $srv) { return "signed out" }`

Why the server should be replaced, or $null. Signed out: at once, it
serves nothing. Older than the installed claude.exe: Claude updated
under it, the daemon follows and the server doesn't (it sat on 2.1.292
through three updates, 10-07 to 10-09).

## 11

Above `$f = Join-Path $State "server.said"`

Log a line only when it differs from the last one said this way, so a
held bounce is logged when what holds it changes, not every minute.

## 12

Above `$all = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue)`

Replace a server of ours that went stale. Ending it ends its sessions.
The next start may be refused for a few minutes ("already served"),
and later passes try again.

## 13

Above `$err = Join-Path $State "server.err"`

Why the last one stopped, if it said. A server that ended without
signing off (a sign-out, a kill) still holds ~/code for a few minutes,
and each start until then is refused: "already served by a terminal
`claude remote-control`". That is the churn after a sign-in. This pass
tries again, as every pass does.

## 14

Above `$a = "remote-control --no-create-session-in-dir --debug-file "$(Join-Path $State 'server.log')""`

No console: input from an empty file, output to server.out and
server.err. It outlives this pass, as the roller's Edge does. Under
conhost --headless a refused server left in about a second with nothing
said anywhere, and at the 2026-10-06 sign-in a cmd.exe under one failed
to start (0xc0000142, a popup on the desktop).

## 15

Above `$crew = Join-Path $Root "refs\fcpublicmedia.org\crews\crew.py"`

The production crew's desktop lines (the rolling TV), a pass a minute:
its supervisor starts with the computer and has no desktop to put them
on (crews/crew.ps1), so this task, in the signed-in session, is
its desktop half. Until the crew's supervisor is in the mirror, the
screen trove directly, as before.

## 16

Above `$s = Join-Path $Root "refs\fcpublicmedia.org\troves\kiosk-screen\screen.ps1"`

The screens this bay drives, kept each pass by their trove, from the
mirror (the admitted code). A child process: the trove's strict mode and
types stay out of the pool. It logs to its own screen.log.

## 17

Above `$env:FCPM_BY = 'pool'`

FCPM_BY, not -By: the mirror's copy may predate the flag, and must still
keep the screen (screen.ps1's param block).

## 18

Above `if (-not (Test-Path $Dev)) { return }`

With dev on, pull fcpublicmedia.org, the mirror this machine runs (not the
reading ones, Autumn 2026-10-10), every $PullMin minutes (bin/refs pull:
fast-forward only, a dirty mirror or one off main is skipped), so
Current places what was merged without anyone pulling. Off, the weekly
task and people pull, as before.

## 19

Above `$mirror = Join-Path $Root "refs\fcpublicmedia.org"`

Keep this machine on what the mirror holds, a pass a minute. The mirror
only ever holds main (bin/refs fast-forwards it), so whatever pulled it,
a session, the weekly task or the watcher, what was merged is placed by
the next pass: the carried files (this script among them, which the
pass after runs), the compiled settings, PATH (machines/sync install).
And the crew's supervisor, when its code moved under it, is restarted on
the new code. Nobody runs an install to catch up (Autumn, 2026-10-09).

## 20

Above `if (-not $was) { return }`

The supervisor runs crews/ from the mirror in place, and reads its
order again on its own; its code it does not. Ended, its task starts it
again on what is there now.

## 21

Above `$all = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue)`

`off` is authoritative (Autumn, 2026-10-09): every Remote Control server
on this box ends, the pool's or one started by hand, with its sessions.
Then it looks again, and says by pid whatever is still up.
