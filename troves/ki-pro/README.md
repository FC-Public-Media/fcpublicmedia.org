# The Ki Pro trove

A first-generation AJA Ki Pro records ProRes `.mov` on a removable Storage Module. **Studio Ki Pro**
(serial `2B03548`, firmware 3.2), the TriCaster's backup recorder, is at `10.1.10.63` (static; MAC
`00:0C:17:08:0B:E8`), usually off. Its web page has no password; its LAN cable's clip is broken.

As read: SDI in from the TriCaster; XLR audio at +12 dBu, apparently the DL32R's outputs 13/14;
ProRes 422 HQ, 1080i 29.97, timecode free-running from 01:00:00:00; clips `LPC Backup`, take 178;
armed by the front REC key, RS-422 off; drive D1 empty.

To record a show: TriCaster on with program out, then the Ki Pro; press record, and stop at the end.
To copy files off, plug the Storage Module's own FireWire 800 port into a Mac.

Reads: `GET /descriptors` (every parameter's `eParamID_…`), `GET /config?action=get&paramid=eParamID_…`
(one value, as JSON), `GET /clips?action=get_clips` (the drive's clips). Nothing here uses
`action=set`, which changes settings and the transport, until whoever owns the LPC recordings agrees.
