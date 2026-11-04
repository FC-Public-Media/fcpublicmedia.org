// ask.js — wizard:model+ask, a question for the model as a bottle: the door's /ask/ on the LAN, and the
// public site's /ask/ (site/you/wizards/ask.md). Three parts and a way
// back to blank:
//   the box       the question being written, and the asker's own instructions if they want any
//   the outbox    exactly what will be poured: the reply, as a code for a camera (or set down on the LAN)
//   the notebook  questions and answers kept on this phone. Ticking one quotes it into the next question;
//                 nothing points anywhere, so it works whichever model answers, or none that remembers.
//   carried       everyone else's answers this phone caught from the loop: it carries them to the people they
//                 answer, who weren't there to read them, and "Show it" pours one again for another phone.
// The reply is OpenAI-enough messages (a role and its text, the question last; no model, bay or session).
// Its answer comes back in the public loop (/loop/) under the reply's nonce. Where the page may open a camera
// (a secure page: the public site), "Catch it from the loop" reads the loop until this question's answer has
// come by (catch.mjs: its own frames kept, everyone else's let go). On the LAN this page also asks the door
// for it (/asks/answer/<nonce>) as a courtesy. Nothing is applied here: replies.py reads the bottle.
import "./sha256.mjs";
import { pour, nonce, localIso } from "./bottle.js";
import { catcher } from "./catch.mjs";
import { can, watch } from "./camera.mjs";

const C = JSON.parse(document.getElementById("ask-config").textContent);
const NOTEBOOK = "fcpm.ask.notebook", OUTBOX = "fcpm.ask.outbox", CARRIED = "fcpm.ask.carried", CARRIED_MOST = 200;
const el = (id) => document.getElementById(id);
const load = (k, d) => { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch { return d; } };
const save = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch { /* not kept */ } };

let notebook = load(NOTEBOOK, []), outbox = load(OUTBOX, null), pouring = null, waiting = null, eye = null;
let carried = load(CARRIED, []), relaying = null;

function messages() {
  const m = [];
  const inst = el("inst").value.trim();
  if (inst) m.push({ role: "system", content: inst });
  for (const n of notebook.filter((x) => x.quote)) {
    m.push({ role: "user", content: n.q });
    m.push({ role: "assistant", content: n.a });
  }
  m.push({ role: "user", content: el("box").value.trim() });
  return m;
}
const size = (m) => m.reduce((t, x) => t + x.content.length, 0);

function paintNotebook() {
  const list = el("notebook");
  list.replaceChildren(...notebook.slice().reverse().map((n) => {
    const li = document.createElement("li");
    const tick = Object.assign(document.createElement("input"), { type: "checkbox", checked: !!n.quote });
    tick.addEventListener("change", () => { n.quote = tick.checked; save(NOTEBOOK, notebook); paintCount(); });
    const q = Object.assign(document.createElement("p"), { className: "q", textContent: n.q });
    const a = Object.assign(document.createElement("p"), { className: "a", textContent: n.a });
    const meta = Object.assign(document.createElement("span"), { className: "meta",
      textContent: `${n.label || ""}${n.label ? " · " : ""}${(n.at || "").slice(0, 16).replace("T", " ")}` });
    const label = document.createElement("label");
    label.append(tick, Object.assign(document.createElement("span"), { textContent: "quote it" }));
    li.append(q, a, meta, label);
    return li;
  }));
  el("notebook-empty").hidden = notebook.length > 0;
}

function paintCount() {
  const n = size(messages());
  el("count").textContent = `${n} / ${C.limit}`;
  el("count").classList.toggle("over", n > C.limit);
  el("pour").disabled = !el("box").value.trim() || n > C.limit;
}

async function showOutbox() {
  if (pouring) { pouring.stop(); pouring = null; }
  el("outbox").hidden = !outbox;
  if (!outbox) return;
  el("asked").textContent = outbox.reply.messages[outbox.reply.messages.length - 1].content;
  pouring = await pour(el("code"), JSON.stringify(outbox.reply), { sign: true });
  el("read").textContent = `${pouring.read} · …${outbox.reply.nonce.slice(-6)}`;
  el("said").textContent = "Show this to the camera. Its answer comes back in the loop.";
  listen();
}

// Read the loop with this phone's camera: everything in it is caught, this phone's own answer into the
// notebook, everyone else's into what it carries. It keeps reading until stopped.
async function catchIt() {
  if (eye) return stopCatch("Stopped.");
  const want = outbox && outbox.reply.nonce, c = catcher((n) => n === want);
  el("eye").hidden = false;
  el("catch").textContent = "Stop";
  el("caught").textContent = "Point it at the loop.";
  try {
    eye = await watch(el("eye"), async (text) => {
      const got = await c.feed(text);
      paintCatching(c.bottles);
      const answers = c.bottles.filter((b) => b.kind === "fcpm.answer");
      el("caught").textContent = `${answers.length} answer${answers.length === 1 ? "" : "s"} caught`
        + (c.index ? ` of ${c.index.answers.length}` : "") + (want ? "" : " · carrying them");
      if (got && got.answer) {
        if (got.mine) take(got.answer);
        else carry(got.answer);
      }
    });
  } catch (error) {
    stopCatch("The camera didn't open: " + (error && error.message || error));
  }
}

function carry(a) {
  carried = carried.filter((x) => x.in_reply_to !== a.in_reply_to);
  carried.push({ ...a, caught: localIso(new Date()) });
  carried = carried.slice(-CARRIED_MOST);
  save(CARRIED, carried);
  paintCarried();
}

function paintCarried() {
  el("carried").replaceChildren(...carried.slice().reverse().map((a) => {
    const li = document.createElement("li");
    li.append(Object.assign(document.createElement("p"), { className: "q", textContent: a.label || "An answer" }),
              Object.assign(document.createElement("p"), { className: "a", textContent: a.answer }),
              Object.assign(document.createElement("span"), { className: "meta",
                textContent: `for …${String(a.in_reply_to).slice(-6)} · ${(a.answered || "").slice(0, 16).replace("T", " ")}` }));
    const show = Object.assign(document.createElement("button"), { type: "button", className: "quiet", textContent: "Show it" });
    show.addEventListener("click", () => relay(a));
    li.append(show);
    return li;
  }));
  el("carried-empty").hidden = carried.length > 0;
}

// Pour a carried answer again, as an answer, for the phone of the person it answers (or anyone's).
async function relay(a) {
  if (relaying) { relaying.stop(); relaying = null; }
  el("relay").hidden = false;
  const { in_reply_to, label, answer, answered, schema, shape, model } = a;
  relaying = await pour(el("relay-code"), JSON.stringify({ schema, in_reply_to, shape, label, answer, model, answered }),
                        { sign: true, kind: "fcpm.answer" });
  el("relay-read").textContent = `${label || "An answer"} · for …${String(in_reply_to).slice(-6)} · ${relaying.read}`;
}

// Every bottle going by, as it goes by: what it is (once known), how far it has got, and whose it is.
function paintCatching(bottles) {
  el("catching").replaceChildren(...bottles.map((b) => {
    const li = document.createElement("li");
    li.className = b.mine ? "mine" : b.kind === "fcpm.index" ? "index" : "";
    const what = Object.assign(document.createElement("span"), { className: "what",
      textContent: b.label || (b.kind === "fcpm.index" ? "the index" : `…${b.id.slice(-6)}`) });
    const how = Object.assign(document.createElement("span"), { className: "how",
      textContent: b.done ? (b.mine ? "yours" : b.kind === "fcpm.index" ? "read" : "carried")
                 : b.total ? `${b.mine ? "yours · " : ""}${b.have} of ${b.total}` : "…" });
    const bar = Object.assign(document.createElement("span"), { className: "bar" });
    bar.style.setProperty("--p", b.total ? Math.min(1, b.have / b.total) : 0);
    li.append(what, how, bar);
    return li;
  }));
}

function stopCatch(why) {
  if (eye) { eye.stop(); eye = null; }
  el("eye").hidden = true;
  el("catching").replaceChildren();
  el("catch").textContent = "Catch from the loop";
  el("caught").textContent = why || "";
}

function make() {
  const m = messages();
  if (!m[m.length - 1].content || size(m) > C.limit) return;
  outbox = { reply: { schema: "fcpm.reply/v0", wizard: "wizard:model+ask", at: C.at, issued: localIso(new Date()),
                      nonce: nonce(), messages: m }, made: localIso(new Date()) };
  save(OUTBOX, outbox);
  showOutbox();
}

async function dropIt() {
  if (!outbox || !C.lan) return;
  try {
    const res = await fetch("/drop", { method: "POST", headers: { "Content-Type": "application/json" },
                                       body: JSON.stringify(outbox.reply) });
    el("said").textContent = res.ok ? "Set down here. Its answer comes back in the loop." : "Not set down.";
  } catch {
    el("said").textContent = "Not on our network: show the code to the camera instead.";
  }
}

// On the LAN, ask the door now and then; off it, this simply finds nothing.
function listen() {
  clearInterval(waiting);
  if (!C.lan) return;
  waiting = setInterval(async () => {
    if (!outbox) return clearInterval(waiting);
    try {
      const r = await fetch(`/asks/answer/${encodeURIComponent(outbox.reply.nonce)}`, { cache: "no-store" });
      if (r.ok) take(await r.json());
    } catch { /* off the LAN */ }
  }, 8000);
}

function take(a) {
  if (!outbox || a.in_reply_to !== outbox.reply.nonce) return;
  notebook.push({ q: outbox.reply.messages[outbox.reply.messages.length - 1].content, a: a.answer, label: a.label,
                  nonce: a.in_reply_to, at: a.answered, quote: false });
  save(NOTEBOOK, notebook);
  outbox = null; save(OUTBOX, null);
  el("box").value = "";
  showOutbox(); paintNotebook(); paintCount();
}

function blank() {
  stopCatch();
  outbox = null; save(OUTBOX, null);
  el("box").value = ""; el("inst").value = "";
  for (const n of notebook) n.quote = false;
  save(NOTEBOOK, notebook);
  showOutbox(); paintNotebook(); paintCount();
}

el("box").addEventListener("input", paintCount);
el("inst").addEventListener("input", paintCount);
el("pour").addEventListener("click", make);
el("drop").addEventListener("click", dropIt);
el("blank").addEventListener("click", blank);
el("catch").addEventListener("click", catchIt);
el("relay-stop").addEventListener("click", () => { if (relaying) relaying.stop(); relaying = null; el("relay").hidden = true; });
el("forget").addEventListener("click", () => {
  if (!confirm("Forget every question and answer kept on this phone?")) return;
  notebook = []; save(NOTEBOOK, notebook); paintNotebook(); paintCount();
});
el("drop").hidden = !C.lan;
el("loop-catch").hidden = !can();
paintNotebook(); paintCarried(); paintCount(); showOutbox();
