---
title: Learn
---

{%- comment -%} `photo` in _data/classes.yml; never rendered without alt, as it shows identifiable people. {%- endcomment %}
{%- assign shot = site.data.classes.photo -%}
{%- if shot and shot.src != "" and shot.alt != "" %}
<figure class="page-photo">
  <img src="{{ shot.src }}" alt="{{ shot.alt | escape }}"
       loading="lazy" decoding="async">
  {%- if shot.caption and shot.caption != "" %}
  <figcaption>{{ shot.caption }}</figcaption>
  {%- endif %}
</figure>
{%- endif %}

## Upcoming

{% include transaction.html key="tickets" text="Register for a class"
   todo="Check back soon!" %}

Classes are open to everyone, member or not. Members pay a reduced rate, and some tiers include classes. [Membership]({{ '/join/' }}) pays for itself quickly if you plan to come back.

## Teach with us

<p class="transaction transaction-todo">
  <b>Instructor application.</b>
  <span class="muted">Check back soon!</span>
</p>

We're always looking for instructors. If you know something worth teaching, email
[{{ site.fcpm.email.info }}](mailto:{{ site.fcpm.email.info }}).
