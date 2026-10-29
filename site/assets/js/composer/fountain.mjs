// Vendored from FCCN-ANTIBODY/anecdote.channel composer/fountain.mjs @ 800162ca7643ec6adeee7cd15424e47d10b602c7,
// unchanged below this header, by way of troves/scanner/composer. The check-in pours its bottle with it (bottle.js).
// composer/fountain.mjs — rateless erasure coding for the video/streaming carrier (docs/offline-transfer.md).
// The upgrade from fixed-index bricks: instead of "catch all N specific frames," the sender emits an ENDLESS
// stream of DROPLETS (each an XOR of a random subset of the source blocks), and the receiver reconstructs the
// whole payload from ANY sufficient subset — so a lost or damaged frame is just one you make up for by
// catching another. "Loop as many times as a bad camera needs" (origin.md). Damage-heals-with-resilience:
// corrupt frames are dropped at the frame layer (they carry a checksum) and become mere erasures, which the
// fountain fills from the rest; the whole-payload signature/checksum still has the final say.
//
// Scheme: Luby-Transform (LT) codes with a robust-soliton degree distribution and a peeling (belief-
// propagation) decoder. A droplet is self-describing from a tiny SEED: encoder and decoder derive the same
// degree + source-index set from the seed, so a droplet carries only { K, B, L, s, xor } — the combination
// is recomputed, not transmitted. Pure, vendorless, deterministic.

// ---- deterministic PRNG (encoder + decoder must agree bit-for-bit from a seed) ----------------------
function mulberry32(a) {
  return function () { a |= 0; a = (a + 0x6D2B79F5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
}

// ---- robust soliton degree distribution (cached per K) ----------------------------------------------
const solitonCache = new Map();
function robustSoliton(K, c = 0.1, delta = 0.5) {
  if (K <= 1) return { sample: () => 1 };
  if (solitonCache.has(K)) return solitonCache.get(K);
  const rho = new Float64Array(K + 1); rho[1] = 1 / K;
  for (let d = 2; d <= K; d++) rho[d] = 1 / (d * (d - 1));
  const R = c * Math.log(K / delta) * Math.sqrt(K);
  const tau = new Float64Array(K + 1); const kr = Math.max(1, Math.floor(K / R));
  for (let d = 1; d < kr; d++) tau[d] = R / (d * K);
  if (kr <= K) tau[kr] = (R * Math.log(R / delta)) / K;
  let Z = 0; for (let d = 1; d <= K; d++) Z += rho[d] + tau[d];
  const cdf = new Float64Array(K + 1); let acc = 0;
  for (let d = 1; d <= K; d++) { acc += (rho[d] + tau[d]) / Z; cdf[d] = acc; }
  const s = { sample(u) { for (let d = 1; d <= K; d++) if (u <= cdf[d]) return d; return K; } };
  solitonCache.set(K, s); return s;
}

// The droplet's combination (degree + which source blocks), derived deterministically from its seed.
function dropletPlan(seed, K, soliton) {
  const rng = mulberry32(((seed >>> 0) ^ 0x9e3779b9) >>> 0);
  const d = Math.min(K, Math.max(1, soliton.sample(rng())));
  const idx = new Set();
  while (idx.size < d) idx.add(Math.floor(rng() * K));
  return [...idx];
}

function xorInto(dst, src) { for (let i = 0; i < dst.length; i++) dst[i] ^= src[i]; }

// ---- encode: a rateless droplet generator -----------------------------------------------------------
// Returns { K, B, L, droplet(seed) }. Pull droplet(0), droplet(1), … as many as you want — MORE droplets =
// MORE resilience. Nothing is fixed at N; the stream is endless.
export function ltEncode(bytes, { blockSize = 256 } = {}) {
  const L = bytes.length;
  const B = Math.max(1, blockSize);
  const K = Math.max(1, Math.ceil(L / B));
  const soliton = robustSoliton(K);
  const src = [];
  for (let i = 0; i < K; i++) { const b = new Uint8Array(B); b.set(bytes.subarray(i * B, Math.min(L, (i + 1) * B))); src.push(b); }
  const droplet = (seed) => {
    const xor = new Uint8Array(B);
    for (const idx of dropletPlan(seed, K, soliton)) xorInto(xor, src[idx]);
    return { v: "lt1", K, B, L, s: seed >>> 0, xor };
  };
  return { K, B, L, droplet };
}

// ---- decode: peeling / belief propagation -----------------------------------------------------------
// Feed droplets in any order; it reconstructs once enough independent ones have arrived. `add` returns
// { done, recovered } (recovered = source blocks solved so far, of K). Duplicate/redundant droplets are
// harmless. Ignores a droplet whose (K,B,L) disagree (a different payload's droplet).
export function ltDecoder(K, B, L) {
  const soliton = robustSoliton(K);
  const recovered = new Array(K).fill(null);
  const containing = Array.from({ length: K }, () => new Set());   // source idx -> pending droplets that still include it
  const pending = new Set();
  let have = 0;

  function recover(i, block, work) { if (recovered[i]) return; recovered[i] = block; have++; work.push(i); }
  function drain(work) {
    while (work.length) {
      const i = work.pop();
      for (const d of [...containing[i]]) {
        if (!d.rem.has(i)) { containing[i].delete(d); continue; }
        xorInto(d.val, recovered[i]); d.rem.delete(i); containing[i].delete(d);
        if (d.rem.size === 1) { const j = [...d.rem][0]; pending.delete(d); d.rem.clear(); recover(j, d.val, work); }
        else if (d.rem.size === 0) pending.delete(d);
      }
    }
  }

  function add(drop) {
    if (have === K) return { done: true, recovered: have };
    if (drop.K !== K || drop.B !== B || drop.L !== L) return { done: false, recovered: have, ignored: true };
    const d = { rem: new Set(dropletPlan(drop.s, K, soliton)), val: drop.xor.slice() };
    const work = [];
    for (const idx of [...d.rem]) if (recovered[idx]) { xorInto(d.val, recovered[idx]); d.rem.delete(idx); }
    if (d.rem.size === 0) { /* redundant */ }
    else if (d.rem.size === 1) { const j = [...d.rem][0]; recover(j, d.val, work); }
    else { for (const idx of d.rem) containing[idx].add(d); pending.add(d); }
    drain(work);
    return { done: have === K, recovered: have };
  }
  function bytes() { if (have !== K) return null; const out = new Uint8Array(K * B); for (let i = 0; i < K; i++) out.set(recovered[i], i * B); return out.slice(0, L); }
  return { add, bytes, done: () => have === K, get recovered() { return have; }, K, B, L };
}
