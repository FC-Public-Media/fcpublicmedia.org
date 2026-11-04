// loop.js — the public fountain (door.py, /loop/): every answer the model gave today, in turn, as AC1
// fountain frames, with the index between them. A phone in the cradle watches; it reads the index (each
// question's nonce, its label, its bottle's id), then keeps only the frames of the bottles it wants and
// lets the rest go by. Others seeing them is the point. The bottles are made by machines/digitization/asks;
// this page only draws them, so any screen can show it, on any browser, over plain http.
//
// ?fps=N    frames a second (8).  ?index=N  the index again after every N answers (3).
// Each bottle gets K and a bit fresh droplets a pass (any K-and-a-bit rebuild it: the fountain's promise), then
// the loop moves on; the next pass takes the next droplets of its stock, so a phone that caught half the first
// time gets new ones, not the same again. The loop flows; nothing waits on a slow reader.
// Both may change any time: the next frame uses them. What is shown is asked again after every pass,
// so the loop is a pointer on a set that changes under it, never a fixed reel.
import { encodeQR } from "/js/qr-encode.mjs";

const QUIET = 4;
const P = new URLSearchParams(location.search);
const knob = (k, d) => Math.max(1, Math.min(30, Number(P.get(k)) || d));
let fps = knob("fps", 8), every = knob("index", 3);
const offset = new Map();                 // bottle id -> where in its stock the next pass starts
const share = (b) => Math.min(b.frames.length, Math.ceil((b.K || b.frames.length / 4) * 1.15) + 2);
const canvas = document.getElementById("code"), said = document.getElementById("said"), what = document.getElementById("what");

function draw(text) {
  const qr = encodeQR(text, { ecLevel: "M" });
  const box = canvas.parentElement.getBoundingClientRect(), dpr = window.devicePixelRatio || 1;
  const n = qr.size + 2 * QUIET, scale = Math.max(1, Math.floor(Math.min(box.width, box.height) * dpr / n));
  canvas.width = canvas.height = n * scale;
  canvas.style.width = canvas.style.height = `${(n * scale) / dpr}px`;
  const g = canvas.getContext("2d");
  g.fillStyle = "#fff"; g.fillRect(0, 0, canvas.width, canvas.height);
  g.fillStyle = "#000";
  for (let r = 0; r < qr.size; r++)
    for (let c = 0; c < qr.size; c++)
      if (qr.modules[r][c]) g.fillRect((c + QUIET) * scale, (r + QUIET) * scale, scale, scale);
}

// One pass: the index, then the answers, the index again after every `every` of them.
function pass(now) {
  if (!now.index) return [];
  const steps = [{ index: true, b: now.index }];
  now.bottles.forEach((b, i) => {
    steps.push({ index: false, b });
    if ((i + 1) % every === 0 && i + 1 < now.bottles.length) steps.push({ index: true, b: now.index });
  });
  return steps;
}

let steps = [], step = 0, at = 0, timer = null;
// This pass's droplets for a bottle: the next `share` of its stock, wrapping round.
function slice(b) {
  const from = offset.get(b.id) || 0, n = share(b);
  offset.set(b.id, (from + n) % b.frames.length);
  return Array.from({ length: n }, (_, i) => b.frames[(from + i) % b.frames.length]);
}
async function next() {
  try {
    const now = await (await fetch("/loop/now", { cache: "no-store" })).json();
    steps = pass(now).map((s) => ({ ...s, shown: slice(s.b) })); step = 0; at = 0;
    if (!steps.length) {
      canvas.width = canvas.height = 0;
      what.textContent = "Nothing answered today yet.";
      said.textContent = "";
    }
  } catch (error) {
    steps = [];
  }
}

async function tick() {
  if (!steps.length) { await next(); return schedule(); }
  const s = steps[step];
  if (at === 0) {
    what.textContent = s.index ? `Index · ${s.b.answers} answer${s.b.answers === 1 ? "" : "s"}`
                               : (s.b.label || "An answer");
    said.textContent = s.index ? `${s.b.id.slice(7, 15)} · ${fps}/s`
                               : `for …${String(s.b.in_reply_to).slice(-6)} · ${s.b.id.slice(7, 15)} · ${fps}/s`;
  }
  draw(s.shown[at]);
  if (++at >= s.shown.length) {
    at = 0;
    if (++step >= steps.length) await next();
  }
  schedule();
}
function schedule() { timer = setTimeout(tick, 1000 / fps); }

addEventListener("popstate", () => {
  const p = new URLSearchParams(location.search);
  fps = Math.max(1, Math.min(30, Number(p.get("fps")) || fps));
  every = Math.max(1, Math.min(30, Number(p.get("index")) || every));
});
await next();
schedule();
