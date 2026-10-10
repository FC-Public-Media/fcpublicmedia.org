# `site/assets/js/qr-decode.mjs`

Moved out of the file. Unreviewed.

## 1

Above `import { TOTAL_CW, BLOCKS, ALIGN, EC_BITS, MASKS, functionModules } from "./qr-encode.mjs";`

Vendored from FCCN-ANTIBODY/anecdote.channel composer/qr-decode.mjs @ 048af64bebbdce7b8f92f69123a5f4afd736eaff,
unchanged below this header. The kiosk's camera reads with it (machines/kiosk-1/door.py, THE CAMERA).
composer/qr-decode.mjs — "the bigger lens": a vendorless QR DECODER (docs/offline-transfer.md,
docs/anti-signature.md "acquire-by-doing"). The encoder (qr-encode.mjs) made us a sender; this makes any
browser a RECEIVER — BarcodeDetector is absent on iOS Safari and headless Linux (measured), so we bring
our own. It reads pixels (a camera frame, a screenshot, a rendered PNG) or a clean module matrix, and
returns the text — correcting real errors through Reed–Solomon, which is what lets a dented tile still
speak (and a too-dented one fail HONESTLY instead of lying).

Two entry points:
  decodeMatrix(modules)            — a clean 0/1 grid → { text, version, ecLevel, mask, corrected }
  decodeImage({data,width,height}) — RGBA or grayscale pixels → locate + sample + decodeMatrix
The pixel path: grayscale → adaptive threshold (integral image) → finder-pattern scan (1:1:3:1:1 runs,
cross-checked) → perspective transform from the three finders (+ inferred fourth corner) → grid sample.
Mirrored codes (scanned through glass) are retried transposed. All four ECC levels, versions 1–40,
byte / alphanumeric / numeric modes (kanji is refused honestly).

Shares the spec tables and the function-module map with the encoder — the decoder must skip exactly the
cells the encoder painted.

## 2

Above `export function rsDecode(word, ec) {`

---- Reed–Solomon DECODE with error correction --------------------------------------------------------
`word` = [data…, ec…] exactly as the encoder emits (c[0] is the highest power). Corrects up to
floor(ec/2) byte errors IN PLACE. Returns { ok, corrected } — ok:false means uncorrectable (too dented).

## 3

Above `let merged = false;`

merge with an existing candidate if close AND the module size agrees — without the size gate,
data-pattern rows beside a finder drag the cluster off-center and inflate its m (a feedback loop:
bigger m → wider merge radius → more pollution). Seen at scale 3; the gate closes it.

## 4

Above `const out = cands.filter((c) => c.hits >= 2);`

refine each surviving cluster with a final cross-check pass — the exact center comes from walking
the pattern, not from averaging merged rows (residual drift otherwise misaligns the whole grid)

## 5

Above `function compose(a, b) {`

zxing's times() convention (column-major flat layout t[col*3+row]): out = b-then-a in APPLY order —
compose(A, B) applied to a point runs B first, then A. Hand-verified against known correspondences.

## 6

Above `const RETRY_UNDER_PX = 8;    // located a code this small and failed → worth another look`

Decode from pixels. `data` is RGBA (w*h*4) or grayscale (w*h). Returns decodeMatrix's result + geometry,
or null. Tries a couple of threshold biases and the mirrored orientation before giving up.
Under this many pixels per module the geometry estimate and the one-sample-per-
module read have no room to be wrong in, even when the code is perfectly intact.

## 7

Above `function cropUp({ data, width, height }, box, n) {`

Crop a region and blow it up nearest-neighbour. Adds NO information — it buys
spatial room. Cropping first keeps the cost proportional to the code, not the
frame, which is what makes this affordable on a phone at camera frame rates.

## 8

Above `const maxHits = finders[0].hits;`

choose the trio: strong candidates first (a real finder is seen on many rows — a data-region
impostor on few), then score by geometry — a right angle between two equal legs

## 9

Above `if (!opts.rescaled && weakest && weakest.mSize < RETRY_UNDER_PX) {`

We FOUND a code and could not read it, and its modules are only a couple of
pixels across — the failure is scale, not damage. Blowing up nearest-neighbour
gives the geometry and the sampler room without inventing detail: measured
0% → 99% on a loop that SMS had shrunk to 2.6 px/module, whose data OpenCV
could read all along. Gated on finders having been located, so a frame with
no code in it costs nothing extra — which matters at camera frame rates.
