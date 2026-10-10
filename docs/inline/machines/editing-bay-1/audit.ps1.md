# `machines/editing-bay-1/audit.ps1`

Moved out of the file. Unreviewed.

## 1

Above `param(`

audit.ps1 -- a record, kept on this bay, of the commands run on it.

audit.ps1 status        what is being recorded, and how much is held
audit.ps1 on            start recording (Windows' own logging; asks for an administrator)
audit.ps1 collect [OUT] copy the record out to a dated folder on this machine, with SHA-256s
audit.ps1 off           stop recording (what was recorded stays)

For the board's secretary, so that work done on this machine by anyone,
including in PowerShell and from a USB stick, can be audited afterwards from
here. It records; it does not watch, block or send anything anywhere. Every
part of it is Windows' own logging, switched on:

- PowerShell transcripts: every PowerShell session's input and output, as
text files in C:\ProgramData\FCPM\audit\transcripts
- PowerShell script block logging: the code PowerShell runs, scripts
included, whatever window or file it came from (event 4104)
- PowerShell module logging: each command in a pipeline, with its
parameters (event 4103)
- process creation with its command line: every program started (cmd,
robocopy, reg, a tool on a stick), by whom, with its arguments (Security
log, event 4688)
- removable storage: files opened, written or deleted on USB drives
(Security log, event 4663)
- audit policy changes, so turning this off shows (Security log, 4719);
Windows always records clearing the Security log (1102)
- USB devices plugged in and out (DriverFrameworks-UserMode log)

The logs are made big enough to hold weeks. An administrator can still
turn all of it off or clear it, and both of those are themselves recorded.

`collect` copies the logs (.evtx, Windows' own format), the transcripts and
each user's PowerShell history into OUT, with a commands.tsv to read, and a
SHA256SUMS of every file. The copy on this machine is the record. What it
holds can include names, paths and anything typed, so it never goes in a
repo.

`on`, `off` and `collect` need an administrator. Run from a plain shell, they
ask Windows for it (one prompt) and show their log when done.

Windows PowerShell 5.1, no modules. ASCII only.
