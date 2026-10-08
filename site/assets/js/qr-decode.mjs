// Vendored from FCCN-ANTIBODY/anecdote.channel composer/qr-decode.mjs @ 048af64bebbdce7b8f92f69123a5f4afd736eaff,
// unchanged below this header. The kiosk's camera reads with it (machines/kiosk-1/door.py, THE CAMERA).
// composer/qr-decode.mjs — "the bigger lens": a vendorless QR DECODER (docs/offline-transfer.md,
// docs/anti-signature.md "acquire-by-doing"). The encoder (qr-encode.mjs) made us a sender; this makes any
// browser a RECEIVER — BarcodeDetector is absent on iOS Safari and headless Linux (measured), so we bring
// our own. It reads pixels (a camera frame, a screenshot, a rendered PNG) or a clean module matrix, and
// returns the text — correcting real errors through Reed–Solomon, which is what lets a dented tile still
// speak (and a too-dented one fail HONESTLY instead of lying).
//
// Two entry points:
//   decodeMatrix(modules)            — a clean 0/1 grid → { text, version, ecLevel, mask, corrected }
//   decodeImage({data,width,height}) — RGBA or grayscale pixels → locate + sample + decodeMatrix
// The pixel path: grayscale → adaptive threshold (integral image) → finder-pattern scan (1:1:3:1:1 runs,
// cross-checked) → perspective transform from the three finders (+ inferred fourth corner) → grid sample.
// Mirrored codes (scanned through glass) are retried transposed. All four ECC levels, versions 1–40,
// byte / alphanumeric / numeric modes (kanji is refused honestly).
//
// Shares the spec tables and the function-module map with the encoder — the decoder must skip exactly the
// cells the encoder painted.

import { TOTAL_CW, BLOCKS, ALIGN, EC_BITS, MASKS, functionModules } from "./qr-encode.mjs";

// ---- GF(256) (primitive 0x11d — same field as the encoder) -------------------------------------------
const EXP = new Uint8Array(512), LOG = new Uint8Array(256);
(() => { let x = 1; for (let i = 0; i < 255; i++) { EXP[i] = x; LOG[x] = i; x <<= 1; if (x & 0x100) x ^= 0x11d; } for (let i = 255; i < 512; i++) EXP[i] = EXP[i - 255]; })();
const mul = (a, b) => (a === 0 || b === 0 ? 0 : EXP[LOG[a] + LOG[b]]);
const inv = (a) => EXP[255 - LOG[a]];
const polyEval = (p, x) => { let y = p[0]; for (let i = 1; i < p.length; i++) y = mul(y, x) ^ p[i]; return y; };   // big-endian coeffs

// ---- Reed–Solomon DECODE with error correction --------------------------------------------------------
// `word` = [data…, ec…] exactly as the encoder emits (c[0] is the highest power). Corrects up to
// floor(ec/2) byte errors IN PLACE. Returns { ok, corrected } — ok:false means uncorrectable (too dented).
export function rsDecode(word, ec) {
  const n = word.length;
  const synd = [];                                       // S[j] = C(α^j), j = 0..ec-1
  let clean = true;
  for (let j = 0; j < ec; j++) { const s = polyEval(word, EXP[j]); synd.push(s); if (s) clean = false; }
  if (clean) return { ok: true, corrected: 0 };

  // Berlekamp–Massey → error locator σ (big-endian coefficient list)
  let errLoc = [1], oldLoc = [1];
  for (let i = 0; i < ec; i++) {
    oldLoc.push(0);
    let delta = synd[i];
    for (let j = 1; j < errLoc.length; j++) delta ^= mul(errLoc[errLoc.length - 1 - j], synd[i - j]);
    if (delta !== 0) {
      if (oldLoc.length > errLoc.length) {
        const newLoc = oldLoc.map((c) => mul(c, delta));
        oldLoc = errLoc.map((c) => mul(c, inv(delta)));
        errLoc = newLoc;
      }
      const scaled = oldLoc.map((c) => mul(c, delta));
      const off = errLoc.length - scaled.length;
      const merged = errLoc.slice();
      for (let j = 0; j < scaled.length; j++) merged[off + j] ^= scaled[j];
      errLoc = merged;
    }
  }
  while (errLoc.length && errLoc[0] === 0) errLoc.shift();
  const nErr = errLoc.length - 1;
  if (nErr === 0 || nErr * 2 > ec) return { ok: false, corrected: 0 };

  // Chien search: array index k has an error iff σ(α^{-(n-1-k)}) = 0
  const errPos = [];                                     // array indices
  for (let k = 0; k < n; k++) { const p = n - 1 - k; if (polyEval(errLoc, EXP[(255 - (p % 255)) % 255]) === 0) errPos.push(k); }
  if (errPos.length !== nErr) return { ok: false, corrected: 0 };

  // Forney: Ω(x) = S(x)·σ(x) mod x^ec  (both little-endian here), magnitudes from Ω/σ'
  const syndLE = synd.slice();                           // S as little-endian poly
  const locLE = errLoc.slice().reverse();
  const omega = new Array(ec).fill(0);
  for (let i = 0; i < syndLE.length; i++) for (let j = 0; j < locLE.length; j++) { if (i + j < ec) omega[i + j] ^= mul(syndLE[i], locLE[j]); }
  for (const k of errPos) {
    const p = n - 1 - k, X = EXP[p % 255], Xi = inv(X);
    let num = 0; for (let i = omega.length - 1; i >= 0; i--) num = mul(num, Xi) ^ omega[i];           // Ω(X^{-1})
    let den = 0; for (let i = 1; i < locLE.length; i += 2) { let t = locLE[i]; let xp = 1; for (let q = 0; q < i - 1; q++) xp = mul(xp, Xi); den ^= mul(t, xp); }  // σ'(X^{-1})
    if (den === 0) return { ok: false, corrected: 0 };
    word[k] ^= mul(X, mul(num, inv(den)));               // b=0 ⇒ magnitude = X·Ω(X⁻¹)/σ'(X⁻¹)
  }
  for (let j = 0; j < ec; j++) if (polyEval(word, EXP[j]) !== 0) return { ok: false, corrected: 0 };  // recheck
  return { ok: true, corrected: nErr };
}

// ---- format info (tolerant): match against all 32 candidates, min Hamming distance ------------------
const msb = (x) => { let p = -1; while (x) { x >>>= 1; p++; } return p; };
function bchFormat(fmt5) { let d = fmt5 << 10; while (msb(d) >= 10) d ^= 0x537 << (msb(d) - 10); return ((fmt5 << 10) | d) ^ 0x5412; }
const FORMATS = (() => { const out = []; for (const level of ["L", "M", "Q", "H"]) for (let mask = 0; mask < 8; mask++) out.push({ level, mask, bits: bchFormat((EC_BITS[level] << 3) | mask) }); return out; })();
const hamming = (a, b) => { let x = a ^ b, c = 0; while (x) { c += x & 1; x >>>= 1; } return c; };

function readFormat(m) {
  const s = m.length;
  // both copies, cells in spec order i=0..14 (the encoder wrote bit (14-i) at position i)
  const copy1 = [];
  for (let i = 0; i <= 5; i++) copy1.push(m[8][i]);
  copy1.push(m[8][7], m[8][8], m[7][8]);
  for (let i = 9; i <= 14; i++) copy1.push(m[14 - i][8]);
  const copy2 = [];
  for (let i = 0; i <= 6; i++) copy2.push(m[s - 1 - i][8]);
  for (let i = 7; i <= 14; i++) copy2.push(m[8][s - 15 + i]);
  const toVal = (cells) => cells.reduce((v, bit, i) => v | ((bit ? 1 : 0) << (14 - i)), 0);
  let best = null;
  for (const v of [toVal(copy1), toVal(copy2)]) for (const f of FORMATS) { const d = hamming(v, f.bits); if (!best || d < best.d) best = { d, ...f }; }
  return best && best.d <= 3 ? best : null;
}

// ---- matrix → text ------------------------------------------------------------------------------------
const ALNUM = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ $%*+-./:";

export function decodeMatrix(modules) {
  const size = modules.length;
  if (size < 21 || (size - 17) % 4 !== 0) return null;
  const version = (size - 17) / 4;
  if (version > 40) return null;
  const fmt = readFormat(modules);
  if (!fmt) return null;
  const { level, mask } = fmt;

  const x = functionModules(version);
  const maskFn = MASKS[mask];
  const bits = [];
  let up = true;
  for (let col = size - 1; col > 0; col -= 2) {
    if (col === 6) col--;
    for (let i = 0; i < size; i++) { const row = up ? size - 1 - i : i; for (let c2 = 0; c2 < 2; c2++) { const cc = col - c2; if (!x.fn[row][cc]) bits.push((modules[row][cc] ? 1 : 0) ^ (maskFn(row, cc) ? 1 : 0)); } }
    up = !up;
  }
  const totalCW = TOTAL_CW[version];
  if (bits.length < totalCW * 8) return null;
  const cw = [];
  for (let i = 0; i < totalCW; i++) { let b = 0; for (let j = 0; j < 8; j++) b = (b << 1) | bits[i * 8 + j]; cw.push(b); }

  // de-interleave into blocks of [data…, ec…], correct each, concatenate the data
  const [ecPerBlock, groups] = BLOCKS[level][version];
  const lengths = []; for (const [count, dpb] of groups) for (let b = 0; b < count; b++) lengths.push(dpb);
  const nBlocks = lengths.length, maxLen = Math.max(...lengths);
  const totalData = lengths.reduce((a, b) => a + b, 0);
  const blocks = lengths.map((len) => ({ data: new Array(len), ec: new Array(ecPerBlock) }));
  let idx = 0;
  for (let i = 0; i < maxLen; i++) for (let bi = 0; bi < nBlocks; bi++) if (i < lengths[bi]) blocks[bi].data[i] = cw[idx++];
  for (let i = 0; i < ecPerBlock; i++) for (let bi = 0; bi < nBlocks; bi++) blocks[bi].ec[i] = cw[idx++];
  let corrected = 0;
  const data = [];
  for (const blk of blocks) {
    const word = [...blk.data, ...blk.ec];
    const r = rsDecode(word, ecPerBlock);
    if (!r.ok) return null;                             // too dented — fail honestly, never guess
    corrected += r.corrected;
    data.push(...word.slice(0, blk.data.length));
  }
  if (data.length !== totalData) return null;

  // parse mode segments
  const stream = []; for (const b of data) for (let j = 7; j >= 0; j--) stream.push((b >> j) & 1);
  let p = 0;
  const take = (nb) => { let v = 0; for (let k = 0; k < nb; k++) v = (v << 1) | (stream[p++] || 0); return v; };
  const left = () => stream.length - p;
  const out = [];
  while (left() >= 4) {
    const mode = take(4);
    if (mode === 0) break;                              // terminator
    if (mode === 0b0100) {                              // byte
      const len = take(version <= 9 ? 8 : 16);
      if (left() < len * 8) return null;
      for (let i = 0; i < len; i++) out.push(take(8));
    } else if (mode === 0b0010) {                       // alphanumeric
      const len = take(version <= 9 ? 9 : version <= 26 ? 11 : 13);
      let got = 0;
      while (got + 2 <= len) { const v = take(11); out.push(ALNUM.charCodeAt(Math.floor(v / 45)), ALNUM.charCodeAt(v % 45)); got += 2; }
      if (got < len) out.push(ALNUM.charCodeAt(take(6)));
    } else if (mode === 0b0001) {                       // numeric
      const len = take(version <= 9 ? 10 : version <= 26 ? 12 : 14);
      let got = 0;
      while (got + 3 <= len) { const v = take(10); out.push(48 + Math.floor(v / 100), 48 + (Math.floor(v / 10) % 10), 48 + (v % 10)); got += 3; }
      if (len - got === 2) { const v = take(7); out.push(48 + Math.floor(v / 10), 48 + (v % 10)); }
      else if (len - got === 1) out.push(48 + take(4));
    } else if (mode === 0b0111) {                       // ECI — read the designator, assume UTF-8, continue
      const first = take(8);
      if ((first & 0x80) !== 0) take((first & 0x40) !== 0 ? 16 : 8);
    } else {
      return null;                                      // kanji / structured append — refused honestly
    }
  }
  return { text: new TextDecoder().decode(new Uint8Array(out)), version, ecLevel: level, mask, corrected };
}

// ---- pixels → matrix ----------------------------------------------------------------------------------

function toGray(data, width, height) {
  if (data.length === width * height) return data;      // already gray
  const g = new Uint8Array(width * height);
  for (let i = 0, j = 0; i < g.length; i++, j += 4) g[i] = (data[j] * 77 + data[j + 1] * 150 + data[j + 2] * 29) >> 8;
  return g;
}

// adaptive threshold via integral image: dark = below a fraction of the local mean
function binarize(gray, w, h, frac = 0.85) {
  const ii = new Float64Array((w + 1) * (h + 1));
  for (let y = 0; y < h; y++) { let row = 0; for (let x = 0; x < w; x++) { row += gray[y * w + x]; ii[(y + 1) * (w + 1) + x + 1] = ii[y * (w + 1) + x + 1] + row; } }
  const win = Math.max(15, ((Math.min(w, h) / 8) | 0) | 1);
  const half = win >> 1;
  const bin = new Uint8Array(w * h);                     // 1 = dark
  for (let y = 0; y < h; y++) {
    const y0 = Math.max(0, y - half), y1 = Math.min(h, y + half + 1);
    for (let x = 0; x < w; x++) {
      const x0 = Math.max(0, x - half), x1 = Math.min(w, x + half + 1);
      const sum = ii[y1 * (w + 1) + x1] - ii[y0 * (w + 1) + x1] - ii[y1 * (w + 1) + x0] + ii[y0 * (w + 1) + x0];
      const mean = sum / ((y1 - y0) * (x1 - x0));
      bin[y * w + x] = gray[y * w + x] < mean * frac ? 1 : 0;
    }
  }
  return bin;
}

// finder-pattern candidates: rows of 1:1:3:1:1 runs, cross-checked down the column
function findFinders(bin, w, h) {
  const cands = [];
  const ratioOK = (r) => {
    const m = (r[0] + r[1] + r[2] + r[3] + r[4]) / 7;
    if (m < 1) return 0;
    const t = m * 0.75;
    return (Math.abs(r[0] - m) < t && Math.abs(r[1] - m) < t && Math.abs(r[2] - 3 * m) < 3 * t && Math.abs(r[3] - m) < t && Math.abs(r[4] - m) < t) ? m : 0;
  };
  // walk a line through (cx,cy) along one axis, expect 1:1:3:1:1 — returns the refined center or null
  const crossCheck = (cx, cy, mEst, vertical) => {
    const at = (t) => (vertical ? bin[t * w + cx] : bin[cy * w + t]);
    const limit = vertical ? h : w, start = vertical ? cy : cx;
    const runs = [0, 0, 0, 0, 0];
    let back = 0, t = start;
    while (t >= 0 && at(t)) { back++; t--; }                     // center dark run, backward part
    for (let i = 1; i >= 0 && t >= 0; i--) while (t >= 0 && at(t) === (i % 2 === 0 ? 1 : 0)) { runs[i]++; t--; }
    let fwd = 0; t = start + 1;
    while (t < limit && at(t)) { fwd++; t++; }                   // center dark run, forward part
    for (let i = 3; i <= 4 && t < limit; i++) while (t < limit && at(t) === (i % 2 === 0 ? 1 : 0)) { runs[i]++; t++; }
    runs[2] = back + fwd;
    const m = ratioOK(runs);
    if (!m || Math.abs(m - mEst) > mEst) return null;
    return start - back + runs[2] / 2;                           // refined center along the walked axis
  };
  for (let y = 0; y < h; y++) {
    const runs = []; let x = 0;
    while (x < w) { const v = bin[y * w + x]; let n = 0; while (x < w && bin[y * w + x] === v) { n++; x++; } runs.push({ v, n, end: x }); }
    for (let i = 0; i + 4 < runs.length; i++) {
      if (runs[i].v !== 1) continue;
      const r = [runs[i].n, runs[i + 1].n, runs[i + 2].n, runs[i + 3].n, runs[i + 4].n];
      const m = ratioOK(r);
      if (!m) continue;
      let cx = runs[i + 4].end - r[4] - r[3] - Math.ceil(r[2] / 2);
      const cy = crossCheck(cx, y, m, true);
      if (cy == null) continue;
      const cx2 = crossCheck(Math.round(cx), Math.round(cy), m, false);   // horizontal re-check at the refined y
      if (cx2 == null) continue;
      cx = cx2;
      // merge with an existing candidate if close AND the module size agrees — without the size gate,
      // data-pattern rows beside a finder drag the cluster off-center and inflate its m (a feedback loop:
      // bigger m → wider merge radius → more pollution). Seen at scale 3; the gate closes it.
      let merged = false;
      for (const c of cands) if (Math.abs(c.x - cx) < 3 * m && Math.abs(c.y - cy) < 3 * m && Math.abs(c.m - m) < 0.6 * Math.min(c.m, m)) { c.x = (c.x * c.hits + cx) / (c.hits + 1); c.y = (c.y * c.hits + cy) / (c.hits + 1); c.m = (c.m * c.hits + m) / (c.hits + 1); c.hits++; merged = true; break; }
      if (!merged) cands.push({ x: cx, y: cy, m, hits: 1 });
    }
  }
  // refine each surviving cluster with a final cross-check pass — the exact center comes from walking
  // the pattern, not from averaging merged rows (residual drift otherwise misaligns the whole grid)
  const out = cands.filter((c) => c.hits >= 2);
  for (const c of out) {
    const cy2 = crossCheck(Math.round(c.x), Math.round(c.y), c.m, true);
    if (cy2 == null) continue;
    const cx2 = crossCheck(Math.round(c.x), Math.round(cy2), c.m, false);
    if (cx2 != null) { c.x = cx2; c.y = cy2; }
  }
  return out.sort((a, b) => b.hits - a.hits);
}

// perspective transform: module-space quad → pixel quad (zxing-style square↔quadrilateral composition)
function squareToQuad(p) {
  const [[x0, y0], [x1, y1], [x2, y2], [x3, y3]] = p;
  const dx3 = x0 - x1 + x2 - x3, dy3 = y0 - y1 + y2 - y3;
  if (dx3 === 0 && dy3 === 0) return [x1 - x0, x3 - x0, x0, y1 - y0, y3 - y0, y0, 0, 0, 1];   // affine
  const dx1 = x1 - x2, dx2 = x3 - x2, dy1 = y1 - y2, dy2 = y3 - y2;
  const den = dx1 * dy2 - dx2 * dy1;
  const a13 = (dx3 * dy2 - dx2 * dy3) / den, a23 = (dx1 * dy3 - dx3 * dy1) / den;
  return [x1 - x0 + a13 * x1, x3 - x0 + a23 * x3, x0, y1 - y0 + a13 * y1, y3 - y0 + a23 * y3, y0, a13, a23, 1];
}
function adjugate(t) {
  const [a11, a21, a31, a12, a22, a32, a13, a23, a33] = t;
  return [a22 * a33 - a23 * a32, a23 * a31 - a21 * a33, a21 * a32 - a22 * a31,
          a13 * a32 - a12 * a33, a11 * a33 - a13 * a31, a12 * a31 - a11 * a32,
          a12 * a23 - a13 * a22, a13 * a21 - a11 * a23, a11 * a22 - a12 * a21];
}
// zxing's times() convention (column-major flat layout t[col*3+row]): out = b-then-a in APPLY order —
// compose(A, B) applied to a point runs B first, then A. Hand-verified against known correspondences.
function compose(a, b) {
  const o = new Array(9);
  for (let j = 0; j < 3; j++) for (let i = 0; i < 3; i++) { let s = 0; for (let k = 0; k < 3; k++) s += a[j * 3 + k] * b[k * 3 + i]; o[j * 3 + i] = s; }
  return o;
}
function quadToQuad(src, dst) { return compose(squareToQuad(dst), adjugate(squareToQuad(src))); }
function apply(t, u, v) { const d = t[6] * u + t[7] * v + t[8]; return [(t[0] * u + t[1] * v + t[2]) / d, (t[3] * u + t[4] * v + t[5]) / d]; }

// the lens innards, exposed for gap-hunting (tests probe each stage — observability on the probe)
export const _lens = { toGray, binarize, findFinders, quadToQuad, apply };

// Decode from pixels. `data` is RGBA (w*h*4) or grayscale (w*h). Returns decodeMatrix's result + geometry,
// or null. Tries a couple of threshold biases and the mirrored orientation before giving up.
// Under this many pixels per module the geometry estimate and the one-sample-per-
// module read have no room to be wrong in, even when the code is perfectly intact.
const RETRY_UNDER_PX = 8;    // located a code this small and failed → worth another look
const TARGET_MODULE_PX = 10; // measured: 7px→72%, 8.8px→92%, 10.5px→99% on the same bits

// Crop a region and blow it up nearest-neighbour. Adds NO information — it buys
// spatial room. Cropping first keeps the cost proportional to the code, not the
// frame, which is what makes this affordable on a phone at camera frame rates.
function cropUp({ data, width, height }, box, n) {
  const chans = data.length / (width * height);
  const x0 = Math.max(0, box.x | 0), y0 = Math.max(0, box.y | 0);
  const cw = Math.min(width - x0, Math.ceil(box.w)), ch = Math.min(height - y0, Math.ceil(box.h));
  const w = cw * n, h = ch * n, out = new Uint8ClampedArray(w * h * chans);
  for (let y = 0; y < h; y++) {
    const sy = y0 + ((y / n) | 0);
    for (let x = 0; x < w; x++) {
      const s = (sy * width + x0 + ((x / n) | 0)) * chans, d = (y * w + x) * chans;
      for (let c = 0; c < chans; c++) out[d + c] = data[s + c];
    }
  }
  return { img: { data: out, width: w, height: h }, x0, y0 };
}

export function decodeImage({ data, width, height }, opts = {}) {
  const gray = toGray(data, width, height);
  let weakest = null;                  // smallest code we LOCATED but could not read
  for (const frac of [0.85, 1.0, 0.72]) {
    const bin = binarize(gray, width, height, frac);
    const finders = findFinders(bin, width, height);
    if (finders.length < 3) continue;
    // choose the trio: strong candidates first (a real finder is seen on many rows — a data-region
    // impostor on few), then score by geometry — a right angle between two equal legs
    const maxHits = finders[0].hits;
    const strong = finders.filter((f) => f.hits * 3 >= maxHits);
    const pool = strong.length >= 3 ? strong : finders;
    let trio = pool.slice(0, 3);
    if (pool.length > 3) {
      let best = null;
      for (let a = 0; a < pool.length - 2; a++) for (let b = a + 1; b < pool.length - 1; b++) for (let c = b + 1; c < pool.length; c++) {
        const t = [pool[a], pool[b], pool[c]];
        const ms = t.map((f) => f.m), spread = (Math.max(...ms) - Math.min(...ms)) / Math.min(...ms);
        let geo = Infinity;
        for (let i = 0; i < 3; i++) {
          const [p, q2, r2] = [t[i], t[(i + 1) % 3], t[(i + 2) % 3]];
          const v1 = [q2.x - p.x, q2.y - p.y], v2 = [r2.x - p.x, r2.y - p.y];
          const l1 = Math.hypot(...v1), l2 = Math.hypot(...v2);
          if (!l1 || !l2) continue;
          const dot = Math.abs(v1[0] * v2[0] + v1[1] * v2[1]) / (l1 * l2);          // 0 at a right angle
          const legs = Math.abs(l1 - l2) / Math.max(l1, l2);                        // 0 for equal legs
          geo = Math.min(geo, dot + legs);
        }
        const score = geo + spread - (t.reduce((s2, f) => s2 + f.hits, 0) / (3 * maxHits)) * 0.5;
        if (!best || score < best.score) best = { t, score };
      }
      trio = best.t;
    }
    // order: TL is the corner where the angle to the other two is closest to 90°
    let tl = null, bestDot = Infinity;
    for (let i = 0; i < 3; i++) {
      const [p, q, r] = [trio[i], trio[(i + 1) % 3], trio[(i + 2) % 3]];
      const v1 = [q.x - p.x, q.y - p.y], v2 = [r.x - p.x, r.y - p.y];
      const dot = Math.abs(v1[0] * v2[0] + v1[1] * v2[1]) / (Math.hypot(...v1) * Math.hypot(...v2));
      if (dot < bestDot) { bestDot = dot; tl = i; }
    }
    const TL = trio[tl]; let A = trio[(tl + 1) % 3], B = trio[(tl + 2) % 3];
    // TR is the one such that cross(TL→TR, TL→BL) > 0 (screen coords, y down)
    const cross = (a, b) => (a.x - TL.x) * (b.y - TL.y) - (a.y - TL.y) * (b.x - TL.x);
    let TR = A, BL = B;
    if (cross(A, B) < 0) { TR = B; BL = A; }
    const mSize = (TL.m + TR.m + BL.m) / 3;
    const dimEst = (Math.hypot(TR.x - TL.x, TR.y - TL.y) / mSize + Math.hypot(BL.x - TL.x, BL.y - TL.y) / mSize) / 2 + 7;
    let dim = Math.round((dimEst - 17) / 4) * 4 + 17;
    if (dim < 21) dim = 21; if (dim > 177) dim = 177;
    const Q4 = { x: TR.x + BL.x - TL.x, y: TR.y + BL.y - TL.y };
    const T = quadToQuad(
      [[3.5, 3.5], [dim - 3.5, 3.5], [dim - 3.5, dim - 3.5], [3.5, dim - 3.5]],
      [[TL.x, TL.y], [TR.x, TR.y], [Q4.x, Q4.y], [BL.x, BL.y]]);
    const modules = [];
    for (let v = 0; v < dim; v++) {
      const row = new Array(dim);
      for (let u = 0; u < dim; u++) {
        const [px, py] = apply(T, u + 0.5, v + 0.5);
        const xi = px | 0, yi = py | 0;
        row[u] = xi >= 0 && yi >= 0 && xi < width && yi < height ? bin[yi * width + xi] : 0;
      }
      modules.push(row);
    }
    let r = decodeMatrix(modules);
    if (!r) {                                            // mirrored? (glass, front camera) — transpose
      const t = modules.map((row, i) => row.map((_, j) => modules[j][i]));
      r = decodeMatrix(t);
      if (r) r.mirrored = true;
    }
    if (r) return { ...r, dim, moduleSize: mSize, finders: { TL, TR, BL } };
    if (!weakest || mSize < weakest.mSize) weakest = { mSize, pts: [TL, TR, BL, Q4] };
  }
  // We FOUND a code and could not read it, and its modules are only a couple of
  // pixels across — the failure is scale, not damage. Blowing up nearest-neighbour
  // gives the geometry and the sampler room without inventing detail: measured
  // 0% → 99% on a loop that SMS had shrunk to 2.6 px/module, whose data OpenCV
  // could read all along. Gated on finders having been located, so a frame with
  // no code in it costs nothing extra — which matters at camera frame rates.
  if (!opts.rescaled && weakest && weakest.mSize < RETRY_UNDER_PX) {
    const n = Math.min(6, Math.max(2, Math.round(TARGET_MODULE_PX / weakest.mSize)));
    const xs = weakest.pts.map((p) => p.x), ys = weakest.pts.map((p) => p.y);
    const pad = 5 * weakest.mSize;                                  // quiet zone + slack
    const box = { x: Math.min(...xs) - pad, y: Math.min(...ys) - pad,
                  w: Math.max(...xs) - Math.min(...xs) + 2 * pad,
                  h: Math.max(...ys) - Math.min(...ys) + 2 * pad };
    const { img, x0, y0 } = cropUp({ data, width, height }, box, n);
    const r = decodeImage(img, { rescaled: true });
    if (r) return { ...r, moduleSize: r.moduleSize / n, rescaledBy: n,
      finders: Object.fromEntries(Object.entries(r.finders).map(([k, f]) =>
        [k, { ...f, x: x0 + f.x / n, y: y0 + f.y / n, m: f.m / n }])) };
  }
  return null;
}
