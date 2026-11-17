# The LAN's lines

How FCPM's machines tell each other things: by data piles, never by an SSH login, a code carried
between computers, or a card. A line is one way, a tell and not a conversation: one machine
writes, one reads. Two machines that talk both ways have two lines.

Everything here stays on the LAN. The origin holds it (`retain/` is never carried to GitHub,
[`../machines/origin/intake`](../machines/origin/intake) `LAN_ONLY`), and the origin is the gate.

## Where it lives proves nothing

The origin is where we meet, not what we trust. A pile is good wherever it is found: on the origin, on a
neighbor, carried across the QR air gap, or fetched over plain HTTP. Its keyholders, its shape and the
hook that plays the shape are signed into it, so a reader plays the origin's own rules on what it
fetched (`lines-gate --check`) before it opens anything. What the origin centralizes is provisioning:
minting an identity, first contact, a person's yes. A machine once provisioned acts as itself: it
keeps its keys, checks for itself, and with the origin away fetches from any neighbor's copy
(`lines/<name>/serves`). Writes wait for the origin. Nothing here is secret but what is sealed:
the branches, the pins and the keyholder lists are plain.

## The slice: `retain/lines`

One branch every machine shares, in fcpublicmedia.org at the origin. Each machine writes only its own
folder, so pushes never collide:

    lines/<me>/reader.age.pub     what a pile to me is sealed to (age)
    lines/<me>/signer.pub         the key my commits are signed with (ssh)
    lines/<me>/out/<reader>       the pile I tell <reader>, pinned where I last told
    lines/<me>/in/<writer>        the pile <writer> tells me, pinned where I last read
    lines/<me>/serves             where my copy of all of it can be fetched, read-only

Each line shows twice, once from each end. The writer's pin is what was sent and the reader's is what
was read: the gap is what waits, and the time between them is the delay. The pins are gitlinks,
so a pile keeps its own history. A rotation is a new pile beside it and a new pin, and nothing anyone
holds is rewritten.

## A pile: `retain/pile/<writer>.<reader>`

data-pile's drop channel ([`.pile-engine`](https://github.com/FCCN-ANTIBODY/data-pile)): each entry
sealed to the reader's age key, the manifest signed by the writer's ssh key, entries in time order with
the time each entered. The writer bears it, and it is born with, all signed in:

| | |
|---|---|
| `keys/allowed_signers` | its keyholders: the writer and the reader, as `<name>@lines.fcpublicmedia.local` |
| `keys/drop.signers`, `keys/pile.age.pub`, `pile.yml` | data-pile's: who signs the manifest, who it is sealed to |
| `shape/hears` | the channels the reader hears on it, one a line. Empty at birth: it hears nothing |
| `hooks/admit` | the hook that plays the shape ([`../machines/pile-admit`](../machines/pile-admit)) |

The reader changes what it hears by its own signed commit to `shape/hears`, and nothing else. The
writer's commits only add entries, each naming its channel (`Tell-Channel: C`). A new generation
(`.g2`) is a new pile, born again.

## The gate

[`../machines/origin/door-hooks/lines-gate`](../machines/origin/door-hooks/lines-gate) runs on every
push through the origin's door, which now tells it the pusher. It takes:

- on `retain/lines`, a push that changes only the pusher's own folder;
- on a pile, commits that are each signed by a keyholder the pile names and pushed by that same keyholder;
- from the writer, only new entries, with every earlier one untouched. The pile's own `hooks/admit`
  admits each one, played from the pile as it stood before. Then data-pile's `verify` must pass;
- from the reader, only `shape/hears`.

The shape is part of the signed payload, so what a pile refuses is something its keyholders signed.
Tests: `bin/test_lines.py`:
- a pile that hears nothing, then one shape, then an answer back;
- another machine's folder, and a push by someone who did not sign;
- a read from a neighbor's copy with the origin away;
- a forged pile, refused by the reader's own check.

## On a machine

    fcpm lines                          every line: told and read, waiting, what it hears
    fcpm lines reader                   once: my reader key (kept in ~/.local/state/fcpm/lines) and signer, published
    fcpm lines hear WRITER CHANNEL...   what I hear on WRITER's pile to me
    fcpm lines tell READER CHANNEL FILE...
    fcpm lines read WRITER              checked here, then into the workshed (~/.local/state/fcpm/lines/workshed), never a tracked tree
    fcpm lines serve                    my copy, as files: lines.<host>.fcpublicmedia.local (lan.yml `lines: true`; the crew's `lines` line)

A first tell bears the pile and is refused, because the reader hears nothing yet. Once the reader says
what it hears, the next one lands. A machine needs `age`, `jq`, `openssl` and `bash`.

## Not built

- A machine with no key yet: its first line comes after its reader key and signer are published, by
  the machine provisioning it.
- Bay 1 on Windows: Git Bash with `age.exe` and `jq.exe`, or a port.
- Helm telling, tell's neighborhoods, and the atlas that says which pile listens where.
- The keychain delivering through a line (Bay 1's minted identity waits for it).
