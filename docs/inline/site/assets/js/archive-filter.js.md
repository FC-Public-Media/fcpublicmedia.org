# `site/assets/js/archive-filter.js`

Moved out of the file. Unreviewed.

## 1

Above `const panel = document.querySelector('[data-filter]');`

Filtering and sorting for the program archive.

The full list is in the HTML already — this only hides and reorders rows.
With JavaScript off you get every program, which is the point of rendering
the archive statically in the first place. Both controls stay hidden until
this file runs, so neither ever appears as something that does nothing.

SORTING HAS TO FLATTEN THE CATEGORIES

The archive is grouped under category headings, which is the right default:
it is how someone browses. But the questions worth asking of airing data cut
straight across those groups — a program nobody has run in two years is
interesting whether it sits under "Public Affairs" or "Uncategorized".

So any sort other than "Category" moves every row into one list and hides
the headings, and choosing "Category" again puts them back where they came
from. Rows remember their own origin rather than the code trying to
reconstruct it.

## 2

Above `const home = new Map();`

Where each row started, so "Category" is a real return rather than an
approximation of one.

Recorded as a position in a list rather than as "insert before that
element": the remembered sibling may itself have been moved by the time we
get to it, and restoring in the wrong order silently reorders the archive.

## 3

Above `const lastAired = (row) => row.dataset.last || '0000-00-00';`

A program with no airings has no "last aired" date at all. For the
longest-since-aired sort that is the most extreme case, not a missing value,
so it sorts as if it aired at the beginning of time.

## 4

Above `for (const list of lists) {`

Rebuild each list from its own rows, in their original positions.
Appending in index order cannot get this wrong the way inserting
relative to a moving target can.
