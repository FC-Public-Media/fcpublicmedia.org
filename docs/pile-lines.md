# Lines on a pile: masked metadata, signed by whoever x-rayed it

A design, not built. A data pile seals content. A line is the honest metadata that sits beside each
sealed entry. Some of it is shown, some is masked, and it is signed by whoever x-rayed the content.
This is a petition-shaped draft for [data-pile](https://github.com/FCCN-ANTIBODY/data-pile). It
extends that repository's drop channel (`docs/transfer.md` B), and it needs no change to what
`bin/verify` already checks.

## Why

The library keeps metadata without moving files ([library.md](library.md)). Some files should not
wear their metadata in a pile of mixed-privilege documents, but their metadata must not be lied about
either. So the content goes into a pile and leaves the holding. The line stays in the open: true,
partly masked, and signed. The pile entry is also the proof of when we held that exact file, whatever
it is. That is the reason to pile anything at all.

## The pieces

**The shape** is the pile's declaration of which lines it wants and how each one is shown. A pile
already "holds the shape of what it is looking for". This writes that shape down:

```yaml
# pile.yml
lines:
  schema: fcpm.xray/v1            # the x-ray's own columns: path kind bytes modified created attrs, sha256
  shown:  [kind, bytes, modified] # kind is the floor: a simple reader could prove it from a title or header
  masked: [path, sha256]          # a commitment shows; the value is sealed
  sealed: [created, attrs]        # inside the block only
```

The shape is hashed, and each entry carries the hash of the shape it was admitted under. A shape can
change later without turning old entries into lies.

**The line** is a new `line` field on the drop manifest entry. It is plaintext, so the head digest
already covers it:

```json
"line": {
  "schema": "fcpm.xray/v1", "shape": "sha256:…",
  "kind": "pdf", "bytes": 912344, "modified": "2024-08-29",
  "path": "mask:sha256:…", "sha256": "mask:sha256:…",
  "sig": "…"
}
```

**The mask** of a field is `sha256(salt_f ‖ field ‖ value)`, where `salt_f = HMAC(salt, field)` and
`salt` is one random value per entry, kept inside the sealed block together with the unmasked line.
Anyone who opens the block can check every mask. Outsiders can't guess their way in by trying likely
paths, because of the salt. Revealing one field means revealing only that field's `salt_f`, a new
`bin/prove --field` disclosure, so the other fields stay sealed. Whether the content's sha256 (the
key that joins libraries) is shown or masked is the shape's choice. For a public city agreement,
show it. For the attic, mask it: a shown hash tells anyone holding the same file that we hold it too.

**The signature** says the line is true. It is the x-ray-er's SSH signature, under its own namespace
`data-pile-line` so it can never be replayed as a drop or feed signature. It covers the canonical
line without `sig`, the entry's `this_hash`, and the shape hash. It means: "I read the plaintext of
this block, and these lines are true of it, under this shape." That is a different claim from the
manifest head's, which only vouches for order. The sender and the x-ray-er may be different machines.
The pile checks the signature against `keys/line.signers`. A signature from an unknown signer is
recorded for a later trust decision, never trusted, by the same rule as `keys/drop.signers`.

## Hooks, and listening only for your own

The drivers are git hooks. What a hook must not do is look at everything that arrives and refuse
everything that isn't for its user id. That is work in proportion to all traffic, to accept a
statistical sliver of it. The address goes where git already indexes it, so a hook is handed only
its own:

- **The address is the path (or the ref), never the content.** A line for a recipient lives at
  `lines/<id>/…` on `retain/lines`, or on its own ref. A hook reads `git diff-tree` over the pushed
  range with the pathspec `lines/<id>/`. Git does the filtering, and nothing is decrypted or scanned
  to learn who an entry is for.
- **One dispatcher, not one guard per pile.** On the origin, a single post-receive takes the updated
  refs and paths and hands each recipient's slice to that recipient's pile. Nothing is refused for
  being someone else's: it just isn't handed over.
- **Admission is the shape check, at the recipient.** A pile's hook refuses only its own entries
  whose line doesn't match its shape or whose signature doesn't verify. That work grows with what
  was addressed to it.
- **A read marker is a ref.** "Lines moved like read markers": a recipient's marker is a ref it
  advances once it has read up to a commit. Whatever lies between the marker and the tip is the
  queue. A jammed queue is a marker that stopped moving while the tip went on. That is how an
  observability account finds a jam without reading any entry: it compares marker to tip, and x-rays
  only the lines, never the blocks.

## Who does what

| | where | does |
|---|---|---|
| ours | `fcpm library` | reads the pile's shape, makes the plaintext block (file bytes, unmasked line, salt), masks, signs the line, hands it to `drop-pack` |
| data-pile | `bin/drop-pack --line` | puts `line` on the entry |
| data-pile | `bin/verify` | checks the line's shape hash and its signature against `keys/line.signers`, without the block |
| data-pile | `bin/verify` with `Kb` | opens the block and checks every mask against the sealed line |
| data-pile | `bin/prove --field` | reveals one field's `salt_f` and value |
| origin | post-receive | dispatches by path to each recipient; advances nothing on anyone's behalf |

Once a file is piled, its `retain` note cites the pile entry (pile id and seq) and the line, and the
holding can let the file go.

## Open

- Which key bay 1 signs lines with. It needs its own, not `fcpm-public signing`, which signs commits.
- Whether `kind` is always shown, or only when the shape shows it. Even a kind can say something
  ("keychain").
- Whether `retain/lines` keeps one branch with paths per recipient, or a ref per recipient. Paths
  keep a single history. Refs let git's own ref advertisement do the routing.
- Bay 1 receiving its own identity this way: its line points at an entry wrapped to a key it already
  holds (age accepts an ssh-ed25519 recipient), which only it opens. What it unwraps goes into
  Credential Manager.
