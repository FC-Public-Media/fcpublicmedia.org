// camera.mjs — the phone's camera as a reader of codes: each new code's text, handed to onText. Only a
// secure page may open a camera (the public site; not a plain-http .local page), so `can()` says first.
import { decodeImage } from "./qr-decode.mjs";

export const can = () => Boolean(globalThis.isSecureContext && navigator.mediaDevices && navigator.mediaDevices.getUserMedia);

export async function watch(video, onText, { every = 100 } = {}) {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: false,
    video: { facingMode: { ideal: "environment" }, width: { ideal: 1280 }, height: { ideal: 720 } } });
  video.srcObject = stream;
  video.setAttribute("playsinline", "");
  video.muted = true;
  await video.play();
  const c = document.createElement("canvas"), g = c.getContext("2d", { willReadFrequently: true });
  let last = "", timer = null, live = true;
  const look = async () => {
    if (!live) return;
    if (video.videoWidth) {
      c.width = video.videoWidth; c.height = video.videoHeight;
      g.drawImage(video, 0, 0);
      const r = decodeImage(g.getImageData(0, 0, c.width, c.height));
      if (r && r.text && r.text !== last) { last = r.text; await onText(r.text); }
    }
    timer = setTimeout(look, every);
  };
  look();
  return { stop() { live = false; clearTimeout(timer); for (const t of stream.getTracks()) t.stop(); video.srcObject = null; } };
}
