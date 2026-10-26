// host.js — wizard:kiosk+host, the staff check-in for a room (door.py, /host/). The page helps one
// person form one reply: I am hosting this room (or I have left), until when, and what is in it. The
// reply is bottled (a signed transfer, poured as AC1 fountain frames: a video from the first byte, so
// a long one costs nothing new) for a camera, or set down over the LAN as the same bytes (POST /drop).
// Nothing is applied here: replies.py reads the bottle later. The composer is the scanner trove's,
// served by the door from troves/scanner/composer when checked out; without it the code is the bare
// reply as one QR, and the drop still works.
import { encodeQR } from "./qr-encode.mjs";

const C = JSON.parse(document.getElementById("host-config").textContent);
const WIZARD = "wizard:kiosk+host";
const QUIET = 4, FPS = 4, DROPLET = 48;        // bytes per frame: low, so every bottle is a video
const PROFILE = "fcpm-host-profile", KEY = "fcpm-host-key";

let composer = null;
try {
  const [sign, transfer, carrier] = await Promise.all(
    ["sign", "transfer", "carrier"].map((m) => import(`./composer/${m}.mjs`)));
  composer = { ...sign, ...transfer, ...carrier };
} catch (e) { composer = null; }

// ---- the phone's own key: Ed25519 in WebCrypto, kept here, its fingerprint the pseudonym -------------
const store = {
  get(k) { try { return JSON.parse(localStorage.getItem(k)); } catch { return null; } },
  set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch {} },
};
const ALG = { name: "Ed25519" };
async function identity() {
  if (!composer || !crypto.subtle) return null;
  try {
    let jwk = store.get(KEY);
    if (!jwk) {
      const pair = await crypto.subtle.generateKey(ALG, true, ["sign", "verify"]);
      jwk = await crypto.subtle.exportKey("jwk", pair.privateKey);
      store.set(KEY, jwk);
    }
    const privateKey = await crypto.subtle.importKey("jwk", jwk, ALG, false, ["sign"]);
    const { d, key_ops, ...pub } = jwk;
    const publicKey = await crypto.subtle.importKey("jwk", pub, ALG, true, ["verify"]);
    const raw = new Uint8Array(await crypto.subtle.exportKey("raw", publicKey));
    return { privateKey, publicKey, raw, fingerprint: await composer.fingerprint(raw) };
  } catch (e) { return null; }     // no Ed25519 here (older Safari): the reply goes unsigned
}

// ---- the reply -------------------------------------------------------------------------------------
export function localIso(d) {
  const p = (n) => String(Math.trunc(Math.abs(n))).padStart(2, "0");
  const off = -d.getTimezoneOffset();
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`
    + `${off >= 0 ? "+" : "-"}${p(off / 60)}:${p(off % 60)}`;
}
export function nonce() {
  const b = crypto.getRandomValues(new Uint8Array(16));
  return btoa(String.fromCharCode(...b)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}
export function nextAt(hhmm, now = new Date()) {
  const [h, m] = hhmm.split(":").map(Number);
  const d = new Date(now);
  d.setHours(h, m, 0, 0);
  if (d <= now) d.setDate(d.getDate() + 1);
  return d;
}
// The reply, in the door's key order. `at` is the wizard's commit: the form's version.
export function reply({ room, hosting, host, until, present, at }, now = new Date()) {
  const r = { schema: "fcpm.reply/v0", wizard: WIZARD, at, room, hosting, host };
  if (hosting) r.until = localIso(until);
  r.present = present;
  r.issued = localIso(now);
  r.nonce = nonce();
  r.sig = null;                     // the bottle's envelope signs; this stays for the shape
  return r;
}

// ---- drawing -----------------------------------------------------------------------------------------
function draw(canvas, qr) {
  const box = canvas.parentElement.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  const n = qr.size + 2 * QUIET;
  const scale = Math.max(1, Math.floor(Math.min(box.width, box.height) * dpr / n));
  canvas.width = canvas.height = n * scale;
  canvas.style.width = canvas.style.height = `${(n * scale) / dpr}px`;
  const g = canvas.getContext("2d");
  g.fillStyle = "#fff";
  g.fillRect(0, 0, canvas.width, canvas.height);
  g.fillStyle = "#000";
  for (let r = 0; r < qr.size; r++)
    for (let c = 0; c < qr.size; c++)
      if (qr.modules[r][c]) g.fillRect((c + QUIET) * scale, (r + QUIET) * scale, scale, scale);
}

// ---- the page ------------------------------------------------------------------------------------------
const el = (id) => document.getElementById(id);
const root = document.querySelector("[data-host]");
const canvas = root.querySelector("canvas"), read = el("read"), said = el("said");
const form = el("host-form");
const me = await identity();
let frames = [], frameAt = 0, timer = null, bottle = null, text = "";

function profile() { return store.get(PROFILE) || { name: "" }; }
function fields() {
  const hosting = form.elements.hosting.value === "on";
  const present = [...form.querySelectorAll("[name=present]:checked")].map((i) => i.value);
  return { room: C.room, hosting, host: el("name").value.trim(), until: nextAt(el("until").value || "23:59"),
           present, at: C.at };
}

async function render() {
  const f = fields();
  store.set(PROFILE, { name: f.host });
  root.dataset.hosting = f.hosting ? "on" : "off";
  el("until").disabled = !f.hosting;
  el("drop").disabled = f.hosting && !f.host;
  const r = reply(f);
  text = JSON.stringify(r);
  clearInterval(timer); timer = null;
  if (composer && me) {
    bottle = await composer.packTransfer("fcpm.reply", new TextEncoder().encode(text), me);
    const ft = await composer.fountainTransfer(bottle, { blockSize: DROPLET });
    const count = Math.max(40, ft.K * 4);
    frames = ft.frames(count).map((s) => encodeQR(s, { ecLevel: "M" }));
    frameAt = 0;
    draw(canvas, frames[0]);
    timer = setInterval(() => { frameAt = (frameAt + 1) % frames.length; draw(canvas, frames[frameAt]); }, 1000 / FPS);
    read.textContent = `bottle · ${ft.K} blocks of ${DROPLET} B · ${count} frames · v${frames[0].version} · ${FPS}/s · signed ${me.fingerprint.slice(11, 19)}`;
  } else {
    bottle = null;
    const qr = encodeQR(text, { ecLevel: "M" });
    frames = [qr];
    draw(canvas, qr);
    read.textContent = `plain code · v${qr.version} · ${new TextEncoder().encode(text).length} B · ${composer ? "no key on this phone" : "no composer here"}: unsigned`;
  }
  canvas.dataset.reply = text;
}

// Set down over the LAN: the same bytes the camera would read, kept first and read later.
async function dropIt() {
  const body = JSON.stringify(bottle || JSON.parse(text));
  said.textContent = "setting down…";
  let kept;
  try {
    const res = await fetch("/drop", { method: "POST", headers: { "Content-Type": "application/json" }, body });
    const d = await res.json();
    if (!res.ok) throw new Error(d.why || res.status);
    kept = d.kept;
  } catch (e) { said.textContent = "not kept: " + e.message; return; }
  said.textContent = "kept · waiting to be read";
  for (let i = 0; i < 40; i++) {
    await new Promise((ok) => setTimeout(ok, 1000));
    try {
      const s = await (await fetch(`/drop/${kept}`, { cache: "no-store" })).json();
      if (s.state === "applied") { said.textContent = "applied · " + (s.why || ""); render(); return; }
      if (s.state === "held") { said.textContent = "held · " + (s.why || ""); return; }
    } catch {}
  }
  said.textContent = "kept · not read yet (the door reads every half minute)";
}

// Names: the one the public check-in handed over (?name=), else the one this phone used last; the
// hosts.yml's people as one-tap picks.
const given = (new URLSearchParams(location.search).get("name") || "").trim().slice(0, 40);
el("name").value = given || profile().name || "";
const picks = el("picks");
(C.crew || []).forEach((n) => {
  const b = document.createElement("button");
  b.type = "button"; b.textContent = n;
  b.addEventListener("click", () => { el("name").value = n; render(); });
  picks.appendChild(b);
});
if (!el("until").value) el("until").value = "23:59";
form.addEventListener("change", render);
el("name").addEventListener("input", render);
canvas.addEventListener("click", render);      // a fresh nonce: a code is never shown twice on purpose
el("drop").addEventListener("click", dropIt);
addEventListener("resize", () => frames.length && draw(canvas, frames[frameAt]));
const wake = () => navigator.wakeLock?.request("screen").catch(() => {});
wake();
document.addEventListener("visibilitychange", () => { if (!document.hidden) { wake(); render(); } });
render();
