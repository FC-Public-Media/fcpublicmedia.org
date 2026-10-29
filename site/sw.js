---
layout: null
permalink: /sw.js
sitemap: false
---
{%- comment -%}
The offline kit: a service worker. It runs in the visitor's browser and nowhere else (not a Cloudflare
Worker; nothing of ours runs). It keeps the pages marked `offline: true` and the site's scripts, styles
and fonts, so the check-in, /you/ and the forms open with no signal, and Show it still pours. Pages and
files always come from the network when there is one; the kept copy answers only when there isn't. The
cache is named for the commit the site was built from, so each deploy replaces the last kit.
docs/site.md#offline.
{%- endcomment -%}
{%- assign kit_pages = site.pages | where: "offline", true -%}
{%- assign kit_version = site.revision | default: "" -%}
{%- if kit_version == "" %}{% assign kit_version = site.time | date: "%s" %}{% endif -%}
const KIT = 'fcpm-kit-{{ kit_version }}';
const PAGES = [
{%- for p in kit_pages %}
  {{ p.url | relative_url | jsonify }},
{%- endfor %}
];
const FILES = [
{%- for f in site.static_files -%}
  {%- if f.path contains '/assets/js/' or f.path contains '/assets/css/' or f.path contains '/assets/fonts/' or f.path contains '/assets/img/icon' -%}
  {%- unless f.path contains '.spec.' %}
  {{ f.path | relative_url | jsonify }},
  {%- endunless -%}
  {%- endif -%}
{%- endfor %}
  {{ '/assets/css/site.css' | relative_url | jsonify }},
  {{ '/manifest.webmanifest' | relative_url | jsonify }},
];
const KEPT = new Set([...PAGES, ...FILES]);

// One file that will not come does not stop the rest of the kit.
self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(KIT).then((cache) =>
    Promise.all([...KEPT].map((path) => cache.add(path).catch(() => null)))));
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(caches.keys()
    .then((names) => Promise.all(names.filter((n) => n.startsWith('fcpm-kit-') && n !== KIT).map((n) => caches.delete(n))))
    .then(() => self.clients.claim()));
});

// Only the kit's own paths, and only GET; everything else is the browser's as if we were not here.
self.addEventListener('fetch', (event) => {
  const request = event.request;
  if (request.method !== 'GET') return;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin || !KEPT.has(url.pathname)) return;
  event.respondWith((async () => {
    const cache = await caches.open(KIT);
    try {
      const fresh = await fetch(request);
      if (fresh.ok) cache.put(url.pathname, fresh.clone());
      return fresh;
    } catch (error) {
      const kept = await cache.match(url.pathname);
      if (kept) return kept;
      throw error;
    }
  })());
});
