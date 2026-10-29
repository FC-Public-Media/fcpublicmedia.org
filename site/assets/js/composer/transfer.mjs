// Vendored from FCCN-ANTIBODY/anecdote.channel composer/transfer.mjs @ 800162ca7643ec6adeee7cd15424e47d10b602c7,
// unchanged below this header, by way of troves/scanner/composer. The check-in pours its bottle with it (bottle.js).
// composer/transfer.mjs — offline data transfer ("gravel"), the carrier-agnostic innards
// (docs/offline-transfer.md). Move a payload — a data-pile, a poll, an anecdote — to someone with no
// network, over ANY carrier (QR / file / phone-to-phone). The trust stance is DELIVERY.md's: verify the
// bytes, accept them from anyone; a LOCAL friend-list decides *whether to act*, never a global registry.
// Reuses the same Ed25519 attest primitive as the firmware pin (composer/sign.mjs), so it inherits the
// verify-a-signed-payload-and-decide-locally machinery the whole possession model rests on.
//
// THREE independent concerns, kept separate on purpose:
//   1. the ENVELOPE — a signed payload (authenticity + content integrity). `by` is who; the friend-list is
//      whether to trust. Verifying and trusting are different questions.
//   2. CHUNKING (size) — one payload too big for one carrier unit → N blocks ("bricks in the road"). The
//      platform has NO opinion about N; capacity is the carrier's. Whole-payload checksum on reassembly, so
//      a partial scan can't be processed as if whole. Blocks carry no signature — the reassembled envelope's
//      does.
//   3. the LAYOUT (constellation) — several DIFFERENT envelopes laid out together, with a signed manifest
//      that attests the whole set's shape. An intruder tile "on the side" is caught because it is not an
//      attested member — not by branding (which a face-copy defeats), by the set signing itself.

import { attest, verifyAttestation, canonicalize } from "./sign.mjs";
import { defaultHash } from "./anecdote.mjs";

export const TRANSFER = "anecdote.transfer/v1";
export const BLOCK = "anecdote.block/v1";
export const LAYOUT = "anecdote.layout/v1";
const te = new TextEncoder(), td = new TextDecoder();

// ---- 1. the envelope --------------------------------------------------------------------------------

// Wrap bytes into a signed, content-addressed transfer. `kind` names what's inside ("data-pile", "poll",
// "anecdote", "firmware", …). Signing can be gesture-gated by the caller (composer/gesture.mjs's
// gatedAttest) — this module stays gesture-agnostic; the page composes the gate.
export async function packTransfer(kind, bytes, identity, opts = {}) {
  const u8 = toBytes(bytes);
  const env = { schema: TRANSFER, kind, size: u8.length, hash: await defaultHash(u8), bytes: b64(u8) };
  return attest(env, identity, opts);
}

// Verify a transfer: authentic (signature) + intact (payload hashes to its `hash`). `ok` is
// "verify-from-anyone" — well-formed and truly signed by `by`. `trusted` is the LOCAL decision: is `by` on
// your friend list? A valid-but-untrusted transfer verifies fine and waits on your accept (friend-add +
// gesture). Returns { ok, by, kind, trusted, bytes, errors }.
export async function verifyTransfer(signed, { friends = [] } = {}) {
  if (!signed || signed.schema !== TRANSFER) return { ok: false, by: null, trusted: false, errors: ["not a transfer"] };
  const errors = [];
  const att = await verifyAttestation(signed, {});
  if (!att.ok) errors.push("signature: " + att.errors.join("; "));
  let bytes = null;
  try { bytes = unb64(signed.bytes); } catch { errors.push("bad payload encoding"); }
  if (bytes) { const got = await defaultHash(bytes); if (got !== signed.hash) errors.push("payload hash mismatch"); }
  const ok = att.ok && errors.length === 0;
  return { ok, by: att.by, kind: signed.kind, trusted: ok && !!att.by && friends.includes(att.by),
           bytes: ok ? bytes : null, errors };
}

// The content id of a transfer — the hash of its exact canonical bytes. Used as the chunk id and the
// layout member id, so all three concerns address a transfer the same way.
export async function transferId(signed) { return defaultHash(te.encode(canonicalize(signed))); }

// ---- 2. chunking (bricks in the road) ---------------------------------------------------------------

// Split a signed transfer into blocks of at most `capacity` bytes each. The platform has no opinion about
// how many — it lays down as many bricks as it takes. Blocks are unsigned transport; the envelope inside is
// what's signed, and reassembly re-checks the whole-payload checksum.
export async function chunk(signed, capacity) {
  if (!(capacity > 0)) throw new Error("chunk: capacity must be > 0");
  const data = te.encode(canonicalize(signed));
  const id = await defaultHash(data);
  const n = Math.max(1, Math.ceil(data.length / capacity));
  const blocks = [];
  for (let i = 0; i < n; i++) blocks.push({ schema: BLOCK, t: id, i, n, b: b64(data.slice(i * capacity, (i + 1) * capacity)) });
  return blocks;
}

// Reassemble blocks into the transfer's bytes. Foreign blocks (a different payload's id) are ignored — a
// stray brick from another road can't corrupt this one. A partial set returns ok:false with the missing
// indices (so it is NEVER handed on as if whole). On a full set the reassembled bytes must hash to the
// payload id (`t`) — a swapped brick is caught here. Returns { ok, id, total, have, missing, bytes }.
export async function reassemble(blocks) {
  const valid = (blocks || []).filter((b) => b && b.schema === BLOCK && typeof b.t === "string" && Number.isInteger(b.i) && Number.isInteger(b.n));
  if (!valid.length) return { ok: false, id: null, total: 0, have: 0, missing: [], bytes: null };
  const id = valid[0].t;
  const total = valid.find((b) => b.t === id).n;
  const byIndex = new Map();
  for (const b of valid) if (b.t === id && b.n === total && b.i >= 0 && b.i < total) byIndex.set(b.i, b);
  const missing = [];
  for (let i = 0; i < total; i++) if (!byIndex.has(i)) missing.push(i);
  if (missing.length) return { ok: false, id, total, have: byIndex.size, missing, bytes: null };
  const parts = [];
  for (let i = 0; i < total; i++) parts.push(unb64(byIndex.get(i).b));
  const bytes = concat(...parts);
  if (await defaultHash(bytes) !== id) return { ok: false, id, total, have: total, missing: [], bytes: null, corrupt: true };
  return { ok: true, id, total, have: total, missing: [], bytes };
}

// ---- 3. the layout (constellation / physical checksum) ----------------------------------------------

// Sign a manifest that attests a whole SET of transfers laid out together: the member content-hashes + the
// intended shape (count, and whatever physical arrangement a carrier wants to record). This signed tile is
// the "physical checksum" — the codes-you-can't-alter that say what the shape must be.
export async function packLayout(memberSigneds, identity, { shape = {}, ...opts } = {}) {
  const members = [];
  for (const m of memberSigneds) members.push({ hash: await transferId(m), kind: m.kind });
  return attest({ schema: LAYOUT, members, shape: { count: members.length, ...shape } }, identity, opts);
}

// Check a scanned arrangement against its signed layout. `scannedSigneds` are the transfers the app decoded
// from the physical set. Detects an INTRUDER tile (scanned but not an attested member) and a MISSING tile
// (attested but not scanned) — so a stranger's QR on the side is caught by the set, not the eye. `ok` =
// layout truly signed; `trusted` = signer on your friend list; `complete` = exactly the attested set, no
// interlopers, none missing. Returns { ok, by, trusted, shapeOk, complete, interlopers, missing, errors }.
export async function verifyLayout(layoutSigned, scannedSigneds = [], { friends = [] } = {}) {
  if (!layoutSigned || layoutSigned.schema !== LAYOUT) return { ok: false, by: null, trusted: false, complete: false, errors: ["not a layout"] };
  const errors = [];
  const att = await verifyAttestation(layoutSigned, {});
  if (!att.ok) errors.push("signature: " + att.errors.join("; "));
  const want = new Set((layoutSigned.members || []).map((m) => m.hash));
  const scanned = [];
  for (const s of scannedSigneds) scanned.push(await transferId(s));
  const have = new Set(scanned);
  const interlopers = scanned.filter((h) => !want.has(h));      // foreign tiles — not in the attested shape
  const missing = [...want].filter((h) => !have.has(h));        // attested tiles absent from the scan
  const shapeOk = (layoutSigned.shape && layoutSigned.shape.count) === want.size;
  const ok = att.ok && errors.length === 0;
  return { ok, by: att.by, trusted: ok && !!att.by && friends.includes(att.by), shapeOk,
           complete: ok && interlopers.length === 0 && missing.length === 0, interlopers, missing, errors };
}

// ---- helpers ----------------------------------------------------------------------------------------
function toBytes(x) { if (x instanceof Uint8Array) return x; if (typeof x === "string") return te.encode(x); if (ArrayBuffer.isView(x)) return new Uint8Array(x.buffer, x.byteOffset, x.byteLength); if (x instanceof ArrayBuffer) return new Uint8Array(x); throw new Error("transfer: bytes must be Uint8Array/ArrayBuffer/string"); }
function concat(...as) { let n = 0; for (const a of as) n += a.length; const o = new Uint8Array(n); let i = 0; for (const a of as) { o.set(a, i); i += a.length; } return o; }
function b64(u8) { if (typeof Buffer !== "undefined") return Buffer.from(u8).toString("base64"); let s = ""; for (const x of u8) s += String.fromCharCode(x); return btoa(s); }
function unb64(s) { if (typeof Buffer !== "undefined") return new Uint8Array(Buffer.from(s, "base64")); const b = atob(s); const u = new Uint8Array(b.length); for (let i = 0; i < b.length; i++) u[i] = b.charCodeAt(i); return u; }
