// ask.js — wizard:model+ask, a question for the model as a bottle: the door's /ask/ on the LAN, and the
// public site's /ask/ (site/you/wizards/ask.md). The parts, and a way back to blank:
//   the box       the question being written, and the asker's own instructions if they want any
//   the outbox    the code of the message being shown: what goes to the camera (or is set down on the LAN)
//   the notebook  every message this phone made, from the moment its code was made, its answer filled in when
//                 it comes. Each is a live item: "Use again" loads it back into the box (its instructions and
//                 the answers it quoted too) to edit and send; a waiting one can show its code again, or, once
//                 it has fallen off the loop, ask the loop for its answer back. Ticking an answered one quotes
//                 it into the next question; nothing points anywhere, so it works whichever model answers.
//   carried       everyone else's answers this phone caught from the loop: it carries them to the people they
//                 answer, who weren't there to read them, and "Show it" pours one again for another phone.
// The reply is OpenAI-enough messages (a role and its text, the question last; no model, bay or session). Its
// answer comes back in the public loop under the reply's nonce. Where the page may open a camera (a secure page:
// the public site), "Catch from the loop" reads everything in it (catch.mjs). On the LAN this page also asks the
// door for its waiting answers (/asks/answer/<nonce>) as a courtesy. Nothing is applied here: replies.py reads
// each bottle.
import "./sha256.mjs";
import { pour, nonce, localIso } from "./bottle.js";
import { catcher } from "./catch.mjs";
import { can, watch } from "./camera.mjs";

const C = JSON.parse(document.getElementById("ask-config").textContent);
const NOTEBOOK = "fcpm.ask.notebook", OUTBOX = "fcpm.ask.outbox", CARRIED = "fcpm.ask.carried", CARRIED_MOST = 200;
const URGENT = (C.urgent || 600) * 1000;          // how long the loop carries an answer before it falls off
const el = (id) => document.getElementById(id);
const load = (k, d) => { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch { return d; } };
const save = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch { /* not kept */ } };
const last = (reply) => reply.messages[reply.messages.length - 1].content;
const when = (iso) => (iso || "").slice(0, 16).replace("T", " ");

// An entry: {nonce, reply, q, made, a, label, at, quote}. `a` is null until the answer comes.
let notebook = load(NOTEBOOK, []), showing = null, current = null, pouring = null, waiting = null, eye = null;
let carried = load(CARRIED, []), relaying = null;

// What an older page kept as its one outbox becomes an entry like any other.
(() => {
  const old = load(OUTBOX, null);
  if (old && old.reply && !notebook.some((n) => n.nonce === old.reply.nonce)) {
    notebook.push({ nonce: old.reply.nonce, reply: old.reply, q: last(old.reply), made: old.made, a: null, quote: false });
    showing = old.reply.nonce;
  }
  save(NOTEBOOK, notebook);
  try { localStorage.removeItem(OUTBOX); } catch { /* nothing kept */ }
})();
const entry = (n) => notebook.find((x) => x.nonce && x.nonce === n);
const pending = () => notebook.filter((x) => x.reply && !x.a);

function messages() {
  const m = [];
  const inst = el("inst").value.trim();
  if (inst) m.push({ role: "system", content: inst });
  for (const n of notebook.filter((x) => x.quote && x.a)) {
    m.push({ role: "user", content: n.q });
    m.push({ role: "assistant", content: n.a });
  }
  m.push({ role: "user", content: el("box").value.trim() });
  return m;
}
const size = (m) => m.reduce((t, x) => t + x.content.length, 0);

const button = (text, fn, quiet = true) => {
  const b = Object.assign(document.createElement("button"), { type: "button", className: quiet ? "quiet" : "", textContent: text });
  b.addEventListener("click", fn);
  return b;
};

function paintNotebook() {
  el("notebook").replaceChildren(...notebook.slice().reverse().map((n) => {
    const li = document.createElement("li");
    if (n.nonce && n.nonce === showing) li.className = "showing";
    const q = Object.assign(document.createElement("p"), { className: "q", textContent: n.q });
    const a = Object.assign(document.createElement("p"), { className: "a",
      textContent: n.a || `Waiting for its answer, since ${when(n.made).slice(11)}.` });
    const meta = Object.assign(document.createElement("span"), { className: "meta",
      textContent: [n.label, when(n.at || n.made), n.nonce && `…${n.nonce.slice(-6)}`].filter(Boolean).join(" · ") });
    const acts = Object.assign(document.createElement("div"), { className: "acts" });
    acts.append(button("Use again", () => useAgain(n)));
    if (n.reply && !n.a) {
      acts.append(button("Show its code", () => show(n.nonce)));
      if (Date.now() - Date.parse(n.made) > URGENT) acts.append(button("Ask the loop for it", () => recall([n.nonce])));
    }
    if (n.a) {
      const tick = Object.assign(document.createElement("input"), { type: "checkbox", checked: !!n.quote });
      tick.addEventListener("change", () => { n.quote = tick.checked; save(NOTEBOOK, notebook); paintCount(); });
      const label = document.createElement("label");
      label.append(tick, Object.assign(document.createElement("span"), { textContent: "quote it" }));
      acts.append(label);
    }
    li.append(q, a, meta, acts);
    return li;
  }));
  el("notebook-empty").hidden = notebook.length > 0;
}

// A message back into the box: its question, its instructions, and the answers it quoted, ticked again.
function useAgain(n) {
  const msgs = (n.reply && n.reply.messages) || [{ role: "user", content: n.q }];
  el("inst").value = msgs.filter((m) => m.role === "system").map((m) => m.content).join("\n");
  el("inst").closest("details").open = Boolean(el("inst").value);
  for (const x of notebook) x.quote = false;
  for (let i = 0; i < msgs.length - 1; i++)
    if (msgs[i].role === "user" && msgs[i + 1] && msgs[i + 1].role === "assistant") {
      const q = notebook.find((x) => x.a && x.q === msgs[i].content && x.a === msgs[i + 1].content);
      if (q) q.quote = true;
    }
  el("box").value = msgs[msgs.length - 1].content;
  save(NOTEBOOK, notebook);
  paintNotebook(); paintCount();
  el("box").focus();
  el("box").scrollIntoView({ block: "center" });
}

function paintCount() {
  const n = size(messages());
  el("count").textContent = `${n} / ${C.limit}`;
  el("count").classList.toggle("over", n > C.limit);
  el("pour").disabled = !el("box").value.trim() || n > C.limit;
}

// The outbox: one entry's code (its reply, or a recall), poured until another is shown or it is answered.
async function show(n, bottle = null) {
  if (pouring) { pouring.stop(); pouring = null; }
  showing = n; current = null;
  const e = entry(n);
  el("outbox").hidden = !e && !bottle;
  paintNotebook();
  if (!e && !bottle) return;
  const reply = current = bottle || e.reply;
  el("asked").textContent = bottle ? "Ask the loop for its answer again" : e.q;
  pouring = await pour(el("code"), JSON.stringify(reply), { sign: true });
  el("read").textContent = `${pouring.read} · …${reply.nonce.slice(-6)}`;
  el("said").textContent = bottle ? "Show this to the camera: the answer comes back into the loop."
                                  : "Show this to the camera. Its answer comes back in the loop.";
  el("outbox").scrollIntoView({ block: "nearest" });
  listen();
}

function make() {
  const m = messages();
  if (!m[m.length - 1].content || size(m) > C.limit) return;
  const reply = { schema: "fcpm.reply/v0", wizard: "wizard:model+ask", at: C.at, issued: localIso(new Date()),
                  nonce: nonce(), messages: m };
  notebook.push({ nonce: reply.nonce, reply, q: last(reply), made: reply.issued, a: null, quote: false });
  save(NOTEBOOK, notebook);
  el("box").value = "";
  for (const x of notebook) x.quote = false;
  paintCount();
  show(reply.nonce);
}

// Bring answers back into the loop: one takes it over briefly (out of the way, then back to normal); several
// are put back in the running loop for another while.
function recall(nonces) {
  const bottle = { schema: "fcpm.reply/v0", wizard: "wizard:loop+recall", at: C.at, issued: localIso(new Date()),
                   nonce: nonce(), nonces, mode: nonces.length === 1 ? "takeover" : "inject" };
  show(null, bottle);
}

async function dropIt() {
  if (!C.lan || !current) return;
  try {
    const res = await fetch("/drop", { method: "POST", headers: { "Content-Type": "application/json" },
                                       body: JSON.stringify(current) });
    el("said").textContent = res.ok ? "Set down here. Its answer comes back in the loop." : "Not set down.";
  } catch {
    el("said").textContent = "Not on our network: show the code to the camera instead.";
  }
}

// On the LAN, ask the door now and then for whatever is still waiting; off it, this simply finds nothing.
function listen() {
  clearInterval(waiting);
  if (!C.lan) return;
  waiting = setInterval(async () => {
    const open = pending();
    if (!open.length) return clearInterval(waiting);
    for (const n of open) {
      try {
        const r = await fetch(`/asks/answer/${encodeURIComponent(n.nonce)}`, { cache: "no-store" });
        if (r.ok) take(await r.json());
      } catch { return; /* off the LAN */ }
    }
  }, 8000);
}

function take(a) {
  const e = entry(a.in_reply_to);
  if (!e || e.a) return;
  Object.assign(e, { a: a.answer, label: a.label, at: a.answered });
  save(NOTEBOOK, notebook);
  if (showing === e.nonce) show(null);
  paintNotebook(); paintCount();
}

// Read the loop with this phone's camera: everything in it is caught, this phone's own answers into the
// notebook, everyone else's into what it carries. It keeps reading until stopped.
async function catchIt() {
  if (eye) return stopCatch("Stopped.");
  const c = catcher((n) => Boolean(entry(n)));
  el("eye").hidden = false;
  el("catch").textContent = "Stop";
  el("caught").textContent = "Point it at the loop.";
  try {
    eye = await watch(el("eye"), async (text) => {
      const got = await c.feed(text);
      paintCatching(c.bottles);
      const answers = c.bottles.filter((b) => b.kind === "fcpm.answer");
      el("caught").textContent = `${answers.length} answer${answers.length === 1 ? "" : "s"} caught`
        + (c.index ? ` of ${c.index.answers.length}` : "");
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
                textContent: `for …${String(a.in_reply_to).slice(-6)} · ${when(a.answered)}` }),
              button("Show it", () => relay(a)));
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

function blank() {
  stopCatch();
  show(null);
  el("box").value = ""; el("inst").value = "";
  for (const n of notebook) n.quote = false;
  save(NOTEBOOK, notebook);
  paintNotebook(); paintCount();
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
  notebook = []; save(NOTEBOOK, notebook); show(null); paintNotebook(); paintCount();
});
el("drop").hidden = !C.lan;
el("loop-catch").hidden = !can();
paintNotebook(); paintCarried(); paintCount();
if (showing) show(showing);
if (pending().length) listen();
