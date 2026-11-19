# keychain

FCPM's one keychain for operations. Every key FCPM's operations hold ends up here, and every machine asks here for it. There are
no machines holding keychains of their own. A machine may hold a key for a while (a deploy token in
`~/.config/fcpm/keys/`), but that is a local hold, and it is flushed up here. That is how it works
for every machine; no program chooses to do it. We administer machines that the public uses, so we
decide what each one's canonical key is. A machine's own identity is made here and handed to it.
It is never born on the machine and reported back.

Until FCPM has another box, the origin's box wears it (`names`: the HP t510, [`../thin-client`](../thin-client/PROFILE.md)),
beside [`origin`](../origin/PROFILE.md). The library joins them there. This is the control box: what
every other machine gives up to the controller.

| | |
|---|---|
| `names` | `linux Hostname origin`: `origin.local`, while the origin's box wears it |
| `keys` | the account every holder's key is forced into, through [`door`](door). Its home `/srv/keychain` is the keychain itself |
| holders | [`HOLDERS`](HOLDERS): `office holder key since`. A holder is a job. The box rereads the file from the origin's main every minute ([`run-keys`](run-keys)), so a holder is a line added by merged PR. Offices: `keeper` (inits, unlocks, locks, mints, is handed every protected key) and any other (puts, is handed what is its own) |
| at rest | `held/<group>/<key>/<time>.age`: every version, sealed with age to the keychain's own recipient. `meta.json` beside it records the class, for whom, by whom and when, and a salted print, so the same value put twice is held once. The identity that opens them is `identity.age`, sealed under the passphrase. All of it is ciphertext, safe to copy for backup |
| open | `unlock` opens the identity into memory (`/dev/shm/keychain`) until the box restarts or `lock`. Putting needs no unlock (sealing takes only the recipient), so flushing works while it is locked. Handing out needs it unlocked |
| log | `/srv/keychain/actions.ndjson`: every put, get, refusal, mint, unlock and lock, with the holder |
| tests | `bin/test_keychain_door.py` (needs age; the box has it) |

## Protected and secret

When a key is put or made here it is one of two classes. Nothing has to decide: it is `protected`
unless someone says `secret`.

- **protected**: the one who made it has it already. The keychain hands it to a keeper, back to
  its maker, and to any holder whose job's `keys.yml` names its group (on the origin's main). A deploy
  token is protected.
- **secret**: lodged for one holder, and handed to that holder only. Its maker never gets it back,
  a keeper included. A machine's ssh identity is secret: `mint ssh editing-bay-2` makes it here,
  prints the public half, and keeps the private half for editing-bay-2 to ask for.

## From a machine

`fcpm keys` (machines/keys) is the same on every machine:

    fcpm keys take G K        stores it here and flushes it up at once
    fcpm keys flush           every key held here, up (the crew's `flush` line does it every 15 min)
    fcpm keys run G -- CMD    a key not held here comes from the keychain, into CMD's environment only
    fcpm keys keychain        its state and what it holds, never a value
    fcpm keys init | unlock | lock     a keeper's; the passphrase in a window on this screen
    fcpm keys mint ssh FOR    a keeper's

A machine reaches the door as `~/.ssh/config`'s `fcpm-keychain` (`keys@origin.local` by its own key).

## A secondary keychain: projects

Keys for public-run projects (work FCPM supports for others, such as Layers for Spirit Crossing
Clubhouse's sister clubhouses) are kept apart from operations. Nothing about them mixes: they have their own
store, passphrase, holders and ledgers, and the same door serves them.

| | operations | `projects` |
|---|---|---|
| account, store | `keys`, `/srv/keychain` | `projects`, `/srv/keychain-projects` |
| holders | [`HOLDERS`](HOLDERS) | [`HOLDERS.projects`](HOLDERS.projects) |
| a job's ledger | `machines/<job>/keys.yml` | `machines/<job>/keys.projects.yml` |
| from a machine | `fcpm-keychain` | `fcpm-projects` (`projects@origin.local`) |
| making, opening | `fcpm keys init`, `unlock` | `fcpm keys init projects`, `unlock projects` |
| installing | `install fcpm@origin.local` | `install fcpm@origin.local projects` |

`take`, `offer`, `run` and `flush` find a group's keychain from the ledger it is in. `backup` and
`proof` are operations' only for now.

## Installing it

    machines/keychain/install fcpm@origin.local       outfits it; touches nothing held
    fcpm keys init                                   once: makes the identity under a keeper's passphrase

After a power cut the keychain comes back locked. Puts still land. A keeper's `fcpm keys unlock`
opens it again, the same as the signing key needs the board's Unlock after a reboot.

## The one place it fails, and the backup

The keychain is the one thing every line and every credential depends on: a single point of failure,
taken on on purpose as the foothold. What keeps it from being the end of everything is that all of
it is ciphertext but its salt, so a copy is safe anywhere. Only the passphrase opens it.

    fcpm keys backup [DIR]      the whole store as one dated tar (default ~/.local/state/fcpm/keychain)
    fcpm keys proof FILE        opens it here with the passphrase, as a new box would, and checks every key
                                against its print without showing one

A backup to the card is a canonical act, done rarely and on purpose. Run `proof` on the copy before
calling it one.

**Restoring, and what a rollback costs.** A box that will wear the keychain gets the outfit, then
the tar unpacked into `/srv/keychain` as `keys`, then a keeper's `unlock`. Restoring a backup
older than the live keychain rolls it back to that day:

- a key put since is gone from the keychain, but not from the machine that put it. Its next flush puts it back;
- a secret lodged since is gone for good. An identity minted since is minted again, and its public
  half changes, so its `KEYHOLDERS`, `HOLDERS` and pile `allowed_signers` lines change with it;
- a key replaced since comes back at its old value, though the newer one may already be the only one
  that works. Rotate it again;
- the log (`actions.ndjson`) ends at the backup. What came after is known only from the machines' own logs.

`held/` only ever gains versions, so a newer backup holds everything an older one does.

## Not built yet

- **Delivery, through the data pile.** Nothing is handed out by a code carried between computers, a
  card, or an account that answers without a key. A lodged secret is sealed to the asking machine's own
  key and set down in a data pile that machine listens on, by tell; the library's LAN-only branches at the
  origin carry it. A new machine's first key comes the same way, from the machine provisioning it. Bay 1's
  identity (`identity-production`, minted 2026-11-17) waits here for that.
- **Moving digitization's raw files** (Cablecast, YouTube) behind `keys run` like the env groups.
- **The library** on this box. Transcripts and notes, in wings: one per engine or concern, and
  branches that hold more aisles and are never merged. A resident's scratch space is outside git
  altogether. It needs storage the box can lose without losing itself: a card or SSD in one of the
  t510's inside USB sockets. The flash has 400 MB free.
