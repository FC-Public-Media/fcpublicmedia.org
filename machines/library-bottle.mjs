// library-bottle.mjs — the library's iced bottles, by .you-engine's codec (docs/pickup.md, The iced bottle).
//
//     node library-bottle.mjs mint              a new signer: one JSON line, {key, fingerprint}; library.py keeps it
//     node library-bottle.mjs who               LIBRARY_SIGNER's fingerprint, never the key
//     node library-bottle.mjs bottle KIND OUT   stdin's bytes as an iced bottle at OUT (a GIF), read back first
//     node library-bottle.mjs open GIF          a bottle's bytes on stdout; what it says of itself on stderr
//
// The signer comes in LIBRARY_SIGNER (pkcs8, base64): the keychain's `library` group, never a file here. It says
// "the library on this machine bottled these bytes". A bottle is read back with the reader a phone uses and is
// kept only when the bytes that come out are the bytes that went in, as the engine's own bin/publish does.

import { readFileSync, writeFileSync } from "node:fs";

const engine = (p) => import(new URL(`../.you-engine/${p}`, import.meta.url).href).catch(() => {
  console.error("library-bottle: the bottle code (.you-engine) is not on this machine: `fcpm install` fetches it");
  process.exit(3);
});
const subtle = globalThis.crypto.subtle;
const b64 = (u) => Buffer.from(u).toString("base64");
const unb64 = (s) => new Uint8Array(Buffer.from(s, "base64"));
const stdin = () => new Uint8Array(readFileSync(0));

async function signer() {
  const { fingerprint } = await engine("anecdote.channel/composer/sign.mjs");
  const key = (process.env.LIBRARY_SIGNER || "").trim();
  if (!key) {
    console.error("library-bottle: no LIBRARY_SIGNER. Nothing was bottled: fcpm library signer mint, once, on purpose");
    process.exit(4);
  }
  const privateKey = await subtle.importKey("pkcs8", unb64(key), { name: "Ed25519" }, true, ["sign"]);
  const jwk = await subtle.exportKey("jwk", privateKey);
  const raw = unb64(jwk.x.replace(/-/g, "+").replace(/_/g, "/"));
  return { privateKey, raw, fingerprint: await fingerprint(raw) };
}

const [verb, a, b] = process.argv.slice(2);
if (verb === "mint") {
  const { fingerprint } = await engine("anecdote.channel/composer/sign.mjs");
  const pair = await subtle.generateKey({ name: "Ed25519" }, true, ["sign", "verify"]);
  const raw = new Uint8Array(await subtle.exportKey("raw", pair.publicKey));
  console.log(JSON.stringify({ key: b64(new Uint8Array(await subtle.exportKey("pkcs8", pair.privateKey))),
                               fingerprint: await fingerprint(raw) }));
} else if (verb === "who") {
  console.log((await signer()).fingerprint);
} else if (verb === "bottle" && a && b) {
  const { bottle, unbottle } = await engine("bottle/bottle.mjs");
  const bytes = stdin();
  const made = await bottle(bytes, await signer(), { kind: a });
  const back = await unbottle(made.gif);
  if (!(back.ok && back.bytes.length === bytes.length && back.bytes.every((v, i) => v === bytes[i]))) {
    console.error("library-bottle: the GIF did not read back as the bytes: " + back.errors.join("; "));
    process.exit(5);
  }
  writeFileSync(b, made.gif);
  console.log(JSON.stringify({ id: made.id, kind: a, by: back.by, frames: made.frames, version: made.version,
                               size: made.size, bytes: bytes.length, gif: made.gif.length }));
} else if (verb === "open" && a) {
  const { unbottle } = await engine("bottle/bottle.mjs");
  const back = await unbottle(new Uint8Array(readFileSync(a)));
  console.error(JSON.stringify({ ok: back.ok, kind: back.kind, by: back.by, frames: back.frames, errors: back.errors }));
  if (!back.ok) process.exit(6);
  process.stdout.write(Buffer.from(back.bytes));
} else {
  console.error("usage: library-bottle.mjs mint | bottle KIND OUT | open GIF");
  process.exit(2);
}
