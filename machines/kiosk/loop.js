// loop.js — the public fountain (door.py, /loop/): every answer on the air, in turn, as AC1 fountain frames, with
// the index between them. Everyone catches everything: a phone in the cradle keeps its own answers and carries
// the rest to the people they answer. The bottles are made by machines/digitization/asks; this page only draws
// them, so any screen can show it, on any browser, over plain http.
//
// ?fps=N    frames a second (8).  ?index=N  the index again after every N answers (3).
// ?up=N     codes up at once: 1, 2 (side by side) or 4 (two by two). Each tile takes the next bottle of the pass
//           as it finishes its own, so several bottles are on the air together; a phone reads them all at once.
// ?tiles=N  the press's collage (anecdote.channel press/broadcast.mjs): N droplets of the SAME bottle on screen at
//           once, redundancy in space, so one good look catches N pieces; each bottle's share goes by N times
//           faster. Smaller codes, so the camera needs to be closer or better. With ?up it applies to each tile.
// Each bottle gets K and a bit fresh droplets a pass (any K-and-a-bit rebuild it: the fountain's promise), then
// its tile moves on; the next pass takes the next droplets of its stock, so a phone that caught half the first
// time gets new ones, not the same again. The loop flows; nothing waits on a slow reader.
// Every few seconds it asks /loop/head: a recalled answer that takes the loop over (wizard:loop+recall,
// takeover) is shown at once on every tile, then the loop goes back to what it was doing.
import { encodeQR } from "/js/qr-encode.mjs";

const QUIET = 4;
const P = new URLSearchParams(location.search);
const knob = (k, d, most = 30) => Math.max(1, Math.min(most, Number(P.get(k)) || d));
const fps = knob("fps", 8), every = knob("index", 3), up = [1, 2, 4].includes(knob("up", 1, 4)) ? knob("up", 1, 4) : 1;
const tilesEach = knob("tiles", 1, 16), side = Math.ceil(Math.sqrt(tilesEach));
const said = document.getElementById("said"), what = document.getElementById("what"), box = document.getElementById("tiles");
box.style.setProperty("--cols", up === 1 ? 1 : 2);
box.style.setProperty("--rows", up === 4 ? 2 : 1);
box.replaceChildren(...Array.from({ length: up }, () => {
  const d = document.createElement("div");
  d.className = "up";
  d.style.cssText = `display:grid; gap:1.2vmin; grid-template-columns:repeat(${side}, auto); align-content:center; justify-content:center;`;
  for (let i = 0; i < tilesEach; i++) d.append(Object.assign(document.createElement("canvas"), { className: "code" }));
  return d;
}));
const tiles = [...box.querySelectorAll("div.up")].map((d) => ({ canvases: [...d.querySelectorAll("canvas")], step: null, at: 0 }));

const offset = new Map();                 // bottle id -> where in its stock the next pass starts
const share = (b) => Math.min(b.frames.length, Math.ceil((b.K || b.frames.length / 4) * 1.15) + 2);
function slice(b) {                       // this pass's droplets for a bottle: the next `share` of its stock
  const from = offset.get(b.id) || 0, n = share(b);
  offset.set(b.id, (from + n) % b.frames.length);
  return Array.from({ length: n }, (_, i) => b.frames[(from + i) % b.frames.length]);
}

function draw(canvas, text) {
  const qr = encodeQR(text, { ecLevel: "M" });
  const area = canvas.parentElement.getBoundingClientRect(), dpr = window.devicePixelRatio || 1;
  const room = Math.min(area.width, area.height) / side - 8;    // a collage's tiles share their part of the screen
  const n = qr.size + 2 * QUIET, scale = Math.max(1, Math.floor(room * dpr / n));
  canvas.width = canvas.height = n * scale;
  canvas.style.width = canvas.style.height = `${(n * scale) / dpr}px`;
  const g = canvas.getContext("2d");
  g.fillStyle = "#fff"; g.fillRect(0, 0, canvas.width, canvas.height);
  g.fillStyle = "#000";
  for (let r = 0; r < qr.size; r++)
    for (let c = 0; c < qr.size; c++)
      if (qr.modules[r][c]) g.fillRect((c + QUIET) * scale, (r + QUIET) * scale, scale, scale);
}
const blank = (canvas) => { canvas.width = canvas.height = 0; };

// One pass: the index, then the answers, the index again after every `every` of them.
function pass(now) {
  if (!now.index) return [];
  const steps = [{ index: true, b: now.index }];
  now.bottles.forEach((b, i) => {
    steps.push({ index: false, b });
    if ((i + 1) % every === 0 && i + 1 < now.bottles.length) steps.push({ index: true, b: now.index });
  });
  return steps.map((s) => ({ ...s, shown: slice(s.b) }));
}

let queue = [], latest = null, lastNow = null, headId = null, takeover = null;
async function next() {
  try {
    latest = await (await fetch("/loop/now", { cache: "no-store" })).json();
    queue = pass(latest);
    headId = latest.index && latest.index.id;
  } catch (error) {
    queue = [];
  }
}

// A takeover: the recalled answers, at once, on every tile; the loop resumes when they have been shown.
async function watchHead() {
  try {
    const head = await (await fetch("/loop/head", { cache: "no-store" })).json();
    const now = head.now;
    if (now && now.at !== lastNow) {
      lastNow = now.at;
      if (head.id !== headId) await next();
      const wanted = (latest && latest.bottles || []).filter((b) => now.nonces.includes(b.in_reply_to));
      if (wanted.length) {
        takeover = wanted.map((b) => ({ index: false, b, shown: slice(b), takeover: true }));
        for (const t of tiles) { t.step = null; t.at = 0; }
      }
    } else if (!lastNow && now) {
      lastNow = now.at;                   // a takeover from before this page opened is old news
    }
  } catch (error) { /* the next look will do */ }
  setTimeout(watchHead, 3000);
}

function caption() {
  const on = tiles.filter((t) => t.step).map((t) => t.step);
  if (!on.length) {
    what.textContent = latest && latest.index ? "" : "Nothing on the air.";
    said.textContent = "";
    return;
  }
  const s = on[0];
  what.textContent = on.length > 1 ? on.map((x) => (x.index ? "Index" : x.b.label || "An answer")).join(" · ")
    : s.index ? `Index · ${latest.bottles.length} answer${latest.bottles.length === 1 ? "" : "s"}` : (s.b.label || "An answer");
  said.textContent = (s.takeover ? "asked for again · " : "") + `${fps}/s` + (up > 1 ? ` · ${up} up` : "")
    + (tilesEach > 1 ? ` · ${tilesEach} pieces at once` : "");
}

async function tick() {
  if (!queue.length && !takeover && tiles.every((t) => !t.step)) await next();
  let changed = false;
  for (const t of tiles) {
    if (!t.step) {
      const src = takeover || queue;
      t.step = src.shift() || null; t.at = 0; changed = true;
      if (takeover && !takeover.length) takeover = null;
    }
    if (!t.step) { for (const c of t.canvases) blank(c); continue; }
    t.canvases.forEach((c, i) => (t.at + i < t.step.shown.length ? draw(c, t.step.shown[t.at + i]) : blank(c)));
    t.at += t.canvases.length;
    if (t.at >= t.step.shown.length) { t.step = null; changed = true; }
  }
  if (changed) caption();
  setTimeout(tick, 1000 / fps);
}

await next();
caption();
tick();
watchHead();
