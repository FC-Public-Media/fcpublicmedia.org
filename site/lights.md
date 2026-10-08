---
title: Lights
layout: pass
theme_color: "#ffffff"
sitemap: false
---

{%- comment -%}
  The lights reply: someone in the studio off host hours holds this up to the
  kiosk's camera to say "I'm here, keep the screens awake until X". The kiosk
  can't be reached from the LAN, so the code lives here, on the public site,
  and carries nothing personal: on or off, until when, when it was made, and a
  nonce the kiosk accepts once. A new nonce on every render or tap. Formed and
  drawn by assets/js/lights.js; the kiosk's rules are there too.
{%- endcomment -%}

<style>
  .lights { position: fixed; inset: 0; display: flex; flex-direction: column; background: #fff; color: #111;
            font: 15px/1.3 system-ui, -apple-system, "Segoe UI", sans-serif; }
  .lights-code { flex: 1; min-height: 0; display: grid; place-items: center; }
  .lights-code canvas { image-rendering: pixelated; image-rendering: crisp-edges; display: block; cursor: pointer;
                        touch-action: manipulation; }
  .lights-bar { flex: none; display: flex; align-items: center; justify-content: center; gap: 14px; flex-wrap: wrap;
                padding: 12px 14px calc(12px + env(safe-area-inset-bottom)); background: #111; color: #eee; }
  .lights-bar label { display: inline-flex; align-items: center; }
  .lights-bar input[type=radio] { position: absolute; opacity: 0; pointer-events: none; }
  .lights-bar .seg { padding: 8px 16px; border: 1px solid #555; font-size: 22px; line-height: 1; cursor: pointer; }
  .lights-bar label:first-of-type .seg { border-radius: 8px 0 0 8px; }
  .lights-bar label:nth-of-type(2) .seg { border-radius: 0 8px 8px 0; border-left: none; }
  .lights-bar input:checked + .seg { background: #eee; color: #111; }
  .lights-bar input:focus-visible + .seg { outline: 2px solid #6af; outline-offset: 2px; }
  .lights-bar input[type=time] { font: inherit; font-size: 20px; padding: 6px 8px; border-radius: 8px;
                                  border: 1px solid #555; background: #222; color: #eee; }
  .lights-bar input[type=time]:disabled { opacity: .35; }
  .lights-bar [data-read] { color: #888; font-size: 12px; font-variant-numeric: tabular-nums; }
</style>

<div class="lights" data-lights-reply>
  <div class="lights-code"><canvas role="img" aria-label="Lights reply code for the kiosk's camera; tap for a fresh one"></canvas></div>
  <form class="lights-bar" onsubmit="return false">
    <label title="on: keep the screens awake"><input type="radio" name="lights" value="on" checked><span class="seg" aria-label="on">☀</span></label>
    <label title="off: let them sleep"><input type="radio" name="lights" value="off"><span class="seg" aria-label="off">☾</span></label>
    <input type="time" name="until" value="22:00" aria-label="until" title="until (today, or tomorrow if it's past)">
    <span data-read></span>
  </form>
</div>

<script type="module" src="{{ '/assets/js/lights.js' | relative_url }}?v={{ site.time | date: '%s' }}"></script>
