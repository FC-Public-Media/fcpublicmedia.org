---
title: Studio Reservations
lede: Book the video studio, the podcast studio, or an editing bay.
---

You must be an [FCPM member]({{ '/membership/' | relative_url }}) to reserve any
of our facilities.

## Spaces

<ul class="rows">
{% for space in site.data.facilities %}
  <li><b>{{ space.name }}</b> <span>{{ space.slot }}</span></li>
{% endfor %}
</ul>

## Reserve

{% include transaction.html key="booking" text="Check availability" %}

Pick the space and time you want. Please give as much notice as you can &mdash;
sessions need a host from the FCPM board, and if you don't name one we will try
to find a volunteer. We'll contact you if a reservation can't be honored.

## Help while you're here

Beyond the room itself, we can offer:

- Production assistance
- Technical training on lighting, audio, and camera
- Video critique
- Advice on what gear to buy

## Questions

Reservations: {{ site.data.org.phone }}
Lighting and equipment: [{{ site.data.org.equipment_email }}](mailto:{{ site.data.org.equipment_email }})
