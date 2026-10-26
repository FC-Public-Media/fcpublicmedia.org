---
title: Membership
---

{%- assign m = site.data.membership -%}

Access to local news and local perspectives keeps shrinking. FCPM exists so
that creators, producers, artists, and students in Fort Collins still have
somewhere to make work and somewhere to put it.

{% comment %} The rules come before the prices: the rules are what readers find hard. {% endcomment %}

## Tiers

{%- comment -%} Each tile is a native radio stretched over the card; its value is the checkout SKU. {%- endcomment %}

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
    {%- comment -%} `times` by a float yields "20.0"; `round` makes it 20. {%- endcomment %}
    <p class="muted">Nonprofits ${{ tier.price | times: m.nonprofit.rate | round }}</p>
  </li>
{% endfor %}
</ul>
</fieldset>

Supporter is for backing the organization without needing studio access. The other three open
the building; what separates them is still being settled by the board.

{%- comment -%} Shown once a tier is chosen; leads to Join until a checkout step exists. {%- endcomment %}
<p class="tier-next" id="tier-next" aria-live="polite" hidden>
  <a class="btn btn-primary" id="tier-continue" href="#join">Continue with <span id="tier-chosen"></span></a>
</p>

## How it works

<ul class="rows">
  <li><b>A full year from the day you join.</b></li>
  <li>Not the calendar year. Join in November and you are covered until the following November.</li>
  <li>No half-year price any more, because there is no half year to buy &mdash; everyone gets
      twelve months.</li>
  <li>No monthly option.</li>
  <li><b>Nonprofits pay half, on every tier.</b></li>
</ul>

## What every membership includes

- Studio space
- Equipment for video, photography, audio, and podcasting
- Editing software and editing bays
- Training classes
- Community support and connection

## If you're with a nonprofit

<p>
  Tell us which organization you're with before you pay, and we'll set the rate. You should never
  have to buy the wrong membership and wait for a refund.
</p>

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

{%- comment -%} Never a gate: "not listed" is always visible. See docs/payments.md#nonprofit-rate. {%- endcomment %}
<p class="muted">
  Not listed? That happens &mdash; new organizations, chapters, and anyone
  working under a fiscal sponsor often aren't.
  <a href="mailto:{{ site.fcpm.email.info }}">Tell us who you are</a> and we'll sort it out.
</p>

## Join

{% include transaction.html key="membership" text="Join or renew"
   todo="Email or call and we'll set you up by hand, including the nonprofit rate." %}

Signing up asks for your contact information and a little about your production
experience, and requires agreeing to the studio and equipment terms and
conditions.

## Questions

Email [{{ site.fcpm.email.info }}](mailto:{{ site.fcpm.email.info }}) or call
{{ site.fcpm.phone }}.

<script type="application/json" id="nonprofit-config">
{
  "data": {{ '/assets/nonprofits.json' | jsonify }},
  "email": {{ site.fcpm.email | jsonify }}
}
</script>
<script type="module" src="{{ '/assets/js/nonprofit.js' }}?v={{ site.time | date: '%s' }}"></script>
<script type="module" src="{{ '/assets/js/tiers.js' }}?v={{ site.time | date: '%s' }}"></script>
