# `site/_layouts/show.html`

Moved out of the file. Unreviewed.

## 1

Above `{%- assign cc = site.data.cablecast -%}`

One show. The page a Details button goes to.

Its episode list is a fold of the catalog, not a stored list: filter
_data/cablecast.json by this show's match prefixes. That means a show page
is never out of date with the catalog, and adding a show costs one file
rather than one file plus a list somebody has to remember to update.

Deliberately no per-episode page. Episodes play in a player, here or in the
jukebox, and a thousand thin pages would be a thousand things to keep
looking right for no one's benefit.

## 2

Above `<p class="transaction transaction-todo">`

Visible on purpose. A show whose name was guessed by a script and never
checked should say so where somebody will see it, not only in a comment
in the file. It disappears by deleting one line.

## 3

Above `{%- assign episodes = "" | split: "" -%}`

Match on the normalised title the same way propose-shows.py does: lower
case, and the separators people vary on removed. Liquid has no regex, so
this replaces the punctuation that actually appears in these titles rather
than everything a regex would.
