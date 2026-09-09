---
title: Learn
lede: Short, hands-on training at the studio. Open to the public.
---

{%- comment -%}
  The picture Bryan asked for. Above "Upcoming" rather than below it, because
  the thing it has to answer is "what is this like" — which is a question
  somebody asks before they read a schedule, not after.

  Set it in _data/classes.yml under `photo`. A src with no alt is not rendered
  at all: these are photographs of identifiable people, and shipping one with
  an empty alt is the failure this guard exists to make impossible rather than
  merely discouraged.
{%- endcomment -%}
{%- assign shot = site.data.classes.photo -%}
{%- if shot and shot.src != "" and shot.alt != "" %}
<figure class="page-photo">
  <img src="{{ shot.src | relative_url }}" alt="{{ shot.alt | escape }}"
       loading="lazy" decoding="async">
  {%- if shot.caption and shot.caption != "" %}
  <figcaption>{{ shot.caption }}</figcaption>
  {%- endif %}
</figure>
{%- endif %}

## Upcoming

<p class="transaction transaction-todo">
  <b>Class listings need a home.</b>
  <span class="muted">This is the only genuinely scheduled content on the site.
  Once a ticketing provider is chosen it becomes either a
  <code>_data/classes.yml</code> loop rendered here, or an embed from that
  provider. Do not hand-maintain listings in this file &mdash; they will go
  stale.</span>
</p>

{% include transaction.html key="tickets" text="Register for a class" %}

## Past classes

Recent sessions have included Podcasting 101, Social Media Marketing 101,
Adobe Lightroom, Beginner Photoshop, Studio Light Board Training, and Lighting
Basics for Beginners.

## Teach with us

We're always looking for instructors. See [Teach a Class]({{ '/teach/' | relative_url }}).
