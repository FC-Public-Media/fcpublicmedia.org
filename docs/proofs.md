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
tree cb6a556e7283...                       the tree tested: what a deploy builds
made main 3b0dd62... with 1a2b3c... merged as landing merges
ordered land some-branch 1a2b3c... by tiliv at 2026-11-24T23:00:00+00:00
checks .github/workflows/smoke.yml blob 9f0e..., main's
by dj, machines/proof.py at 41397f2..., steps run as proof
on Debian GNU/Linux 13 (trixie), Linux 6.12..., x86_64
tools python 3.13.5, git 2.47.3, ruby 3.3.14, bundler 2.6.7, node v22.23.5, npm 10.9.9
started 2026-11-24T23:21:14Z
given actions/setup-node@v4 {"node-version": "22"}: by dj's own tools (above)
step 1 passed 21.4s exit 0 sha256 5e3c... 1200B Build the site
...
skipped 23 Check embeds and outbound links (if: github.event_name == 'schedule' || ...)
finished 2026-11-24T23:27:40Z
result passed 22 of 22
-----BEGIN SSH SIGNATURE-----
...
```

- **The tree, not the commit.** A deploy builds a tree. A branch ordered to land is tested as main with the branch
  merged the way the origin's landing merges them (`merge-tree` by main's own attributes), so once it lands, its
  proof is the proof of main's tree.
- **The checks are the tree's own.** The steps come from the workflow file the tree carries (for
  fcpublicmedia.org, the smoke workflow GitHub runs), in order. `uses:` steps are the runner's setup: the proof
  says they were given by DJ's own tools and names their versions. A step with `if:` is skipped and said so.
  The first failed step stops the rest, as on GitHub. `checks` says whether the file is main's: a branch that
  changed its own checks says so.
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
Its `sudo` is [a stand-in](../machines/dj/proof-shims/sudo) that raises nothing: a step asking for system packages
passes when they are installed already and fails naming the ones that are not (they go in
[`machines/dj/gear`](../machines/dj/gear)).

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

Not built: Helm showing proofs; a deploy or a landing that waits for one; member material (stapled manifests).
