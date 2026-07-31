---
title: Equipment
lede: Members can check out cameras, audio, and lighting for their own projects.
---

## How to check out equipment

FCPM members reserve equipment by emailing
[{{ site.data.org.equipment_email }}](mailto:{{ site.data.org.equipment_email }}).
Include:

- Your contact information
- What equipment you need
- When you need it, and for how long

**All requests must be made at least one week before checkout.** Requests made
with less than one week's notice will not be considered.

Every user of FCPM equipment must agree to the
[Equipment Terms and Conditions](#terms).

Equipment cannot be reserved through the studio booking calendar &mdash; email
is the only way.

## What's available

{% for group in site.data.equipment %}
### {{ group.category }}

<ul class="rows">
{% for item in group.items %}
  <li><b>{{ item.name }}</b> <span>{{ item.notes }}</span></li>
{% endfor %}
</ul>
{% endfor %}

<p class="transaction transaction-todo">
  <b>Inventory is a placeholder.</b>
  <span class="muted">The current site publishes the inventory as a photo
  gallery, so it could not be read as text. Replace
  <code>_data/equipment.yml</code> with the real list &mdash; it will then be
  searchable and indexable, which the gallery never was.</span>
</p>

## Terms {#terms}

TODO &mdash; the current site links out to a separate Equipment Terms and
Conditions document. Decide whether to host it here as a page or keep it as a
downloadable PDF.
