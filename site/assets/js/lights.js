// see docs/inline/site/assets/js/lights.js.md#1

import { encodeQR } from "./qr-encode.mjs";

const QUIET = 4;           // modules of white around the code
const WIZARD = "wizard:kiosk+lights";

// Local time with its offset, to the second: 2026-10-08T22:00:00-06:00.
export function localIso(d) {
  const p = n => String(Math.trunc(Math.abs(n))).padStart(2, "0");
  const off = -d.getTimezoneOffset();
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`
    + `${off >= 0 ? "+" : "-"}${p(off / 60)}:${p(off % 60)}`;
}

// 16 bytes of fresh randomness, base64url without padding (22 characters).
export function nonce() {
  const b = crypto.getRandomValues(new Uint8Array(16));
  return btoa(String.fromCharCode(...b)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

// The next time the clock reads hh:mm: today if it's still ahead, else tomorrow.
export function nextAt(hhmm, now = new Date()) {
  const [h, m] = hhmm.split(":").map(Number);
  const d = new Date(now);
  d.setHours(h, m, 0, 0);
  if (d <= now) d.setDate(d.getDate() + 1);
  return d;
}

// The reply, in the kiosk's key order. `until` only means something for "on".
export function reply(lights, until, now = new Date()) {
  const r = { schema: "fcpm.reply/v0", wizard: WIZARD, lights };
  if (lights === "on") r.until = localIso(until);
  r.issued = localIso(now);
  r.nonce = nonce();
  r.sig = null;
  return JSON.stringify(r);
}

function draw(canvas, qr) {
  // see docs/inline/site/assets/js/lights.js.md#2
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

export function start(root) {
  const canvas = root.querySelector("canvas");
  const until = root.querySelector("[name=until]");
  const read = root.querySelector("[data-read]");
  const on = () => root.querySelector("[name=lights]:checked").value;
  if (!until.value) until.value = "22:00";
  let text = "";

  function render() {
    const lights = on();
    root.dataset.lights = lights;
    until.disabled = lights !== "on";
    text = reply(lights, nextAt(until.value || "22:00"));
    const qr = encodeQR(text, { ecLevel: "M" });
    draw(canvas, qr);
    canvas.dataset.reply = text;   // for the page's tests; the code is the reply
    read.textContent = `v${qr.version} · ${qr.size} · ${new TextEncoder().encode(text).length} B`;
  }

  // A new nonce on every render: a code is never shown twice.
  root.addEventListener("change", render);
  canvas.addEventListener("click", render);
  addEventListener("resize", render);
  document.addEventListener("visibilitychange", () => { if (!document.hidden) render(); });
  // Keep the phone's screen up while the code is held to the camera.
  const wake = () => navigator.wakeLock?.request("screen").catch(() => {});
  wake();
  document.addEventListener("visibilitychange", () => { if (!document.hidden) wake(); });
  render();
}

const root = document.querySelector("[data-lights-reply]");
if (root) start(root);
