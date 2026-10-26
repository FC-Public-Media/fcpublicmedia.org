---
title: Learn
lede: Short, hands-on training at the studio. Open to the public.
---

{%- comment -%} `photo` in _data/classes.yml; never rendered without alt, as it shows identifiable people. {%- endcomment -%}
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

Classes are open to everyone, member or not. Members pay a reduced rate, and some tiers include
classes &mdash; [membership]({{ '/membership/' | relative_url }}) pays for itself quickly if you
plan to come back. If a class is full we'll say so and put you first in line for the next one.
Turning up on the day without registering is usually fine too; registering just means we know to
expect you.

## Past classes

Recent sessions have included Podcasting 101, Social Media Marketing 101,
Adobe Lightroom, Beginner Photoshop, Studio Light Board Training, and Lighting
Basics for Beginners.

## Teach with us

We're always looking for instructors. If you know something worth teaching &mdash; production,
editing, audio, distribution, the business side &mdash; we want to hear about it. Email
[{{ site.data.org.email }}](mailto:{{ site.data.org.email }}).

<p class="transaction transaction-todo">
  <b>Instructor application.</b>
  <span class="muted">The current application asks a specific set of questions; they have not been
  copied over. Same forms decision as the contact page.</span>
</p>
