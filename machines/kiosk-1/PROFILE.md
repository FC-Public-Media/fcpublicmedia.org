# kiosk 1

**Status: stood up and working, 2026-09-23.** The first FCPM host that is
Windows, the first one with anything on it that this repository put there, and
the first one an agent has been inside.

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

**Claims nothing structural yet.** This directory holds no folders, which under
the rule in [`../README.md`](../README.md) is a complete statement rather than
an omission: nothing on this machine has yet been established as ours to
configure. What it holds instead is `names` and this page, which is what a
profile is for before it is a claim.
