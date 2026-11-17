// The footer's language choice, and the page in that language. English is the page as built; another
// language is its strings file (/strings.json, from _data/strings/) put over it. With no choice made, the
// device's own languages decide. See docs/site.md#languages.

import { norm, translate } from './strings.mjs';
import { read, remember } from './prefs.js';

const ENGLISH = 'en';
const meta = document.querySelector('meta[name="fcpm-strings"]');
const offered = (meta?.dataset.langs || '').split(' ').filter(Boolean);
const root = document.documentElement;

const known = (code) => code === ENGLISH || offered.includes(code);

/** The stored choice, else the first of the device's languages we have, else English. */
function chosen() {
  const stored = read('lang');
  if (stored && known(stored)) return stored;
  for (const tag of navigator.languages || [navigator.language || '']) {
    const base = String(tag).toLowerCase().split('-')[0];
    if (known(base)) return base;
  }
  return ENGLISH;
}

const reveal = () => root.removeAttribute('data-lang-pending');

async function load(code) {
  const response = await fetch(meta.content);
  if (!response.ok) throw new Error(`strings: HTTP ${response.status}`);
  const all = await response.json();
  const file = all[code] || {};
  return {
    strings: new Map(Object.entries(file.strings || {}).map(([k, v]) => [norm(k), String(v)])),
    images: new Map(Object.entries(file.images || {})),
  };
}

function retitle(strings) {
  const parts = document.title.split(' — ');
  const said = parts.map((part) => strings.get(norm(part)) || part).join(' — ');
  if (said !== document.title) document.title = said;
}

let observer = null;

async function apply(code) {
  if (code === ENGLISH || !meta) return reveal();
  let table;
  try {
    table = await load(code);
  } catch (error) {
    return reveal();
  }
  const run = () => {
    translate(document.body, table.strings, table.images);
    retitle(table.strings);
  };
  run();
  root.lang = code;
  reveal();

  // Words other scripts write later (a form's answer, what is on now) get the same treatment.
  let queued = false;
  observer = new MutationObserver(() => {
    if (queued) return;
    queued = true;
    requestAnimationFrame(() => {
      queued = false;
      observer.disconnect();
      run();
      observer.observe(document.body, { childList: true, subtree: true, characterData: true });
    });
  });
  observer.observe(document.body, { childList: true, subtree: true, characterData: true });
}

const current = chosen();
apply(current);

const control = document.querySelector('[data-lang-choice]');
if (control && meta) {
  const buttons = [...control.querySelectorAll('[data-lang]')];
  const mark = (code) => buttons.forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.lang === code)));
  mark(current);
  control.hidden = false;

  let showing = current;
  for (const button of buttons) {
    button.addEventListener('click', () => {
      const code = button.dataset.lang;
      remember('lang', code);
      mark(code);
      if (code === showing) return;
      // English is the page as built, so leaving another language is a fresh copy of it.
      if (showing !== ENGLISH) {
        location.reload();
        return;
      }
      showing = code;
      apply(code);
    });
  }
}
