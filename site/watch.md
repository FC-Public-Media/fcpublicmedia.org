---
title: Watch
---

{% assign cc = site.data.cablecast %}
{% assign air = site.data.airings %}

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
  {{ channel.name }} <span>{{ channel.detail }}</span>
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

## The archive

{{ cc.total }} programs on record, {{ cc.watchable }} of them watchable online.

{%- comment -%} Airing history from _data/airings.json, joined on the Cablecast show id. {%- endcomment %}
{% if air and air.totals.distinct > 0 %}
<p class="lede">
  In the last year, <b>{{ air.totals.slots }}</b> airings covered
  <b>{{ air.totals.distinct }}</b> programs.
</p>
{% endif %}

### By category

<ul class="rows rows-tight">
{% for category in cc.categories %}
  {%- assign anchor = category.name | slugify -%}
  <a href="#{{ anchor }}">{{ category.name }} (<span>{{ category.count }}</span>)</a>
{% endfor %}
</ul>

<div class="filter" data-filter hidden>
  <label for="archive-filter">Filter</label>
  <input type="search" id="archive-filter" placeholder="Title, producer, or category" autocomplete="off">

  {%- comment -%} Any sort but Category flattens the groups; archive-filter.js restores them. {%- endcomment %}
  <label for="archive-sort">Sort</label>
  <select id="archive-sort">
    <option value="category">Category</option>
    <option value="least">Least aired</option>
    <option value="most">Most aired</option>
    <option value="stale">Longest since aired</option>
    <option value="recent">Aired most recently</option>
    <option value="title">Title A&ndash;Z</option>
  </select>

  <p class="filter-count" data-filter-count></p>
</div>

{% assign by_category = cc.shows | group_by: "category" | sort: "name" %}

{% for group in by_category %}
  {% assign label = group.name %}
  {% if label == "" %}{% assign label = "Uncategorized" %}{% endif %}

  <h3 id="{{ label | slugify }}">{{ label }} <span class="muted">{{ group.size }}</span></h3>

  <ul class="rows rows-archive" data-archive>
    {% for show in group.items %}
      {%- comment -%} Stringify the id: an integer silently fails to index the JSON object. {%- endcomment %}
      {%- assign key = show.id | append: "" -%}
      {%- assign a = air.shows[key] -%}
      <li data-search="{{ show.title | downcase | escape }} {{ show.producer | downcase | escape }} {{ label | downcase }}"
          data-title="{{ show.title | downcase | escape }}"
          data-airings="{{ a.airings | default: 0 }}"
          data-last="{{ a.last | default: '' }}">
        <b><a href="{{ show.watch_url }}">{{ show.title }}</a></b>
        <span>
          {% if show.date and show.date != "" %}{{ show.date }}{% endif %}
          {% if show.producer and show.producer != "" %} &middot; {{ show.producer }}{% endif %}
          {% unless show.watchable %} &middot; cable only{% endunless %}
          {%- if air and air.totals.distinct > 0 -%}
            {%- if a %}
              &middot; <b class="airings">{{ a.airings }} airing{% unless a.airings == 1 %}s{% endunless %}</b>,
              last {{ a.last | date: "%b %Y" }}
            {%- else %}
              &middot; <b class="airings airings-none">not aired this year</b>
            {%- endif -%}
          {%- endif -%}
        </span>
      </li>
    {% endfor %}
  </ul>
{% endfor %}

<script src="{{ '/assets/js/archive-filter.js' }}?v={{ site.time | date: '%s' }}" defer></script>
{% endif %}
