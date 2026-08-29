---
title: Reserve
lede: Book the video studio, the podcast studio, or an editing bay — or borrow
  equipment to take out.
---

[FC Public Media membership]({{ '/membership/' | relative_url }}),
at any tier will allow you to reserve advance time for using
the video/podcast studio, an editing bay with ready-to-go software,
or borrow equipment outside the studio.

## Spaces

By email: [{{ site.data.org.email }}](mailto:{{ site.data.org.email }})
By phone: {{ site.data.org.phone }}

<ul class="rows">
{% for space in site.data.facilities %}
  <li><b>{{ space.name }}</b>{% if space.slot %} <span>{{ space.slot }}</span>{% endif %}</li>
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
