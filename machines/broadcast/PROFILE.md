# broadcast

FCPM's broadcast point: what we play out to the cable channel, 97, and record. It is the one instrument
we play rather than one that plays to us. The box is a Cablecast server (Tightrope) and runs that
vendor's software; we don't install anything on it. We drive it through its API, from
[`cablecast.py`](cablecast.py).

| | |
|---|---|
| where | the building's server room, which FCPM doesn't enter. On the building's other network, `10.1.10.84`, the only box of ours over there; the city's network team keeps it reachable from ours |
| name | `fcpublicmedia.cablecast.tv` (its certificate, Let's Encrypt). Port 80 forwards to 443; `/` goes to `FrontDoor/`, the sign-in for Cablecast's own pages |
| API | `/CablecastAPI/v1`. Reading needs no key, at the box or at `reflect-fcpublicmedia.cablecast.tv/cablecastapi/v1`, which is what the site's syncs read ([`docs/programming.md`](../../docs/programming.md)). Changing needs `Authorization: Bearer <token>`. Its own reference lists every call (336 of them): `/CablecastAPI/Help` |
| token | for changes only. Made in Cablecast under the secretary's account, kept on digitization in `~/.config/fcpm/cablecast.token` (600). What the token does is credited to `technology@fcpublicmedia.org`: the device side of the work |
| public | the Internet Channel, `/internetchannel/`, also served from Cablecast's cloud at `reflect-fcpublicmedia.cablecast.tv`; the old bulletin board, `/CablecastCGWebDisplay/` |

## Shows

A show is one episode: one title, one reel of video, a VOD copy for the web. It links to one
**category** (36, for genre), one **producer** (the person), one **project** (the series, which also
publishes a podcast feed, `/Cablecast/Podcasts/<project>.rss`). About 1,500 shows date back to 2020.
Ask for `?page_size=` to see them all; `meta.count` is the true total.

An upload arrives as a show titled with the file's name, with no category, producer or project, and
its `localId` holds the file's name too. Making it right is done by hand today: Nate downloads the
members' Dropbox zip, uploads each file, makes the VOD, then fills in each show. That takes about an
hour each round.

Our own fields sit beside Cablecast's, in [`fields.yml`](fields.yml): an id of our own, a runtime
bucket, the member repository, and whether a show may run again. The legacy `custom1`–`custom8`
slots are unused, and their labels can only be set in Cablecast's own pages, so we don't use them.

## The schedule

A flat list of airings (`scheduleitems`, by `?channel=1&start=&end=`): show, time, overlay text. The
day is copied forward and changed by hand on the day it must change, so one day is a fair picture of
any. Snapshots are kept with `cablecast.py snapshot`. Between airings and after the last one, the
channel shows its output's default input: today CG Player 1, the bulletin board. Edits reach the playout hardware
when an autopilot send commits them (`autopilotsends`). The vendor's examples, show to schedule to
send, are in `github.com/trms/cablecast-api-examples`. Their `cablecast-supercopy` copies a day
forward.

## The look

How we look on the channel and the website is kept as files in its own repository,
`FC-Public-Media/broadcast`, on our origin only (`/srv/origin/FC-Public-Media/broadcast`, and
origin.local by the standby); see its README. `cablecast.py eject <checkout>` copies it out of
the box: the website's logos, words, colours and home rows (`website/`), what rides on the picture
(`on-air/`), and the bulletin board's fixed pieces and slides, in order (`bulletin-board/`). It
writes the same bytes for the same box, so a commit after an eject is exactly what changed in
Cablecast. Sending the files back into Cablecast is still to come.

The bulletin board is Cablecast CG: 15 zones on one page (`/CablecastCGWebDisplay/WebDisplay.aspx?ChannelID=2`),
each zone's pictures listed by `?op=getLatestBulletins&ZoneID=`. Nine are fixed art, one is the 28
slides that take turns, and the rest (two clocks, the North Forty News feed, the schedule, the
weather) are drawn by the board. The corner logo on the channel points at Cablecast's sample
picture (`/Carousel/Images/TRMS.png`) and renders as nothing, so the channel carries no logo today.

## The public site

One record, `publicsites/1`, holds the whole of it: logo, square logo, colours, custom CSS, favicon,
the home carousel (a saved search) and the nine galleries under it, preroll, membership and Stripe.
A show page shows only the fields its list names, today: producer, project ("Production Info"), run
time, and `comments` ("Description"). A new show field stays off the site until it is added there.

As of 2026-10-21: the old logo throughout; upload filenames as public titles; `/live` errors; `/join`
is empty (no Stripe table); the bulletin board is 2007-era script on the old logo. The Wix site
embedded the bulletin board (`community-bulletin-board`) and the public site (`watch-live`).

## The machines and the router

Four Cablecast servers, each with one job: Live 350 (`10.1.10.62`) encodes the channel for the web
and nothing else; VIOLite-600 (`.86`) plays programs out and records one input; VIOLite CG Server
(`.87`) runs the bulletin board; ProVOD (`.84`) makes the on-demand copies, and serves Cablecast's own
pages and API. A Blackmagic 12x12 Videohub (`.83`) routes between them: its outputs are the console's
Channel Output (the air), Preview Output and VIOLite Encoder. A player that plays network streams
(CG Player 1, the VIOLite Player) can put a stream from elsewhere on the air; the three Screenweave
"network streams" are such sources. The console only offers what a server supports, so a Live 350
has no play.

## To YouTube

Channel 97 goes to YouTube all day, everything on it, from our side: [`relay`](relay), the crew's
`youtube` line wherever this job is worn ([`names`](names)), copies the channel's web stream (the
largest picture, 1080p at about 2 Mbps, and the audio) to YouTube by RTMPS, without re-encoding. It
takes it on the LAN, from the Live 350's own copy (`http://10.1.10.62/live/stream-1/`, found by asking
Cablecast for its Live server), and from the cloud copy only when that one does not answer. The
key is kept in `~/.config/fcpm/youtube.key` (600). Nothing is pushed until the stream is seen to move,
and ffmpeg is stopped when its output stops; `~/.local/state/fcpm/broadcast/relay.json` says which:
`pushing`, `frozen`, `waiting` (no key), `stalled`, `unreachable`. `relay --check` says it without
pushing. `--backup` feeds YouTube's backup ingest from a second box.

Cablecast's own way to YouTube is a network broadcast event tied to a scheduled run, one run at a
time, and a paid add-on; it suits events, not a whole channel.

The web stream stopped on 2026-10-19 at 23:19 here, while Cablecast went on saying BROADCASTING. The
Live 350's own playlist stopped there (its encoder stopped writing segments; the cloud copy only
mirrors it), and stopping and starting the live stream or the device in Cablecast's pages did not
start it again: the 350's encoding needs a restart by Tightrope's support or a reboot. The relay says
`frozen` until it moves.

