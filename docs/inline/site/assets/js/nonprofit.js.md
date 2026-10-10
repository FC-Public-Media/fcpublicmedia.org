# `site/assets/js/nonprofit.js`

Moved out of the file. Unreviewed.

## 1

Above `const config = JSON.parse(document.getElementById('nonprofit-config').textContent);`

Finding your own organization on the IRS list.

The problem this solves is a sequencing one, not an identity one. Nonprofits
pay half, and until now there was no way to establish that anybody was one
until after they had paid — so organizations bought the wrong tier and
waited for a cheque back, or did not join at all. Neither is a pricing
problem. It is a "we asked in the wrong order" problem.

So: no upload, no determination letter, no form. The IRS publishes every
501(c)(3), and somebody can pick their own name off it in one gesture. What
comes out is an EIN, which is something staff can check before any money
moves.

THIS IS NOT A GATE, AND MUST NEVER BECOME ONE
---------------------------------------------
The list is Larimer County 501(c)(3)s and nothing else. A new organization,
a chapter of a national body, one filing under a parent's EIN, or one
working through a fiscal sponsor will all be legitimately absent. So "not
listed" is a visible, equal path on the page rather than something you reach
by failing — see membership.md. A lookup that refuses people would be worse
than no lookup.

The data is only fetched when somebody says they are with a nonprofit. It is
a hundred and sixteen kilobytes, and most visitors are not.

## 2

Above `function search(query) {`

Every word you typed has to appear, in any order.

Somebody looking for the Poudre River Library Trust will type two of those
four words and not necessarily the first two. A prefix match on the whole
string would find nothing and look broken.

## 3

Above `const start = fold(query);`

Something starting with what you typed is almost always the thing you
meant, so it goes first.

## 4

Above `el('nonprofit-status').textContent =`

Not an error state. Plenty of real organizations are not on this list,
and the way forward is already on the page below.

## 5

Above `el('nonprofit-status').textContent =`

The list failing to load must not strand anybody — the contact route is
already visible below, so say so plainly and stop.

## 6

Above `panel.hidden = false;`

Revealed only once the script is running, so a browser with no JavaScript
sees the "tell us who you are" route rather than a search box that does
nothing when typed into.
