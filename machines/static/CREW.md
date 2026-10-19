# static

Static serves finished sites to the LAN, each under the names a machine's `lan.yml` gives it, and
hides any build step behind them. It holds no keys: a site is a folder of files, and nginx serves it.

| file | |
|---|---|
| `names` | who wears the job: `digitization` today |
| `sites.yml` | each site: its folder (`root`), or its `build` and what it is built `from` |
| `nginx.conf` | port 80: a name with a site is files, by Host (the file, then `.html`, then a folder's `index.html`; else the site's `404.html`), with Range, ETag and gzip; any other name goes to the door on loopback :8081 |
| `publish.py` | each site that moved into `/var/lib/fcpm/sites/<site>/<rev>`, `current` flipped to it, and a `by-name/<name>` link per LAN name. Run by `install` and by `follow` when it moves the checkout; nothing polls |
| `site-build`, `site-lan.yml` | the public site from `site/` by Debian's Jekyll, only when `site/` or this folder has a new commit |
| `install` | nginx-light, `nginx.conf` as Debian's one site, the sites' folder, a first publish (sudo) |
| `check.sh` | the gear, nginx's config and port, each site published, each name served, Range answered |

| site | names (digitization's `lan.yml`) | published from |
|---|---|---|
| `site` | `fcpublicmedia.local`, `www.fcpublicmedia.local` | `site/`, built |
| `wix` | `wix.fcpublicmedia.local` | `wix/site`: the Wix site, photocopied ([FC-Public-Media/wix](https://github.com/FC-Public-Media/wix)), copied as it sits |

A machine takes the job by its `names` line and `sudo sh machines/static/install`. Port 80 is
nginx's; whatever held it moves behind it (on digitization, the door: `../digitization/at-login`).
A site is never down because the door is: the door bounces on every commit, nginx does not.
A new site is a `sites.yml` entry and a `lan.yml` name; nginx.conf does not change.

Everything is served here first. A site goes to the cloud only once it is right on the LAN, and
it goes from here.
