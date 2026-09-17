// Filtering and sorting for the program archive.
//
// The full list is in the HTML already — this only hides and reorders rows.
// With JavaScript off you get every program, which is the point of rendering
// the archive statically in the first place. Both controls stay hidden until
// this file runs, so neither ever appears as something that does nothing.
//
// SORTING HAS TO FLATTEN THE CATEGORIES
//
// The archive is grouped under category headings, which is the right default:
// it is how someone browses. But the questions worth asking of airing data cut
// straight across those groups — a program nobody has run in two years is
// interesting whether it sits under "Public Affairs" or "Uncategorized".
//
// So any sort other than "Category" moves every row into one list and hides
// the headings, and choosing "Category" again puts them back where they came
// from. Rows remember their own origin rather than the code trying to
// reconstruct it.

const panel = document.querySelector('[data-filter]');
const input = document.getElementById('archive-filter');
const sorter = document.getElementById('archive-sort');
const count = document.querySelector('[data-filter-count]');
const lists = Array.from(document.querySelectorAll('[data-archive]'));
const rows = Array.from(document.querySelectorAll('[data-archive] li'));
const headings = Array.from(document.querySelectorAll('h2[id]'));

// Where each row started, so "Category" is a real return rather than an
// approximation of one.
//
// Recorded as a position in a list rather than as "insert before that
// element": the remembered sibling may itself have been moved by the time we
// get to it, and restoring in the wrong order silently reorders the archive.
const home = new Map();
for (const list of lists) {
  Array.from(list.children).forEach((row, index) => home.set(row, { list, index }));
}

const num = (row, name) => Number(row.dataset[name] || 0);

// A program with no airings has no "last aired" date at all. For the
// longest-since-aired sort that is the most extreme case, not a missing value,
// so it sorts as if it aired at the beginning of time.
const lastAired = (row) => row.dataset.last || '0000-00-00';

const ORDERS = {
  least: (a, b) => num(a, 'airings') - num(b, 'airings') || byTitle(a, b),
  most: (a, b) => num(b, 'airings') - num(a, 'airings') || byTitle(a, b),
  stale: (a, b) => lastAired(a).localeCompare(lastAired(b)) || byTitle(a, b),
  recent: (a, b) => lastAired(b).localeCompare(lastAired(a)) || byTitle(a, b),
  title: (a, b) => byTitle(a, b),
};

function byTitle(a, b) {
  return (a.dataset.title || '').localeCompare(b.dataset.title || '');
}

function applySort() {
  const order = sorter ? sorter.value : 'category';

  if (order === 'category') {
    // Rebuild each list from its own rows, in their original positions.
    // Appending in index order cannot get this wrong the way inserting
    // relative to a moving target can.
    for (const list of lists) {
      const mine = rows
        .filter((row) => home.get(row).list === list)
        .sort((a, b) => home.get(a).index - home.get(b).index);
      for (const row of mine) list.append(row);
      list.dataset.flat = '';
    }
    return;
  }

  const target = lists[0];
  const sorted = [...rows].sort(ORDERS[order]);
  for (const row of sorted) target.append(row);
  target.dataset.flat = 'true';
}

function apply() {
  const term = input.value.trim().toLowerCase();
  const flattened = sorter && sorter.value !== 'category';

  let shown = 0;
  for (const row of rows) {
    const match = !term || row.dataset.search.includes(term);
    row.hidden = !match;
    if (match) shown += 1;
  }

  // Category headings only mean anything while the rows are still under them.
  for (const heading of headings) {
    const list = heading.nextElementSibling;
    if (flattened) {
      heading.hidden = true;
      if (list) list.hidden = list !== lists[0];
      continue;
    }
    const anyVisible = list && Array.from(list.children).some((li) => !li.hidden);
    heading.hidden = !anyVisible;
    if (list) list.hidden = !anyVisible;
  }

  count.textContent = term
    ? `${shown} of ${rows.length} programs`
    : flattened
      ? `${rows.length} programs, sorted`
      : '';
}

if (panel && input && rows.length) {
  panel.hidden = false;
  input.addEventListener('input', apply);

  if (sorter) {
    sorter.addEventListener('change', () => {
      applySort();
      apply();
    });
  }
}
