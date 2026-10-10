# The PTZ trove

Pan-tilt-zoom cameras on the studio network: shots an operator triggers with one button, configured
in a file this trove carries, and feeds recorded through [`../recorder/`](../recorder/README.md)
when they are not on air. A concept: the cameras, donated by the Fort Collins city TV station, have
not arrived, so no make, model or protocol is known.

- The TriCaster wins: while a show holds a camera, this trove reads its position and never moves it.
- Recording people behind the scenes waits on the board's policy: who is told, where files go, for how long.
- Each camera's login goes in Credential Manager as `fcpm-ptz:<camera>`, never in a file.
- Each camera is read by hand, and written here, before it joins anything.
