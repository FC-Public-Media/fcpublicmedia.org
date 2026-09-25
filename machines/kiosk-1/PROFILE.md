# kiosk 1

**Status: stood up, working, and wearing this profile, 2026-09-23.** The first
FCPM host that is Windows, the first one with anything on it that this
repository put there, and the first one an agent has been inside.
`machines/binding` run on it says `wearing: kiosk-1`.

> It has a view of fcpublicmedia.org, and it will be the one who grows up
> thinking of itself as a media node.
>
> — Autumn, 2026-09-23, from a remote-control session open on the box

**The name is a placeholder**, the same way `editing-bay-1` and
`editing-bay-2` are. Renaming a directory is free while nothing points at it
and expensive afterwards, and nothing points at this one yet.

## Why this machine exists

Autumn, 2026-09-23:

> I am setting up Git and Claude on one of the kiosk boxes because I want to
> use it to prove fcpm.org as a station node of its own.

That is a change to a written position rather than a new machine. Until today
[`../../docs/STATION.md`](../../docs/STATION.md) said, and still says in the
paragraph this one amends, that *"there is no FCPM station-node machine yet,
and that is deliberate"* — the posture travelled but the hardware did not.
This box is the first attempt at the other half.

It is worth being precise about what "prove" means here, because it is not
"install station-node". FCPM is a **tenant** of the shape, not a copy of the
node — [`../../docs/TENANCY.md`](../../docs/TENANCY.md) limits what travels,
and the stranger-at-the-studio role explicitly does not. What is being tested
is whether the *profile* idea holds up on a host that shares none of the
prototype's platform assumptions.

## What is known

Everything below was reported in the same briefing and none of it has been read
off the machine by anything in this repository.

- **It is Windows, by convention rather than by exclusion.** That makes it the
  default here — see [`../README.md`](../README.md), "What a default is" — but
  the default is a convention and not a boundary. *"It is simply by convention
  that we have Windows stuff. We would add Mac or Linux bindings later. It's
  meant to be copied."* Which is why `names` carries a platform column and
  `gear.yml` carries a `provisioner:` at all, rather than this directory simply
  hardcoding what the only described host happens to run.
- **It is the box with the three portrait panels.** Confirmed rather than
  inferred. The 1050×1680 monitors that [`../../brand/`](../../brand/README.md)
  was made for are this machine's, which means the wallpapers and
  `brand/idle/index.html` are gear questions *about this profile* and not
  general ones. The slot in the idle screen is a slot on this box.
- **An agent has been inside it.** A remote-control session, with a working
  view of the repository. That is the first time anything in `machines/`
  describes a host somebody has actually reached rather than one somebody has
  stood in front of.
- **Gear comes from winget.** `git` and `vscode` went on that way.
  [`../gear.yml`](../gear.yml) is this machine's roster, and it is the shared
  default rather than a copy — **this profile carries no `gear.yml` of its own,
  and that absence is the claim that nothing here diverges.**
- **Claude Code did not come from winget.** It went on with the PowerShell
  installer, before anybody checked whether a winget package existed. One does.
  Recorded in `../gear.yml` as `provisioner: hand` with a `reconcile:` note,
  because what happened and what should have happened are different facts and
  only one of them is true.
- **The crew is one person at a console.** No pool, no supervisor, nothing that
  survives the window closing. [`../crew.yml`](../crew.yml) says so at length,
  including what would have to exist before that changes.

## What an agent arriving here needs and cannot get yet

None of these needs a decision. They are all observations, and the machine is
sitting right there.

- **What does it answer to?** → `names`, which is unfilled.

      echo %COMPUTERNAME%          :: cmd
      $env:COMPUTERNAME            # PowerShell

- **What does `winget list` say?** This is the most valuable unrun command on
  any machine in this directory. It is the Windows census — better than the
  macOS one, because it reports who installed each thing — and the first run of
  it is what turns `../gear.yml` from a list of intentions into a diff.
- **What is the winget id for Claude Code?** `winget search claude`. It is left
  blank in `../gear.yml` rather than guessed.
- **Which Windows, and which edition?** Decides whether winget is present by
  default and whether a scheduled task at logon is available for the crew
  question.
- **Where is this repository checked out, and on which branch?**
- **Can this box build the site?** Jekyll on Windows is a known friction and
  nobody has tried. If it cannot, that is not a fault in the box — CI builds
  the site and always has — but it decides whether `../toolkits` can ever fill
  in its `ruby` row.
- **Which services move here, and which stay on station-node?** This is the
  live question and it is the only one on this page that needs a decision
  rather than an observation. See
  [`../../docs/STATION.md`](../../docs/STATION.md), "What stays with the
  prototype and what moves to the box".

## What the box said, 2026-09-23

Read off the machine by an agent working on it. Answers to the list above, in
order, then what the list did not think to ask.

- **It answers to `200-FCPANEDIT2`**, now in `names`. It is **the old editing
  bay 2**, retired from media work because it can no longer keep up, and given
  a second life here. Autumn: *"This is actually an old predecessor of that
  bay."* So the name is not a mistake and not bay 2's current machine.
- **`winget list`**, the census, says it is **an IT-managed box**: CyberArk
  Endpoint Privilege Manager, McAfee Endpoint Security, a SysAid agent,
  DameWare remote control, a password-policy client, Cisco AnyConnect. Also
  Adobe Premiere and Media Encoder 2020 to 2022, from its editing life. That is
  the environment every other answer here works inside.
- **Claude Code's winget id** was not looked up. Still blank in `../gear.yml`.
- **Windows 10 Pro 1909**, on a Dell Precision T3600 with 12 GB and a Quadro
  4000. winget is present but **v1.3**, too old to install zip or portable
  packages. The account is a **user account, not an administrator**, and the
  admin password is not currently usable. Everything below was done without it.
- **The checkout** is a worktree at
  `C:\Users\FCPM-user\code\work\fcpublicmedia.org@media-node`, on branch
  **`media-node`**. That branch is what the box stays checked out on and what
  its services run from. It is rebased onto `origin/main` every five minutes
  by the door, and moving it is the bounce signal: the door restarts on the
  new code and every screen reloads.
- **It cannot build the site, and does not need to.** No Ruby. Python came by
  the bay route: uv 0.12.18 from the vendor's release, hash-checked against
  the published value, Authenticode-signed "OpenAI OpCo, LLC", then
  `uv python install 3.13`. `bin/build-kiosk.py --check` passes here.
- **It is becoming a builder, on purpose (2026-09-24).** Autumn: *"We are
  going to become a builder, so I just wanted to provision it with
  intent."* Not with Ruby: the site's build viability here is jekyll-enough,
  in the browser. What it adds is the means to run and test the rest of the
  stack locally: the broker (a Cloudflare Worker, run with `wrangler dev`),
  and integration tests on invented `*.localhost` hosts (`you.fcpm.localhost`,
  `<show>.you.fcpm.localhost`), which Edge sends to loopback with no hosts
  file. Passkeys come from a virtual authenticator attached over the
  DevTools protocol, because this box has no passkey hardware. Tooling came
  by the same bay route as uv:
  - **Node 24.21.0 LTS** (npm 11.19.0), the official win-x64 zip, checked
    against nodejs.org's `SHASUMS256.txt`. `node.exe` is signed "OpenJS
    Foundation". It lives in `%LOCALAPPDATA%\media-node\node`, on the user's
    PATH.
  - **gh 2.101.0**, the official zip, checked against the release's
    checksums and signed "GitHub, Inc.", in `~/.local/bin`. Its login is in
    the keyring.
  - **The broker runs here.** `node --test worker/test/*.test.mjs` passes
    all 119 tests. `npx wrangler@4 dev --ip 127.0.0.1` serves the real Worker
    on loopback, with `--var RP_ID:fcpm.localhost` and local KV. It needed one
    fix: `workerd` crashed with an access violation against the system's
    Visual C++ runtime (14.32, from 2022), and a newer one needs an
    administrator to install. Copying `msvcp140.dll`, `vcruntime140.dll` and
    `vcruntime140_1.dll` (14.50, signed by Microsoft) from Edge's own
    application folder next to `workerd.exe` fixes it. Windows loads a
    program's own copy first. The npx cache is temporary, so redo this after
    wrangler updates.
- **Services: one, the door.** `door.py`, on `[::]:8080`, reached by name at
  `http://200-fcpanedit2.local:8080/`. It serves the welcome screen, the
  depot (the studio drive's contents) and the idle screen. A per-user
  scheduled task, `media-node door`, starts it at logon and again every five
  minutes if it has died. That is the door's own job, as
  `com.autumn.station-door.plist` is on station-node, and `door.py startup`
  says whether it is registered and points at this checkout. Nothing reaches
  it from other machines yet, because the firewall rule that would allow it
  needs an administrator.

Two portrait panels are connected, 1050×1680, with a third on its way once a
DVI adapter turns up. Edge 106 (Chromium) shows the pages, one kiosk-mode
instance per panel with a profile folder of its own under
`%LOCALAPPDATA%\media-node\screens\`. The door opens any missing panel when
it starts, and `door.py screens --launch` does the same by hand.

### Asked of IT

- **Sign in automatically.** A reboot waits at the sign-in screen until
  somebody signs in. Nothing above can run before that, and setting up
  automatic sign-in needs an administrator. Seen 2026-09-24: the box came back
  at 14:05 and the door at 14:21, when somebody signed in.
- **Allow TCP 8080 in** for the venv's `pythonw.exe`, once `/kiosk/wifi/<n>`
  answers only the box itself.

## What this folder holds now

A folder here is a claim to have the thing it names (`../README.md`). These
are the first claims this profile makes:

| | |
|---|---|
| `door.py` | the door: every page, the scanner for the studio drive, the background rebase, and `screens`, `startup` and `wifi-password` |
| `node.yml` | what the door shows, and where: screens, Wi-Fi networks, stations, the depot's shares, draft wording |
| `bookings.sample.yml` | a made-up week standing in for the booking calendars. Every booking is for "Sample" |
| `GOTCHAS.log`, `gotcha` | what this box taught us, one line each. `merge=union`, after station-node's |

Secrets are not here. The Wi-Fi passwords and the drive's login are in
Windows Credential Manager on the box, readable only by its user.

## Where it is going

Not a question — a direction, recorded so that the next session does not read
the list above as the whole of it.

**It is meant to run its own station-like services.** station-node is currently
running the things this box was going to reach across the network, and that was
the arrangement when the box was a client. It has since been seen to turn on
and do things.

> I have station-node running the services that it was going to access over the
> network, but it may be free to run it by itself now that I've actually seen it
> turn on and do things. […] I want it to do its own station-like services. So
> we are working towards that.

**Publishing is not one of them, and that is settled rather than pending.**
This repository is mounted in station-node's library as a submodule —
`library/FCPM/fcpublicmedia.org` in that node's `.gitmodules` — and it stays
there. *"I'm still going to handle its publishing, so it's correct that we did
put it as a site in this process."* Nothing about this box changes who
publishes, and an agent that finds itself designing a publishing path here has
taken a wrong turn. (The live website is built by Cloudflare from the git
connection either way; see [`../../docs/deploying.md`](../../docs/deploying.md).
The two facts are not in tension — one is about the repository's home, the
other about the website's build.)

**It claims one service now: the door.** See *What this folder holds now*
above. The first draft of this page ended by claiming nothing, and it was right
when it was written. Later the same day the box started serving its own
screens.
