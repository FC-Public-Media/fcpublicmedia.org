# Troves

A trove is one discipline's gear, packed: the facts about a kind of hardware, the software that
plays it and its configuration, per platform. Each trove is a private repository of its own in
FC-Public-Media, mounted here as a submodule at `troves/<repository>`. Jobs
([`machines/`](../machines/README.md)) assemble gear from troves; what is plugged in is never
written, the host finds it.

## Rules

- One discipline per repository, citing outside itself only. Change it in its own worktree
  (`bin/refs work <trove> <branch>`), merge it there, then move this repository's pin.
- `.gitmodules` says `update = none` for every trove, so CI's token never tries a private
  repository. `bin/refs pull` and the kiosk's door check every trove out anyway (`--checkout`), at
  the commit this repository pins, as the account origin's URL names, never with a prompt.
- Its gear lives under its own prefix, `%LOCALAPPDATA%\<profile>\troves\<trove>\` on Windows: the
  path says whose code runs and which grant it needs.
- It never touches gear a person operates; it brings its own copy, profile and ports.
- Its gear comes aboard through the bay ([`docs/station.md`](../docs/station.md)). The trove carries
  the procedure (`bay/`); the host keeps each arrival's record (`machines/<profile>/bay/`).
- A setup volume (gear that mounts as a drive of programs) is copied into the bay's `received\` and
  never run; its hashes, signatures and a reading of each program go in the trove.

## The troves

| trove | plays | where |
|---|---|---|
| [aja-helo](https://github.com/FC-Public-Media/aja-helo) | an AJA HELO encoder | the media hub |
| [atem-mini-pro](https://github.com/FC-Public-Media/atem-mini-pro) | a Blackmagic ATEM Mini Pro | the media hub |
| [buffalo-drivestation](https://github.com/FC-Public-Media/buffalo-drivestation) | a Buffalo DriveStation Ultra | device facts |
| [camera](https://github.com/FC-Public-Media/camera) | a camera on USB | the Pocket 6K Pro, from production |
| [drobo](https://github.com/FC-Public-Media/drobo) | the Drobo iSCSI array | the tank, from production |
| [edgerouter-x](https://github.com/FC-Public-Media/edgerouter-x) | an EdgeRouter X as a switch | three prepared |
| [etc-colorsource-20](https://github.com/FC-Public-Media/etc-colorsource-20) | the ETC ColorSource 20 lighting console | Export to a stick only |
| [game-intake](https://github.com/FC-Public-Media/game-intake) | game recording intake | consoles, handhelds, YouTube |
| [ki-pro](https://github.com/FC-Public-Media/ki-pro) | an AJA Ki Pro over the LAN | Studio Ki Pro |
| [kiosk-screen](https://github.com/FC-Public-Media/kiosk-screen) | a screen showing a studio page | the roller TV, from production |
| [nest-cam](https://github.com/FC-Public-Media/nest-cam) | a 2015 Nest Cam's setup drive | retired |
| [pools](https://github.com/FC-Public-Media/pools) | the storage pools and their recordings | production |
| [post](https://github.com/FC-Public-Media/post) | a recording after release | production |
| [ptz](https://github.com/FC-Public-Media/ptz) | PTZ cameras on the studio network | concept |
| [recorder](https://github.com/FC-Public-Media/recorder) | whatever makes files a node catches | OBS aboard production |
| [rodecaster-pro-ii](https://github.com/FC-Public-Media/rodecaster-pro-ii) | the RØDECaster Pro II | borrowed by station-node |
| [scanner](https://github.com/FC-Public-Media/scanner) | a camera and a screen where codes are redeemed | the qr Pi, the kiosk's pickup point |
| [ti-89](https://github.com/FC-Public-Media/ti-89) | a TI-89: the browser runner, and `cable/` for the GraphLink | the kiosk |
