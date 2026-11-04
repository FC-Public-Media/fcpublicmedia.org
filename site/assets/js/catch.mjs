// catch.mjs — a phone's catch from the public loop (the door's /loop/, qr.local's broadcast): frames in, every
// bottle out. The loop shows many bottles in turn, and every AC1 frame names its bottle by id; each id gets a
// catch of its own, and whichever completes is read by its kind. Everything in the stream is caught, not just
// this phone's own: an answer is public, and a phone that was at the cradle carries the others to the people
// they answer, who weren't there to read them. The index says which bottle answers which question; `wants`
// says which questions are this phone's, so its own are marked, never the only ones kept.
import { carrierSession } from "./composer/carrier.mjs";

const OPEN_MOST = 24;      // catches kept at once; the oldest is let go when a new id arrives
const td = new TextDecoder();

function bytesOf(b64) {
  const s = atob(b64), u = new Uint8Array(s.length);
  for (let i = 0; i < s.length; i++) u[i] = s.charCodeAt(i);
  return u;
}

// wants(nonce) -> true for this phone's own questions. feed(text) resolves to null, or { index } when an
// index completes, or { answer, mine } when any answer does (each once).
// `bottles` is every bottle seen in the stream, in the order first seen: {id, have, total, done, kind, label,
// for, mine}. `have` of `total` is blocks recovered of the blocks it needs (the composer's own count).
export function catcher(wants) {
  const open = new Map(), done = new Set(), seen = new Map();
  let index = null;
  const row = (id) => { if (!seen.has(id)) seen.set(id, { id, have: 0, total: null, done: false, kind: null,
                                                           label: null, for: null, mine: false });
                        return seen.get(id); };
  return {
    get index() { return index; },
    get bottles() { return [...seen.values()]; },
    async feed(text) {
      if (typeof text !== "string" || !text.startsWith("AC1|")) return null;
      const id = text.split("|")[3];
      const r = row(id);
      if (done.has(id)) return null;
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
        for (const a of json.answers || []) {
          const b = row(a.id);
          b.label = a.label || b.label;
          b.for = a.in_reply_to;
          b.mine = !!wants(a.in_reply_to);
        }
        return { index: json };
      }
      if (t.signed.kind === "fcpm.answer" && json.schema === "fcpm.answer/v0") {
        r.label = json.label || r.label;
        r.for = json.in_reply_to;
        r.mine = !!wants(json.in_reply_to);
        return { answer: json, mine: r.mine };
      }
      return null;
    },
  };
}
