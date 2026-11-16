---
title: The studio
layout: pass
theme_color: "#121417"
permalink: /studio/
sitemap: false
offline: true
---

{%- comment -%} What a phone can do at FC Public Media: every page in site/studio/, listed from its own front matter
(`studio: {kind, says, reaches}`), so a new one appears here by describing itself. A code is shown to one of our
cameras and sends nothing from the phone; a poster is for our walls. What is yours is /you/. {%- endcomment %}

{%- assign studio = site.pages | where_exp: "p", "p.studio" | sort: "title" -%}

<section class="pass-view" aria-labelledby="studio-title">
  <header class="pass-top">
    <a class="pass-back" href="{{ '/you/' | relative_url }}">Yours</a>
    <h2 id="studio-title">The studio</h2>
  </header>
  <div class="pass-scroll">
    <p class="muted">What your phone can do here. A code is shown to one of our cameras: nothing is sent from your
      phone, and what you made is kept on it. A poster is for our walls.</p>

    <h3>Codes for our cameras</h3>
    <ul class="rows rows-yours">
      {%- for p in studio %}{% if p.studio.kind == "code" %}
      <li><a href="{{ p.url | relative_url }}"><b>{{ p.title }}</b></a><span>{{ p.studio.says }}. For {{ p.studio.reaches }}.</span></li>
      {%- endif %}{% endfor %}
    </ul>

    <h3>Posters for our walls</h3>
    <ul class="rows rows-yours">
      {%- for p in studio %}{% if p.studio.kind == "poster" %}
      <li><a href="{{ p.url | relative_url }}"><b>{{ p.title }}</b></a><span>{{ p.studio.says }}.</span></li>
      {%- endif %}{% endfor %}
    </ul>
  </div>
</section>
