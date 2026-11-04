---
title: Ask the model
layout: pass
theme_color: "#121417"
sitemap: false
offline: true
permalink: /ask/
---

{%- comment -%}
wizard:model+ask on the public site: the same page as the door's /ask/ on our LAN (assets/js/ask.js), here on a
secure page, so a phone signs its bottle and may open its camera to catch the answer from the loop. The
question becomes a code for the camera at FC Public Media; nothing is sent from here. The limit is the shape's
(machines/production/shapes/ask.yml). See machines/digitization/PROFILE.md, Questions for the model.
{%- endcomment %}

<style>
  .pass-body { overflow: auto; }
  .ask { max-width: 36rem; margin: 0 auto; padding: 1.2rem 1rem calc(1.2rem + env(safe-area-inset-bottom));
         display: flex; flex-direction: column; gap: 1rem; color: #eef0f2; }
  .ask h1 { margin: 0; font-size: 1.7rem; line-height: 1.05; }
  .ask .lede { margin: 0; color: #b7bcc3; font-size: .95rem; line-height: 1.35; }
  .ask .field { display: flex; flex-direction: column; gap: .3rem; }
  .ask .field span, .ask h2 { font-size: .75rem; letter-spacing: .1em; text-transform: uppercase; color: #8a9099; }
  .ask textarea { font: inherit; font-size: 1.1rem; padding: .55rem .7rem; border-radius: .6rem; border: 1px solid #2c3138;
                  background: #1b1f24; color: inherit; resize: vertical; }
  .ask details summary { color: #b7bcc3; font-size: .9rem; cursor: pointer; }
  .ask .bar { display: flex; align-items: center; gap: .8rem; flex-wrap: wrap; }
  .ask .bar button { font: inherit; font-weight: 650; padding: .7rem 1.2rem; border-radius: 99px; border: none;
                     background: #f5c518; color: #121417; cursor: pointer; }
  .ask .bar button:disabled { opacity: .4; cursor: default; }
  .ask button.quiet { background: none; border: 1px solid #2c3138; color: #b7bcc3; font-weight: 500; }
  .ask #count { font-variant-numeric: tabular-nums; font-size: .8rem; color: #8a9099; }
  .ask #count.over { color: #f5c518; }
  .ask .asked { margin: 0; font-size: 1.05rem; }
  .ask .code { display: flex; flex-direction: column; align-items: center; gap: .5rem; }
  .ask .code canvas { width: min(84vw, 46vh); height: min(84vw, 46vh); background: #fff; image-rendering: pixelated; }
  .ask .code span, .ask #caught, .ask #said { font-size: .8rem; color: #8a9099; }
  .ask #eye { width: 100%; border-radius: .6rem; background: #000; }
  .ask .notebook .acts { display:flex; flex-wrap:wrap; gap:.5rem; align-items:center; margin-top:.45rem; }
  .ask .notebook .acts button { font:inherit; font-size:.85rem; padding:.35rem .8rem; border-radius:99px; cursor:pointer; }
  .ask .notebook li.showing { border-top-color:#f5c518; }
  .ask .catching { list-style:none; margin:0; padding:0; display:flex; flex-direction:column; gap:.35rem; }
  .ask .catching li { position:relative; display:flex; justify-content:space-between; gap:1rem; padding:.45rem .7rem; overflow:hidden; }
  .ask .catching .bar { position:absolute; left:0; bottom:0; height:3px; width:calc(var(--p) * 100%); background:#f5c518; }
  .ask .catching .how { font-variant-numeric:tabular-nums; }
  .ask .catching li.mine { font-weight:700; } .catching li.passing { opacity:.55; }
  .ask .catching li { background: #1b1f24; }
  .ask .notebook ol { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: .8rem; }
  .ask .notebook li { border-top: 1px solid #2c3138; padding-top: .6rem; }
  .ask .notebook .q { margin: 0; font-weight: 650; }
  .ask .notebook .a { margin: .3rem 0; color: #b7bcc3; }
  .ask .notebook .meta { font-size: .75rem; color: #8a9099; display: block; }
  .ask .notebook label { display: inline-flex; gap: .4rem; align-items: center; font-size: .85rem; margin-top: .3rem; }
</style>

<div class="ask">
  <h1>Ask the model</h1>
  <p class="lede">Write one question. It becomes a code: show it to the camera at FC Public Media, and its answer
  comes back in the loop on the big screen, under this question's own number. Tick an earlier answer to quote it in.</p>
  <label class="field"><span>Your question</span><textarea id="box" rows="4" maxlength="1500"></textarea></label>
  <details><summary>Your own instructions (if you like)</summary>
    <label class="field"><textarea id="inst" rows="2" maxlength="400" placeholder="Answer like a librarian."></textarea></label></details>
  <div class="bar"><button id="pour" type="button" disabled>Make the code</button><span id="count"></span>
    <button id="blank" type="button" class="quiet">Start over</button></div>
  <section id="outbox" hidden>
    <p class="asked" id="asked"></p>
    <div class="code"><canvas id="code" role="img" aria-label="Your question, as a code"></canvas><span id="read"></span></div>
    <div class="bar"><button id="drop" type="button" hidden>Set it down here</button><span id="said"></span></div>
  </section>
  <section id="loop-catch" hidden><h2>From the loop</h2>
    <div class="bar"><button id="catch" type="button">Catch from the loop</button><span id="caught"></span></div>
    <ol id="catching" class="catching"></ol>
    <video id="eye" hidden muted playsinline></video>
  </section>
  <section class="notebook carried"><h2>Carried for others</h2><p id="carried-empty" class="lede">Nothing yet. Everyone's answers in the loop are caught,
    so you can carry them to the people they answer.</p><ol id="carried"></ol>
    <div class="code" id="relay" hidden><canvas id="relay-code" role=img aria-label="A carried answer, as a code"></canvas><span id="relay-read"></span>
      <div class="bar"><button id="relay-stop" type="button" class="quiet">Done showing it</button></div></div></section>
  <section class="notebook"><h2>Kept on this phone</h2><p id="notebook-empty" class="lede">Nothing yet.</p>
    <ol id="notebook"></ol><button id="forget" type="button" class="quiet">Forget them all</button></section>
</div>

<script type="application/json" id="ask-config">{"at": {{ site.revision | default: "dev" | jsonify }}, "limit": 1500, "lan": false, "urgent": 600}</script>
<script type="module" src="{{ '/assets/js/ask.js' }}?v={{ site.time | date: '%s' }}"></script>
