# `site/assets/js/onair.js`

Moved out of the file. Unreviewed.

## 1

Above `const API = 'https://reflect-fcpublicmedia.cablecast.tv/cablecastapi/v1';`

"On now" and "up next" for the cable channel.

Cablecast's API is public and sends Access-Control-Allow-Origin: *, so the
browser can read the schedule directly. No backend, no key, no build step.

This is progressive enhancement: the markup it fills already says something
sensible, and if the request fails the block is removed rather than left
showing a spinner forever.
