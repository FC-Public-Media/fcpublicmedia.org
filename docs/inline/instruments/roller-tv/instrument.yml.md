# `instruments/roller-tv/instrument.yml`

Moved out of the file. Unreviewed.

## 1

Above `version: 1`

instrument.yml — the studio's rolling TV. See ../README.md.

AN INSTRUMENT WE DO NOT OWN. The TV is the building's. It is lent to the
studio, and it can be taken away without our being able to bring it back
(Autumn, 2026-09-25). Nothing here may assume it stays: a driver that finds
no matching screen shows nothing and says so, and does not take another
screen instead.

PRESENCE IS DISCOVERED. A driver asks the display stack, every time, for a
monitor answering to `match:`. Never the display number: on editing bay 1,
Settings calls this "monitor 1" and Win32 calls it \\.\DISPLAY3.

Unread by any tool yet.

## 2

Above `match:`

What the display reports about itself, over EDID. Read on editing bay 1
2026-09-25 with WmiMonitorID, which needed no administrator. Matched on
maker + product code (../README.md, "How a screen is matched"); `model` is
the readable name. The serial is a filler value, 16843009 (0x01010101), and
the port is not matched, so a cable moved to another port keeps the show.

## 3

Above `# As seen on editing bay 1, 2026-09-25: portrait, 720x1280 logical, most`

EDID gives 2013 and 160x90 cm. The year is plausible. The size is not a
55" panel, which is why size is not used to match.

## 4

Above `orientation: portrait`

As seen on editing bay 1, 2026-09-25: portrait, 720x1280 logical, most
likely 1080x1920 at 150% scaling. Where it sits on the desktop is the
host's business and is not recorded; a driver reads it off the match.

## 5

Above `input: pointer`

Nobody touches it. It is out of reach behind the control room glass, and it
is not a touch screen. A pointer can reach it from the driving host, so a
show may still have controls, sized for a mouse.

## 6

Above `played-through: msedge`

How it is played, on a Windows host: through Edge, in kiosk mode, with a
profile of its own that no person uses. Nothing else on the host is touched.
The bays are production machines that other people use every week; their
browsers, OBS and display settings are not ours.
