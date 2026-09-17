---
title: Check-In Poster
lede: Print this and put it by the door.
permalink: /check-in/poster/
sitemap: false
---

{%- assign ci = site.data.checkin -%}

<p class="no-print muted">
  Print this page. The code below points at
  <code>{{ ci.url }}</code>. If that URL ever changes, regenerate the code with
  <code>python3 script/make-qr.py</code> — a printed code with the wrong URL is
  worse than no code at all.
</p>

<div class="poster">
  <p class="poster-eyebrow">{{ site.data.org.name }}</p>
  <h2 class="poster-title">Checking in?</h2>

  <img class="poster-qr"
       src="{{ '/assets/img/check-in-qr.svg' | relative_url }}"
       alt="QR code linking to the check-in page"
       width="320" height="320">

  <p class="poster-url">{{ ci.url | remove: 'https://' }}</p>
  <p class="poster-note">
    Scan with your camera, then tap once. Your visits are kept on your own
    phone &mdash; we don't create an account for you.
  </p>
</div>

<p class="no-print muted">
  The paper log stays by the door. This does not replace it &mdash; see the
  note in <code>_data/checkin.yml</code> for why.
</p>
