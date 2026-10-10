# `machines/editing-bay-1/check.ps1`

Moved out of the file. Unreviewed.

## 1

Above `$ErrorActionPreference = "Continue"`

check.ps1 -- what editing bay 1 needs that files cannot say. Changes nothing.

Run by `machines/sync` status on this profile, or alone:
  powershell -NoProfile -File machines\editing-bay-1\check.ps1

One line per fact, "ok" or "WANTED" and what would make it so. The WANTED
lines are the Day 0 list (docs/machines/editing-bay-1/PROFILE.md) for whatever is still missing.

Windows PowerShell 5.1, no modules. ASCII only: 5.1 reads a BOM-less script
as ANSI.

## 2

Above `Get-NetConnectionProfile -ErrorAction SilentlyContinue | ForEach-Object { "note    network $($_.Inte`

Reported, not judged. Public is the intended posture (Autumn, 2026-09-26):
the network is managed and isolated, what matters is what we do inside, and
Windows making a new Public profile for each new gateway is it healing, not
drifting.

## 3

Above `$depot = $false`

Where this bay reaches, and what it cannot yet.
Its SMB port, for 800 ms, as troves/kiosk-screen's DepotAnswers asks.
Test-NetConnection waited out the full TCP timeout (21 s, measured
2026-10-09) behind a progress box, twice a watcher visit.
