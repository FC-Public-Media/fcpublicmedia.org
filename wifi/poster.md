---
title: Guest Wi-Fi Poster
lede: Print this and put it where guests sit.
permalink: /wifi/poster/
sitemap: false
---

{%- assign wifi = site.data.wifi -%}
{%- assign qr = site.static_files | where: "path", "/assets/img/wifi-qr.svg" | first -%}

{%- comment -%}
  The code is generated locally and is NOT committed, so on the deployed site
  this page shows the instructions and no image. That is the intended state,
  not a broken build — a Wi-Fi QR carries the password in plain decodable form,
  and this repository is public. See the header of _data/wifi.yml.
{%- endcomment -%}

{% if qr %}
<div class="poster">
  <p class="poster-eyebrow">{{ site.data.org.name }}</p>
  <h2 class="poster-title">{{ wifi.poster.title }}</h2>

  <img class="poster-qr"
       src="{{ '/assets/img/wifi-qr.svg' | relative_url }}"
       alt="QR code that joins the {{ wifi.network.ssid }} network"
       width="320" height="320">

  <p class="poster-url">{{ wifi.network.ssid }}</p>
  <p class="poster-note">{{ wifi.poster.note }}</p>
</div>
{% else %}
<p class="transaction transaction-todo">
  <b>The code has not been generated on this machine.</b>
  <span class="muted">That is expected here &mdash; it is never committed, so it
  is absent from the deployed site by design.</span>
</p>
{% endif %}

<div class="no-print">
  <h2>Generating it</h2>

  <p>From a checkout of this repository:</p>

  <pre><code>python3 script/make-wifi-qr.py</code></pre>

  <p>It asks for the password rather than taking it as an argument, so the
  password stays out of your shell history. Then print this page.</p>

  {% unless wifi.network.confirmed %}
  <p class="transaction transaction-todo">
    <b>The network name is still unconfirmed.</b>
    <span class="muted"><code>_data/wifi.yml</code> currently guesses
    <code>{{ wifi.network.ssid }}</code>, and the generator refuses to run until
    somebody who knows sets <code>confirmed: true</code>. A printed code with the
    wrong name scans perfectly and joins nothing, which is the worst way for this
    to fail.</span>
  </p>
  {% endunless %}

  <h2>Why the code is not in the repository</h2>

  <p>A QR code is not encryption &mdash; it is a font. Anyone can point a phone
  at the image and read the password back out. Committing it to a public
  repository, or serving it from this site, publishes the password to everyone
  rather than to the people in the room.</p>

  <p>On the wall that is fine: whoever reads the poster is already here. On the
  open internet it is a different decision, and it is FCPM's to make. See the
  notes at the top of <code>_data/wifi.yml</code> for what changing it would
  take.</p>
</div>
