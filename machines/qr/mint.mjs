// mint.mjs — mint a one-time AC1 code for the qr Pi, signed with this station's digitization key.
//   node mint.mjs fingerprint            print this key's {name, fingerprint} (the Pi's friends.json entry)
//   node mint.mjs approval "<words>"     an approval code; the Pi shows <words> when it accepts it
//   node mint.mjs pickup <row-id>        a pickup code for a row in the Pi's inbox.json
// Add --loop[=<bytes>] to pour it as a fountain video instead (droplets of <bytes>, default 48): writes
// $QR_LOOP (default /tmp/qr-codes/loop.html), a self-contained page that cycles the frames.
// Writes the code to $QR_OUT (default /tmp/qr-codes/code.png) and prints its frame and transfer id.
// The key lives in ~/.config/fcpm-qr/digitization.jwk (private; created on first use).
import { mkdirSync, readFileSync, writeFileSync, existsSync, chmodSync } from "node:fs";
import { deflateSync } from "node:zlib";
import { homedir } from "node:os";
import { randomBytes } from "node:crypto";
import { fingerprint } from "./composer/sign.mjs";
import { packTransfer } from "./composer/transfer.mjs";
import { frameTransfer, fountainTransfer } from "./composer/carrier.mjs";
import { encodeQR } from "./composer/qr-encode.mjs";

const NAME = "digitization";
const KEYDIR = `${homedir()}/.config/fcpm-qr`, KEY = `${KEYDIR}/${NAME}.jwk`;
const subtle = globalThis.crypto.subtle, ALG = { name: "Ed25519" };

async function identity() {
  if (!existsSync(KEY)) {
    mkdirSync(KEYDIR, { recursive: true, mode: 0o700 });
    const pair = await subtle.generateKey(ALG, true, ["sign", "verify"]);
    writeFileSync(KEY, JSON.stringify(await subtle.exportKey("jwk", pair.privateKey)), { mode: 0o600 });
    chmodSync(KEY, 0o600);
  }
  const jwk = JSON.parse(readFileSync(KEY, "utf8"));
  const privateKey = await subtle.importKey("jwk", jwk, ALG, false, ["sign"]);
  const { d, key_ops, ...pub } = jwk;
  const publicKey = await subtle.importKey("jwk", pub, ALG, true, ["verify"]);
  const raw = new Uint8Array(await subtle.exportKey("raw", publicKey));
  return { privateKey, publicKey, raw, fingerprint: await fingerprint(raw) };
}

function png(modules, size, path, scale = 12, quiet = 4) {
  const n = (size + 2 * quiet) * scale, raw = Buffer.alloc((n + 1) * n);
  for (let y = 0; y < n; y++) {
    raw[y * (n + 1)] = 0;
    for (let x = 0; x < n; x++) {
      const my = Math.floor(y / scale) - quiet, mx = Math.floor(x / scale) - quiet;
      raw[y * (n + 1) + 1 + x] = my >= 0 && mx >= 0 && my < size && mx < size && modules[my][mx] ? 0 : 255;
    }
  }
  const table = Array.from({ length: 256 }, (_, k) => { let c = k; for (let i = 0; i < 8; i++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1; return c >>> 0; });
  const crc = (b) => { let c = 0xffffffff; for (const v of b) c = table[(c ^ v) & 255] ^ (c >>> 8); return (c ^ 0xffffffff) >>> 0; };
  const chunk = (type, data) => {
    const len = Buffer.alloc(4); len.writeUInt32BE(data.length);
    const body = Buffer.concat([Buffer.from(type), data]), c = Buffer.alloc(4); c.writeUInt32BE(crc(body));
    return Buffer.concat([len, body, c]);
  };
  const ihdr = Buffer.alloc(13); ihdr.writeUInt32BE(n, 0); ihdr.writeUInt32BE(n, 4); ihdr[8] = 8; ihdr[9] = 0;
  writeFileSync(path, Buffer.concat([Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), chunk("IHDR", ihdr),
    chunk("IDAT", deflateSync(raw)), chunk("IEND", Buffer.alloc(0))]));
}

const flags = process.argv.slice(2).filter((a) => a.startsWith("--"));
const [cmd, arg] = process.argv.slice(2).filter((a) => !a.startsWith("--"));
const loopFlag = flags.find((f) => f.startsWith("--loop"));
const id = await identity();
if (cmd === "fingerprint") {
  console.log(JSON.stringify({ name: NAME, fingerprint: id.fingerprint }));
  process.exit(0);
}
const kinds = { approval: ["fcpm.approval", { say: arg || "" }], pickup: ["fcpm.pickup", { pickup: arg }] };
if (!kinds[cmd] || (cmd === "pickup" && !arg)) {
  console.error('usage: node mint.mjs fingerprint | approval "<words>" | pickup <row-id>');
  process.exit(2);
}
const [kind, body] = kinds[cmd];
body.nonce = randomBytes(6).toString("hex");
body.issued = new Date().toISOString();
const signed = await packTransfer(kind, new TextEncoder().encode(JSON.stringify(body)), id);
if (loopFlag) {
  const blockSize = +(loopFlag.split("=")[1] || 48);
  const ft = await fountainTransfer(signed, { blockSize });
  const count = Math.max(40, ft.K * 4);
  const frames = [];
  for (let seed = 0; seed < count; seed++) {
    const { modules, version } = encodeQR(ft.frame(seed), { ecLevel: "M" });
    frames.push({ v: version, m: modules.map((row) => row.map((x) => (x ? 1 : 0)).join("")) });
  }
  const out = process.env.QR_LOOP || "/tmp/qr-codes/loop.html";
  mkdirSync(out.replace(/\/[^/]*$/, ""), { recursive: true });
  writeFileSync(out, loopPage(frames, { kind, K: ft.K, blockSize, id: ft.memberId.slice(7, 23) }));
  console.log(JSON.stringify({ kind, body, K: ft.K, blockSize, frames: count, version: frames[0].v, loop: out }));
  process.exit(0);
}
const [frame, ...more] = await frameTransfer(signed, 4000);
if (more.length) throw new Error("expected a single frame");
const { size, modules, version } = encodeQR(frame, { ecLevel: "L" });
const out = process.env.QR_OUT || "/tmp/qr-codes/code.png";
mkdirSync(out.replace(/\/[^/]*$/, ""), { recursive: true });
png(modules, size, out);
if (process.env.QR_FRAME) writeFileSync(process.env.QR_FRAME, frame);
console.log(JSON.stringify({ kind, body, version, chars: frame.length, id: frame.split("|")[3].slice(7, 23), png: out }));

// A self-contained looping projector: no imports, opens from file://. Space pauses, +/- change speed.
function loopPage(frames, info) {
  return `<!doctype html><meta charset="utf-8"><title>AC1 loop · ${info.kind}</title>
<style>html,body{margin:0;height:100%;background:#fff;font:16px system-ui;color:#555}
canvas{display:block;margin:2vh auto 0;image-rendering:pixelated}#m{text-align:center}</style>
<canvas id="c"></canvas><div id="m"></div>
<script>
const F = ${JSON.stringify(frames)}, info = ${JSON.stringify(info)};
let i = 0, fps = 4, paused = false, timer;
const c = document.getElementById("c"), g = c.getContext("2d"), m = document.getElementById("m");
function draw() {
  const f = F[i], n = f.m.length, q = 4, side = Math.floor(Math.min(innerWidth, innerHeight * 0.92));
  const s = Math.max(1, Math.floor(side / (n + 2 * q)));
  c.width = c.height = (n + 2 * q) * s;
  g.fillStyle = "#fff"; g.fillRect(0, 0, c.width, c.height); g.fillStyle = "#000";
  f.m.forEach((row, y) => { for (let x = 0; x < n; x++) if (row[x] === "1") g.fillRect((x + q) * s, (y + q) * s, s, s); });
  m.textContent = "AC1 fountain · " + info.kind + " · " + info.id + " · frame " + (i + 1) + "/" + F.length +
    " · v" + f.v + " · " + info.blockSize + " B droplets · needs ~" + info.K + "+ · " + fps + "/s" + (paused ? " · paused" : "");
}
function arm() { clearInterval(timer); timer = setInterval(() => { if (!paused) { i = (i + 1) % F.length; draw(); } }, 1000 / fps); }
addEventListener("keydown", (e) => {
  if (e.key === " ") paused = !paused;
  if (e.key === "+" || e.key === "=") fps = Math.min(30, fps + 1);
  if (e.key === "-") fps = Math.max(1, fps - 1);
  arm(); draw();
});
addEventListener("resize", draw);
draw(); arm();
</script>`;
}
