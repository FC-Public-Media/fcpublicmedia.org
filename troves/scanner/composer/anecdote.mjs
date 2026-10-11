// Vendored from FCCN-ANTIBODY/anecdote.channel composer/anecdote.mjs @ 800162ca7643ec6adeee7cd15424e47d10b602c7,
// unchanged below this header. The qr screen reads AC1 frames with it (bridge.mjs). Refresh by copying it again.
// anecdote/v1 — the payload a CONFIRMED send hands off (CONSTITUTION §"Mobile LLM" / §"Responses").
//
// This is the schema that route.prepare's {to, label, text} grows into when a statement actually
// leaves the device. It stays in the same spirit as the rest of the channel: a pure core with no
// DOM, no network, no event loop, and the one heavy primitive (hashing) behind a single seam, the
// way the reducer keeps the embedder behind one. It BUILDS and VALIDATES the object; it never
// transmits and it never signs (signing is the next slice — see "The signing seam" below).
//
// The shape, in one breath:
//
//   { schema:"anecdote/v1", to, label, body:[ <part>, … ] }
//
// where body[0] is always the TEXT statement (the thing you typed, reduced to `label`), and any
// further parts are ATTACHMENTS. The crux — drawn straight from the boundary work, where a GeoJSON
// boundary proved an anecdote's content "could be anything":
//
//   anecdote does NOT host arbitrary files. Text rides inline; everything else (an image, a
//   GeoJSON shape, a citation) rides as a REFERENCE — a receipt that says "I have these bytes and
//   they came from here": a content hash + a provenance source, optionally a pointer to YOUR local
//   references data-pile that holds them, and optionally the bytes themselves when you choose to
//   include a copy. The canonical thing is the receipt; the bytes are licensable from your pile
//   consentfully, never hosted here. (See docs/anecdote-schema.md.)

export const SCHEMA = "anecdote/v1";

// Above this many bytes, an attachment will not carry an inline copy even if you asked to include
// one — the receipt still goes (hash + source + pile), the bytes stay in your references pile.
// Text is never subject to this; it is the statement and always rides inline.
export const INLINE_MAX = 64 * 1024;

// ---- the hashing seam (the only heavy primitive) -------------------------------------------------
// hash(bytes) -> "sha256:<hex>". Works in the browser (SubtleCrypto) and in Node (node:crypto) with
// no dependency and no network. Pluggable like the reducer's embedder: pass your own to build/verify.
export async function defaultHash(bytes) {
  const u8 = toBytes(bytes);
  if (globalThis.crypto && globalThis.crypto.subtle) {
    const digest = await globalThis.crypto.subtle.digest("SHA-256", u8);
    return "sha256:" + hex(new Uint8Array(digest));
  }
  const { createHash } = await import("node:crypto");
  return "sha256:" + createHash("sha256").update(u8).digest("hex");
}

// ---- parts ---------------------------------------------------------------------------------------

// The statement you typed, reduced to its label. Always body[0], always inline. `text` is the raw
// utterance (kept verbatim — anecdote never rewrites you); `label` is the reducer's fewest-verbs
// subject that rides along.
export function textPart(text, label) {
  if (typeof text !== "string" || text.trim() === "") throw new Error("anecdote: empty statement");
  return { kind: "text", text, label: label || "" };
}

// Turn raw bytes you want to attach into a REFERENCE part — a receipt, not a hosted file.
//
//   attachment = { mediaType, bytes, source, pile?, include? }
//     mediaType  e.g. "image/jpeg", "application/geo+json", "text/plain"
//     bytes      Uint8Array | string (the content you are citing)
//     source     where it came from — a URL, a citation, "drawn by me" (provenance, "came from here")
//     pile       optional id/url of YOUR references data-pile that holds the bytes
//     include    if true, also carry an inline copy (subject to INLINE_MAX)
//
// Returns { kind:"ref", mediaType, hash, source, pile?, bytes?(base64), receipt }. The `receipt` is
// the UNSIGNED possession+provenance attestation — the exact object a signer will later sign to make
// it "something signed to say you have it, and it came from here". This function computes the hash
// (the "you have it" proof) but does not sign.
export async function reference(attachment, opts = {}) {
  const { mediaType, bytes, source, pile, include = false } = attachment;
  if (!mediaType) throw new Error("anecdote: reference needs a mediaType");
  if (bytes == null) throw new Error("anecdote: reference needs bytes to hash");
  if (!source) throw new Error("anecdote: reference needs a source (where it came from)");
  const hash = opts.hash || defaultHash;
  const inlineMax = opts.inlineMax ?? INLINE_MAX;

  const u8 = toBytes(bytes);
  const digest = await hash(u8);
  const part = { kind: "ref", mediaType, hash: digest, source };
  if (pile) part.pile = pile;
  if (include) {
    if (u8.length <= inlineMax) part.bytes = b64(u8);
    else part.dropped_inline = { reason: "over inlineMax", bytes_len: u8.length, inlineMax };
  }
  // The receipt is what gets signed: it binds the content (hash) to its origin (source) and, when
  // known, to the pile that vouches it is held. No timestamp here — determinism is the core's job;
  // a signer adds time/identity at signing.
  part.receipt = { schema: "anecdote.receipt/v1", hash: digest, source, ...(pile ? { pile } : {}) };
  return part;
}

// ---- build ---------------------------------------------------------------------------------------

// Assemble an anecdote/v1 from a routed statement plus optional attachments. `routed` is what
// route.prepare returns ({ to, label, text }); `attachments` are raw {mediaType, bytes, source, …}
// descriptors (NOT yet references) — this turns each into a receipt via `reference`.
export async function build(routed, attachments = [], opts = {}) {
  const { to, label, text } = routed || {};
  if (!to || !to.id) throw new Error("anecdote: missing destination (route.prepare first)");
  const body = [textPart(text, label)];
  for (const a of attachments) body.push(await reference(a, opts));
  return { schema: SCHEMA, to: { id: to.id, kind: to.kind, url: to.url }, label: label || "", body };
}

// ---- validate (shape, sync) ----------------------------------------------------------------------

// Structural check only — does this look like a well-formed anecdote/v1? Returns { ok, errors }.
// It does NOT recompute hashes or check signatures (see `verify` for the hash check). The platform
// can run this on anything it receives without holding any bytes.
export function validate(a) {
  const errors = [];
  const bad = (m) => errors.push(m);
  if (!a || typeof a !== "object") return { ok: false, errors: ["not an object"] };
  if (a.schema !== SCHEMA) bad(`schema must be "${SCHEMA}"`);
  if (!a.to || !a.to.id || !a.to.kind) bad("to.{id,kind} required");
  if (typeof a.label !== "string") bad("label must be a string");
  if (!Array.isArray(a.body) || a.body.length === 0) bad("body must be a non-empty array");
  else {
    const head = a.body[0];
    if (!head || head.kind !== "text" || typeof head.text !== "string" || head.text.trim() === "")
      bad("body[0] must be a non-empty text part (the statement)");
    a.body.slice(1).forEach((p, i) => {
      const at = `body[${i + 1}]`;
      if (!p || typeof p !== "object") return bad(`${at} not an object`);
      if (p.kind === "text") return; // additional text is allowed
      if (p.kind !== "ref") return bad(`${at} unknown kind "${p.kind}"`);
      if (!p.mediaType) bad(`${at} ref needs mediaType`);
      if (!p.hash || !/^sha256:[0-9a-f]{64}$/.test(p.hash)) bad(`${at} ref needs a sha256 hash`);
      if (!p.source) bad(`${at} ref needs a source`);
      if (!p.receipt || p.receipt.hash !== p.hash || p.receipt.source !== p.source)
        bad(`${at} receipt must cover {hash, source}`);
    });
  }
  return { ok: errors.length === 0, errors };
}

// ---- verify (hash, async) ------------------------------------------------------------------------

// For every reference that chose to INCLUDE an inline copy, recompute its hash and confirm it
// matches the receipt — i.e. the carried bytes really are the ones the receipt promises. References
// that carry no inline copy are reported as { resolvable: false } (their bytes live in a pile and
// are fetched/licensed elsewhere — out of scope here). Returns { ok, checked, errors }.
export async function verify(a, opts = {}) {
  const shape = validate(a);
  if (!shape.ok) return { ok: false, checked: 0, errors: shape.errors };
  const hash = opts.hash || defaultHash;
  const errors = [];
  let checked = 0;
  for (let i = 1; i < a.body.length; i++) {
    const p = a.body[i];
    if (p.kind !== "ref") continue;
    if (p.bytes == null) continue; // receipt-only; nothing to check locally
    const got = await hash(unb64(p.bytes));
    checked++;
    if (got !== p.hash) errors.push(`body[${i}] inline bytes hash ${got} ≠ receipt ${p.hash}`);
  }
  return { ok: errors.length === 0, checked, errors };
}

// ---- tiny, env-portable byte helpers (no deps) ---------------------------------------------------
function toBytes(x) {
  if (x instanceof Uint8Array) return x;
  if (typeof x === "string") return new TextEncoder().encode(x);
  if (ArrayBuffer.isView(x)) return new Uint8Array(x.buffer, x.byteOffset, x.byteLength);
  if (x instanceof ArrayBuffer) return new Uint8Array(x);
  throw new Error("anecdote: bytes must be Uint8Array, ArrayBuffer, or string");
}
function hex(u8) { let s = ""; for (const b of u8) s += b.toString(16).padStart(2, "0"); return s; }
function b64(u8) {
  if (typeof Buffer !== "undefined") return Buffer.from(u8).toString("base64");
  let s = ""; for (const b of u8) s += String.fromCharCode(b); return btoa(s);
}
function unb64(s) {
  if (typeof Buffer !== "undefined") return new Uint8Array(Buffer.from(s, "base64"));
  const bin = atob(s); const u8 = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) u8[i] = bin.charCodeAt(i); return u8;
}

// The signing seam (next slice): a confirmed send signs `body[i].receipt` (and ultimately the whole
// envelope) with the constituent's revocable-nonce identity + the Mobile LLM's co-signature
// (CONSTITUTION §"Mobile LLM": the on-device agent intends to co-sign any submission it touches).
// This module deliberately stops at the unsigned receipt so the signature primitive can drop in
// behind one seam, exactly as the embedder/namer and the hash do. How the platform VALIDATES a
// receipt it cannot see the bytes for (signature + hash now; pile-resolution under license later) is
// the open question recorded in docs/anecdote-schema.md.
