// Finding your own organization on the IRS list.
//
// The problem this solves is a sequencing one, not an identity one. Nonprofits
// pay half, and until now there was no way to establish that anybody was one
// until after they had paid — so organizations bought the wrong tier and
// waited for a cheque back, or did not join at all. Neither is a pricing
// problem. It is a "we asked in the wrong order" problem.
//
// So: no upload, no determination letter, no form. The IRS publishes every
// 501(c)(3), and somebody can pick their own name off it in one gesture. What
// comes out is an EIN, which is something staff can check before any money
// moves.
//
// THIS IS NOT A GATE, AND MUST NEVER BECOME ONE
// ---------------------------------------------
// The list is Larimer County 501(c)(3)s and nothing else. A new organization,
// a chapter of a national body, one filing under a parent's EIN, or one
// working through a fiscal sponsor will all be legitimately absent. So "not
// listed" is a visible, equal path on the page rather than something you reach
// by failing — see membership.md. A lookup that refuses people would be worse
// than no lookup.
//
// The data is only fetched when somebody says they are with a nonprofit. It is
// a hundred and sixteen kilobytes, and most visitors are not.

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

/**
 * Every word you typed has to appear, in any order.
 *
 * Somebody looking for the Poudre River Library Trust will type two of those
 * four words and not necessarily the first two. A prefix match on the whole
 * string would find nothing and look broken.
 */
function search(query) {
  const words = fold(query).split(' ').filter(Boolean);
  if (!words.length) return [];

  const hits = orgs.filter((org) => words.every((word) => org.folded.includes(word)));

  // Something starting with what you typed is almost always the thing you
  // meant, so it goes first.
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
    // Not an error state. Plenty of real organizations are not on this list,
    // and the way forward is already on the page below.
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
    // The list failing to load must not strand anybody — the contact route is
    // already visible below, so say so plainly and stop.
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

  // Revealed only once the script is running, so a browser with no JavaScript
  // sees the "tell us who you are" route rather than a search box that does
  // nothing when typed into.
  panel.hidden = false;
}

init();
