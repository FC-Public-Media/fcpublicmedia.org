// The organization field doubles as a search of the IRS 501(c)(3) list: picking one fills the field with
// its name and EIN. Never a gate: whatever is typed is kept as typed. The list is fetched only once someone
// types there. See docs/payments.md#nonprofit-rate.
// The words are the page's: this shows the field's [data-org="…"] lines and fills [data-count] and [data-ein].

const box = document.querySelector('[data-org-search]');
const field = box && box.querySelector('input');
const results = box && box.querySelector('[data-org-results]');
const LIMIT = 8;

let orgs = null;
let loading = null;

/** Fold accents and punctuation so "St. Mary's" finds "ST MARYS". */
const fold = (text) =>
  text
    .toLowerCase()
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/[^a-z0-9]+/g, ' ')
    .trim();

async function load() {
  if (orgs) return orgs;
  if (!loading) {
    loading = fetch(box.dataset.list)
      .then((response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json();
      })
      .then((payload) => {
        orgs = (payload.orgs || []).map(([ein, name, city]) => ({ ein, name, city, folded: fold(name) }));
        return orgs;
      });
  }
  return loading;
}

/** Every typed word must appear, in any order; prefix matches first. */
function search(query) {
  const words = fold(query).split(' ').filter(Boolean);
  if (!words.length) return [];
  const start = fold(query);
  return orgs
    .filter((org) => words.every((word) => org.folded.includes(word)))
    .sort((a, b) => (b.folded.startsWith(start) - a.folded.startsWith(start)) || a.name.length - b.name.length);
}

function show(key) {
  for (const line of box.querySelectorAll('[data-org]')) line.hidden = line.dataset.org !== key;
}

function choose(org) {
  field.value = `${org.name} (EIN ${org.ein})`;
  results.replaceChildren();
  box.querySelector('[data-ein]').textContent = org.ein;
  show('chosen');
}

function render(hits) {
  results.replaceChildren();
  const shown = hits.slice(0, LIMIT);
  box.querySelector('[data-count]').textContent = hits.length;
  show(hits.length > shown.length ? 'many' : null);
  for (const org of shown) {
    const item = document.createElement('li');
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'btn-link';
    button.textContent = org.name;
    // Before the field's blur clears the list.
    button.addEventListener('pointerdown', (event) => event.preventDefault());
    button.addEventListener('click', () => choose(org));
    const where = document.createElement('span');
    where.className = 'muted';
    where.textContent = ` ${org.city}`;
    item.append(button, where);
    results.append(item);
  }
}

if (box) {
  field.addEventListener('input', async () => {
    show(null);
    if (fold(field.value).length < 2) {
      results.replaceChildren();
      return;
    }
    try {
      await load();
    } catch {
      return; // No suggestions; the field still takes whatever is typed.
    }
    render(search(field.value));
  });
  field.addEventListener('blur', () => results.replaceChildren());
}
