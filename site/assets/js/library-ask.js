// library-ask.js — wizard:library+ask, or wizard:library+urgent when ticked: an ask of the library's
// receptionist as a bottle, for a camera at FC Public Media (site/you/wizards/library.md). The lane is the
// asker's choice. Nothing is sent from here: replies.py reads the bottle at the helm that holds the library.

import { pour, nonce, localIso } from "./bottle.js";

const C = JSON.parse(document.getElementById("library-ask-config").textContent);
const el = (id) => document.getElementById(id);
let pouring = null;

function paint() {
  const n = el("words").value.length;
  el("count").textContent = `${n} / ${C.limit}`;
  el("count").classList.toggle("over", n > C.limit);
  el("pour").disabled = !el("words").value.trim() || n > C.limit;
}

async function make() {
  const words = el("words").value.trim();
  if (!words || words.length > C.limit) return;
  const urgent = el("urgent").checked;
  const reply = { schema: "fcpm.reply/v0", wizard: urgent ? "wizard:library+urgent" : "wizard:library+ask",
                  at: C.at, issued: localIso(new Date()), nonce: nonce(), to: "receptionist", words };
  if (pouring) pouring.stop();
  el("outbox").hidden = false;
  el("asked").textContent = words;
  pouring = await pour(el("code"), JSON.stringify(reply), { sign: true });
  el("read").textContent = `${pouring.read} · ${urgent ? "urgent" : "ordinary"} · …${reply.nonce.slice(-6)}`;
  el("outbox").scrollIntoView({ block: "nearest" });
}

function blank() {
  if (pouring) pouring.stop();
  pouring = null;
  el("words").value = "";
  el("urgent").checked = false;
  el("outbox").hidden = true;
  paint();
}

el("words").addEventListener("input", paint);
el("pour").addEventListener("click", make);
el("blank").addEventListener("click", blank);
paint();
