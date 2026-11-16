// workshed-serve.mjs -- one workshed worktree's site, built whole by jekyll-enough and served on its own port.
//
//   node workshed-serve.mjs --checkout DIR --engine DIR --port N --state DIR [--once]
//
// --checkout is a worktree; its build root is site/ if site/_config.yml is there, else the worktree itself.
// --engine is jekyll-enough, found by workshed.py from the code root (the one place that looks). The whole
// site is built every time, never one page: the header, footer and nav read _data and site.pages, and a
// partial build would leave them wrong. "Per page" is only where the Helm opens it and which pages a
// branch changed. Each build rewrites --state/status.json and --state/pages.json for the Helm (workshed.py).
// It listens on this computer only (127.0.0.1 and ::1, so http://localhost:N works, and passkeys with it),
// and rebuilds when a file under DIR changes. --once builds, says how it went, and exits 1 on a failure.
// Doc: docs/workshed.md.
import fs from "node:fs";
import http from "node:http";
import path from "node:path";
import { pathToFileURL } from "node:url";

const args = {};
for (let i = 2; i < process.argv.length; i++) {
  const a = process.argv[i];
  if (a === "--once") args.once = true;
  else if (a.startsWith("--")) args[a.slice(2)] = process.argv[++i];
}
const CHECKOUT = path.resolve(args.checkout || ".");
const ROOT = fs.existsSync(path.join(CHECKOUT, "site", "_config.yml")) ? path.join(CHECKOUT, "site") : CHECKOUT;
const PORT = Number(args.port || 0);
const STATE = args.state ? path.resolve(args.state) : null;
const ENGINE = args.engine ? path.resolve(args.engine) : "";

function say(m) { console.log(new Date().toISOString().slice(0, 19) + "Z " + m); }

if (!ENGINE || !fs.existsSync(path.join(ENGINE, "build.mjs"))) {
  // An unfilled mount is an empty directory, not an error to most tools: make it loud.
  say("no jekyll-enough at " + (ENGINE || "(none given)") + " (fcpm workshed check says where it looks)");
  process.exit(2);
}
if (!fs.existsSync(path.join(ROOT, "_config.yml"))) {
  say("no _config.yml in " + CHECKOUT + " or its site/: not a site this can build");
  process.exit(2);
}
const { buildSite } = await import(pathToFileURL(path.join(ENGINE, "build.mjs")).href);

// Text goes to the builder as strings (it renders pages and reads _data); everything else rides along as
// bytes, which the builder copies through as a static file untouched.
const TEXT = new Set([".md", ".markdown", ".html", ".htm", ".yml", ".yaml", ".json", ".css", ".js", ".mjs",
  ".txt", ".xml", ".svg", ".webmanifest", ".csv", ".liquid", ""]);
const SKIP = new Set([".git", "node_modules", "_site", ".jekyll-cache", ".sass-cache", "vendor", ".bundle"]);

function readTree() {
  const tree = {};
  (function walk(dir, rel) {
    for (const d of fs.readdirSync(dir, { withFileTypes: true })) {
      if (SKIP.has(d.name)) continue;
      const p = path.join(dir, d.name), r = rel ? rel + "/" + d.name : d.name;
      if (d.isDirectory()) walk(p, r);
      else if (d.isFile()) {
        const buf = fs.readFileSync(p);
        tree[r] = TEXT.has(path.extname(d.name).toLowerCase()) ? buf.toString("utf8").replace(/^﻿/, "") : buf;
      }
    }
  })(ROOT, "");
  return tree;
}

function frontOf(text) {
  // title and permalink only, for the Helm's index; the builder's own reader does the real work.
  const m = /^---\r?\n([\s\S]*?)\r?\n---/.exec(typeof text === "string" ? text : "");
  if (!m) return null;
  const get = (k) => { const x = new RegExp("^" + k + ":[ \\t]*(.*)$", "m").exec(m[1]); return x ? x[1].replace(/^["']|["']$/g, "").trim() : ""; };
  return { title: get("title"), permalink: get("permalink") };
}

let site = {}, built = null;
function write(name, obj) {
  if (!STATE) return;
  fs.mkdirSync(STATE, { recursive: true });
  const tmp = path.join(STATE, name + ".tmp");
  fs.writeFileSync(tmp, JSON.stringify(obj, null, 1) + "\n");
  fs.renameSync(tmp, path.join(STATE, name));
}

function build() {
  const t0 = Date.now(), gaps = [];
  let tree;
  try {
    tree = readTree();
    const out = buildSite(tree, { lenient: true, gaps, time: new Date().toISOString() });
    site = out;
  } catch (exc) {
    built = { ok: false, error: String(exc && exc.message || exc), at: new Date().toISOString() };
    say("build FAILED: " + built.error);
    write("status.json", { ...built, pid: process.pid, port: PORT, root: ROOT });
    return false;
  }
  const ms = Date.now() - t0, uniq = [...new Set(gaps)];
  // The index: every page the build wrote, by the URL a visitor would type, with its title.
  const pages = [];
  for (const [src, text] of Object.entries(tree)) {
    if (!/\.(md|markdown|html)$/.test(src) || src.startsWith("_")) continue;
    const f = frontOf(text);
    if (!f) continue;
    const url = f.permalink || "/" + src.replace(/\.(md|markdown|html)$/, "").replace(/(^|\/)index$/, "$1") + (/(^|\/)index\.\w+$/.test(src) ? "" : "/");
    const want = url.endsWith("/") ? "_site" + url + "index.html" : "_site" + url;
    if (!(want in site) && !(("_site" + url) in site)) continue;   // excluded by the config: not a page
    pages.push({ url: url.replace(/\/+/g, "/"), title: f.title, source: src });
  }
  pages.sort((a, b) => a.url.localeCompare(b.url));
  built = { ok: true, at: new Date().toISOString(), ms, files: Object.keys(site).length, gaps: uniq };
  write("pages.json", pages);
  write("status.json", { ...built, pid: process.pid, port: PORT, root: ROOT });
  say("built " + built.files + " files in " + ms + " ms" + (uniq.length ? ", " + uniq.length + " gaps: " + uniq.slice(0, 5).join("; ") + (uniq.length > 5 ? "; ..." : "") : ""));
  return true;
}

const TYPES = {
  ".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8", ".js": "text/javascript; charset=utf-8",
  ".mjs": "text/javascript; charset=utf-8", ".json": "application/json", ".webmanifest": "application/manifest+json",
  ".xml": "application/xml", ".txt": "text/plain; charset=utf-8", ".svg": "image/svg+xml", ".png": "image/png",
  ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp", ".avif": "image/avif",
  ".ico": "image/x-icon", ".woff": "font/woff", ".woff2": "font/woff2", ".ttf": "font/ttf", ".otf": "font/otf",
  ".mp4": "video/mp4", ".webm": "video/webm", ".mp3": "audio/mpeg", ".pdf": "application/pdf",
};

function handle(req, res) {
  let p;
  try { p = decodeURIComponent(new URL(req.url, "http://localhost").pathname); } catch { p = "/"; }
  if (p === "/__workshed") {                       // the Helm asks this to know it is up, and which build
    res.writeHead(200, { "Content-Type": "application/json", "Cache-Control": "no-store" });
    return res.end(JSON.stringify({ ...built, checkout: CHECKOUT, root: ROOT, port: PORT }));
  }
  let key = "_site" + p;
  if (p.endsWith("/")) key += "index.html";
  else if (!(key in site) && (key + "/index.html") in site) {
    res.writeHead(301, { Location: p + "/" });
    return res.end();
  } else if (!(key in site) && (key + ".html") in site) key += ".html";
  let status = 200;
  if (!(key in site)) { status = 404; key = "_site/404.html"; }
  const body = site[key];
  if (body == null) { res.writeHead(404, { "Content-Type": TYPES[".txt"] }); return res.end("not built: " + p + "\n"); }
  res.writeHead(status, { "Content-Type": TYPES[path.extname(key).toLowerCase()] || "application/octet-stream",
                          "Cache-Control": "no-store" });
  res.end(body);
}

if (!build() && args.once) process.exit(1);
if (args.once) {
  if (built.gaps.length) for (const g of built.gaps) say("gap: " + g);
  process.exit(0);
}

let timer = null;
fs.watch(ROOT, { recursive: true }, (_ev, name) => {
  const n = String(name || "").replace(/\\/g, "/");
  if (n.split("/").some((s) => SKIP.has(s))) return;
  clearTimeout(timer);
  timer = setTimeout(() => { say("changed: " + n); build(); }, 300);
});

let listening = 0;
for (const host of ["127.0.0.1", "::1"]) {
  const srv = http.createServer(handle);
  srv.on("error", (exc) => {
    if (host === "::1" && exc.code === "EADDRNOTAVAIL") return;   // no IPv6 here: 127.0.0.1 is enough
    say("cannot listen on " + host + ":" + PORT + ": " + exc.code);
    process.exit(3);
  });
  srv.listen(PORT, host, () => { if (++listening === 1) say("serving " + ROOT + " at http://localhost:" + PORT + "/"); });
}
