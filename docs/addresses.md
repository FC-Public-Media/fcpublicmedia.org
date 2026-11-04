# Addresses

The front doors, from any computer of ours (a personal one, such as Autumn's iMac, included). Short on
purpose: learn the pattern, not the list. Checked 2026-11-04.

**The pattern.** In the building, every job has a name under `fcpublicmedia.local`, and `helm` is the board.
Away, there is one number: digitization's tailnet address. On the internet, the site is `fcpublicmedia.org`.

## In the building (Helm, 10.209.1.x)

Macs and iPhones resolve these names as they are. Linux needs `mdns.allow` (machines/digitization/check.sh).

| address | what |
|---|---|
| `helm.fcpublicmedia.local` | **the board**: the door's switches, the screens, fcpm's verbs |
| `helm.fcpublicmedia.local/ask/` | ask the model, as a code for the camera |
| `helm.fcpublicmedia.local/loop/` | the public loop: every answer today, for a big screen |
| `helm.fcpublicmedia.local/room/podcast/` | the podcast studio's door (the iPad); `/host/?room=podcast` is staff check-in |
| `helm.fcpublicmedia.local/broadcast/` | channel 97, out: its destinations |
| `fcpublicmedia.local` (or `www.`) | the site, as built here |
| `wix.fcpublicmedia.local` | the Wix site, photocopied |
| `ch97.fcpublicmedia.local` | channel 97's day; `/jukebox/` is the floor's playlist |
| `digitization.fcpublicmedia.local` | this machine's directory; each piece of gear one level deeper (`aja-helo.digitization.…`) |
| `10.209.1.20:9931` | the model on bay 1 (EDIT2), when Autumn has it on (`fcpm model on`) |

## Away (the tailnet)

The tailnet has no MagicDNS: use the number. By number the door shows the board, and its paths work the same.

| address | what |
|---|---|
| `100.115.246.115` | digitization: **the board**, `/ask/`, `/loop/` and the rest of the door's paths |
| `100.115.246.115:9931/v1` | the model, for `tag:operator` devices only (machines/digitization/model-relay) |

The site, the Wix copy and channel 97 answer only to their names, so away, use the internet's.

## On the internet

| address | what |
|---|---|
| `fcpublicmedia.org` | the site (Cloudflare Pages `fcpm-new`; `new.fcpublicmedia.org` is the same) |
| `wix.fcpublicmedia.org` | the Wix site's copy |
| `github.com/FC-Public-Media` | the repositories (FCPM's own origin is origin.local, by SSH: machines/origin) |

Cablecast (`fcpublicmedia.cablecast.tv`, 10.1.10.84) is on the building's other network, 10.1.10.x, and answers
only there.
