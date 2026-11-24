# Administrator steps

**Design; nothing here is built.** Machines install themselves. What needs an administrator waits as a
stack, is approved by a staff wizard, and is done at the machine in one action.

## Where it stands

- The bays' pool pass runs `sync install` when the mirror moves, and on its beat besides
  ([`../machines/pool.ps1`](../machines/pool.ps1)). It has no `FCPM_DESK`, so a `system` line is left:
  `waiting … the next fcpm install at the desk places it`. That line is the stack, said where nobody reads it.
- The pass runs `sync install`, not `fcpm install`: no engines, no working copy. Self-install wants the same verb
  a person runs, told that nobody is at the desk.
- Digitization's `check.sh` prints the `sudo …` line for each thing it finds missing. Same stack, other platform.

## What needs an administrator today

| machine | step | asked by |
|---|---|---|
| production | the hosts file | `system hosts.ps1` (MANIFEST), at `fcpm install` |
| production | inbound TCP 8080 for the helm | `fcpm helm grant` |
| production | inbound TCP 9931 for the models | `fcpm model grant` |
| production | inbound TCP 8888 for the Roku relay | `fcpm roku grant`; `grant-pending` in `bay/mediamtx-*.yml` |
| production | inbound block for OBS | `grant-pending` in `bay/obs-portable-*.yml` |
| production | the crew's task | `fcpm crew install` |
| production | the share | `share.ps1 install` |
| digitization | packages, the crew's unit, the landing share, the clock | `check.sh`'s `sudo` lines |

These place something and stay placed: they belong in the stack. `fcpm audit` and `fcpm drobo` also ask for an
administrator, but each run is an act a person chooses, not a state to reach; they stay verbs.

## The shape

1. **A step that waits is a record**, not a line: what it changes, why, the command, and the blob of the script
   that does it. `sync` writes it where it now prints `waiting`; a `grant` verb and a `grant-pending` record
   write the same.
2. **The machine's helm shows the stack as one page**: the count first (`3 waiting on this computer`), each
   item with what it changes, and one button. Nobody wonders whether a second prompt means the first failed.
3. **One action, one prompt.** The stack runs in one elevated script, item by item, the page counting `1 of 3`.
   Windows: one UAC prompt. Linux: one `pkexec`. macOS: one `osascript … with administrator privileges`.
4. **The yes is a staff wizard's reply**, as `wizard:keys+grant` answers a petition ([keystore.md](keystore.md)):
   it names the stack, each item by its blob, through any helm, by QR or `/drop`. A stack is one reply. A
   script that changed since the yes asks again.

## The fork

- **Presence.** The yes comes from anywhere; the click is at the machine (UAC wants a hand there). Nothing new
  stands elevated.
- **An elevated runner.** Something already elevated (the crew's task, once `crew install` has run) carries out
  approved stacks: that one install is the only click. It is a standing elevated process acting on signed
  replies, so the blob and the signature carry the weight.

Presence first: the records, the page and the wizard are the same either way.

## First cut

1. `sync`: a waiting `system` or `held` step writes its record.
2. `fcpm install` unattended (no `FCPM_DESK`), and the crew's `follow` line runs it.
3. The `grant` verbs and `grant-pending` write records too.
4. The helm page: the count and the list, then the button and its one elevated run.
5. The wizard and its reply.

## Open

- Where the records live, per platform.
- What a stack bottled for QR weighs.
- An item that fails partway: the rest go on, or stop.
