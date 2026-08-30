---
title: Reserve
lede: Book the video studio, the podcast studio, or an editing bay — or borrow
  equipment to take out.
---

{%- comment -%}
  The plan is named for the building, not for us — CONTROL ROOM, STUDIO,
  OFFICE. `plan_label` in _data/facilities.yml carries that mapping and the
  caption below spends one line on it, because somebody reading the page and
  the plan together will otherwise wonder which room is which.
{%- endcomment -%}
<div class="reserve-intro" markdown="1">

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

[FC Public Media membership]({{ '/membership/' | relative_url }}),
at any tier will allow you to reserve advance time for using
the video/podcast studio, an editing bay with ready-to-go software,
or borrow equipment outside the studio.

## Spaces

By email: [{{ site.data.org.email }}](mailto:{{ site.data.org.email }})
By phone: {{ site.data.org.phone }}

</div>

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

Please help us by knowing in advance:

1. Specific equipment from our list, or a description so that we can help you decide.
2. Dates that you'll need it, a week in advance.
3. A credit card for a temporary charge as collateral.

{% include booqable.html %}
