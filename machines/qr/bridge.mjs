// bridge.mjs — feeds decoded QR strings into the AC1 carrier (bottles transit frames) and reports back.
// stdin: one JSON object per line, {"frame": "<decoded QR text>"}. stdout: one JSON object per line.
// The carrier does all the reading: order, duplicates, healing, foreign tiles, signatures. This file only
// keeps one catch going at a time and says who signed what, by the names in friends.json.
import { createInterface } from "node:readline";
import { readFileSync } from "node:fs";
import { carrierSession, parseFrame } from "./composer/carrier.mjs";

// Who this station trusts: this machine's friends.json (in $QR_STATE) if it has one, else the profile's.
const FRIENDS = [process.env.QR_STATE && `${process.env.QR_STATE}/friends.json`, new URL("./friends.json", import.meta.url)].filter(Boolean);
const QUIET_MS = 30_000;   // a catch with no new frame for this long starts over

const loadFriends = () => {
  for (const f of FRIENDS) { try { return JSON.parse(readFileSync(f, "utf8")); } catch {} }
  return [];
};
const out = (o) => process.stdout.write(JSON.stringify(o) + "\n");
const td = new TextDecoder();

let friends = loadFriends(), session = null, last = 0;

for await (const line of createInterface({ input: process.stdin })) {
  let frame;
  try { ({ frame } = JSON.parse(line)); } catch { continue; }
  if (!parseFrame(frame)) { out({ type: "foreign", reason: "not one of our envelopes (no AC1 frame)" }); continue; }

  const now = Date.now();
  if (!session || now - last > QUIET_MS) {
    friends = loadFriends();
    session = carrierSession({ friends: friends.map((f) => f.fingerprint) });
  }
  last = now;

  const snap = await session.feed(frame);
  out({ type: "snapshot", snap });
  if (!snap.complete) continue;

  const r = await session.result();
  out({
    type: "result", ok: r.ok, foreign: r.foreign, ids: snap.present.map((p) => p.id),
    transfers: r.transfers.map(({ verify: v }) => ({
      ok: v.ok, trusted: v.trusted, kind: v.kind, by: v.by,
      name: (friends.find((f) => f.fingerprint === v.by) || {}).name || null,
      errors: v.errors, size: v.bytes ? v.bytes.length : 0,
      text: v.bytes ? td.decode(v.bytes).slice(0, 4000) : null,
    })),
  });
  session = null;
}
