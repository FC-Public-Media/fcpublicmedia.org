# static

Static serves finished sites to the LAN, each under the names a machine's `lan.yml` gives it, and
hides any build step behind them. It writes nothing and holds no keys: a site is a folder of files.

| file | |
|---|---|
| `names` | who wears the job: `digitization` today |
| `sites.yml` | the port, and each site: its folder, and its `build` when it has one |
| `serve.py` | the server, by Host: the file, then `.html`, then `index.html`; else the site's `404.html` |
| `site-build`, `site-lan.yml` | the public site from `site/` by Debian's Jekyll when the commit moves (`site every 5m`) |
| `services` | `site every 5m`, `serve keep` (menu `../static.yml`), kept by `fcpm-crew@static` |
| `check.sh` | Jekyll, the supervisor, the build, the Wix checkout, each name served and forwarded |

| site | names (digitization's `lan.yml`) | folder |
|---|---|---|
| `site` | `fcpublicmedia.local`, `www.fcpublicmedia.local` | `~/.local/state/fcpm/site/current`, built |
| `wix` | `wix.fcpublicmedia.local` | `wix/site`: the Wix site, photocopied ([FC-Public-Media/wix](https://github.com/FC-Public-Media/wix)), served as it sits |

A machine takes the job by its `names` line and `crew.sh install static`. `serve` listens on
`sites.yml`'s port, whatever else the machine runs; whatever owns port 80 there forwards the names to it.
On digitization that is the door (`../kiosk/door.py`).

Everything is served here first. A site goes to the cloud only once it is right on the LAN, and
it goes from here.
