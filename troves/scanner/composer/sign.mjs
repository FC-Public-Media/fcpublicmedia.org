// Vendored from FCCN-ANTIBODY/anecdote.channel composer/sign.mjs @ 800162ca7643ec6adeee7cd15424e47d10b602c7,
// unchanged below this header. The qr screen reads AC1 frames with it (bridge.mjs). Refresh by copying it again.
// composer/sign.mjs — signing an anecdote/v1 on-device (CONSTITUTION §"Mobile LLM").
//
// This is the seam the schema (anecdote.mjs, docs/anecdote-schema.md) left open: making a submission
// "something signed to say you have it, and it came from here." It is a pure core like the rest —
// no DOM, no network, no event loop — over one primitive, WebCrypto's SubtleCrypto, available the
// same way in the browser and in Node.
//
// The honest cryptography of a NO-BACKEND device:
//
//   - There is exactly ONE secret-holding party on the device: the CONSTITUENT. So there is one
//     real signature — the constituent's Ed25519 device key over the canonical envelope. (Ed25519
//     to match the constellation's ssh-ed25519 identities; the alg is recorded in the sig block so
//     it is never frozen.)
//   - The MOBILE LLM "co-signs" without a key. It is a public, vendored, hash-pinned instrument
//     (reducer/model.lock.json) — identical for everyone — so it CANNOT hold a secret. Forging a
//     second keypair for it would be theater. Instead it co-signs the only honest way a
//     content-addressed thing can: its VERIFIABLE pinned identity (`instrument` version hash) and
//     the `constitution` it ran under are bound INTO the bytes the constituent signs. The human's
//     signature therefore vouches "this exact pinned agent was involved" — which is what
//     §"Mobile LLM" asks ("its included CONSTITUTION must intend to co-sign any submission where it
//     becomes involved"). If a real agent-key model ever exists, it slots in as a second `sig`.
//   - Identity is PSEUDONYMOUS: the public id is the key fingerprint, presented behind a REVOCABLE
//     NONCE. Minting and revoking the nonce are the platform/Tell's job (the Tell already mints an
//     HMAC capability; the data-pile already owns join/leave). Here the nonce is CARRIED and bound
//     under the signature, never minted — so the platform can tie an anonymous, unrevoked slot to a
//     submission without ever learning who.
//
// The signed envelope grows three fields on an anecdote/v1:
//
//   agent: { instrument, constitution }     // the Mobile LLM co-signature (named by pinned hash)
//   nonce: "<platform-minted handle>"       // optional; the revocable, anonymous identity handle
//   sig:   { alg, by, key, signature }      // the constituent's Ed25519 signature over the rest

import { validate, defaultHash } from "./anecdote.mjs";

export const SIG_ALG = "ed25519";
const ALG = { name: "Ed25519" };

// ---- identity ------------------------------------------------------------------------------------

function subtleOf(opts = {}) {
  const s = opts.subtle || (globalThis.crypto && globalThis.crypto.subtle);
  if (!s) throw new Error("sign: no WebCrypto SubtleCrypto available");
  return s;
}

// A fresh device identity. In production the private key should be non-extractable and stored as a
// CryptoKey in domain-scoped IndexedDB (never serialized); here it is extractable so the public half
// can be exported and so tests are portable. The returned `fingerprint` is the pseudonymous id.
export async function generateIdentity(opts = {}) {
  const subtle = subtleOf(opts);
  const pair = await subtle.generateKey(ALG, true, ["sign", "verify"]);
  const raw = new Uint8Array(await subtle.exportKey("raw", pair.publicKey));
  return { privateKey: pair.privateKey, publicKey: pair.publicKey, raw, fingerprint: await fingerprint(raw) };
}

// Content-address a public key: "key:sha256:<hex>" — reuses the anecdote hash so a key id and a
// content id are the same kind of thing.
export async function fingerprint(rawPub) {
  return "key:" + (await defaultHash(rawPub));
}

export function exportPublic(identity) { return b64(identity.raw); }

export async function importPublic(b64str, opts = {}) {
  const subtle = subtleOf(opts);
  return subtle.importKey("raw", unb64(b64str), ALG, true, ["verify"]);
}

// ---- canonical bytes (deterministic; sign and verify MUST agree) ---------------------------------

// Canonical JSON: object keys sorted recursively, undefined dropped, no insignificant whitespace.
// Stable across key insertion order so the same logical anecdote always signs to the same bytes.
export function canonicalize(v) {
  if (v === null || typeof v !== "object") return JSON.stringify(v);
  if (Array.isArray(v)) return "[" + v.map(canonicalize).join(",") + "]";
  const keys = Object.keys(v).filter((k) => v[k] !== undefined).sort();
  return "{" + keys.map((k) => JSON.stringify(k) + ":" + canonicalize(v[k])).join(",") + "}";
}

// What actually gets signed: the anecdote with agent/nonce folded in and any prior `sig` removed.
function payload(anecdote, { agent, nonce } = {}) {
  const p = { ...anecdote };
  delete p.sig;
  if (agent !== undefined) p.agent = agent;
  if (nonce !== undefined) p.nonce = nonce;
  return p;
}

// ---- attest / verify (generic: sign ANY object) --------------------------------------------------
// The primitive under both anecdote signing and consent revocation: canonicalize an object (minus
// any prior `sig`), sign the bytes with the identity, attach `sig`. Returns a new object.
export async function attest(obj, identity, opts = {}) {
  const subtle = subtleOf(opts);
  const rest = { ...obj }; delete rest.sig;
  const bytes = new TextEncoder().encode(canonicalize(rest));
  const signature = new Uint8Array(await subtle.sign(ALG, identity.privateKey, bytes));
  return { ...rest, sig: { alg: SIG_ALG, by: identity.fingerprint, key: exportPublic(identity), signature: b64(signature) } };
}

// Verify any attested object: recompute canonical bytes (sig stripped), verify against the EMBEDDED
// key, and confirm that key's fingerprint matches `sig.by` — so swapping the key fails the
// fingerprint check and swapping the content fails the signature. Returns { ok, by, alg, errors }.
export async function verifyAttestation(obj, opts = {}) {
  const errors = [];
  if (!obj || !obj.sig) return { ok: false, by: null, alg: null, errors: ["no sig"] };
  const { sig } = obj;
  if (sig.alg !== SIG_ALG) return { ok: false, by: sig.by || null, alg: sig.alg, errors: [`unsupported alg ${sig.alg}`] };
  const subtle = subtleOf(opts);
  const rest = { ...obj }; delete rest.sig;
  const bytes = new TextEncoder().encode(canonicalize(rest));
  let ok = false;
  try {
    const key = await importPublic(sig.key, opts);
    ok = await subtle.verify(ALG, key, unb64(sig.signature), bytes);
  } catch (e) { errors.push("verify threw: " + e.message); }
  if (!ok) errors.push("signature does not verify");
  const expect = await fingerprint(unb64(sig.key));
  if (expect !== sig.by) errors.push(`key fingerprint ${expect} ≠ sig.by ${sig.by}`);
  return { ok: ok && errors.length === 0, by: sig.by || null, alg: sig.alg, errors };
}

// ---- sign / verify an anecdote -------------------------------------------------------------------

// Sign a (valid) anecdote/v1 with a constituent identity. opts:
//   agent  { instrument, constitution }  — the Mobile LLM co-signature (bind the pinned instrument)
//   nonce  string                        — the revocable, anonymous identity handle (carried, bound)
// Returns a new object: the anecdote + agent? + nonce? + sig. Throws if the anecdote is malformed.
export async function sign(anecdote, identity, opts = {}) {
  const shape = validate(anecdote);
  if (!shape.ok) throw new Error("sign: invalid anecdote — " + shape.errors.join("; "));
  return attest(payload(anecdote, opts), identity, opts);
}

// Verify a signed anecdote: the generic attestation check PLUS the anecdote shape check. Reports WHO
// signed (`by`); whether that identity is expected/unrevoked is the consumer's call against the nonce.
export async function verifySignature(signed, opts = {}) {
  const base = await verifyAttestation(signed, opts);
  const shape = validate(signed);
  const errors = [...base.errors, ...(shape.ok ? [] : shape.errors)];
  return { ok: base.ok && shape.ok, by: base.by, alg: base.alg, errors };
}

// ---- env-portable base64 (no deps) --------------------------------------------------------------
function b64(u8) {
  if (typeof Buffer !== "undefined") return Buffer.from(u8).toString("base64");
  let s = ""; for (const x of u8) s += String.fromCharCode(x); return btoa(s);
}
function unb64(s) {
  if (typeof Buffer !== "undefined") return new Uint8Array(Buffer.from(s, "base64"));
  const bin = atob(s); const u8 = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) u8[i] = bin.charCodeAt(i); return u8;
}
