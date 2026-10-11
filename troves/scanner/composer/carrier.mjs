// Vendored from FCCN-ANTIBODY/anecdote.channel composer/carrier.mjs @ 800162ca7643ec6adeee7cd15424e47d10b602c7,
// unchanged below this header. The qr screen reads AC1 frames with it (bridge.mjs). Refresh by copying it again.
// composer/carrier.mjs — the camera-fluent brain of offline transfer (docs/offline-transfer.md). This is the
// layer between the raw carrier (a QR/tile decoder) and the transfer innards (composer/transfer.mjs). It
// does NOT touch pixels or the camera — it takes DECODED frame strings (whatever a QR yields) and:
//   - learns the expected SHAPE from the earliest frame (any one tile names its set), so the app can put the
//     shape in front of the user for judgment BEFORE the whole thing finishes decoding;
//   - tolerates out-of-order and duplicate frames (a camera catches them however it catches them);
//   - flags a FOREIGN tile the moment the set's shape is known (an intruder QR on the side);
//   - completes into reassembled, ready-to-verify transfers.
// Decoder-agnostic on purpose (BarcodeDetector is absent on iOS/Linux — we bring our own decoder later; this
// brain is the same regardless of which decoder feeds it).
//
// Frame wire format (magic-prefixed so a decode is instantly recognizable as one of ours):
//   block:   AC1|b|<layoutShort|-|>|<memberId>|<i>|<n>|<base64 chunk>
//   droplet: AC1|d|<layoutShort|-|>|<memberId>|<K>|<B>|<L>|<seed>|<sum8>|<base64 xor>   (rateless)
//   layout:  AC1|L|<layoutShort>|<base64 of the signed layout JSON>   (the "physical checksum" tile)
// A `block` is one brick of a member transfer (from transfer.chunk); a `droplet` is one sip of a RATELESS
// fountain stream for a member (fountain.mjs — any sufficient subset reconstructs, so a lost or damaged
// frame is just one you make up for by catching another; "loop as many times as a bad camera needs"); a
// `layout` tile carries the signed set manifest. `memberId` is the full transfer id (both reassembly paths
// re-check the whole-payload hash against it); `layoutShort` is a short grouping key (integrity is the
// layout's signature, not this key).
//
// The droplet's `sum8` is a frame checksum (FNV-1a over the frame's own fields) — NOT security, the
// signature on the reassembled envelope is; it's how a DENTED frame announces itself. A frame that fails
// its checksum is counted as DAMAGE and dropped as an erasure the fountain heals around — which is what
// makes deliberate damage (the anti-signature's crimp, docs/anti-signature.md) survivable-by-design
// instead of silently poisoning the decode.

import { reassemble, verifyLayout, verifyTransfer, transferId, chunk, BLOCK } from "./transfer.mjs";
import { ltEncode, ltDecoder } from "./fountain.mjs";
import { canonicalize } from "./sign.mjs";
import { defaultHash } from "./anecdote.mjs";

export const MAGIC = "AC1";
const td = new TextDecoder(), te = new TextEncoder();

const short = (id) => String(id).replace(/^sha256:/, "").slice(0, 16);
const b64 = (u8) => (typeof Buffer !== "undefined" ? Buffer.from(u8).toString("base64") : btoa(String.fromCharCode(...u8)));
// FNV-1a 32-bit, 8 hex chars — the droplet frame's dent-detector (integrity vs accident, not adversary).
const fnv1a = (s) => { let h = 0x811c9dc5; for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 0x01000193); } return (h >>> 0).toString(16).padStart(8, "0"); };

// ---- encode (render side): turn transfers into frame strings a carrier will draw ----------------------

// Frames for one (possibly chunked) transfer. `layoutShort` groups it into a set (omit for a standalone).
export async function frameTransfer(signed, capacity, { layoutShort = "-" } = {}) {
  const blocks = await chunk(signed, capacity);
  return blocks.map((bk) => [MAGIC, "b", layoutShort, bk.t, bk.i, bk.n, bk.b].join("|"));
}

// RATELESS frames for one signed transfer — the fountain as a ready tool. Returns { frame(seed),
// frames(count, start), K, B, L, memberId }: pull frame(0), frame(1), … as many as the loop wants — more
// frames = more resilience, and ANY sufficient subset reconstructs. The stream codes the same canonical
// bytes chunk() does, so the receiver re-checks the identical whole-payload hash on completion.
export async function fountainTransfer(signed, { blockSize = 256, layoutShort = "-" } = {}) {
  const bytes = te.encode(canonicalize(signed));
  const memberId = await defaultHash(bytes);
  const enc = ltEncode(bytes, { blockSize });
  const frame = (seed) => {
    const d = enc.droplet(seed);
    const payload = b64(d.xor);
    const sum = fnv1a([memberId, d.K, d.B, d.L, d.s, payload].join("|"));
    return [MAGIC, "d", layoutShort, memberId, d.K, d.B, d.L, d.s, sum, payload].join("|");
  };
  return { frame, frames: (count, start = 0) => Array.from({ length: count }, (_, i) => frame(start + i)),
           K: enc.K, B: enc.B, L: enc.L, memberId };
}

// The layout tile — the signed set manifest, as a frame. Returns { frame, layoutShort }.
export async function frameLayout(layoutSigned) {
  const layoutShort = short(await transferId(layoutSigned));
  const payload = b64(new TextEncoder().encode(JSON.stringify(layoutSigned)));
  return { frame: [MAGIC, "L", layoutShort, payload].join("|"), layoutShort };
}

// ---- parse (scan side): one decoded string -> a structured frame, or null if not ours -----------------

export function parseFrame(str) {
  if (typeof str !== "string" || !str.startsWith(MAGIC + "|")) return null;
  const p = str.split("|");
  if (p[1] === "b" && p.length === 7) {
    const [, , layoutShort, memberId, i, n, b] = p;
    if (!/^\d+$/.test(i) || !/^\d+$/.test(n)) return null;
    return { type: "block", layoutShort: layoutShort === "-" ? null : layoutShort, block: { schema: BLOCK, t: memberId, i: +i, n: +n, b } };
  }
  if (p[1] === "d" && p.length === 10) {
    const [, , layoutShort, memberId, K, B, L, seed, sum, payload] = p;
    if (![K, B, L, seed].every((x) => /^\d+$/.test(x))) return null;
    const ls = layoutShort === "-" ? null : layoutShort;
    // a checksum failure is OURS-BUT-DENTED — reported as damage (an erasure the fountain heals), not noise
    if (fnv1a([memberId, +K, +B, +L, +seed, payload].join("|")) !== sum)
      return { type: "droplet", damaged: true, layoutShort: ls, memberId };
    let xor; try { xor = unb64(payload); } catch { return { type: "droplet", damaged: true, layoutShort: ls, memberId }; }
    if (xor.length !== +B) return { type: "droplet", damaged: true, layoutShort: ls, memberId };
    return { type: "droplet", damaged: false, layoutShort: ls, memberId, K: +K, B: +B, L: +L, seed: +seed, xor };
  }
  if (p[1] === "L" && p.length === 4) {
    const [, , layoutShort, payload] = p;
    try { return { type: "layout", layoutShort, layout: JSON.parse(td.decode(unb64(payload))) }; }
    catch { return null; }
  }
  return null;
}

// ---- the accumulator: feed decoded frames, watch the shape emerge, complete + verify ------------------

export function carrierSession({ friends = [] } = {}) {
  let layout = null, layoutShort = null, expected = null;   // expected: { count, memberIds:Set } from the layout
  const members = new Map();   // memberId -> { total, chunks: Map<i,block>, dec: ltDecoder|null, done, bytes }
  const foreign = [];          // frames that don't belong: not ours, wrong set, or not an attested member
  let damaged = 0;             // dented frames seen (checksum failed) — erasures the fountain heals around

  const memberOf = (id) => { if (!members.has(id)) members.set(id, { total: null, chunks: new Map(), dec: null, done: false, bytes: null }); return members.get(id); };
  const isForeignMember = (id) => expected && !expected.memberIds.has(id);

  function snapshot() {
    return {
      haveLayout: !!layout, layoutShort,
      expected: expected ? { count: expected.count } : null,        // the SHAPE, as soon as the layout tile lands
      present: [...members].map(([id, m]) => ({ id: short(id), mode: m.dec ? "fountain" : "blocks",
        have: m.dec ? m.dec.recovered : m.chunks.size, total: m.total, done: m.done, foreign: isForeignMember(id) })),
      foreign: foreign.slice(),
      damaged,                                                      // visible healing: how many dents were absorbed
      complete: isComplete(),
    };
  }

  function isComplete() {
    if (layout) {                                                    // a set: every attested member fully in
      if (![...expected.memberIds].every((id) => members.get(id)?.done)) return false;
      return true;
    }
    // standalone (no layout tile): complete when we have at least one member and all seen members are done
    return members.size > 0 && [...members.values()].every((m) => m.done);
  }

  async function tryFinishMember(id) {
    const m = members.get(id);
    if (m.done || m.total == null || m.chunks.size < m.total) return;
    const r = await reassemble([...m.chunks.values()]);
    if (r.ok) { m.done = true; m.bytes = r.bytes; } else if (r.corrupt) foreign.push({ reason: "corrupt member (checksum failed)", id: short(id) });
  }

  async function feed(frameStr) {
    const f = parseFrame(frameStr);
    if (!f) { foreign.push({ reason: "not a carrier frame" }); return snapshot(); }

    if (f.type === "layout") {
      if (layoutShort && f.layoutShort !== layoutShort) { foreign.push({ reason: "a different set's layout tile", id: f.layoutShort }); return snapshot(); }
      const v = await verifyLayout(f.layout, [], { friends });      // signature/shape now; members checked as they arrive
      if (!v.ok) { foreign.push({ reason: "layout tile signature invalid" }); return snapshot(); }
      layout = f.layout; layoutShort = f.layoutShort;
      expected = { count: (layout.members || []).length, memberIds: new Set((layout.members || []).map((mm) => mm.hash)) };
      // any members already collected that aren't attested are now provably interlopers
      for (const id of members.keys()) if (isForeignMember(id)) foreign.push({ reason: "interloper tile (not in the attested set)", id: short(id) });
      return snapshot();
    }

    if (f.type === "droplet") {
      if (f.damaged) { damaged++; return snapshot(); }               // a dent announced itself; catch another
      if (f.layoutShort && layoutShort && f.layoutShort !== layoutShort) { foreign.push({ reason: "droplet from a different set", id: short(f.memberId) }); return snapshot(); }
      if (isForeignMember(f.memberId)) { foreign.push({ reason: "interloper tile (not in the attested set)", id: short(f.memberId) }); return snapshot(); }
      if (!layoutShort && f.layoutShort) layoutShort = f.layoutShort;
      const m = memberOf(f.memberId);
      if (m.done) return snapshot();                                 // the loop keeps looping; we're already full
      if (!m.dec) { m.dec = ltDecoder(f.K, f.B, f.L); m.total = f.K; }
      const r = m.dec.add({ v: "lt1", K: f.K, B: f.B, L: f.L, s: f.seed, xor: f.xor });
      if (r.ignored) { foreign.push({ reason: "droplet shape mismatch for this member", id: short(f.memberId) }); return snapshot(); }
      if (r.done) {
        const bytes = m.dec.bytes();
        if (await defaultHash(bytes) === f.memberId) { m.done = true; m.bytes = bytes; }   // the same whole-payload re-check reassemble() does
        else foreign.push({ reason: "corrupt member (checksum failed)", id: short(f.memberId) });
      }
      return snapshot();
    }

    // block
    if (f.layoutShort && layoutShort && f.layoutShort !== layoutShort) { foreign.push({ reason: "brick from a different set", id: short(f.block.t) }); return snapshot(); }
    if (isForeignMember(f.block.t)) { foreign.push({ reason: "interloper tile (not in the attested set)", id: short(f.block.t) }); return snapshot(); }
    if (!layoutShort && f.layoutShort) layoutShort = f.layoutShort;  // learn the grouping key from a brick before the layout tile
    const m = memberOf(f.block.t);
    m.total = f.block.n;
    m.chunks.set(f.block.i, f.block);
    await tryFinishMember(f.block.t);
    return snapshot();
  }

  // Once complete, verify: the layout (trusted signer? interlopers?) and each member transfer.
  async function result() {
    if (!isComplete()) return { ok: false, reason: "incomplete", snapshot: snapshot() };
    const transfers = [];
    for (const id of (expected ? expected.memberIds : members.keys())) {
      const m = members.get(id);
      const signed = JSON.parse(td.decode(m.bytes));
      transfers.push({ signed, verify: await verifyTransfer(signed, { friends }) });
    }
    const layoutCheck = layout ? await verifyLayout(layout, transfers.map((t) => t.signed), { friends }) : null;
    return { ok: true, layout: layoutCheck, transfers, foreign: foreign.slice() };
  }

  return { feed, snapshot, result };
}

function unb64(s) { if (typeof Buffer !== "undefined") return new Uint8Array(Buffer.from(s, "base64")); const b = atob(s); const u = new Uint8Array(b.length); for (let i = 0; i < b.length; i++) u[i] = b.charCodeAt(i); return u; }
