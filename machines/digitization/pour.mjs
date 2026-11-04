// pour.mjs — one bottle as AC1 fountain frames, for the public loop (machines/digitization/asks).
// stdin: {"kind": "fcpm.answer", "text": "...", "blockSize": 48, "count": 24}; stdout: {"id", "K", "frames"}.
// The envelope is unsigned (an anecdote transfer with no sig: its bytes and their hash), as a phone
// without Ed25519 makes it; the frames carry its id, so a phone that knows the id from the index keeps
// these frames and lets every other bottle's go by. The composer is given as the one argument.
import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";

const dir = pathToFileURL(process.argv[2].replace(/\/?$/, "/")).href;
const { TRANSFER, transferId } = await import(dir + "transfer.mjs");
const { fountainTransfer } = await import(dir + "carrier.mjs");
const { defaultHash } = await import(dir + "anecdote.mjs");
const { kind, text, blockSize = 48, count = 0 } = JSON.parse(readFileSync(0, "utf8"));
const bytes = new TextEncoder().encode(text);
const env = { schema: TRANSFER, kind, size: bytes.length, hash: await defaultHash(bytes),
              bytes: Buffer.from(bytes).toString("base64") };
const ft = await fountainTransfer(env, { blockSize });
const frames = ft.frames(Math.max(count, ft.K * 4, 40));   // as the site pours (bottle.js): small K needs the overhead
process.stdout.write(JSON.stringify({ id: await transferId(env), K: ft.K, frames }));
