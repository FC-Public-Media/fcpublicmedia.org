# The PTZ trove

**If you have a pan-tilt-zoom camera on the studio network, this is the gear
that runs it.** Shots an operator can trigger with one button, settings
anyone can configure, and a feed that can be recorded even when it isn't
going out live, so it can become content later.

Status: concept, 2026-10-06. No camera yet. The Fort Collins city TV station
is donating its old PTZ cameras, and they are on their way. Their arrival is
also what the TriCaster Flex training is waiting on. Make and model are not
known yet, so nothing below names a protocol as fact.

## What it is for

Autumn, 2026-10-06:

- **Triggered by operators.** Like `../camera/presets.yml`: a page of
  curated shots, one button each (*the whole room*, *the desk*, *the door*),
  so nobody at the button has to drive a joystick.
- **Configurable here.** Shots, names and which camera is which live in a
  file this trove carries, edited like any other.
- **Behind the scenes, recorded.** A camera that isn't on the program feed
  can still be recording, through `../recorder/`'s OBS, for making content
  later.
- **The 24-hour stream.** The concept `../nest-cam/` worked out and couldn't
  run: a wide shot that, by its aim, nobody is ever really on (a corner, or the
  kiosk seen from the shoulder down), with no audio, live and shown. A PTZ
  camera parked on a preset is a better way to do that than the Nest was.

## Rules this trove adds

- **The TriCaster wins.** The TriCaster Flex is operated by people, and under
  *A trove never touches gear a person operates* (`../README.md`), so are the
  cameras whenever it is driving them. One controller at a time: while a show
  holds a camera, this trove reads its position and does not move it. How a
  show says it holds one is the first thing to settle with the TriCaster in
  hand.
- **Recording people is a policy, not a setting.** Behind-the-scenes capture
  records members and guests. Who is told, where the files go and how long
  they are kept is the board's to say before the first recording that isn't
  a test.
- **Every login** a camera has goes in Credential Manager, like the
  EdgeRouters' (`fcpm-ptz:<camera>`), never in a file.

## When the cameras arrive

Read each one before it joins anything, and write it down here:

| question | why it matters |
|---|---|
| make, model, firmware | everything below depends on it |
| control: VISCA over IP, VISCA on a serial port, a vendor's own HTTP, NDI | whether the bay can steer it over the network or needs a serial adapter |
| video out: SDI, HDMI, NDI, an RTSP stream | network video goes straight into OBS; SDI or HDMI needs capture hardware, as in the digitization proposal |
| presets stored in the camera, and how many | whether a shot is a camera preset or a position this trove sends |
| power: PoE or a brick | which switch port. The EdgeRouters' only PoE is passive, on `eth4`, not the standard kind, and stays off |
| factory reset and default login | the reset goes in this README, the new password in Credential Manager |
| how the TriCaster Flex adds and drives it | so the trove and the TriCaster can take turns |

## Not yet

- Any code. The console and presets page come after one camera has been read
  by hand, the way `../camera/` and `../edgerouter-x/` started.
- Where the cameras live on the network. The studio network is `10.1.10.x`;
  where on it the cameras go is Autumn's call.
- A home for behind-the-scenes recordings. `D:` on editing bay 1 has room,
  but the masters question in the digitization proposal is the same question.
