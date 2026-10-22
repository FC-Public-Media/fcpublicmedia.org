# static

Static serves finished sites to the LAN, each under the names its host's `lan.yml` gives it, video and
all. It holds no keys and builds nothing: a workstation builds a site and pushes it; the static host
takes the push and serves it. One job on its own box (decided 2026-10-21): its disk holds the sites.

| file | |
|---|---|
| `names` | who wears the job: `static` (the host, its own box); `digitization` until static.local serves |
| `sites.yml` | every site, where it is served (`serve`: a LAN name, or a path under one), and how a workstation makes it (`build` and `from`; `root`; `export: owner/repo`; none: its own project pushes it) |
| `lan.yml` | the names the host holds by mDNS: `fcpublicmedia.local`, `www.`, `wix.`, `you.`, `nccv.you.` |
| `nginx-host.conf` | the host's port 80: a name with a site is files, by Host (the file, `.html`, a folder's `index.html`, the site's `404.html`), with Range, ETag and gzip, and `frame-ancestors 'self'` (the one CSP part a page's meta cannot say); a member's site is a name of its own (`nccv.you.fcpublicmedia.local`) or a path under `you.` |
| `receive` | the host's deploy door, forced on every key of its `deploy` account: rsync into a hard-linked copy of what is up (only what changed crosses; 260 bytes for a one-page change on a 50 MB site), then `current` flips; the one before stays. A key pushes only its sites. `receive status` on its screen |
| `KEYHOLDERS` | who may push which sites: `sites holder key since`; `*` or `nccv` or `site,wix`. A line by merged PR, then `install fcpm@static.local` |
| `deploy` | a workstation's push: `fcpm deploy SITE DIR` |
| `publish.py`, `site-build`, `site-lan.yml` | a workstation's side: each site that moved, built (Jekyll, only when `site/` or this folder has a new commit), copied, or exported, then pushed. `follow` runs it each pass; what did not move costs nothing but a fetch from the origin |
| `outfit`, `install` | the host, on Alpine: `install root@HOST DISK SERIAL` from a lan card's live system puts Alpine on the box's own disk and outfits it; `install fcpm@static.local` outfits it again |
| `install-debian`, `nginx.conf` | digitization's nginx in front of its door, from when it served the sites itself; it goes when digitization releases the job |
| `check.sh` | the Debian side's gear, nginx, each site published and served |

| site | served at | made by |
|---|---|---|
| `site` | `fcpublicmedia.local`, `www.fcpublicmedia.local` | a workstation, from `site/` |
| `wix` | `wix.fcpublicmedia.local` | a workstation, `wix/site` as it sits ([FC-Public-Media/wix](https://github.com/FC-Public-Media/wix)) |
| `nccv` | `nccv.you.fcpublicmedia.local`, a host root of its own (absolute paths; a passkey binds to an origin) | exported: NCCV-OPINION/platform's main as committed, from the origin by `git archive`, so its private mounts come out empty; nothing is built. `bin/take` stays on NCCV's operator's machine |

Everything is served here first. A site goes to the cloud only once it is right on the LAN, and
it goes from the workstation that built it.
