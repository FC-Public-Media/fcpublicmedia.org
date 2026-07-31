// Client-side filter for the program archive.
//
// The full list is in the HTML already — this only hides rows. With
// JavaScript off you get every program, which is the point of rendering the
// archive statically in the first place. The filter box stays hidden until
// this file runs, so it never appears as a control that does nothing.

const panel = document.querySelector('[data-filter]');
const input = document.getElementById('archive-filter');
const count = document.querySelector('[data-filter-count]');
const rows = Array.from(document.querySelectorAll('[data-archive] li'));
const headings = Array.from(document.querySelectorAll('h2[id]'));

if (panel && input && rows.length) {
  panel.hidden = false;

  const apply = () => {
    const term = input.value.trim().toLowerCase();

    let shown = 0;
    for (const row of rows) {
      const match = !term || row.dataset.search.includes(term);
      row.hidden = !match;
      if (match) shown += 1;
    }

    // Hide a category heading when everything under it is filtered out.
    for (const heading of headings) {
      const list = heading.nextElementSibling;
      const anyVisible = list && Array.from(list.children).some((li) => !li.hidden);
      heading.hidden = !anyVisible;
      if (list) list.hidden = !anyVisible;
    }

    count.textContent = term ? `${shown} of ${rows.length} programs` : '';
  };

  input.addEventListener('input', apply);
}
