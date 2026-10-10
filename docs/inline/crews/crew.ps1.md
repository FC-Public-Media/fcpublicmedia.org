# `crews/crew.ps1`

Moved out of the file. Unreviewed.

## 1

Above `param([Parameter(Position = 0)][string]$Verb = "status",`

The crew's one service is a scheduled task named for the crew ("production").
It starts WITH THE COMPUTER, before anyone signs in, and runs whether anyone
is signed in or not: up after a power cut with nobody at the desk. It is not
a sign-in item: nothing in Startup apps, nothing at anyone's sign-in, no
window. It runs as this machine's user without a stored password (S4U), so
it reaches the local disks and the Drobo, not network shares or the
Credential Manager's secrets.

What it cannot do is put anything on a screen: Windows keeps a task started
with the computer apart from every desktop (session 0). The crew's desktop
lines (the rolling TV) are run in the signed-in session by the pool's task,
a pass a minute (`crew.py desktop`, from code/bin/pool.ps1).

install and uninstall need an administrator: run from a plain shell they ask
Windows for one, and act for the user who asked. Doc: crews/.

ASCII only: Windows PowerShell 5.1 reads a BOM-less script as ANSI.

## 2

Above `New-Item -ItemType Directory -Force -Path $State | Out-Null`

The same verb, elevated, for the user who asked: an administrator's
elevation runs as that administrator, whose profile is not this one.
