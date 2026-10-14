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

{%- comment -%} Podcasts sit here, above the archive, not in the header. {%- endcomment -%}
## Podcasts

<p class="muted">Made in our studios, by people from around Larimer County.</p>

<ul class="grid grid-show">
{% assign podcasts = site.podcasts | sort: "title" %}
{% for show in podcasts %}
  <li class="card">
    <h3><a href="{{ show.url | relative_url }}">{{ show.title }}</a></h3>
    {% if show.explicit %}<p><span class="tag tag-warn">Explicit language</span></p>{% endif %}
    {% if show.lede and show.lede != "" %}<p class="show-meta muted">{{ show.lede }}</p>{% endif %}
  </li>
{% endfor %}
</ul>

## The archive

<p><a class="btn btn-primary" href="{{ '/watch/archive/' | relative_url }}">Browse the full archive</a></p>

{% comment %} Slugify the name alone, not after append. Untrimmed and above the heading, or kramdown joins lines. {% endcomment %}

## By category

<ul class="rows rows-tight">
{% for category in cc.categories %}
  {%- assign anchor = category.name | slugify -%}
  <li><b><a href="{{ '/watch/archive/' | relative_url }}#{{ anchor }}">{{ category.name }}</a></b> <span>{{ category.count }}</span></li>
{% endfor %}
</ul>
{% endif %}
