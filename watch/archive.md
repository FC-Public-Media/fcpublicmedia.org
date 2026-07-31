---
title: Program Archive
lede: Every program in the Cablecast catalog, grouped by category.
permalink: /watch/archive/
---

{% assign cc = site.data.cablecast %}

{{ cc.total }} programs on record, {{ cc.watchable }} of them watchable online.
{{ cc.local_total }} were produced locally.

{% if cc.untitled_omitted and cc.untitled_omitted > 0 %}
<p class="transaction transaction-todo">
  <b>{{ cc.untitled_omitted }} catalog records are not listed.</b>
  <span class="muted">They have no title in Cablecast and no video attached,
  so there is nothing to show and nothing to watch. Give them titles in
  Cablecast and they appear here at the next weekly sync.</span>
</p>
{% endif %}

<p class="muted">
  This page is generated from the station's Cablecast catalog by
  <code>script/sync-cablecast.py</code>. It is plain HTML, so it can be
  searched with your browser's find command and indexed by search engines &mdash;
  neither of which was true when this history lived only inside Cablecast.
</p>

<div class="filter" data-filter hidden>
  <label for="archive-filter">Filter</label>
  <input type="search" id="archive-filter" placeholder="Title, producer, or category" autocomplete="off">
  <p class="filter-count" data-filter-count></p>
</div>

{% assign by_category = cc.shows | group_by: "category" | sort: "name" %}

{% for group in by_category %}
  {% assign label = group.name %}
  {% if label == "" %}{% assign label = "Uncategorized" %}{% endif %}

  <h2 id="{{ label | slugify }}">{{ label }} <span class="muted">{{ group.size }}</span></h2>

  <ul class="rows rows-archive" data-archive>
    {% for show in group.items %}
      <li data-search="{{ show.title | downcase | escape }} {{ show.producer | downcase | escape }} {{ label | downcase }}">
        <b><a href="{{ show.watch_url }}">{{ show.title }}</a></b>
        <span>
          {% if show.date and show.date != "" %}{{ show.date }}{% endif %}
          {% if show.producer and show.producer != "" %} &middot; {{ show.producer }}{% endif %}
          {% unless show.watchable %} &middot; cable only{% endunless %}
        </span>
      </li>
    {% endfor %}
  </ul>
{% endfor %}

<script src="{{ '/assets/js/archive-filter.js' | relative_url }}" defer></script>
