# Proofs

A proof is a signed statement that a tree was tested and what the tests said. It is one text file that makes
sense with nothing else at hand: whoever picks it up can check who signed it, which tree it is about, which
checks ran, where, and how each went. A tree with a good, passed proof is safe to deploy.

DJ makes them ([`machines/dj/proves`](../machines/dj/proves), crew line `proofs`); [`machines/proof.py`](../machines/proof.py)
makes, keeps and reads them.

## What one says

```
fcpm proof 1
repo FC-Public-Media/fcpublicmedia.org
tree 093c966c5e9e...                       the tree tested: what a deploy builds
made main 3b0dd62... with 86e662f... merged as landing merges
ordered land proofs 86e662f... by tiliv at 2026-11-24T23:00:00+00:00
checks .checks blob 9f0e..., main's
by dj, machines/proof.py at 86e662f..., steps run as proof
on Debian GNU/Linux 13 (trixie), Linux 6.12.118+deb13-amd64, x86_64
tools python 3.13.5, git 2.47.3, ruby 3.3.14, bundler 2.6.7, node v22.23.5, npm 10.9.9
started 2026-11-24T23:24:02Z
step 1 passed 1.0s exit 0 sha256 9077... 386B Build the site
step 2 passed 0.2s exit 0 sha256 59b1... 1751B Test the calendar parser
...
finished 2026-11-24T23:25:31Z
result passed 44 of 44
-----BEGIN SSH SIGNATURE-----
...
```

- **The tree, not the commit.** A deploy builds a tree. A branch ordered to land is tested as main with the branch
  merged the way the origin's landing merges them (`merge-tree` by main's own attributes), so once it lands, its
  proof is the proof of main's tree.
- **The checks are the tree's own.** [`.checks`](../.checks) at the repository's root, read in one look like
  `.issues`: a line each, `name: command`, run in order from the root by bash; the first that fails stops the rest.
  `checks` says whether the file is main's: a branch that changed its own checks says so. GitHub has no part in
  it: its workflow files are not read.
- **Each step** has its time, exit, and the sha256 and size of everything it printed. A failed step's last 64 KB
  are kept beside the proof (`<when>.step-<n>.log`).
- **`result`** is `passed N of N`, `failed at step K, ...`, or `untested: <why>` (no checkout, no steps).
- **The signature** is `ssh-keygen -Y sign`, namespace `fcpm-proof`, over every byte above it.

## Who may sign

A holder whose folder has a `proves` file (`machines/<holder>/proves`, `owner/repo checks-file` a line), by its key
in [`machines/origin/KEYHOLDERS`](../machines/origin/KEYHOLDERS). A proof verifies only when its signer is such a
holder, its `by` names that signer, and its `repo` is one the signer proves. Nothing else is trusted: not the
file's place, not the branch it sits on.

The steps run as the user `proof`, which has no sudo and cannot read DJ's keys, so nothing a test does can sign.
What the checks need from the system (Jekyll, Node 22, the browser's libraries) is put there by
[`machines/dj/gear`](../machines/dj/gear), never by a check.

## Where they are

On the tested repository's `retain/proofs` branch on the origin, at `<tree>/<when>.proof`. Like every `retain/`
branch it stays on the LAN. DJ also keeps each one in `/srv/proof/made/` before pushing.

## When DJ makes one

Every minute (`proof watch`): each repository DJ proves is fetched from the origin; every order waiting to land
(the origin's `look`) is tested as it would land, then main itself. A tree is tested once: a proof of it, passed
or failed, is the answer, and a failed one is not run again by itself. By hand: `machines/proof.py run REPO REV
[TIP]` tests again.

## Reading them

- `python3 machines/proof.py for [REV]` in a checkout: fetches `retain/proofs`, finds every proof of REV's tree
  (HEAD unless named), verifies each, and exits 0 only when one is good and passed.
- `python3 machines/proof.py verify FILE` checks one file.

## Members

A member's code is tested on DJ the same way and gets the same kind of proof, with what is theirs said so.

- **Who may ask.** [`machines/dj/members`](../machines/dj/members), `name source env` a line, written by staff. `source`
  is wherever the member's code lives (their origin, any git URL); DJ fetches from it only when a test is asked for.
- **What is tested.** Their tree's own `.checks`, same format as ours.
- **Their environment.** Staff's branch `retain/env/<env>` on fcpublicmedia.org's origin, one file `env`, read by every
  run in a batch: `network none` (the only tier built), `apt PKG...` (installed on DJ by `prepare`), and `shelf SHA256
  SIZE NAME by WHO at WHEN` lines. Members never write it.
- **The shelf.** A large file a member provides is accepted by staff (`stage`): kept on DJ once, by sha256, in
  `/srv/proof/store`, and linked read-only into `/srv/proof/shelf/<env>/` (`$FCPM_SHELF` in a check). Everything on an
  environment's shelf is visible to every member on it, like a makerspace's: a build uses what its scripts name.
- **Their space, kept warm.** Each member has their own user `proof-<name>` and space `/srv/proof/members/<name>`:
  the checkout (`work/`, updated in place, untracked build output kept) and their caches. The proof says `space warm
  since WHEN, run N` (or `new`).
- **No network.** Each check runs in [`machines/dj/sandbox`](../machines/dj/sandbox): a network of loopback only, as
  their user, below the stream (CPU weight 20, 16 GB). Names are looked up only through its resolver and proxy
  ([`trap`](../machines/dj/trap)), which answer nothing and write down every name asked: the system's resolver, mDNS
  and D-Bus sockets are hidden there, since each would look a name up outside; the proof lists them, `wanted dns repo1.maven.org x14`, so a failing run
  still says what it reached for. What they need arrives staged, by staff.
- **The proof** has `member NAME`, `repo SOURCE`, the env's branch commit, its packages and their versions, and the
  space line. It verifies only when the signer's `members` file grants that name at that source. Kept on
  fcpublicmedia.org's `retain/proofs` under `members/<name>/<tree>/`.

Staff, on DJ, from `~/code/work/fcpublicmedia.org`:

```
python3 machines/proof.py env plain network none           # make or change an environment
python3 machines/proof.py env minecraft apt openjdk-21-jdk-headless
python3 machines/proof.py stage minecraft ~/server.zip bedrock-server.zip tiliv
python3 machines/proof.py member sample retain/member-sample    # test a member's code at a ref
```

Not built: Helm showing proofs and taking members' requests; a deploy or a landing that waits for one; the static
server tier; payloads (a member's code is a git ref today).
