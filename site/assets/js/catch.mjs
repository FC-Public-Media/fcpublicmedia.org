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
export function catcher(wants) {
  const open = new Map(), others = new Set(), done = new Set();
  let index = null;
  return {
    get index() { return index; },
    async feed(text) {
      if (typeof text !== "string" || !text.startsWith("AC1|")) return null;
      const id = text.split("|")[3];
      if (others.has(id) || done.has(id)) return null;
      if (!open.has(id)) {
        if (open.size >= OPEN_MOST) open.delete(open.keys().next().value);
        open.set(id, carrierSession());
      }
      const snap = await open.get(id).feed(text);
      if (!(snap && snap.complete)) return null;
      const res = await open.get(id).result();
      open.delete(id);
      done.add(id);
      const t = res.transfers[0];
      if (!t || !t.signed || !t.signed.bytes) return null;
      let json;
      try { json = JSON.parse(td.decode(bytesOf(t.signed.bytes))); } catch { return null; }
      if (t.signed.kind === "fcpm.index" && json.schema === "fcpm.index/v0") {
        index = json;
        others.clear();
        for (const row of json.answers || []) if (!wants(row.in_reply_to)) others.add(row.id);
        for (const k of [...open.keys()]) if (others.has(k)) open.delete(k);
        return { index: json };
      }
      if (t.signed.kind === "fcpm.answer" && json.schema === "fcpm.answer/v0" && wants(json.in_reply_to))
        return { answer: json };
      return null;
    },
  };
}
