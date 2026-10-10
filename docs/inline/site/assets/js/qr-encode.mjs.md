# `site/assets/js/qr-encode.mjs`

Moved out of the file. Unreviewed.

## 1

Above `// ---- GF(256) for Reed–Solomon (primitive 0x11d) -------------------------------------------------`

Vendored from FCCN-ANTIBODY/anecdote.channel composer/qr-encode.mjs @ 6481e38bc7a5f44346be465b0091c3377b33552a,
unchanged below this header. The kiosk reads with the same project's qr-decode.mjs. Refresh by copying it again.
composer/qr-encode.mjs — "qr-enough": a vendorless byte-mode QR encoder (docs/offline-transfer.md). Just
enough of the QR spec to render a payload as a scannable code — versions 1–40, all four ECC levels
L/M/Q/H, byte mode (a signed poll URL runs ~800 B → a mid-teens version). The first hands-on carrier:
a poll QR is a PLAIN URL QR any phone decodes → opens the answer runtime. The spec tables and the
function-module map are exported — composer/qr-decode.mjs (the bigger lens) reads with the same charts
this file draws by.

Correctness without a scanner in this env is guarded three ways: (1) a codeword-count INVARIANT on the
block tables (the typo-prone part) — asserted in the test; (2) format/version info via computed BCH and
Reed–Solomon via computed GF(256), so no hand-typed magic numbers; (3) a SELF-DECODE round-trip in the
test that reads the data back through inverse placement + unmask + de-interleave. Scanner interop is the
physical phone test.

## 2

Above `const div = rsGen(ec).slice(0, ec).reverse(), res = new Array(ec).fill(0);`

rsGen returns the generator constant-first (g[ec] = leading monic term). The LFSR remainder wants the
non-leading coefficients highest-power-first, so drop the leading term and reverse.

## 3

Above `export const TOTAL_CW = [0, 26, 44, 70, 100, 134, 172, 196, 242, 292, 346, 404, 466, 532, 581, 655, `

---- spec tables (versions 1–40, ECC levels L & M) --------------------------------------------------
Total codewords per version, and the block layout [ecPerBlock, [[blockCount, dataPerBlock], …]] and
alignment-pattern centre coordinates. Generated from the ISO 18004 tables (cross-checked against segno);
the codeword-count invariant in qr-encode.test.mjs guards against transcription errors.

## 4

Above `const B = (i) => (bits >> (14 - i)) & 1;`

The 15-bit format string is placed MSB-first: position i (0-based, in spec module order) carries
bit (14 − i) of the value. (Verified against segno/zbar — see qr-encode.test.mjs notes.)

## 5

Above `export function functionModules(version) { const x = newMatrix(17 + 4 * version); functionPatterns(x`

The function-module map for a version — shared with the decoder (composer/qr-decode.mjs), which must
skip exactly the same cells when it reads the zigzag back.

## 6

Above `export function encodeBytes(bytes, { ecLevel = "M", version, mask } = {}) {`

Encode text into a QR. Returns { version, size, ecLevel, mask, modules } where modules[r][c] is 0/1.
`version` and `mask` are optional overrides (mask is normally chosen by penalty scoring; forcing it is for
reference comparison / tests).
Encode RAW BYTES — the real carrier (deflated bytes / a key / a signed token), which is not valid UTF-8
and so cannot go through encodeQR's text path. Byte mode carries any octet stream unchanged.

## 7

Above `export function decodeBytesSelf(modules, version, ecLevel, mask) {`

SELF-DECODE (verification tool, not a general QR reader): reverse our own placement to recover the text —
unmask, read codewords in the same zigzag, de-interleave the data blocks, parse byte mode. It trusts the
EC codewords (a real scanner does Reed–Solomon); it proves the DATA path (placement/mask/interleave/mode).
self-decode to raw BYTES (the byte-carrier round-trip): reverse our own placement — unmask, read
codewords in the same zigzag, de-interleave, parse byte mode. Trusts the EC codewords (a real scanner
runs Reed–Solomon); proves the DATA path (placement / mask / interleave / mode).
