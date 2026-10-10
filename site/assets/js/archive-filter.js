// Filter and sort for the program archive; hides and reorders rows already in the HTML.
// Any sort but "Category" flattens rows into one list. See docs/site.md.

const panel = document.querySelector('[data-filter]');
const input = document.getElementById('archive-filter');
const sorter = document.getElementById('archive-sort');
const count = document.querySelector('[data-filter-count]');
const lists = Array.from(document.querySelectorAll('[data-archive]'));
const rows = Array.from(document.querySelectorAll('[data-archive] li'));
const headings = Array.from(document.querySelectorAll('h2[id]'));

// Each row's original list and index (not a sibling, which may itself have moved).
const home = new Map();
for (const list of lists) {
  Array.from(list.children).forEach((row, index) => home.set(row, { list, index }));
}

const num = (row, name) => Number(row.dataset[name] || 0);

// Never aired sorts as the oldest possible date.
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
    // Rebuild each list from its own rows, appended in original index order.
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
