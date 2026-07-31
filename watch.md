---
title: Watch
lede: Live on cable and online, plus every program we have on record.
---

{% assign cc = site.data.cablecast %}

## Live right now

<div class="embed embed-live">
  <iframe
    src="https://reflect-fcpublicmedia.cablecast.tv/internetchannel/watch-live-embed?streamId=1"
    title="Fort Collins Public Media live stream"
    loading="lazy"
    allow="fullscreen"
    allowfullscreen></iframe>
</div>

<div class="onair-bar onair-inline" data-onair hidden></div>

## Where to find the channel

<ul class="rows">
{% for channel in site.data.watch.carriage %}
  <li><b>{{ channel.name }}</b> <span>{{ channel.detail }}</span></li>
{% endfor %}
</ul>

{% if cc %}
## Recently on the air

<ul class="grid grid-show">
{% for show in cc.recent limit: 12 %}
  {% include show-card.html show=show %}
{% endfor %}
</ul>

## Made in Fort Collins

{{ cc.local_total }} of the {{ cc.total }} programs on record were produced
locally.

<ul class="grid grid-show">
{% for show in cc.recent_local limit: 12 %}
  {% include show-card.html show=show %}
{% endfor %}
</ul>

<p><a class="btn btn-primary" href="{{ '/watch/archive/' | relative_url }}">Browse the full archive</a></p>

## By category

<ul class="rows rows-tight">
{% for category in cc.categories %}
  <li><b><a href="{{ '/watch/archive/#' | append: category.name | slugify | relative_url }}">{{ category.name }}</a></b> <span>{{ category.count }}</span></li>
{% endfor %}
</ul>
{% endif %}
