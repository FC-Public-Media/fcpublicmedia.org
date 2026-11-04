// catch.mjs — a phone's catch from the public loop (the door's /loop/): frames in, its own answers out.
// The loop shows many bottles in turn, and every AC1 frame names its bottle by id. Until the index has been
// read, each id gets a catch of its own; whichever completes is read by its kind. The index says which bottle
// answers which question (by the nonce the phone already holds), so from then on the frames of bottles listed
// for someone else are let go by without being kept. An id the index doesn't list (the next index, or an
// answer newer than it) still gets a catch. Others' answers are public; this only saves the phone the work.
import { carrierSession } from "./composer/carrier.mjs";

const OPEN_MOST = 16;      // catches kept at once; the oldest is let go when a new id arrives
const td = new TextDecoder();

function bytesOf(b64) {
  const s = atob(b64), u = new Uint8Array(s.length);
  for (let i = 0; i < s.length; i++) u[i] = s.charCodeAt(i);
  return u;
}

// wants(nonce) -> true for the questions this phone is waiting on. feed(text) resolves to null, or
// { index } when an index completes, or { answer } when a wanted answer does (each answer once).
// `bottles` is every bottle seen in the stream, in the order first seen: {id, have, total, done, kind, label,
// mine, passing}. `have` of `total` is blocks recovered of the blocks it needs (the composer's own count);
// a bottle the index lists for someone else is `passing`: named, but let go by.
export function catcher(wants) {
  const open = new Map(), others = new Set(), done = new Set(), seen = new Map();
  let index = null;
  const row = (id) => { if (!seen.has(id)) seen.set(id, { id, have: 0, total: null, done: false, kind: null,
                                                           label: null, mine: false, passing: false });
                        return seen.get(id); };
  return {
    get index() { return index; },
    get bottles() { return [...seen.values()]; },
    async feed(text) {
      if (typeof text !== "string" || !text.startsWith("AC1|")) return null;
      const id = text.split("|")[3];
      const r = row(id);
      if (others.has(id) || done.has(id)) return null;
      if (!open.has(id)) {
        if (open.size >= OPEN_MOST) open.delete(open.keys().next().value);
        open.set(id, carrierSession());
      }
      const snap = await open.get(id).feed(text);
      const p = snap && snap.present && snap.present[0];
      if (p) { r.have = p.have || 0; r.total = p.total; }
      if (!(snap && snap.complete)) return null;
      r.done = true;
      const res = await open.get(id).result();
      open.delete(id);
      done.add(id);
      const t = res.transfers[0];
      if (!t || !t.signed || !t.signed.bytes) return null;
      let json;
      try { json = JSON.parse(td.decode(bytesOf(t.signed.bytes))); } catch { return null; }
      r.kind = t.signed.kind;
      if (t.signed.kind === "fcpm.index" && json.schema === "fcpm.index/v0") {
        index = json;
        r.label = `the index · ${(json.answers || []).length}`;
        others.clear();
        for (const a of json.answers || []) {
          const b = row(a.id);
          b.label = a.label || b.label;
          b.mine = !!wants(a.in_reply_to);
          if (!b.mine) { others.add(a.id); b.passing = !b.done; }
        }
        for (const k of [...open.keys()]) if (others.has(k)) open.delete(k);
        return { index: json };
      }
      if (t.signed.kind === "fcpm.answer" && json.schema === "fcpm.answer/v0") {
        r.label = json.label || r.label;
        r.mine = !!wants(json.in_reply_to);
        if (r.mine) return { answer: json };
      }
      return null;
    },
  };
}
