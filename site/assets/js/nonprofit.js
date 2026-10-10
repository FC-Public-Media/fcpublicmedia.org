// Picking your organization off the IRS 501(c)(3) list for an EIN; never a gate.
// Fetched only when someone says they are a nonprofit. See docs/payments.md#nonprofit-rate.

const config = JSON.parse(document.getElementById('nonprofit-config').textContent);

const el = (id) => document.getElementById(id);

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
    loading = fetch(config.data)
      .then((response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json();
      })
      .then((payload) => {
        orgs = (payload.orgs || []).map(([ein, name, city]) => ({
          ein,
          name,
          city,
          folded: fold(name),
        }));
        return orgs;
      });
  }
  return loading;
}

/** Every typed word must appear, in any order. */
function search(query) {
  const words = fold(query).split(' ').filter(Boolean);
  if (!words.length) return [];

  const hits = orgs.filter((org) => words.every((word) => org.folded.includes(word)));

  // Prefix matches first.
  const start = fold(query);
  hits.sort((a, b) => {
    const lead = b.folded.startsWith(start) - a.folded.startsWith(start);
    return lead || a.name.length - b.name.length;
  });
  return hits;
}

/* --------------------------------------------------------------------- view */

function choose(org) {
  el('nonprofit-name').textContent = org.name;
  el('nonprofit-ein').textContent = org.ein;

  const subject = `Nonprofit membership rate for ${org.name}`;
  const body =
    `We'd like the nonprofit rate.\n\n` +
    `Organization: ${org.name}\n` +
    `EIN: ${org.ein}\n` +
    `City: ${org.city}\n\n` +
    `(Found on the IRS 501(c)(3) list via your membership page.)\n`;
  el('nonprofit-email').href =
    `mailto:${config.email}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;

  el('nonprofit-results').replaceChildren();
  el('nonprofit-search').value = org.name;
  el('nonprofit-status').textContent = '';
  el('nonprofit-chosen').hidden = false;
}

function render(hits, query) {
  const list = el('nonprofit-results');
  list.replaceChildren();

  if (!query.trim()) {
    el('nonprofit-status').textContent = '';
    return;
  }
  if (!hits.length) {
    // Not an error: the way forward is already on the page.
    el('nonprofit-status').textContent =
      "Nothing matching that. Plenty of organizations aren't on the IRS list — just tell us who you are.";
    return;
  }

  const shown = hits.slice(0, LIMIT);
  el('nonprofit-status').textContent =
    hits.length > shown.length ? `${hits.length} matches — keep typing to narrow it.` : '';

  for (const org of shown) {
    const item = document.createElement('li');
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'btn-link';
    button.textContent = org.name;
    button.addEventListener('click', () => choose(org));

    const where = document.createElement('span');
    where.className = 'muted';
    where.textContent = ` ${org.city}`;

    item.append(button, where);
    list.append(item);
  }
}

/* --------------------------------------------------------------------- init */

async function onInput(event) {
  const query = event.target.value;
  el('nonprofit-chosen').hidden = true;

  if (!query.trim()) {
    render([], query);
    return;
  }

  try {
    await load();
  } catch (error) {
    // The contact route below is still there.
    el('nonprofit-status').textContent =
      "We couldn't load the organization list. Get in touch and we'll sort your rate out directly.";
    return;
  }

  render(search(query), query);
}

function init() {
  const panel = el('nonprofit-lookup');
  if (!panel) return;

  el('nonprofit-search').addEventListener('input', onInput);
  el('nonprofit-clear').addEventListener('click', () => {
    el('nonprofit-search').value = '';
    el('nonprofit-chosen').hidden = true;
    el('nonprofit-results').replaceChildren();
    el('nonprofit-status').textContent = '';
    el('nonprofit-search').focus();
  });

  // Revealed by script, so without JavaScript there is no dead search box.
  panel.hidden = false;
}

init();
