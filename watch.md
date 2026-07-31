---
title: Watch
lede: Local programs, live and on demand.
---

## Live

<div class="embed">
  {%- comment -%}
    The Cablecast player is an embed and moves over as-is. Confirm the exact
    iframe URL with Cablecast before launch; the link below always works.
  {%- endcomment -%}
  <p><a class="btn btn-primary" href="{{ site.data.watch.live_url }}">Open the live stream</a></p>
</div>

## Where to find us

<ul class="rows">
{% for channel in site.data.watch.carriage %}
  <li><b>{{ channel.name }}</b> <span>{{ channel.detail }}</span></li>
{% endfor %}
</ul>

## On demand

The full library is browsable on our
[{{ site.data.watch.live_provider }} channel]({{ site.data.watch.live_url }}),
organized by category:

{% for category in site.data.watch.categories %}
- {{ category }}
{%- endfor %}

## Schedule

TODO &mdash; the current site publishes a programming schedule through
{{ site.data.watch.live_provider }}. Decide whether to link to it or embed it.
