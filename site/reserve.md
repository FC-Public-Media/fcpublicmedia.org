---
title: Reserve
lede: Book the video studio, the podcast studio, or an editing bay — or borrow
  equipment to take out.
---

At any tier of
[FC Public Media Membership]({{ '/membership/' | relative_url }})
you can reserve both the video and podcast studios, edit with the full Adobe
Creative Suite, and check out production equipment.

## Spaces

By email: [{{ site.data.org.email }}](mailto:{{ site.data.org.email }})
By phone: {{ site.data.org.phone }}

<ul class="rows rows-spaces">
{% for space in site.data.facilities %}
  <li>
    <b>{{ space.name }}</b>
    {%- if space.area %}<span>{{ space.area }} sq ft</span>{% endif %}
    {%- if space.summary %}<p>{{ space.summary | strip_newlines | strip }}</p>{% endif %}
  </li>
{% endfor %}
</ul>
{% include transaction.html key="booking" text="Check availability" %}

## Equipment

By email: [{{ site.data.org.equipment_email }}](mailto:{{ site.data.org.equipment_email }})

In your email please include:

1. Your contact information.
2. What equipment you will need or are looking for.
3. The dates of your production.

All equipment requests must be submitted at least one week in advance. All
users must provide a valid credit card for late fees and incidentals. Any User
of FC Public Media equipment must agree to FC Public Media's Equipment Terms
and Conditions.

{% include booqable.html %}

{%- comment -%} Floor plan at the bottom, per the board president's review; `plan_label` maps its room names. {%- endcomment -%}
<figure class="floor-plan">
  <img src="{{ '/assets/img/floor-plan.png' | relative_url }}"
       alt="Floor plan. The video studio is the large room at the centre, with
            the editing bays along its left wall and the podcast studio below,
            off the corner."
       width="381" height="381" loading="lazy" decoding="async">
  <figcaption>
    {%- comment -%} Filtered before the loop so forloop.last is the last labelled room. {%- endcomment -%}
    {%- assign labelled = site.data.facilities | where_exp: "s", "s.plan_label" -%}
    The plan uses the building's labels:
    {% for space in labelled %}<b>{{ space.plan_label | downcase }}</b> is the {{ space.name | downcase }}{% unless forloop.last %}, {% endunless %}{% endfor %}.
  </figcaption>
</figure>
