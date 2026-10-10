---
title: Membership
lede: Membership is what unlocks the studios, the gear, and the editing bays.
---

{%- assign m = site.data.membership -%}

Access to local news and local perspectives keeps shrinking. FCPM exists so
that creators, producers, artists, and students in Fort Collins still have
somewhere to make work and somewhere to put it.

{% comment %} The rules come before the prices: the rules are what readers find hard. {% endcomment %}

## Tiers

{%- comment -%} Each tile is a native radio stretched over the card; its value is the checkout SKU. {%- endcomment -%}
<fieldset class="tiers">
<legend class="visually-hidden">Choose a tier</legend>
<ul class="grid grid-4">
{% for tier in m.tiers %}
  {%- assign slug = tier.name | downcase -%}
  <li class="card tier">
    <input type="radio" name="tier" id="tier-{{ slug }}" value="membership:{{ slug }}"
           data-name="{{ tier.name }}" data-price="{{ tier.price }}"
           aria-labelledby="tier-{{ slug }}-name tier-{{ slug }}-price">
    <h3 id="tier-{{ slug }}-name">{{ tier.name }}</h3>
    <p class="price" id="tier-{{ slug }}-price">${{ tier.price }}</p>
    {%- comment -%} `times` by a float yields "20.0"; `round` makes it 20. {%- endcomment -%}
    <p class="muted">Nonprofits ${{ tier.price | times: m.nonprofit.rate | round }}</p>
    <p>{{ tier.summary }}</p>
    {% if tier.includes and tier.includes.size > 0 %}
      <ul>
        {% for line in tier.includes %}<li>{{ line }}</li>{% endfor %}
      </ul>
    {% endif %}
  </li>
{% endfor %}
</ul>
</fieldset>

{%- comment -%} Shown once a tier is chosen; leads to Join until a checkout step exists. {%- endcomment -%}
<p class="tier-next" id="tier-next" aria-live="polite" hidden>
  <a class="btn btn-primary" id="tier-continue" href="#join">Continue with <span id="tier-chosen"></span></a>
</p>

## How it works

<ul class="rows">
  <li><b>{{ m.term.summary }}</b></li>
  {%- for note in m.term.notes %}
  <li>{{ note }}</li>
  {%- endfor %}
  <li><b>{{ m.nonprofit.summary }}</b></li>
</ul>

## What every membership includes

{% for benefit in m.shared_benefits %}
- {{ benefit }}
{%- endfor %}

## If you're with a nonprofit

<p>{{ m.nonprofit.before_you_pay }}</p>

<div id="nonprofit-lookup" hidden>
  <div class="field">
    <label for="nonprofit-search">Find your organization</label>
    <input type="search" id="nonprofit-search" autocomplete="off"
           spellcheck="false" placeholder="Start typing the name">
  </div>

  <p class="muted" id="nonprofit-status" role="status" aria-live="polite"></p>
  <ul class="rows" id="nonprofit-results"></ul>

  <div id="nonprofit-chosen" hidden>
    <p class="transaction transaction-todo">
      <b id="nonprofit-name"></b>
      <span class="muted">EIN <span id="nonprofit-ein"></span> &mdash;
      listed with the IRS as a 501(c)(3). Send us this when you get in touch
      and we'll set your rate before you pay.</span>
    </p>
    <p class="hero-actions">
      <a class="btn btn-primary" id="nonprofit-email" href="#">Email us this</a>
      <button class="btn" id="nonprofit-clear" type="button">Choose a different one</button>
    </p>
  </div>
</div>

{%- comment -%} Never a gate: "not listed" is always visible. See docs/payments.md#nonprofit-rate. {%- endcomment -%}
<p class="muted">
  Not listed? That happens &mdash; new organizations, chapters, and anyone
  working under a fiscal sponsor often aren't.
  <a href="/contact/">Tell us who you are</a> and we'll sort it out.
</p>

## Join

{% include transaction.html key="membership" text="Join or renew" %}

Signing up asks for your contact information and a little about your production
experience, and requires agreeing to the studio and equipment terms and
conditions.

## Questions

Email [{{ site.data.org.email }}](mailto:{{ site.data.org.email }}) or call
{{ site.data.org.phone }}.

<script type="application/json" id="nonprofit-config">
{
  "data": {{ '/assets/nonprofits.json' | relative_url | jsonify }},
  "email": {{ site.data.org.email | jsonify }}
}
</script>
<script type="module" src="{{ '/assets/js/nonprofit.js' | relative_url }}?v={{ site.time | date: '%s' }}"></script>
<script type="module" src="{{ '/assets/js/tiers.js' | relative_url }}?v={{ site.time | date: '%s' }}"></script>
