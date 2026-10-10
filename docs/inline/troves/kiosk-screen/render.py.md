# `troves/kiosk-screen/render.py`

Moved out of the file. Unreviewed.

## 1

Above `import importlib.util`

Builds the wall with the media node's own door.py (wall_files, from the same
checkout as this file), so the page is the one kiosk-1 writes to the share,
not a copy of it. Each file lands whole or not at all, and a file the wall no
longer has is removed, as write_wall does on the share.

Prints one line of JSON: where the depot's copy would be, so screen.ps1 can
prefer it without keeping the address twice.

What this host cannot see stays empty: no bookings (the Microsoft 365 key is
kiosk-1's alone) and no depot listing.
