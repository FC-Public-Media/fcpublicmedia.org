# `site/assets/js/tiers.js`

Moved out of the file. Unreviewed.

## 1

Above `const radios = [...document.querySelectorAll('.tiers input[name="tier"]')];`

The membership tiles. Choosing one is plain HTML (a radio button over each
tile, see membership.md); this only adds the Continue line under them and
keeps the choice in the address, so /membership/?tier=creator arrives with
Creator already chosen and a reload keeps it.

The address is REPLACED, never pushed: choosing a tier is not a place, and
Back should leave the page rather than step back through the tiers.
