# Troves

A trove is one discipline's gear, packed: the software that plays a kind of hardware and its
configuration, per platform. Crews assemble gear from troves; the node's instruments are
[`instruments/`](../instruments/README.md); what is plugged in is never written, the host finds it.

## Rules

- One discipline per folder, citing outside itself only, so it can move to its own repository whole.
- Its gear lives under its own prefix, `%LOCALAPPDATA%\<profile>\troves\<trove>\` on Windows: the
  path says whose code runs and which grant it needs.
- It never touches gear a person operates; it brings its own copy, profile and ports.
- Its gear comes aboard through the bay ([`docs/station.md`](../docs/station.md)). The trove carries
  the procedure (`bay/`); the host keeps each arrival's record (`machines/<profile>/bay/`).
- A setup volume (gear that mounts as a drive of programs) is copied into the bay's `received\` and
  never run; its hashes, signatures and a reading of each program go in the trove.

## The troves

| trove | plays | state |
|---|---|---|
| [recorder](recorder/README.md) | whatever makes files a node catches | OBS aboard editing bay 1 |
| [kiosk-screen](kiosk-screen/README.md) | a screen showing a studio page | roller-tv |
| [camera](camera/README.md) | a camera on USB | the Pocket 6K Pro |
| [edgerouter-x](edgerouter-x/README.md) | an EdgeRouter X as a switch | three prepared |
| [ti-89](ti-89/README.md) | a TI-89 on a GraphLink cable | on the media node |
| [pools](pools/README.md) | the storage pools and their recordings | editing bay 1 |
| [post](post/README.md) | a recording after release | editing bay 1 |
| [ki-pro](ki-pro/README.md) | an AJA Ki Pro over the LAN | Studio Ki Pro |
| [nest-cam](nest-cam/README.md) | a 2015 Nest Cam's setup drive | retired |
| [ptz](ptz/README.md) | PTZ cameras on the studio network | concept |
| [game-intake](https://github.com/FC-Public-Media/game-intake) | game recording intake | its own private repository |
