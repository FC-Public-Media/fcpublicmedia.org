// verify-bottle.mjs — the composer reads one bottle for replies.py. stdin: one JSON object; stdout: one.
//   {"transfer": {...}, "friends": [fp...]}     a signed transfer, as set down over the LAN (POST /drop)
//   {"frames": ["AC1|d|...", ...], "friends": []} AC1 frames as a camera read them (the eyes, page.py)
// Answers {ok, by, kind, trusted, unsigned, errors, text}. The composer is the scanner trove's (troves/
// scanner/composer, vendored from anecdote.channel), given as the one argument; the carrier does all the
// reading (order, healing, foreign tiles, signatures), as the Pi's bridge.mjs has it. A transfer with no
// signature at all (a phone without Ed25519) is read by its hash alone and answered `unsigned`; one
// whose signature is there and wrong is not.
import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";

const dir = pathToFileURL(process.argv[2].replace(/\/?$/, "/")).href;
const { verifyTransfer } = await import(dir + "transfer.mjs");
const { carrierSession } = await import(dir + "carrier.mjs");
const { defaultHash } = await import(dir + "anecdote.mjs");
const input = JSON.parse(readFileSync(0, "utf8"));
const friends = input.friends || [];
const say = (o) => process.stdout.write(JSON.stringify(o) + "\n");
const td = new TextDecoder();

// No sig at all, and the bytes hash to `hash`: intact, from nobody in particular.
async function unsigned(env) {
  if (!env || env.schema !== "anecdote.transfer/v1" || env.sig) return null;
  try {
    const bytes = Uint8Array.from(Buffer.from(env.bytes, "base64"));
    if ((await defaultHash(bytes)) !== env.hash) return null;
    return { ok: true, by: null, kind: env.kind, trusted: false, unsigned: true, errors: [], bytes };
  } catch { return null; }
}

let v;
if (Array.isArray(input.frames)) {
  const session = carrierSession({ friends });
  let snap = null;
  for (const f of input.frames) snap = await session.feed(f);
  if (!snap || !snap.complete) {
    say({ ok: false, by: null, kind: null, trusted: false, text: null,
          errors: ["incomplete: " + (snap ? snap.present.map((p) => `${p.have}/${p.total}`).join(", ") : "no frames")] });
    process.exit(0);
  }
  const r = await session.result();
  v = r.transfers.length ? r.transfers[0].verify : { ok: false, by: null, kind: null, trusted: false, errors: ["no transfer"] };
  if (!v.ok && r.transfers.length) v = (await unsigned(r.transfers[0].signed)) || v;
} else {
  v = await verifyTransfer(input.transfer, { friends });
  if (!v.ok) v = (await unsigned(input.transfer)) || v;
}
say({ ok: !!v.ok, by: v.by || null, kind: v.kind || null, trusted: !!v.trusted, unsigned: !!v.unsigned, errors: v.errors || [],
      text: v.bytes ? td.decode(v.bytes) : null });
