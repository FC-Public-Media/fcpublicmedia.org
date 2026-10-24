// app.js -- ch97: the day as we laid it (schedule/<date>.json), Cablecast's copy held up beside it,
// and the reserve to fill from. Data comes in and the page draws it; each request to the box shows in
// the bar for as long as it runs. Nothing here writes. See ../../PROFILE.md, "ch97".
import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import htm from "htm";

const html = htm.bind(React.createElement);

const ZONE = "America/Denver"; // the channel's clock
const PX = 4 / 60;             // pixels per second of air: 4 a minute
const SEAM = 60;               // a gap shorter than this is a seam: drawn, not named
const LATELY = 60;             // days of airings that say what ran lately
const LOOK_AGAIN = 5 * 60e3;   // Cablecast's copy is looked at again this often, quietly
const SHOWN = 150;             // reserve rows drawn at once

// --- time, on the channel's clock -------------------------------------------------------------
const fields = new Intl.DateTimeFormat("en-US", { timeZone: ZONE, hourCycle: "h23", year: "numeric",
  month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", second: "2-digit" });
const parts = (ms) => Object.fromEntries(fields.formatToParts(ms).map((p) => [p.type, p.value]));
const clock = new Intl.DateTimeFormat("en-US", { timeZone: ZONE, hour: "numeric", minute: "2-digit" });
const hourName = new Intl.DateTimeFormat("en-US", { timeZone: ZONE, hour: "numeric" });
const dayName = new Intl.DateTimeFormat("en-US", { timeZone: "UTC", weekday: "short", month: "short", day: "numeric" });

const today = () => { const p = parts(Date.now()); return `${p.year}-${p.month}-${p.day}`; };
const shift = (date, n) => new Date(Date.parse(`${date}T12:00:00Z`) + n * 864e5).toISOString().slice(0, 10);
const named = (date) => dayName.format(Date.parse(`${date}T12:00:00Z`));

// The instant the channel's clock reads `date` 00:00 (a day is 23 or 25 hours when the clocks change).
function midnight(date) {
  const want = Date.parse(`${date}T00:00:00Z`);
  let t = want;
  for (let i = 0; i < 3; i++) {
    const p = parts(t);
    t -= Date.UTC(+p.year, p.month - 1, +p.day, +p.hour, +p.minute, +p.second) - want;
  }
  return t;
}

const span = (s) => s >= 5400 ? `${Math.floor(s / 3600)} h ${Math.round((s % 3600) / 60)} min`
  : s >= 60 ? `${Math.round(s / 60)} min` : `${Math.round(s)} s`;
const length = (s) => s >= 3600
  ? `${Math.floor(s / 3600)}:${String(Math.floor((s % 3600) / 60)).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`
  : `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
const ago = (ms) => { const d = Math.floor((Date.now() - ms) / 864e5); return d <= 0 ? "today" : `${d} d ago`; };

// --- reading -----------------------------------------------------------------------------------
async function get(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${r.status}`);
  return r.json();
}
const api = (path) => get(`/api${path}`);

// Every row of a list; the box counts `offset` in pages, not rows.
async function every(path, key, size, tick) {
  const out = [];
  for (let page = 0; ; page++) {
    const d = await api(`${path}${path.includes("?") ? "&" : "?"}page_size=${size}&offset=${page}`);
    out.push(...d[key]);
    tick(out.length, d.meta?.count);
    if (d[key].length < size || out.length >= (d.meta?.count ?? Infinity)) return out;
  }
}

const theirDay = (date) => api(`/scheduleitems?channel=1&start=${date}T00:00:00&end=${shift(date, 1)}T00:00:00&page_size=1000`)
  .then((d) => d.scheduleItems.filter((i) => !i.deleted));

// What differs between our list and Cablecast's: per airing of ours, and theirs we don't have.
function compare(airings, theirs) {
  const byId = new Map(theirs.map((i) => [i.id, i]));
  const used = new Set();
  const marks = new Map();
  airings.forEach((a, n) => {
    const i = byId.get(a.cablecast);
    if (!i) return void marks.set(n, "not on Cablecast");
    used.add(i.id);
    if (i.show !== a.show.id) marks.set(n, "another show there on Cablecast");
    else if (Date.parse(i.runDateTimeUtc) !== Date.parse(a.at))
      marks.set(n, `at ${clock.format(Date.parse(i.runDateTimeUtc))} on Cablecast`);
  });
  return { marks, extra: theirs.filter((i) => !used.has(i.id)) };
}

// --- the page ----------------------------------------------------------------------------------
function App() {
  const [date, setDate] = useState(() => new URLSearchParams(location.search).get("day") || today());
  const [laid, setLaid] = useState(undefined);      // undefined: coming; null: not laid; else the day
  const [theirs, setTheirs] = useState(undefined);
  const [newer, setNewer] = useState(null);         // Cablecast's copy, changed since we drew it
  const [days, setDays] = useState([]);             // the days laid
  const [cats, setCats] = useState(null);           // category id -> name
  const [reserve, setReserve] = useState(null);     // every show
  const [lately, setLately] = useState(null);       // show id -> last airing (ms)
  const [work, setWork] = useState({});             // what is being asked right now
  const [trouble, setTrouble] = useState({});
  const [chosen, setChosen] = useState(null);       // the gap or airing the reserve is open for
  const [category, setCategory] = useState(null);   // null: all; "": none; else a name
  const [fit, setFit] = useState(null);             // seconds the reserve's shows must fit in
  const [words, setWords] = useState("");
  const [now, setNow] = useState(Date.now());

  // Each request runs under a name in the bar, and leaves when it is done.
  async function ask(key, label, job) {
    setWork((w) => ({ ...w, [key]: { label } }));
    try {
      const out = await job((done, of) => setWork((w) => ({ ...w, [key]: { label, done, of } })));
      setTrouble(({ [key]: _, ...rest }) => rest);
      return out;
    } catch (e) {
      setTrouble((t) => ({ ...t, [key]: label }));
      return undefined;
    } finally {
      setWork(({ [key]: _, ...rest }) => rest);
    }
  }

  // The day: ours first, then Cablecast's to hold up against it.
  useEffect(() => {
    history.replaceState(null, "", date === today() ? location.pathname : `?day=${date}`);
    let gone = false;
    setLaid(undefined); setTheirs(undefined); setNewer(null); setChosen(null); setFit(null);
    ask("laid", "our list", () => fetch(`/schedule/${date}.json`).then((r) => (r.ok ? r.json() : null)))
      .then((d) => !gone && setLaid(d ?? null));
    ask("theirs", "Cablecast's day", () => theirDay(date)).then((d) => !gone && setTheirs(d ?? null));
    const look = setInterval(() => ask("again", "looking again", () => theirDay(date))
      .then((d) => !gone && d && setNewer(d)), LOOK_AGAIN);
    return () => { gone = true; clearInterval(look); };
  }, [date]);

  // What doesn't change with the day: the laid days, the categories, the reserve, what aired lately.
  useEffect(() => {
    ask("days", "days laid", () => get("/schedule/"))
      .then((d) => d && setDays(d.map((f) => f.name.replace(/\.json$/, "")).filter((n) => /^\d{4}-\d\d-\d\d$/.test(n)).sort()));
    ask("cats", "categories", () => api("/categories?page_size=500"))
      .then((d) => d && setCats(Object.fromEntries(d.categories.map((c) => [c.id, c.name.trim()]))));
    ask("reserve", "the reserve", (tick) => every("/shows", "shows", 250, tick)).then((d) => d && setReserve(d));
    const from = shift(today(), -LATELY);
    ask("lately", "aired lately", (tick) => every(`/scheduleitems?channel=1&start=${from}T00:00:00&end=${shift(today(), 1)}T00:00:00`, "scheduleItems", 1000, tick))
      .then((d) => {
        if (!d) return;
        const last = new Map();
        for (const i of d) {
          const t = Date.parse(i.runDateTimeUtc);
          if (!i.deleted && t <= Date.now() && t > (last.get(i.show) ?? 0)) last.set(i.show, t);
        }
        setLately(last);
      });
    const tick = setInterval(() => setNow(Date.now()), 60e3);
    return () => clearInterval(tick);
  }, []);

  // A newer Cablecast copy is only taken when asked for; if it says the same, there is nothing to take.
  const changed = newer && theirs && JSON.stringify(newer.map((i) => [i.id, i.show, i.runDateTimeUtc]))
    !== JSON.stringify(theirs.map((i) => [i.id, i.show, i.runDateTimeUtc]));

  const start = midnight(date);
  const end = midnight(shift(date, 1));
  const y = (ms) => ((ms - start) / 1000) * PX;
  const airings = laid?.airings ?? [];
  const diff = useMemo(() => (laid && theirs ? compare(airings, theirs) : null), [laid, theirs]);
  const shows = useMemo(() => new Map((reserve ?? []).map((s) => [s.id, s])), [reserve]);

  // The day's gaps, our list's: before the first, between each, after the last.
  const gaps = [];
  let edge = start;
  airings.forEach((a, n) => {
    const at = Date.parse(a.at);
    gaps.push({ from: edge, to: at, after: airings[n - 1] });
    edge = Math.max(edge, at + a.seconds * 1000);
  });
  if (laid) gaps.push({ from: edge, to: end, after: airings[airings.length - 1] });
  const holes = gaps.filter((g) => g.to - g.from >= SEAM * 1000);
  const dark = holes.reduce((s, g) => s + (g.to - g.from) / 1000, 0);

  function open(seconds, cat, key) {
    setChosen(key);
    setFit(seconds);
    setCategory(cat ?? "");
  }

  const hours = [];
  for (let t = start; t < end; t += 3600e3) hours.push(t);

  const busy = Object.entries(work);
  const differs = diff ? diff.marks.size + diff.extra.length : 0;

  return html`
    <section class="pane">
      <div class="bar">
        <span class="what">
          <button title="the day before" onClick=${() => setDate(shift(date, -1))}>‹</button>
          ${named(date)}
          <button title="the day after" onClick=${() => setDate(shift(date, 1))}>›</button>
          ${date !== today() && html`<button onClick=${() => setDate(today())}>today</button>`}
        </span>
        <span class="state">
          ${busy.map(([k, w]) => html`<span key=${k} class="busy">${w.label}${w.of ? html` <b>${w.done}/${w.of}</b>` : ""}</span>`)}
          ${Object.entries(trouble).map(([k, label]) => html`<span key=${k} class="off">${label}: no answer</span>`)}
          ${differs > 0 && html`<span class="off">Cablecast differs ${differs}</span>`}
          ${changed && html`<button onClick=${() => { setTheirs(newer); setNewer(null); }}>Cablecast changed ${clock.format(now)}</button>`}
        </span>
      </div>
      <div class="scroll">
        ${laid === null && html`<div class="unlaid">${named(date)} is not laid. ${theirs?.length ? "Cablecast's copy is shown at the right edge." : ""}</div>`}
        <div class="day" style=${{ height: `${y(end)}px` }}>
          ${hours.map((t) => html`<div key=${t} class="hour" style=${{ top: `${y(t)}px` }}>${hourName.format(t)}</div>`)}
          ${laid === undefined && html`<div class="waiting" style=${{ top: 0, height: `${y(end)}px` }}></div>`}
          ${gaps.map((g, n) => {
            const s = (g.to - g.from) / 1000;
            if (s < SEAM && s >= 0) return null;
            if (s < 0) return html`<div key=${`o${n}`} class="mark" title=${`overlaps by ${span(-s)}`} style=${{ top: `${y(g.to)}px`, height: `${Math.max(-s * PX, 3)}px` }}></div>`;
            const h = s * PX;
            const key = `g${g.from}`;
            return html`<div key=${key} class=${`gap${chosen === key ? " chosen" : ""}`} title=${`${span(s)} of the bulletin board, from ${clock.format(g.from)}`}
              style=${{ top: `${y(g.from)}px`, height: `${h}px`, animationDelay: `${n * 6}ms` }}
              onClick=${() => open(s, g.after?.show.category, key)}>
              ${h >= 14 && html`<b>${span(s)}</b> bulletin board`}
            </div>`;
          })}
          ${airings.map((a, n) => {
            const at = Date.parse(a.at);
            const h = Math.max(a.seconds * PX, 2);
            const key = `a${n}`;
            const tip = `${clock.format(at)}  ${a.show.title}\n${a.show.category ?? "no category"} · ${length(a.seconds)}`;
            return html`
              <div key=${key} class=${`airing${chosen === key ? " chosen" : ""}`} title=${tip}
                style=${{ top: `${y(at)}px`, height: `${h}px`, animationDelay: `${n * 6}ms` }}
                onClick=${() => open(a.seconds, a.show.category, key)}>
                ${h >= 13 && html`<span class="at">${clock.format(at)}</span><div class="t">${a.show.on_air ?? a.show.title}</div>`}
                ${h >= 30 && html`<div class="c">${a.show.category ?? "no category"} · ${length(a.seconds)}</div>`}
              </div>
              ${diff?.marks.has(n) && html`<div key=${`m${n}`} class="mark" title=${diff.marks.get(n)} style=${{ top: `${y(at)}px`, height: `${h}px` }}></div>`}`;
          })}
          ${(laid === null ? theirs ?? [] : diff?.extra ?? []).map((i) => {
            const at = Date.parse(i.runDateTimeUtc);
            const s = shows.get(i.show);
            const secs = s?.totalRunTime || 60;
            return html`<div key=${`x${i.id}`} class="airing ghost" title=${`only on Cablecast: ${clock.format(at)} ${s?.title ?? `show ${i.show}`}`}
              style=${{ top: `${y(at)}px`, height: `${Math.max(secs * PX, 3)}px` }}></div>`;
          })}
          ${now >= start && now < end && html`<div class="now" style=${{ top: `${y(now)}px` }}></div>`}
        </div>
      </div>
      <div class="foot">
        ${laid && html`<span><b>${airings.length}</b> airings</span>
          <span><b>${span(dark)}</b> to the bulletin board, in <b>${holes.length}</b> gaps</span>
          <span>laid ${named(laid.laid.slice(0, 10))} ${clock.format(Date.parse(laid.laid))}</span>`}
        ${days.length > 0 && html`<span>laid through <b>${named(days[days.length - 1])}</b></span>`}
      </div>
    </section>
    <${Reserve} ...${{ reserve, cats, lately, category, setCategory, fit, setFit, words, setWords, airings }} />
  `;
}

function Reserve({ reserve, cats, lately, category, setCategory, fit, setFit, words, setWords, airings }) {
  const onDay = useMemo(() => new Set(airings.map((a) => a.show.id)), [airings]);

  // Each category with its hours; a name's size says how much is behind it (four steps, coarse).
  const kinds = useMemo(() => {
    if (!reserve || !cats) return [];
    const hours = new Map();
    for (const s of reserve) {
      const name = cats[s.category] ?? "";
      hours.set(name, (hours.get(name) ?? 0) + (s.totalRunTime || 0) / 3600);
    }
    return [...hours].sort((a, b) => b[1] - a[1]);
  }, [reserve, cats]);
  const step = (h) => (h >= 100 ? 1.5 : h >= 30 ? 1.2 : h >= 5 ? 1 : 0.85);

  const rows = useMemo(() => {
    if (!reserve || !cats) return [];
    const find = words.trim().toLowerCase();
    return reserve
      .filter((s) => category === null || (cats[s.category] ?? "") === category)
      .filter((s) => fit === null || (s.totalRunTime > 0 && s.totalRunTime <= fit))
      .filter((s) => !find || s.title.toLowerCase().includes(find))
      .map((s) => ({ s, last: lately?.get(s.id) ?? 0 }))
      .sort((a, b) => a.last - b.last || a.s.runCount - b.s.runCount);
  }, [reserve, cats, lately, category, fit, words]);

  return html`
    <section class="pane">
      <div class="bar">
        <span class="what">the reserve${category !== null ? html` · ${category || "no category"}` : ""}</span>
        <span class="state">${reserve && html`<span>${rows.length} of ${reserve.length}</span>`}</span>
      </div>
      <div class="cats">
        ${kinds.map(([name, h]) => html`<button key=${name || "-"} class=${`${category === name ? "on" : ""}${name ? "" : " empty"}`}
          style=${{ fontSize: `${step(h)}rem` }} title=${`${Math.round(h)} h`}
          onClick=${() => setCategory(category === name ? null : name)}>${name || "no category"}</button>`)}
      </div>
      <div class="find">
        <input placeholder="find a title" value=${words} onInput=${(e) => setWords(e.target.value)} />
        ${fit !== null && html`<button title="show every length" onClick=${() => setFit(null)}>fits ${span(fit)} ×</button>`}
      </div>
      <div class="scroll">
        ${rows.slice(0, SHOWN).map(({ s, last }) => html`
          <div key=${s.id} class=${`row${onDay.has(s.id) ? " today" : ""}`}>
            <a href=${`https://ch97.fcpublicmedia.org/internetchannel/show/${s.id}`} target="_blank" title=${s.title}>${s.title}</a>
            <span class="n">${length(s.totalRunTime || 0)}</span>
            <span class="n">${last ? ago(last) : ""}</span>
            <span class="n" title="times aired">${s.runCount || ""}</span>
          </div>`)}
        ${rows.length > SHOWN && html`<div class="more">${rows.length - SHOWN} more; a word narrows them</div>`}
      </div>
    </section>`;
}

createRoot(document.getElementById("ch97")).render(html`<${App} />`);
