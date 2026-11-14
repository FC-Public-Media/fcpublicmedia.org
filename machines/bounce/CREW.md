# bounce

The captive bounce from the community-ping study, proven by FCPM as a peer with tools only: a Wi-Fi QR joins
the wearer's own open network, the phone's sign-in sheet opens by itself, and the box's page is in front of
the person with no internet, no app and nothing typed. Worn by [the Pi](PROFILE.md)'s spare radio for now;
a real antenna gets its own box.

| | |
|---|---|
| network | `FC Public Media Bounce`, open, 2.4 GHz channel 11, `10.97.97.0/24`; the box is `10.97.97.1` |
| QR | `WIFI:S:FC Public Media Bounce;T:nopass;;` to join; `http://10.97.97.1/?from=qr` to open the page in the real browser once joined |
| DNS | every name answers `10.97.97.1` ([`dnsmasq.conf`](dnsmasq.conf), run from `dnsmasq-base`) |
| DHCP | 1 h leases; option 114 = `http://10.97.97.1/captive` (RFC 8910) |
| wall | [`wall.nft`](wall.nft): the island reaches DHCP, DNS and port 80 only; anything else is reset at once; nothing is forwarded, so the island never touches Helm |
| page | [`bounce.py`](bounce.py) on port 80 serves [`page/`](page/); island phones asking any other host are sent there; the OS probes (Apple, Android, Windows, Firefox) open the sheet until the phone presses release; a release ends when the phone rejoins (its lease moves) |
| kept | nothing, unless a person presses Send: then `state/reports/<time>.json` beside the code. Events go to the loudspeaker as `bounce` |

## Wear it

From a copy of this folder on the box (the Pi keeps one in `~/bounce`): `sudo sh install`. `sudo sh install remove`
takes all of it down (the connection, the wall, the units). `BOUNCE_SSID` names the network.

## What the page finds out

The study's open questions about the sheet, answered per phone by pressing through the page: does storage
survive closing the sheet (visits, cookie), can a file be downloaded, can a link open the real browser, does
release turn the sheet's button to Done (the page loads `done.html` after it, so the sheet checks again), and does the phone use option 114's API (an `asked the captive API`
line) or only the probe. Plain HTTP, so no service worker or passkey here: that is the HTTPS layer, later.

## Found

- iPhone, iOS 18.7, two phones: the sheet opens from Apple's probe alone; option 114's API is never asked (it is
  plain HTTP; the RFC asks for HTTPS). Storage, cookie and IndexedDB work inside the sheet and are gone the next
  time it opens. A download link renders in the sheet instead of saving, and a `target=_blank` link
  navigates inside the sheet: neither leaves it. Rejoining does not reliably bring the
  sheet back; forgetting the network, Wi-Fi off a while, and waiting minutes usually does.
- The sheet re-asks Apple's probe after every page load, and the phone asks again on its own while idle. Release
  turns the sheet's button to Done only once a page loads after it.
- Inside one sheet, storage lasts across page loads; it is gone when the sheet closes.
- Out of the sheet: after Done the phone stays joined, and the Camera app's scan of `?from=qr` opens real Safari.
  Each scan there started with empty storage and a new cookie, and only an in-page link kept the count.
