// A page's words in another language, keyed by the English as built. No side effects: lang.js uses it
// on the page and tests/strings-report.mjs uses it to list what is there. See docs/site.md#languages.

const SKIP = new Set(['SCRIPT', 'STYLE', 'TEMPLATE', 'NOSCRIPT', 'TEXTAREA', 'CODE', 'PRE', 'SVG']);
const INLINE = new Set([
  'A', 'ABBR', 'B', 'BDI', 'BDO', 'BR', 'CITE', 'DATA', 'DFN', 'EM', 'I', 'IMG', 'KBD', 'MARK', 'Q', 'S',
  'SAMP', 'SMALL', 'SPAN', 'STRONG', 'SUB', 'SUP', 'TIME', 'U', 'VAR', 'WBR',
]);
const ATTRS = ['alt', 'title', 'aria-label', 'placeholder'];
const LETTER = /\p{L}/u;
const MARKUP = /<[a-z]/i;

export const norm = (text) => text.replace(/[\s ]+/g, ' ').trim();

const tag = (el) => el.tagName.toUpperCase();
const skipped = (el) => SKIP.has(tag(el)) || el.getAttribute('translate') === 'no';
const inline = (node) => node.nodeType === 3 || (node.nodeType === 1 && INLINE.has(tag(node)));
const words = (node) => node.nodeType === 3 && LETTER.test(node.data);

/** The words an element says itself: its text and its inline children's, never a block inside it. */
function textOf(el) {
  let text = '';
  for (const node of el.childNodes) {
    if (node.nodeType === 3) text += node.data;
    else if (node.nodeType === 1 && !skipped(node) && inline(node)) {
      text += tag(node) === 'BR' ? ' ' : textOf(node);
    }
  }
  return text;
}

/** Text nodes inside an element's own inline run. */
function ownTexts(el, out = []) {
  for (const node of el.childNodes) {
    if (words(node)) out.push(node);
    else if (node.nodeType === 1 && !skipped(node) && inline(node)) ownTexts(node, out);
  }
  return out;
}

const speaks = (el) => [...el.childNodes].some(words);

/** Every key a page offers: [key, kind] where kind is `text`, `markup` or an attribute's name. */
export function keys(root) {
  const out = [];
  const walk = (el) => {
    if (skipped(el)) return;
    for (const name of ATTRS) {
      const value = el.getAttribute(name);
      if (value && LETTER.test(value)) out.push([norm(value), name]);
    }
    if (speaks(el)) {
      const hasMarkup = [...el.children].some((c) => inline(c) && tag(c) !== 'BR' && !skipped(c));
      out.push([norm(textOf(el)), hasMarkup ? 'markup' : 'text']);
      for (const child of el.children) if (!inline(child)) walk(child);
      return;
    }
    for (const child of el.children) walk(child);
  };
  walk(root);
  return out;
}

function put(el, value) {
  const blocks = [...el.children].some((c) => !inline(c));
  if (MARKUP.test(value) && !blocks) {
    el.innerHTML = value;
    return;
  }
  const texts = ownTexts(el);
  texts.forEach((node, i) => { node.data = i === 0 ? value : ''; });
}

function keep(node, value) {
  const lead = node.data.match(/^[\s ]*/)[0];
  const tail = node.data.match(/[\s ]*$/)[0];
  node.data = lead + value + tail;
}

const swapPaths = (text, images) => {
  let out = text;
  for (const [from, to] of images) out = out.split(from).join(to);
  return out;
};

/**
 * Put `strings` (a Map of English to the other language) on everything under `root`, and `images`
 * (a Map of path to path) on pictures. A key not in the map is left as it is, so this can run again.
 */
export function translate(root, strings, images = new Map()) {
  const walk = (el) => {
    if (skipped(el)) return;
    for (const name of ATTRS) {
      const value = el.getAttribute(name);
      if (value && strings.has(norm(value))) el.setAttribute(name, strings.get(norm(value)));
    }
    if (images.size) {
      for (const name of ['src', 'poster', 'srcset', 'style']) {
        const value = el.getAttribute(name);
        if (value) {
          const swapped = swapPaths(value, images);
          if (swapped !== value) el.setAttribute(name, swapped);
        }
      }
    }
    if (speaks(el)) {
      const key = norm(textOf(el));
      if (strings.has(key)) {
        put(el, strings.get(key));
        for (const child of el.children) if (!inline(child)) walk(child);
        return;
      }
      for (const node of el.childNodes) {
        if (words(node) && strings.has(norm(node.data))) keep(node, strings.get(norm(node.data)));
      }
    }
    for (const child of el.children) walk(child);
  };
  walk(root);
}
