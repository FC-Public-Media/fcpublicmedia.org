// camera.mjs — the phone's camera as a reader of codes: every code it sees, each new one's text handed to onText.
// A screen may show several codes up at once (the loop's ?up=2 and ?up=4), and the decoder (qr-decode.mjs) reads
// one code an image, so each frame is read whole and then by region: its halves side by side, its halves top and
// bottom, and its quarters. Every distinct code found is handed on, so codes side by side or two by two are all
// caught together. Only a secure page may open a camera (the public site; not a plain-http .local page), so
// `can()` says first.
import { decodeImage } from "./qr-decode.mjs";

export const can = () => Boolean(globalThis.isSecureContext && navigator.mediaDevices && navigator.mediaDevices.getUserMedia);

const RECENT = 256;        // texts already handed on, so a code held still isn't handed on every frame

// The regions a frame is read in, as [x, y, w, h] fractions: whole, then overlapping windows (60% wide or tall,
// from the start or from 40%), side by side, top and bottom, and in quarters. They overlap because a camera never
// lines up with a screen's grid: whichever way the codes sit, each lies whole inside one window.
const REGIONS = [[0, 0, 1, 1], [0, 0, .6, 1], [.4, 0, .6, 1], [0, 0, 1, .6], [0, .4, 1, .6],
                 [0, 0, .6, .6], [.4, 0, .6, .6], [0, .4, .6, .6], [.4, .4, .6, .6]];

// Every distinct code in one image (an ImageData's worth: {data, width, height} and a way to cut regions).
export function readAll(g, width, height, regions = REGIONS) {
  const found = new Set();
  for (const [fx, fy, fw, fh] of regions) {
    const x = Math.floor(fx * width), y = Math.floor(fy * height), w = Math.floor(fw * width), h = Math.floor(fh * height);
    if (w < 64 || h < 64) continue;
    const r = decodeImage(g.getImageData(x, y, w, h));
    if (r && r.text) found.add(r.text);
  }
  return [...found];
}

export async function watch(video, onText, { every = 100 } = {}) {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: false,
    video: { facingMode: { ideal: "environment" }, width: { ideal: 1280 }, height: { ideal: 720 } } });
  video.srcObject = stream;
  video.setAttribute("playsinline", "");
  video.muted = true;
  await video.play();
  const c = document.createElement("canvas"), g = c.getContext("2d", { willReadFrequently: true });
  const recent = [];
  let timer = null, live = true;
  const look = async () => {
    if (!live) return;
    if (video.videoWidth) {
      c.width = video.videoWidth; c.height = video.videoHeight;
      g.drawImage(video, 0, 0);
      for (const text of readAll(g, c.width, c.height)) {
        if (recent.includes(text)) continue;
        recent.push(text);
        if (recent.length > RECENT) recent.shift();
        await onText(text);
      }
    }
    timer = setTimeout(look, every);
  };
  look();
  return { stop() { live = false; clearTimeout(timer); for (const t of stream.getTracks()) t.stop(); video.srcObject = null; } };
}
