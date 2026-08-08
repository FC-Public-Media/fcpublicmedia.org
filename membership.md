---
title: Membership
lede: Membership is what unlocks the studios, the gear, and the editing bays.
---

{%- assign m = site.data.membership -%}

Access to local news and local perspectives keeps shrinking. FCPM exists so
that creators, producers, artists, and students in Fort Collins still have
somewhere to make work and somewhere to put it.

{% comment %}
The rules come before the prices, on purpose. The feedback on the current site
is that the pricing is hard to understand — and it is the rules that are hard,
not the amounts. See _data/membership.yml.
{% endcomment %}

## Tiers

<ul class="grid grid-4">
{% for tier in m.tiers %}
  <li class="card">
    <h3>{{ tier.name }}</h3>
    <p class="price">${{ tier.price }}</p>
    {%- comment -%}
      The nonprofit price is shown next to the full one rather than explained
      somewhere further down. Half of the confusion this page is fixing was
      people not knowing the rate existed.

      `times` on an integer and a float returns a float, so 40 would render as
      "20.0" — `round` brings it back to something you would write on a cheque.
    {%- endcomment -%}
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

{%- comment -%}
  The list is every 501(c)(3) the IRS records in Larimer County, which is not
  every nonprofit — a new one, a chapter of a national body, or one operating
  under a fiscal sponsor will not be there. So this can never be a gate, and
  the way through is always visible rather than a fallback you reach by
  failing. See script/sync-nonprofits.py.
{%- endcomment -%}
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
<script type="module" src="{{ '/assets/js/nonprofit.js' | relative_url }}"></script>
