# `site/_data/providers.yml`

Moved out of the file. Unreviewed.

## 1

Above `tickets:`

Every place the site hands a visitor off to something that isn't static.

This is the whole dynamic surface of fcpublicmedia.org. It is five entries
long. Each one is rendered by _includes/transaction.html, so switching a
vendor means editing one line here — not hunting through page copy.

An entry with an empty `url` renders as a visible "not wired up yet"
placeholder instead of a dead button. That is intentional: an unconfigured
transaction should be obvious on the page, not silently broken.

status: live | pending | placeholder

## 2

Above `subdomain: ""`

Set this when booking moves to its own host, e.g. book.fcpublicmedia.org.
See README, "Booking on a subdomain", for how to keep it feeling like part
of this site rather than a scheduling tool someone bolted on.
