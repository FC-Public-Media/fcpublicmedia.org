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

## ch97

`ch97.fcpublicmedia.local` is our page for the channel, so nobody has to find their way through
Cablecast's own pages to see the day. Cablecast keeps calling itself `fcpublicmedia.cablecast.tv`,
and `ch97.fcpublicmedia.org` is its public face under our name; the `.local` name is the one we work
from.

The day we intend is a file: `schedule/<date>.json` in the broadcast repository, laid down from
Cablecast once (`cablecast.py lay <checkout> [date] [days]`) and ours from then on. The page draws
that first: one column, a minute of air to four pixels, each gap left empty at its real size with
what fills it (the bulletin board). Cablecast's own copy of the day is read beside it, and where the
two differ is marked at the column's edge; a later change on Cablecast's side is offered in the bar,
never drawn in under someone's hand. Clicking a gap or an airing opens the reserve: every show,
narrowed to that category and to what fits, least lately aired first. Each request to the box shows
in the bar while it runs.

| | |
|---|---|
| page | `ch97/page/`: plain files, React by an import map; the libraries are CDN files kept in `ch97/page/vendor/`, listed with their sums in `ch97/vendor.yml` (`python3 ch97/vendor` checks them). Nothing is built |
| served | nginx (`ch97/nginx.conf`, by `sudo sh machines/broadcast/ch97/install`). `/api/` reads the box's API by its address and name, and turns away anything but GET |
| laid | each night at midnight, the crew's `lay` line (`lay`): every day Cablecast has and the repository doesn't yet is laid down, committed as `technology@fcpublicmedia.org` and pushed to our origin, from the crew's own checkout (`~/.local/share/fcpm/broadcast`). A day is laid only once Cablecast has airings on the day after it, so one still being filled in isn't frozen half-done. Other machines (kiosk screens, websites, the YouTube title) read the days from the repository |
| published | the crew's `ch97` line (`ch97/publish`): the page, and the days as the broadcast repository's main has them, into `/var/lib/fcpm/ch97` |
| name | `ch97` in `digitization/lan.yml`, held by the crew's `names` line |

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

Channel 97 goes to YouTube all day, everything on it, from Cablecast itself: the Live 350 pushes it to
the YouTube network stream destination (`addOutput`), with YouTube's current key. Our part is to be
under it, never to carry it.

Whether the 350 pushes to a destination is a switch: attaching it (`addOutput`, a forced event) starts
the push and detaching it (`removeOutput`) stops it. The box's automation status lists what is attached,
and reading it needs no key. `cablecast.py push [NAME on|off]` says or switches, and the door's
`/broadcast/` page (`helm.fcpublicmedia.local/broadcast/`) shows each destination with its switch, for
whoever is on Helm; switching needs the token, so it works where the token is kept.

[`relay`](relay) is the emergency tool if the 350 cannot push: it copies the channel's web stream (taken
on the LAN from the 350, the cloud copy as fallback) to YouTube's primary ingest without re-encoding,
and pushes only once the source is seen to move. It is not a crew line; `relay --check` says what it
would do. It carried the channel on 2026-10-22 from 00:03 while the 350's own push could not.

When the channel's stream pauses (a gap in the schedule, an IP-exempt program), YouTube would end the
broadcast. So [`standby`](standby), the crew's `backup` line, feeds YouTube's backup ingest all the
time with our own picture: the brand's mark and lockup (from `site/_data/brand.json`) and the room's
clock, at 1080p30 like the channel, decoded once and encoded by the GPU (about a tenth of a core and
a few hundred kbit/s). YouTube shows it while the channel is away and goes back when it returns.

Its sound is a bus, `fcpm-standby`: a null sink standby makes in the desktop's PulseAudio, sent from
its monitor. Anything played into it is on YouTube's backup stream; with nothing playing, it is
silence, as before. Until PulseAudio is up (the desktop's login), standby sends silence, and once the
bus can be made it starts again with it. [`jukebox`](jukebox), the crew's `jukebox` line, is the first
thing played into it: every sound file in `/srv/landing/jukebox`, by name, A to Z and round again, the
folder read afresh each round. Only music FCPM has the rights to goes in that folder. What it plays is
in `~/.local/state/fcpm/broadcast/jukebox.json`; nothing shows it on the picture yet. `jukebox --check`
says what it would play and whether the bus is there.

Cablecast's own way to YouTube is a network broadcast event tied to a scheduled run, one run at a
time, and a paid add-on; it suits events, not a whole channel. A Live server can also push to a
network stream destination by itself (`addOutput`): that wants the destination's key to be YouTube's
current one, and an encoder that is not stuck.

The web stream stopped on 2026-10-19 at 23:19 here, while Cablecast went on saying BROADCASTING: its
playlist kept its last four segments and stopped moving. Stopping and starting the live stream in
Cablecast is what starts it again; the relay says `frozen` until then.

