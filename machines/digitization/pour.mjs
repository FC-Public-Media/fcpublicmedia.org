// pour.mjs — one bottle as AC1 fountain frames, for the public loop (machines/digitization/asks).
// stdin: {"kind": "fcpm.answer", "text": "...", "blockSize": 48, "count": 0, "qr": "L"};
// stdout: {"id", "K", "frames", "modules"?}. With `qr`, each frame's QR is drawn here too (site/assets/js/
// qr-encode.mjs, at that error level), as rows of 0 and 1: what a text screen (qr.local) prints in half blocks.
// The envelope is unsigned (an anecdote transfer with no sig: its bytes and their hash), as a phone without
// Ed25519 makes it; the frames carry its id, so a phone that knows the id from the index keeps these frames
// and lets every other bottle's go by. The composer is given as the one argument.
import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";

const dir = pathToFileURL(process.argv[2].replace(/\/?$/, "/")).href;
const { TRANSFER, transferId } = await import(dir + "transfer.mjs");
const { fountainTransfer } = await import(dir + "carrier.mjs");
const { defaultHash } = await import(dir + "anecdote.mjs");
const { kind, text, blockSize = 48, count = 0, overhead = 4, qr = null } = JSON.parse(readFileSync(0, "utf8"));
const bytes = new TextEncoder().encode(text);
const env = { schema: TRANSFER, kind, size: bytes.length, hash: await defaultHash(bytes),
              bytes: Buffer.from(bytes).toString("base64") };
const ft = await fountainTransfer(env, { blockSize });
// As the site pours (bottle.js): at least 40, and K×4 (small K needs the overhead). A loop that comes round
// again may ask for less (`overhead`): a phone left watching keeps its catch from one pass to the next.
const frames = ft.frames(Math.max(count, Math.ceil(ft.K * overhead), 40));
const out = { id: await transferId(env), K: ft.K, frames };
if (qr) {
  const { encodeQR } = await import(new URL("../qr-encode.mjs", dir).href);
  out.modules = frames.map((f) => { const q = encodeQR(f, { ecLevel: qr });
    return q.modules.map((row) => row.map((m) => (m ? "1" : "0")).join("")); });
}
process.stdout.write(JSON.stringify(out));
