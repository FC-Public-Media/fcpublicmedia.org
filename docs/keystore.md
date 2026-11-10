# The keystore

How an FCPM machine comes by its keys. There are two parts. A machine's own key is born on the machine, and a merge grants it. A
real secret (a token, a stream key) sits sealed in the keystore, and a board wizard unlocks it for one
delivery. Only birth is built (`fcpm keys birth`); the keystore is a design. The keychain's ledgers:
`machines/<job>/keys.yml`, read by `machines/keys`.

## Birth

A machine makes its own key, once, and its private half never leaves it. On Windows the OpenSSH
agent holds the private half, a service that keeps it across restarts, and no file does. On Linux it
is `~/.ssh/fcpm-<job>`, mode 600, on the card's encrypted home. The public half, `~/.ssh/fcpm-<job>.pub`,
is shown as text and as a QR code. It is safe to show anyone.

A PR grants it: the public half goes into `machines/origin/KEYHOLDERS` (origin.local, by its office),
and onto fcpm-public as that machine's signing key. The merge is the board's signature on the birth
certificate, and emptying the line by another merge takes it back. Nothing secret moves. A person
at the desk runs one verb and merges one PR, and never handles an SSH key.

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
