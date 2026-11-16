---
title: Ask the library
layout: pass
theme_color: "#121417"
sitemap: false
offline: true
permalink: /library/ask/
---

{%- comment -%}
wizard:library+ask, or wizard:library+urgent when ticked: an ask of the library's receptionist, as a code for a
camera at FC Public Media. The lane is the asker's to choose, so nothing behind the camera has to guess. Helm passes
it to the helm that holds the library (machines/helms.yml), which sets it down in the library's inbox; a seat takes
it on its round. Nothing is sent from here. The limit is replies.py's LIBRARY_LIMIT. See docs/library.md.
{%- endcomment %}

<style>
  .pass-body { overflow: auto; }
  .libask { max-width: 36rem; margin: 0 auto; padding: 1.2rem 1rem calc(1.2rem + env(safe-area-inset-bottom));
            display: flex; flex-direction: column; gap: 1rem; color: #eef0f2; }
  .libask h1 { margin: 0; font-size: 1.7rem; line-height: 1.05; }
  .libask .lede { margin: 0; color: #b7bcc3; font-size: .95rem; line-height: 1.35; }
  .libask .field { display: flex; flex-direction: column; gap: .3rem; }
  .libask .field span { font-size: .75rem; letter-spacing: .1em; text-transform: uppercase; color: #8a9099; }
  .libask textarea { font: inherit; font-size: 1.1rem; padding: .55rem .7rem; border-radius: .6rem;
                     border: 1px solid #2c3138; background: #1b1f24; color: inherit; resize: vertical; }
  .libask .urgent { display: inline-flex; gap: .5rem; align-items: center; color: #b7bcc3; font-size: .95rem; }
  .libask .bar { display: flex; align-items: center; gap: .8rem; flex-wrap: wrap; }
  .libask .bar button { font: inherit; font-weight: 650; padding: .7rem 1.2rem; border-radius: 99px; border: none;
                        background: #f5c518; color: #121417; cursor: pointer; }
  .libask .bar button:disabled { opacity: .4; cursor: default; }
  .libask button.quiet { background: none; border: 1px solid #2c3138; color: #b7bcc3; font-weight: 500; }
  .libask #count { font-variant-numeric: tabular-nums; font-size: .8rem; color: #8a9099; }
  .libask #count.over { color: #f5c518; }
  .libask .asked { margin: 0; font-size: 1.05rem; }
  .libask .code { display: flex; flex-direction: column; align-items: center; gap: .5rem; }
  .libask .code canvas { width: min(84vw, 46vh); height: min(84vw, 46vh); background: #fff; image-rendering: pixelated; }
  .libask .code span { font-size: .8rem; color: #8a9099; }
</style>

<div class="libask">
  <h1>Ask the library</h1>
  <p class="lede">Ask the library's receptionist something: what we hold, where it is, who is working on it. It
  becomes a code: show it to the camera at FC Public Media. Ordinary asks are taken a few at a time; an urgent
  one is taken before any other.</p>
  <label class="field"><span>Your ask</span><textarea id="words" rows="4" maxlength="2000"></textarea></label>
  <label class="urgent"><input type="checkbox" id="urgent"> This is urgent</label>
  <div class="bar"><button id="pour" type="button" disabled>Make the code</button><span id="count"></span>
    <button id="blank" type="button" class="quiet">Start over</button></div>
  <section id="outbox" hidden>
    <p class="asked" id="asked"></p>
    <div class="code"><canvas id="code" role="img" aria-label="Your ask of the library, as a code"></canvas><span id="read"></span></div>
  </section>
</div>

<script type="application/json" id="library-ask-config">{"at": {{ site.revision | default: "dev" | jsonify }}, "limit": 2000}</script>
<script type="module" src="{{ '/assets/js/library-ask.js' }}?v={{ site.time | date: '%s' }}"></script>
