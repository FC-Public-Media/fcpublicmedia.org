# The keystore

How an FCPM machine comes by its keys, with no operator in the path. A machine's own key is born on
it and lodged with the keystore; a real secret (a token, a stream key) sits sealed there. Either way a
board wizard grants it. Built: birth and its petition (`fcpm keys birth`, `wizard:keys+birth`); the
keystore's grant is a design. The keychain's ledgers: `machines/<job>/keys.yml`, read by `machines/keys`.

## Birth

A machine makes its own key, once, and its private half never leaves it. On Windows the OpenSSH
agent holds the private half, a service that keeps it across restarts, and no file does. On Linux it
is `~/.ssh/fcpm-<job>`, mode 600, on the card's encrypted home. The public half, `~/.ssh/fcpm-<job>.pub`,
is shown as text and as a QR code. It is safe to show anyone.

Nobody carries it. The same verb sets a petition down at the machine's own helm, once
(`wizard:keys+birth`, docs/kiosk.md). Helms pass a reply to the one that holds its wizard, and the
keystore's helm holds this one: digitization's, until the keystore is a job of its own. There it is
lodged as `petitions/<nonce>.json` beside the replies, inert. Lodging grants nothing. No operator
may grant it, a session included.

The grant is the keystore's act, once a board wizard says yes through the QR inbox. It puts the
public half into `machines/origin/KEYHOLDERS` (origin.local, by its office), and onto fcpm-public as
that machine's signing key. The merge of that line is the board's signature on the birth certificate,
and emptying the line by another merge takes it back. Nothing secret moves at any step. Not built:
the grant itself, and the wizard that says yes.

The first agent-held key on Windows asks an administrator once to turn the agent service on.
Windows ships it off. Git's own ssh does not talk to that agent, so a checkout that fetches by this
key sets `core.sshCommand` to `C:/Windows/System32/OpenSSH/ssh.exe`.

## The keystore (design)

The secrets FCPM holds (`keys.yml`: Stripe, Cloudflare, Cablecast, YouTube, Microsoft 365) live today
as files on the machine that uses them. The keystore is where they go instead, as a job of its own:

- **Inert at rest.** Every value is sealed with age. What the keystore keeps is ciphertext, safe to
  back up and to move to a new profile, which is how a move is proved. The identity that opens it is
  the one live thing, and it stays locked.
- **Not the origin.** The keys do not sit beside the source. The keystore is its own name on the LAN,
  `keystore.local`, whose only page asks for an unlock. It may start on digitization, but as a
  job that can be moved.
- **Unlock is an escalation.** A request comes in through the QR inbox, and a board wizard signs it,
  by passkey, the way a publishing device approves another (docs/identity.md). It can take two
  steps. First the wizard says "I am here", so the keystore knows an answer will be timely. Then the
  real request comes while the phone is still in the cradle. The store opens for that one request
  and closes again.
- **Delivery is sealed to the one who asked.** A value is sealed to the asking machine's own key, the
  one from its birth. So it can travel by any road (the inbox, the repository, the share) and only that
  machine opens it. A secret can be lodged to be delivered once and then gone, like `keys offer`'s
  one-time page.
- **Act rather than hand over.** Where the keystore can do the thing itself, it does, for example
  registering a newborn's signing key on GitHub. The secret then never leaves it.

Open: what holds the keystore's own identity while it is locked. Also open: a Windows bay's age
identity. The agent signs with an ed25519 key but will not decrypt with one, so a bay needs a second
key, which Windows protects (DPAPI). And the talk-back screen: a reply to the phone that is still in the cradle.

## The grant: a study for digitization to build

Written on bay 1 on 2026-11-10 for the job that holds the keystore, digitization for now, to
build and run. Bay 1 built birth and the petition (#411, #412). Everything below is digitization's to
build, in this order. Each step stands on its own, and each is to be revised where the machine says
otherwise.

1. **Read the petitions.** They wait in the helm's state, `petitions/<nonce>.json` beside the replies
   (`~/.local/state/media-node/replies/` on Linux). Each holds `job`, `host`, `key` (one ssh-ed25519
   line), `issued`, `at`, `trust` (`unsigned`: a machine's petition carries no phone's signature), and
   `lodged`. A verb that lists them, a fingerprint each (`ssh-keygen -lf`), is the first piece, and
   the helm's inbox page can show them as waiting.
2. **The yes: `wizard:keys+grant`.** `{petition: <nonce>, fingerprint: "SHA256:…"}`, shown in the
   cradle from a board member's phone. Unlike `kiosk+host` or `model+up`, being on the studio's
   network is no authority here. The handler applies only `trust: friend` (a phone named by
   `replies.py trust`) and holds anything else, saying why. Its `issued` must be minutes old, not
   the day `SKEW` allows. The fingerprint must match the petition's key, so the yes names exactly
   what it grants. The two-step form ("I am here", then the yes while the phone is still in the cradle)
   is a later tightening; one signed, fresh reply is the first form.
3. **The acts**, by the keystore itself, never by a session:
   - **Signing key.** `POST /user/ssh_signing_keys` on fcpm-public, titled `<host> (<job>) commit
     signing`. Bay 1's is "EDIT2 (Bay 1) commit signing". The token is a keychain group of its own, say
     `github-signing`, holding one classic token with only `admin:ssh_signing_key`. It is issued by
     the board and listed in `machines/digitization/keys.yml` like the others.
   - **KEYHOLDERS.** One line, `<office> <job> <key type> <key> <date>`, committed on a branch
     pushed to origin.local by digitization's own keyholder key, and opened as a PR for the board
     to merge. The merge stays the grant of origin access. Which office a bay holds is the board's
     to name; today's offices are `secretary` and `workstation`.
   - **Record.** The petition moves to `granted/` with the GitHub key's id and the PR. Revoking deletes that
     key by its id and empties the line by another PR.
4. **The bay, after the merge.** Its checkout fetches by the new key: `core.sshCommand` set to Windows'
   OpenSSH (Git's own ssh does not reach the agent), and the remote set to
   `git@origin.local:FC-Public-Media/fcpublicmedia.org`. That is the change bay 2's `follow` waits for.
   It is machine-side, so it belongs in `fcpm keys birth`'s next run or in `sync`, never in a person's hands.
5. **Then the keystore proper** (the design above). The keychain's values are sealed with age.
   `keystore.local` is the only page. An unlock is the same signed, fresh yes, sealed to the asking
   machine's birth key. The first test of a move is to move the keystore off digitization onto another
   profile and still unlock it.

Known on 2026-11-10: bay 2 (FCPMEDIT2) has not yet run `fcpm keys birth` against its real agent, so no
petition has been lodged yet. `bin/test_keys.py` and `bin/test_helms.py` cover birth and lodging.
`bin/test_replies.py` needs Node, which bay 1 lacks.
