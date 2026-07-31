---
title: Membership
lede: Membership is what unlocks the studios, the gear, and the editing bays.
---

Access to local news and local perspectives keeps shrinking. FCPM exists so
that creators, producers, artists, and students in Fort Collins still have
somewhere to make work and somewhere to put it.

## What every membership includes

{% for benefit in site.data.membership.shared_benefits %}
- {{ benefit }}
{%- endfor %}

## Tiers

<ul class="grid grid-4">
{% for tier in site.data.membership.tiers %}
  <li class="card">
    <h3>{{ tier.name }}</h3>
    <p class="price">${{ tier.price }}</p>
    <p>{{ tier.summary }}</p>
    {% if tier.includes and tier.includes.size > 0 %}
      <ul>
        {% for line in tier.includes %}<li>{{ line }}</li>{% endfor %}
      </ul>
    {% endif %}
  </li>
{% endfor %}
</ul>

<p class="muted"><b>Term:</b> {{ site.data.membership.term }}</p>

## Join

{% include transaction.html key="membership" text="Join or renew" %}

Signing up asks for your contact information and a little about your production
experience, and requires agreeing to the studio and equipment terms and
conditions.

## Questions

Email [{{ site.data.org.email }}](mailto:{{ site.data.org.email }}) or call
{{ site.data.org.phone }}.
