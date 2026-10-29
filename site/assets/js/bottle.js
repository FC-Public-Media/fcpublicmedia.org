// A wizard's reply, poured for our camera. The reply is kept text (its bytes never change once made);
// pouring it signs it with this browser's own key (Ed25519 in WebCrypto, kept here, its fingerprint the
// pseudonym), packs it as a transfer and draws it as AC1 fountain frames, 48 bytes a frame: a video
// from the first byte, and any enough of it heals. The composer is anecdote.channel's (./composer/,
// vendored), the same the door and the qr screen read with. Without Ed25519 (Safari before 17) the
// same frames carry the reply unsigned: the intake checks its hash and records it as `unsigned`. Only
// without the composer or WebCrypto at all (plain http) is it one plain code. See docs/kiosk.md#replies.

import { encodeQR } from './qr-encode.mjs';

const QUIET = 4, FPS = 4, DROPLET = 48;   // bytes per frame: low, so every bottle is a video
const KEY = 'fcpm.key';

let composer;
async function loadComposer() {
  if (composer !== undefined) return composer;
  try {
    const [sign, transfer, carrier, anecdote] = await Promise.all(
      ['sign', 'transfer', 'carrier', 'anecdote'].map((m) => import(`./composer/${m}.mjs`)));
    composer = { ...sign, ...transfer, ...carrier, defaultHash: anecdote.defaultHash };
  } catch (error) {
    composer = null;
  }
  return composer;
}

// ---- the reply's own parts ----------------------------------------------------------------------

// Local time with its offset, to the second: 2026-10-28T19:02:11-06:00.
export function localIso(d) {
  const p = (n) => String(Math.trunc(Math.abs(n))).padStart(2, '0');
  const off = -d.getTimezoneOffset();
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`
    + `${off >= 0 ? '+' : '-'}${p(off / 60)}:${p(off % 60)}`;
}

// 16 bytes of fresh randomness, base64url without padding.
export function nonce() {
  const b = crypto.getRandomValues(new Uint8Array(16));
  return btoa(String.fromCharCode(...b)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

// ---- this browser's key --------------------------------------------------------------------------

const ALG = { name: 'Ed25519' };
async function identity(c) {
  if (!c || !crypto.subtle) return null;
  try {
    let jwk = JSON.parse(localStorage.getItem(KEY) || 'null');
    if (!jwk) {
      const pair = await crypto.subtle.generateKey(ALG, true, ['sign', 'verify']);
      jwk = await crypto.subtle.exportKey('jwk', pair.privateKey);
      localStorage.setItem(KEY, JSON.stringify(jwk));
    }
    const privateKey = await crypto.subtle.importKey('jwk', jwk, ALG, false, ['sign']);
    const { d, key_ops, ...pub } = jwk;
    const publicKey = await crypto.subtle.importKey('jwk', pub, ALG, true, ['verify']);
    const raw = new Uint8Array(await crypto.subtle.exportKey('raw', publicKey));
    return { privateKey, publicKey, raw, fingerprint: await c.fingerprint(raw) };
  } catch (error) {
    return null;
  }
}

export function forgetKey() {
  try { localStorage.removeItem(KEY); } catch (error) { /* nothing kept */ }
}

// ---- drawing ---------------------------------------------------------------------------------------

function draw(canvas, qr) {
  const box = canvas.parentElement.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  const n = qr.size + 2 * QUIET;
  const scale = Math.max(1, Math.floor(Math.min(box.width, box.height) * dpr / n));
  canvas.width = canvas.height = n * scale;
  canvas.style.width = canvas.style.height = `${(n * scale) / dpr}px`;
  const g = canvas.getContext('2d');
  g.fillStyle = '#fff';
  g.fillRect(0, 0, canvas.width, canvas.height);
  g.fillStyle = '#000';
  for (let r = 0; r < qr.size; r++)
    for (let c = 0; c < qr.size; c++)
      if (qr.modules[r][c]) g.fillRect((c + QUIET) * scale, (r + QUIET) * scale, scale, scale);
}

// Pour `text` onto `canvas` until stop() is called. Resolves to { stop, signed, read }: `read` is one
// line about what is showing. canvas.dataset.frames holds every frame, for the page's tests.
// The transfer envelope with no signature: what packTransfer makes, before it signs.
async function unsignedTransfer(c, bytes) {
  return { schema: c.TRANSFER, kind: 'fcpm.reply', size: bytes.length, hash: await c.defaultHash(bytes),
           bytes: btoa(String.fromCharCode(...bytes)) };
}

export async function pour(canvas, text, { sign = true } = {}) {
  const c = await loadComposer();
  const me = sign ? await identity(c) : null;
  const bytes = new TextEncoder().encode(text);
  let frames, read, timer = null, at = 0;
  if (c && crypto.subtle) {
    const bottle = me ? await c.packTransfer('fcpm.reply', bytes, me) : await unsignedTransfer(c, bytes);
    const ft = await c.fountainTransfer(bottle, { blockSize: DROPLET });
    const strings = ft.frames(Math.max(40, ft.K * 4));
    frames = strings.map((s) => encodeQR(s, { ecLevel: 'M' }));
    canvas.dataset.frames = JSON.stringify(strings);
    read = `${ft.K} blocks · ${frames.length} frames · ${FPS}/s · `
      + (me ? `signed ${me.fingerprint.slice(11, 19)}` : 'unsigned');
  } else {
    frames = [encodeQR(text, { ecLevel: 'M' })];
    canvas.dataset.frames = JSON.stringify([text]);
    read = `one code · ${c ? 'no WebCrypto here' : 'no composer'}: unsigned`;
  }
  const tick = () => { draw(canvas, frames[at]); at = (at + 1) % frames.length; };
  tick();
  if (frames.length > 1) timer = setInterval(tick, 1000 / FPS);
  const redraw = () => draw(canvas, frames[(at + frames.length - 1) % frames.length]);
  addEventListener('resize', redraw);
  return {
    signed: Boolean(c && crypto.subtle && me),
    read,
    stop() {
      clearInterval(timer);
      removeEventListener('resize', redraw);
    },
  };
}
