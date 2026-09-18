# editing bay 2

**Status: one real fact, otherwise undescribed.**

## What is known

**It already runs something of ours.** Autumn, 2026-09-17:

> Any machine I check this out to — such as editing bay two, which is already
> empowered to do a couple of things, like schedule our Cablecast stuff.

That makes this the first bay with a reason to carry a profile, and it means the
Cablecast sync is not purely a GitHub Actions concern: something on this machine
is, or has been, doing part of that work. **What exactly, and how it is
invoked, is not written down anywhere** — which is precisely the kind of thing
this directory exists to stop being true.

### True of the bays generally

Recorded here rather than in both profiles, to avoid two copies of a fact that
would drift apart:

- **Identity is a browser profile, not an account.** The machines have a PIN on
  one shared account; you open a browser and pick a profile. *"It could be done
  better, but it's clear that no one has tackled it yet."* The passkey work in
  [`../../docs/DESIGN-NOTES.md`](../../docs/DESIGN-NOTES.md) is aimed at this.
- **There is a shared network drive**, roughly 32 GB, partitioned about eight
  ways — one partition per box, a little under 4 GB each, with different uses to
  be coordinated. Where it mounts and which partition belongs to which bay is
  not established.
- **A checkout here is a backup.** Because the repository is public and holds
  nothing that needs a secret, checking it out onto a bay carries no risk — see
  [`../../docs/STATION.md`](../../docs/STATION.md). That property is
  load-bearing and the reason profiles can be this relaxed.

## What an agent arriving here needs and cannot get yet

- What does `scutil --get LocalHostName` say? → `names`
- **What is "empowered to schedule our Cablecast stuff"?** A launchd job, a cron
  entry, a person running a script, a browser tab left open? This is the most
  valuable unknown on the machine.
- Where does the network drive mount, and which partition is bay 2's?
- Is this repository checked out on it, and on which branch?

**Claims nothing yet.** No folders, which is a complete statement and not an
omission: nothing on this machine has yet been established as ours to configure.
The Cablecast answer will probably produce the first one.
