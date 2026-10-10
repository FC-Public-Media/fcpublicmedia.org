# `machines/editing-bay-1/gear.yml`

Moved out of the file. Unreviewed.

## 1

Above `version: 1`

gear.yml — what editing bay 1's crew stands on. REPLACES ../gear.yml here.

Same fields as the default (`../gear.yml`, after station-node's docs/gear.md);
`at:` is added, because most of this bay's gear is not in winget's inventory
and is found by where it was put. `check.ps1` reads `package:` and `at:` and
reports each entry present or WANTED. Presence is never written here.

NOTHING HERE NEEDS AN ADMINISTRATOR. Where winget can install for this user
alone (`--scope user`), winget is the provisioner: uv is. Where its package
is a machine-wide installer that raises an elevation prompt, the vendor's
portable archive comes through the bay instead: gh and Node are.
What the bay brings arrives the bay's way (receive,
verify against the vendor's digest and Authenticode, stage, install, confirm:
docs/machines/BAY.md), into ~/.local/bin or this profile's folder in
%LOCALAPPDATA%, and each arrival leaves a record in ./bay/.

NOT OURS, AND LISTED SO NOBODY TAKES IT FOR OURS: the OBS in Program Files
(winget, 32.1.1) is the one people operate here every week. The recorder
trove brings its own portable copy beside it (troves/recorder/).

## 2

Above `signer: OpenAI OpCo, LLC`

Signed as "OpenAI OpCo, LLC", not Astral: measured 2026-09-26, Authenticode
Valid. Written down so the next arrival signed otherwise is a question.

## 3

Above `- gear: node`

winget puts `uv`, `uvx` and `uvw` on PATH for shells started after it.
An older shell needs the full path:
  %LOCALAPPDATA%\Microsoft\WinGet\Packages\astral-sh.uv_Microsoft.Winget.Source_8wekyb3d8bbwe\uv.exe
Python comes from it: `uv run --no-project --python 3.12 --with pyyaml ...`

## 4

PROPOSED, NOT WANTED YET: ffmpeg, for transcoding digitization masters. It
waits on the capture decision (Autumn, HDCP testing, and a home for masters).
