// What each page says, and how much of it each strings file covers. Reads ../_site, so build first.
//   node strings-report.mjs                 the scorecard
//   node strings-report.mjs --missing es    what es.yml does not have yet, as YAML to fill in
//   node strings-report.mjs --unused es     what es.yml has that no page says any more
// Only what a page says on arrival: words a script writes later are not seen. See docs/site.md#languages.

import { createRequire } from 'node:module';
import { readFile, stat } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const { chromium } = require('@playwright/test');
const { PAGES } = require('./pages.js');

const SITE = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../_site');
const ORIGIN = 'http://localhost:4567';
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json', '.css': 'text/css', '.svg': 'image/svg+xml' };

const [mode, lang] = process.argv.slice(2);

async function file(pathname) {
  let target = path.join(SITE, decodeURIComponent(pathname));
  if ((await stat(target).catch(() => null))?.isDirectory()) target = path.join(target, 'index.html');
  return { body: await readFile(target), contentType: TYPES[path.extname(target)] || 'application/octet-stream' };
}

const browser = await chromium.launch(process.env.CHROMIUM ? { executablePath: process.env.CHROMIUM } : {});
const context = await browser.newContext({ locale: 'en-US', javaScriptEnabled: true });
await context.route('**/*', async (route) => {
  const url = new URL(route.request().url());
  if (url.origin !== ORIGIN) return route.abort();
  try {
    await route.fulfill({ status: 200, ...(await file(url.pathname)) });
  } catch {
    await route.fulfill({ status: 404, body: '' });
  }
});

const all = JSON.parse(await readFile(path.join(SITE, 'strings.json'), 'utf8'));
const norm = (text) => text.replace(/[\s ]+/g, ' ').trim();
const tables = Object.fromEntries(Object.entries(all).map(([code, f]) =>
  [code, new Set(Object.keys(f.strings || {}).map(norm))]));

const seen = new Map();
const rows = [];
for (const { path: pagePath, name } of PAGES) {
  const page = await context.newPage();
  await page.goto(ORIGIN + pagePath, { waitUntil: 'domcontentloaded' });
  const found = await page.evaluate(async () => {
    const { keys } = await import('/assets/js/strings.mjs');
    const title = document.title.split(' — ')[0];
    return [[title, 'title'], ...keys(document.body)];
  });
  await page.close();
  const unique = new Map(found);
  for (const [key, kind] of unique) if (!seen.has(key)) seen.set(key, { kind, page: name });
  const words = [...unique.keys()].reduce((n, k) => n + k.split(' ').length, 0);
  const covered = Object.fromEntries(Object.entries(tables).map(([code, keys]) =>
    [code, [...unique.keys()].filter((k) => keys.has(k)).length]));
  rows.push({ name, strings: unique.size, words, covered });
}
await browser.close();

if (mode === '--missing' || mode === '--unused') {
  const keys = tables[lang];
  if (!keys) throw new Error(`no _data/strings/${lang}.yml`);
  if (mode === '--unused') {
    for (const key of keys) if (!seen.has(key)) console.log(key);
  } else {
    let last = '';
    for (const [key, { kind, page }] of seen) {
      if (keys.has(key)) continue;
      if (page !== last) console.log(`  # ${page}`);
      last = page;
      console.log(`  ${JSON.stringify(key)}: ""${kind === 'text' ? '' : `  # ${kind}`}`);
    }
  }
} else {
  const codes = Object.keys(tables);
  console.log(['page', 'strings', 'words', ...codes].join('\t'));
  for (const r of rows) {
    console.log([r.name, r.strings, r.words, ...codes.map((c) => `${r.covered[c]}/${r.strings}`)].join('\t'));
  }
  const total = seen.size;
  console.log(['all (once each)', total, [...seen.keys()].reduce((n, k) => n + k.split(' ').length, 0),
    ...codes.map((c) => `${[...seen.keys()].filter((k) => tables[c].has(k)).length}/${total}`)].join('\t'));
}
