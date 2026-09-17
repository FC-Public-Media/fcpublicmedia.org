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

{%- comment -%}
  THE FLOOR PLAN LIVES AT THE BOTTOM, ON PURPOSE.

  It opened this page until September 2026. The board president's review moved
  it: he likes having it here, but "I don't think it needs to be at the top. I
  think a video/slideshow of the space will be a better selling point. The
  floor plan might be better at the bottom as extra information."

  He is right about what it is. A plan answers "which room is which" — a
  question you have after you are interested, not before. The slot it vacated
  is where photography of the spaces goes when it exists; until then the page
  opens on the offer rather than on a diagram.

  The wrapper that used to hold this went with it. `.reserve-intro` was a
  two-column grid whose only job was standing the plan beside the
  introduction; with the plan down here it would have reserved a 17rem column
  for nothing and squeezed the text into what was left.

  The plan is named for the building, not for us — CONTROL ROOM, STUDIO,
  OFFICE. `plan_label` in _data/facilities.yml carries that mapping and the
  caption spends one line on it, because somebody reading the page and the
  plan together will otherwise wonder which room is which.
{%- endcomment -%}
<figure class="floor-plan">
  <img src="{{ '/assets/img/floor-plan.png' | relative_url }}"
       alt="Floor plan. The video studio is the large room at the centre, with
            the editing bays along its left wall and the podcast studio below,
            off the corner."
       width="381" height="381" loading="lazy" decoding="async">
  <figcaption>
    {%- comment -%}
      Filtered before the loop, not tested inside it. Testing inside meant
      forloop.last was the last facility rather than the last labelled one, so
      the trailing comma landed on a room that had one and the sentence ended
      ", .".
    {%- endcomment -%}
    {%- assign labelled = site.data.facilities | where_exp: "s", "s.plan_label" -%}
    The plan uses the building's labels:
    {% for space in labelled %}<b>{{ space.plan_label | downcase }}</b> is the {{ space.name | downcase }}{% unless forloop.last %}, {% endunless %}{% endfor %}.
  </figcaption>
</figure>
