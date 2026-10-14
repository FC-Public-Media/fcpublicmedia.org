// Vendored from FCCN-ANTIBODY/anecdote.channel composer/qr-encode.mjs @ 6481e38bc7a5f44346be465b0091c3377b33552a,
// unchanged below this header. The kiosk reads with the same project's qr-decode.mjs. Refresh by copying it again.
// See docs/site.md.
// composer/qr-encode.mjs — "qr-enough": a vendorless byte-mode QR encoder (docs/offline-transfer.md). Just
// enough of the QR spec to render a payload as a scannable code — versions 1–40, all four ECC levels
// L/M/Q/H, byte mode (a signed poll URL runs ~800 B → a mid-teens version). The first hands-on carrier:
// a poll QR is a PLAIN URL QR any phone decodes → opens the answer runtime. The spec tables and the
// function-module map are exported — composer/qr-decode.mjs (the bigger lens) reads with the same charts
// this file draws by.
//
// Correctness without a scanner in this env is guarded three ways: (1) a codeword-count INVARIANT on the
// block tables (the typo-prone part) — asserted in the test; (2) format/version info via computed BCH and
// Reed–Solomon via computed GF(256), so no hand-typed magic numbers; (3) a SELF-DECODE round-trip in the
// test that reads the data back through inverse placement + unmask + de-interleave. Scanner interop is the
// physical phone test.

// ---- GF(256) for Reed–Solomon (primitive 0x11d) -----------------------------------------------------
const EXP = new Uint8Array(512), LOG = new Uint8Array(256);
(() => { let x = 1; for (let i = 0; i < 255; i++) { EXP[i] = x; LOG[x] = i; x <<= 1; if (x & 0x100) x ^= 0x11d; } for (let i = 255; i < 512; i++) EXP[i] = EXP[i - 255]; })();
const gfMul = (a, b) => (a === 0 || b === 0 ? 0 : EXP[LOG[a] + LOG[b]]);
export const _gf = { EXP, LOG, gfMul };   // exposed for the RS syndrome check in the test

export function rsGen(ec) { let g = [1]; for (let i = 0; i < ec; i++) { const ng = new Array(g.length + 1).fill(0); for (let j = 0; j < g.length; j++) { ng[j] ^= gfMul(g[j], EXP[i]); ng[j + 1] ^= g[j]; } g = ng; } return g; }
export function rsEncode(data, ec) {
  // rsGen returns the generator constant-first (g[ec] = leading monic term). The LFSR remainder wants the
  // non-leading coefficients highest-power-first, so drop the leading term and reverse.
  const div = rsGen(ec).slice(0, ec).reverse(), res = new Array(ec).fill(0);
  for (const d of data) { const f = d ^ res[0]; res.shift(); res.push(0); if (f !== 0) for (let j = 0; j < ec; j++) res[j] ^= gfMul(div[j], f); }
  return res;
}

// ---- spec tables (versions 1–40, ECC levels L & M) --------------------------------------------------
// Total codewords per version, and the block layout [ecPerBlock, [[blockCount, dataPerBlock], …]] and
// alignment-pattern centre coordinates. Generated from the ISO 18004 tables (cross-checked against segno);
// the codeword-count invariant in qr-encode.test.mjs guards against transcription errors.
export const TOTAL_CW = [0, 26, 44, 70, 100, 134, 172, 196, 242, 292, 346, 404, 466, 532, 581, 655, 733, 815, 901, 991, 1085, 1156, 1258, 1364, 1474, 1588, 1706, 1828, 1921, 2051, 2185, 2323, 2465, 2611, 2761, 2876, 3034, 3196, 3362, 3532, 3706];
export const BLOCKS = {
  L: {
    1: [7, [[1, 19]]], 2: [10, [[1, 34]]], 3: [15, [[1, 55]]], 4: [20, [[1, 80]]],
    5: [26, [[1, 108]]], 6: [18, [[2, 68]]], 7: [20, [[2, 78]]], 8: [24, [[2, 97]]],
    9: [30, [[2, 116]]], 10: [18, [[2, 68], [2, 69]]], 11: [20, [[4, 81]]], 12: [24, [[2, 92], [2, 93]]],
    13: [26, [[4, 107]]], 14: [30, [[3, 115], [1, 116]]], 15: [22, [[5, 87], [1, 88]]], 16: [24, [[5, 98], [1, 99]]],
    17: [28, [[1, 107], [5, 108]]], 18: [30, [[5, 120], [1, 121]]], 19: [28, [[3, 113], [4, 114]]], 20: [28, [[3, 107], [5, 108]]],
    21: [28, [[4, 116], [4, 117]]], 22: [28, [[2, 111], [7, 112]]], 23: [30, [[4, 121], [5, 122]]], 24: [30, [[6, 117], [4, 118]]],
    25: [26, [[8, 106], [4, 107]]], 26: [28, [[10, 114], [2, 115]]], 27: [30, [[8, 122], [4, 123]]], 28: [30, [[3, 117], [10, 118]]],
    29: [30, [[7, 116], [7, 117]]], 30: [30, [[5, 115], [10, 116]]], 31: [30, [[13, 115], [3, 116]]], 32: [30, [[17, 115]]],
    33: [30, [[17, 115], [1, 116]]], 34: [30, [[13, 115], [6, 116]]], 35: [30, [[12, 121], [7, 122]]], 36: [30, [[6, 121], [14, 122]]],
    37: [30, [[17, 122], [4, 123]]], 38: [30, [[4, 122], [18, 123]]], 39: [30, [[20, 117], [4, 118]]], 40: [30, [[19, 118], [6, 119]]],
  },
  M: {
    1: [10, [[1, 16]]], 2: [16, [[1, 28]]], 3: [26, [[1, 44]]], 4: [18, [[2, 32]]],
    5: [24, [[2, 43]]], 6: [16, [[4, 27]]], 7: [18, [[4, 31]]], 8: [22, [[2, 38], [2, 39]]],
    9: [22, [[3, 36], [2, 37]]], 10: [26, [[4, 43], [1, 44]]], 11: [30, [[1, 50], [4, 51]]], 12: [22, [[6, 36], [2, 37]]],
    13: [22, [[8, 37], [1, 38]]], 14: [24, [[4, 40], [5, 41]]], 15: [24, [[5, 41], [5, 42]]], 16: [28, [[7, 45], [3, 46]]],
    17: [28, [[10, 46], [1, 47]]], 18: [26, [[9, 43], [4, 44]]], 19: [26, [[3, 44], [11, 45]]], 20: [26, [[3, 41], [13, 42]]],
    21: [26, [[17, 42]]], 22: [28, [[17, 46]]], 23: [28, [[4, 47], [14, 48]]], 24: [28, [[6, 45], [14, 46]]],
    25: [28, [[8, 47], [13, 48]]], 26: [28, [[19, 46], [4, 47]]], 27: [28, [[22, 45], [3, 46]]], 28: [28, [[3, 45], [23, 46]]],
    29: [28, [[21, 45], [7, 46]]], 30: [28, [[19, 47], [10, 48]]], 31: [28, [[2, 46], [29, 47]]], 32: [28, [[10, 46], [23, 47]]],
    33: [28, [[14, 46], [21, 47]]], 34: [28, [[14, 46], [23, 47]]], 35: [28, [[12, 47], [26, 48]]], 36: [28, [[6, 47], [34, 48]]],
    37: [28, [[29, 46], [14, 47]]], 38: [28, [[13, 46], [32, 47]]], 39: [28, [[40, 47], [7, 48]]], 40: [28, [[18, 47], [31, 48]]],
  },
  Q: {
    1: [13, [[1, 13]]], 2: [22, [[1, 22]]], 3: [18, [[2, 17]]], 4: [26, [[2, 24]]],
    5: [18, [[2, 15], [2, 16]]], 6: [24, [[4, 19]]], 7: [18, [[2, 14], [4, 15]]], 8: [22, [[4, 18], [2, 19]]],
    9: [20, [[4, 16], [4, 17]]], 10: [24, [[6, 19], [2, 20]]], 11: [28, [[4, 22], [4, 23]]], 12: [26, [[4, 20], [6, 21]]],
    13: [24, [[8, 20], [4, 21]]], 14: [20, [[11, 16], [5, 17]]], 15: [30, [[5, 24], [7, 25]]], 16: [24, [[15, 19], [2, 20]]],
    17: [28, [[1, 22], [15, 23]]], 18: [28, [[17, 22], [1, 23]]], 19: [26, [[17, 21], [4, 22]]], 20: [30, [[15, 24], [5, 25]]],
    21: [28, [[17, 22], [6, 23]]], 22: [30, [[7, 24], [16, 25]]], 23: [30, [[11, 24], [14, 25]]], 24: [30, [[11, 24], [16, 25]]],
    25: [30, [[7, 24], [22, 25]]], 26: [28, [[28, 22], [6, 23]]], 27: [30, [[8, 23], [26, 24]]], 28: [30, [[4, 24], [31, 25]]],
    29: [30, [[1, 23], [37, 24]]], 30: [30, [[15, 24], [25, 25]]], 31: [30, [[42, 24], [1, 25]]], 32: [30, [[10, 24], [35, 25]]],
    33: [30, [[29, 24], [19, 25]]], 34: [30, [[44, 24], [7, 25]]], 35: [30, [[39, 24], [14, 25]]], 36: [30, [[46, 24], [10, 25]]],
    37: [30, [[49, 24], [10, 25]]], 38: [30, [[48, 24], [14, 25]]], 39: [30, [[43, 24], [22, 25]]], 40: [30, [[34, 24], [34, 25]]],
  },
  H: {
    1: [17, [[1, 9]]], 2: [28, [[1, 16]]], 3: [22, [[2, 13]]], 4: [16, [[4, 9]]],
    5: [22, [[2, 11], [2, 12]]], 6: [28, [[4, 15]]], 7: [26, [[4, 13], [1, 14]]], 8: [26, [[4, 14], [2, 15]]],
    9: [24, [[4, 12], [4, 13]]], 10: [28, [[6, 15], [2, 16]]], 11: [24, [[3, 12], [8, 13]]], 12: [28, [[7, 14], [4, 15]]],
    13: [22, [[12, 11], [4, 12]]], 14: [24, [[11, 12], [5, 13]]], 15: [24, [[11, 12], [7, 13]]], 16: [30, [[3, 15], [13, 16]]],
    17: [28, [[2, 14], [17, 15]]], 18: [28, [[2, 14], [19, 15]]], 19: [26, [[9, 13], [16, 14]]], 20: [28, [[15, 15], [10, 16]]],
    21: [30, [[19, 16], [6, 17]]], 22: [24, [[34, 13]]], 23: [30, [[16, 15], [14, 16]]], 24: [30, [[30, 16], [2, 17]]],
    25: [30, [[22, 15], [13, 16]]], 26: [30, [[33, 16], [4, 17]]], 27: [30, [[12, 15], [28, 16]]], 28: [30, [[11, 15], [31, 16]]],
    29: [30, [[19, 15], [26, 16]]], 30: [30, [[23, 15], [25, 16]]], 31: [30, [[23, 15], [28, 16]]], 32: [30, [[19, 15], [35, 16]]],
    33: [30, [[11, 15], [46, 16]]], 34: [30, [[59, 16], [1, 17]]], 35: [30, [[22, 15], [41, 16]]], 36: [30, [[2, 15], [64, 16]]],
    37: [30, [[24, 15], [46, 16]]], 38: [30, [[42, 15], [32, 16]]], 39: [30, [[10, 15], [67, 16]]], 40: [30, [[20, 15], [61, 16]]],
  },
};
export const ALIGN = {
  1: [], 2: [6, 18], 3: [6, 22], 4: [6, 26],
  5: [6, 30], 6: [6, 34], 7: [6, 22, 38], 8: [6, 24, 42],
  9: [6, 26, 46], 10: [6, 28, 50], 11: [6, 30, 54], 12: [6, 32, 58],
  13: [6, 34, 62], 14: [6, 26, 46, 66], 15: [6, 26, 48, 70], 16: [6, 26, 50, 74],
  17: [6, 30, 54, 78], 18: [6, 30, 56, 82], 19: [6, 30, 58, 86], 20: [6, 34, 62, 90],
  21: [6, 28, 50, 72, 94], 22: [6, 26, 50, 74, 98], 23: [6, 30, 54, 78, 102], 24: [6, 28, 54, 80, 106],
  25: [6, 32, 58, 84, 110], 26: [6, 30, 58, 86, 114], 27: [6, 34, 62, 90, 118], 28: [6, 26, 50, 74, 98, 122],
  29: [6, 30, 54, 78, 102, 126], 30: [6, 26, 52, 78, 104, 130], 31: [6, 30, 56, 82, 108, 134], 32: [6, 34, 60, 86, 112, 138],
  33: [6, 30, 58, 86, 114, 142], 34: [6, 34, 62, 90, 118, 146], 35: [6, 30, 54, 78, 102, 126, 150], 36: [6, 24, 50, 76, 102, 128, 154],
  37: [6, 28, 54, 80, 106, 132, 158], 38: [6, 32, 58, 84, 110, 136, 162], 39: [6, 26, 54, 82, 110, 138, 166], 40: [6, 30, 58, 86, 114, 142, 170],
};
export const EC_BITS = { L: 0b01, M: 0b00, Q: 0b11, H: 0b10 };

export function dataCodewords(version, level) { const [ec, groups] = BLOCKS[level][version]; let d = 0, n = 0; for (const [c, dpb] of groups) { d += c * dpb; n += c; } return { data: d, ec, blocks: n }; }

// ---- BCH (format + version info) --------------------------------------------------------------------
const msb = (x) => { let p = -1; while (x) { x >>>= 1; p++; } return p; };
function bchFormat(fmt5) { let d = fmt5 << 10; while (msb(d) >= 10) d ^= 0x537 << (msb(d) - 10); return ((fmt5 << 10) | d) ^ 0x5412; }
function bchVersion(v) { let d = v << 12; while (msb(d) >= 12) d ^= 0x1f25 << (msb(d) - 12); return (v << 12) | d; }

// ---- bit buffer -------------------------------------------------------------------------------------
class Bits { constructor() { this.a = []; } push(val, n) { for (let i = n - 1; i >= 0; i--) this.a.push((val >>> i) & 1); } get length() { return this.a.length; } }

// ---- byte-mode data codewords -----------------------------------------------------------------------
function byteData(bytes, version, level) {
  const { data: cap } = dataCodewords(version, level);
  const capBits = cap * 8;
  const countBits = version <= 9 ? 8 : 16;
  const bits = new Bits();
  bits.push(0b0100, 4);                 // byte mode
  bits.push(bytes.length, countBits);
  for (const b of bytes) bits.push(b, 8);
  if (bits.length + 4 <= capBits) bits.push(0, 4); else while (bits.length < capBits) bits.push(0, 1);   // terminator
  while (bits.length % 8) bits.push(0, 1);
  const cw = [];
  for (let i = 0; i < bits.length; i += 8) { let v = 0; for (let j = 0; j < 8; j++) v = (v << 1) | bits.a[i + j]; cw.push(v); }
  const pads = [0xec, 0x11]; let pi = 0; while (cw.length < cap) cw.push(pads[pi++ % 2]);
  return cw;
}

// Interleave data + EC codewords across blocks (QR ordering).
function interleave(cw, version, level) {
  const [ec, groups] = BLOCKS[level][version];
  const dataBlocks = [], ecBlocks = []; let p = 0;
  for (const [count, dpb] of groups) for (let b = 0; b < count; b++) { const blk = cw.slice(p, p + dpb); p += dpb; dataBlocks.push(blk); ecBlocks.push(rsEncode(blk, ec)); }
  const out = [];
  const maxD = Math.max(...dataBlocks.map((b) => b.length));
  for (let i = 0; i < maxD; i++) for (const b of dataBlocks) if (i < b.length) out.push(b[i]);
  for (let i = 0; i < ec; i++) for (const b of ecBlocks) out.push(b[i]);
  return out;
}

// ---- matrix + function patterns ---------------------------------------------------------------------
function newMatrix(size) { const m = [], fn = []; for (let r = 0; r < size; r++) { m.push(new Array(size).fill(null)); fn.push(new Array(size).fill(false)); } return { m, fn, size }; }
function setF(x, r, c, v) { x.m[r][c] = v ? 1 : 0; x.fn[r][c] = true; }
function placeFinder(x, r, c) { for (let dr = -1; dr <= 7; dr++) for (let dc = -1; dc <= 7; dc++) { const rr = r + dr, cc = c + dc; if (rr < 0 || cc < 0 || rr >= x.size || cc >= x.size) continue; const inRing = dr >= 0 && dr <= 6 && dc >= 0 && dc <= 6; const dark = inRing && ((dr === 0 || dr === 6 || dc === 0 || dc === 6) || (dr >= 2 && dr <= 4 && dc >= 2 && dc <= 4)); setF(x, rr, cc, dark ? 1 : 0); } }
function placeAlignment(x, r, c) { for (let dr = -2; dr <= 2; dr++) for (let dc = -2; dc <= 2; dc++) setF(x, r + dr, c + dc, (Math.abs(dr) === 2 || Math.abs(dc) === 2 || (dr === 0 && dc === 0)) ? 1 : 0); }

function functionPatterns(x, version) {
  const s = x.size;
  placeFinder(x, 0, 0); placeFinder(x, 0, s - 7); placeFinder(x, s - 7, 0);
  for (let i = 8; i < s - 8; i++) { const v = i % 2 === 0 ? 1 : 0; if (x.m[6][i] === null) setF(x, 6, i, v); if (x.m[i][6] === null) setF(x, i, 6, v); }   // timing
  const ac = ALIGN[version];
  for (const r of ac) for (const c of ac) { const nearFinder = (r <= 8 && c <= 8) || (r <= 8 && c >= s - 9) || (r >= s - 9 && c <= 8); if (!nearFinder) placeAlignment(x, r, c); }
  setF(x, s - 8, 8, 1);                                   // dark module
  // reserve format areas (filled later) so data placement skips them
  for (let i = 0; i < 9; i++) { if (x.m[8][i] === null) { x.m[8][i] = 0; x.fn[8][i] = true; } if (x.m[i][8] === null) { x.m[i][8] = 0; x.fn[i][8] = true; } }
  for (let i = 0; i < 8; i++) { x.fn[8][s - 1 - i] = true; x.m[8][s - 1 - i] = 0; }        // format copy 2 — horizontal (8 cells: cols s-8..s-1)
  for (let i = 0; i < 7; i++) { x.fn[s - 1 - i][8] = true; x.m[s - 1 - i][8] = 0; }        // format copy 2 — vertical (7 cells: rows s-1..s-7; (s-8,8) is the dark module)
  if (version >= 7) { for (let i = 0; i < 6; i++) for (let j = 0; j < 3; j++) { x.fn[i][s - 11 + j] = true; x.m[i][s - 11 + j] = 0; x.fn[s - 11 + j][i] = true; x.m[s - 11 + j][i] = 0; } }
}

function placeData(x, cw) {
  const s = x.size; let bit = 0; const total = cw.length * 8;
  const get = () => (bit < total ? (cw[bit >> 3] >> (7 - (bit & 7))) & 1 : 0);
  let up = true;
  for (let col = s - 1; col > 0; col -= 2) {
    if (col === 6) col--;                                 // skip timing column
    for (let i = 0; i < s; i++) { const row = up ? s - 1 - i : i; for (let c2 = 0; c2 < 2; c2++) { const cc = col - c2; if (x.m[row][cc] === null) { x.m[row][cc] = get(); bit++; } } }
    up = !up;
  }
}

export const MASKS = [(r, c) => (r + c) % 2 === 0, (r, c) => r % 2 === 0, (r, c) => c % 3 === 0, (r, c) => (r + c) % 3 === 0, (r, c) => (Math.floor(r / 2) + Math.floor(c / 3)) % 2 === 0, (r, c) => ((r * c) % 2) + ((r * c) % 3) === 0, (r, c) => (((r * c) % 2) + ((r * c) % 3)) % 2 === 0, (r, c) => (((r + c) % 2) + ((r * c) % 3)) % 2 === 0];
function applyMask(x, maskFn) { const o = x.m.map((row) => row.slice()); for (let r = 0; r < x.size; r++) for (let c = 0; c < x.size; c++) if (!x.fn[r][c] && maskFn(r, c)) o[r][c] ^= 1; return o; }

function penalty(m) {
  const s = m.length; let p = 0;
  const line = (get) => { let run = 1, prev = get(0); for (let i = 1; i < s; i++) { const v = get(i); if (v === prev) { run++; } else { if (run >= 5) p += 3 + (run - 5); run = 1; prev = v; } } if (run >= 5) p += 3 + (run - 5); };
  for (let r = 0; r < s; r++) line((i) => m[r][i]);
  for (let c = 0; c < s; c++) line((i) => m[i][c]);
  for (let r = 0; r < s - 1; r++) for (let c = 0; c < s - 1; c++) if (m[r][c] === m[r][c + 1] && m[r][c] === m[r + 1][c] && m[r][c] === m[r + 1][c + 1]) p += 3;
  const pat1 = [1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0], pat2 = [0, 0, 0, 0, 1, 0, 1, 1, 1, 0, 1];
  const scan = (get) => { for (let i = 0; i + 11 <= s; i++) { let a = true, b = true; for (let k = 0; k < 11; k++) { if (get(i + k) !== pat1[k]) a = false; if (get(i + k) !== pat2[k]) b = false; } if (a || b) p += 40; } };
  for (let r = 0; r < s; r++) scan((i) => m[r][i]);
  for (let c = 0; c < s; c++) scan((i) => m[i][c]);
  let dark = 0; for (let r = 0; r < s; r++) for (let c = 0; c < s; c++) dark += m[r][c]; const pct = (dark * 100) / (s * s); p += Math.floor(Math.abs(pct - 50) / 5) * 10;
  return p;
}

function writeFormat(m, x, level, mask) {
  const bits = bchFormat((EC_BITS[level] << 3) | mask), s = x.size;
  // The 15-bit format string is placed MSB-first: position i (0-based, in spec module order) carries
  // bit (14 − i) of the value. (Verified against segno/zbar — see qr-encode.test.mjs notes.)
  const B = (i) => (bits >> (14 - i)) & 1;
  // copy 1 (around the top-left finder)
  for (let i = 0; i <= 5; i++) m[8][i] = B(i);
  m[8][7] = B(6); m[8][8] = B(7); m[7][8] = B(8);
  for (let i = 9; i <= 14; i++) m[14 - i][8] = B(i);
  // copy 2 (bottom-left vertical, then top-right horizontal)
  for (let i = 0; i <= 6; i++) m[s - 1 - i][8] = B(i);   // rows s-1..s-7
  m[s - 8][8] = 1;                                        // dark module — always dark
  for (let i = 7; i <= 14; i++) m[8][s - 15 + i] = B(i);  // cols s-8..s-1
}
function writeVersion(m, x, version) { if (version < 7) return; const bits = bchVersion(version), s = x.size; for (let i = 0; i < 18; i++) { const b = (bits >> i) & 1; const r = Math.floor(i / 3), c = i % 3; m[s - 11 + c][r] = b; m[r][s - 11 + c] = b; } }

// The function-module map for a version — shared with the decoder (composer/qr-decode.mjs), which must
// skip exactly the same cells when it reads the zigzag back.
export function functionModules(version) { const x = newMatrix(17 + 4 * version); functionPatterns(x, version); return x; }

// ---- public API -------------------------------------------------------------------------------------

// Pick the smallest version 1–40 that fits `bytes` at `level`; throw if it doesn't fit v40.
export function chooseVersion(len, level = "M") {
  for (let v = 1; v <= 40; v++) { const { data } = dataCodewords(v, level); const countBits = v <= 9 ? 8 : 16; if (4 + countBits + 8 * len <= data * 8) return v; }
  throw new Error(`qr-enough: ${len} bytes exceeds version 40 at level ${level} (use a shorter URL or a chunked carrier)`);
}

// Encode text into a QR. Returns { version, size, ecLevel, mask, modules } where modules[r][c] is 0/1.
// `version` and `mask` are optional overrides (mask is normally chosen by penalty scoring; forcing it is for
// reference comparison / tests).
// Encode RAW BYTES — the real carrier (deflated bytes / a key / a signed token), which is not valid UTF-8
// and so cannot go through encodeQR's text path. Byte mode carries any octet stream unchanged.
export function encodeBytes(bytes, { ecLevel = "M", version, mask } = {}) {
  bytes = bytes instanceof Uint8Array ? bytes : new Uint8Array(bytes);
  const v = version || chooseVersion(bytes.length, ecLevel);
  const cw = interleave(byteData(bytes, v, ecLevel), v, ecLevel);
  const size = 17 + 4 * v;
  const x = newMatrix(size);
  functionPatterns(x, v);
  placeData(x, cw);
  const candidates = mask == null ? [0, 1, 2, 3, 4, 5, 6, 7] : [mask];
  let best = null;
  for (const mk of candidates) { const masked = applyMask(x, MASKS[mk]); writeFormat(masked, x, ecLevel, mk); writeVersion(masked, x, v); const pen = penalty(masked); if (!best || pen < best.pen) best = { mask: mk, masked, pen }; }
  return { version: v, size, ecLevel, mask: best.mask, modules: best.masked };
}
// Text is just a UTF-8 byte payload — the string path is a thin wrapper over the byte path.
export function encodeQR(text, opts = {}) { return encodeBytes(new TextEncoder().encode(text), opts); }

// SELF-DECODE (verification tool, not a general QR reader): reverse our own placement to recover the text —
// unmask, read codewords in the same zigzag, de-interleave the data blocks, parse byte mode. It trusts the
// EC codewords (a real scanner does Reed–Solomon); it proves the DATA path (placement/mask/interleave/mode).
// self-decode to raw BYTES (the byte-carrier round-trip): reverse our own placement — unmask, read
// codewords in the same zigzag, de-interleave, parse byte mode. Trusts the EC codewords (a real scanner
// runs Reed–Solomon); proves the DATA path (placement / mask / interleave / mode).
export function decodeBytesSelf(modules, version, ecLevel, mask) {
  const size = modules.length, x = newMatrix(size); functionPatterns(x, version);
  const maskFn = MASKS[mask], bits = [];
  let up = true;
  for (let col = size - 1; col > 0; col -= 2) {
    if (col === 6) col--;
    for (let i = 0; i < size; i++) { const row = up ? size - 1 - i : i; for (let c2 = 0; c2 < 2; c2++) { const cc = col - c2; if (!x.fn[row][cc]) bits.push(modules[row][cc] ^ (maskFn(row, cc) ? 1 : 0)); } }
    up = !up;
  }
  const totalCW = TOTAL_CW[version], cw = [];
  for (let i = 0; i < totalCW; i++) { let b = 0; for (let j = 0; j < 8; j++) b = (b << 1) | (bits[i * 8 + j] || 0); cw.push(b); }
  const [, groups] = BLOCKS[ecLevel][version]; const lengths = [];
  for (const [count, dpb] of groups) for (let b = 0; b < count; b++) lengths.push(dpb);
  const totalData = lengths.reduce((a, b) => a + b, 0);
  const inter = cw.slice(0, totalData), blocks = lengths.map(() => []); let idx = 0; const maxLen = Math.max(...lengths);
  for (let i = 0; i < maxLen; i++) for (let bi = 0; bi < blocks.length; bi++) if (i < lengths[bi]) blocks[bi].push(inter[idx++]);
  const data = [].concat(...blocks);
  // parse byte mode
  const stream = []; for (const b of data) for (let j = 7; j >= 0; j--) stream.push((b >> j) & 1);
  let p = 0; const take = (n) => { let v = 0; for (let k = 0; k < n; k++) v = (v << 1) | stream[p++]; return v; };
  if (take(4) !== 0b0100) throw new Error("decodeSelf: not byte mode");
  const len = take(version <= 9 ? 8 : 16), out = new Uint8Array(len);
  for (let i = 0; i < len; i++) out[i] = take(8);
  return out;
}
// the text path: decode the bytes as UTF-8 (what the URL/poll demo uses).
export function decodeSelf(modules, version, ecLevel, mask) { return new TextDecoder().decode(decodeBytesSelf(modules, version, ecLevel, mask)); }
