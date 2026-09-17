---
title: Program Archive
lede: Every program in the Cablecast catalog, grouped by category.
permalink: /watch/archive/
---

{% assign cc = site.data.cablecast %}
{% assign air = site.data.airings %}

{{ cc.total }} programs on record, {{ cc.watchable }} of them watchable online.
{{ cc.local_total }} were produced locally.

{%- comment -%}
  Airing history, joined from _data/airings.json on the Cablecast show id.
  Cablecast already records every run, so none of this is tracked here — it is
  read from the system that does the broadcasting.

  The interesting number is the one nobody asks for: how much of the
  catalogue never runs.
{%- endcomment -%}
{% if air and air.totals.distinct > 0 %}
<p class="lede">
  In the last year, <b>{{ air.totals.slots }}</b> airings covered
  <b>{{ air.totals.distinct }}</b> programs.
</p>
<p class="muted">
  Sort by <b>Least aired</b> below to see what has been sitting unwatched.
  Airing counts come from the station&rsquo;s own broadcast log and exclude
  filler.
</p>
{% endif %}

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

  {%- comment -%}
    Sorting by anything other than category has to flatten the groups — a
    program that has not aired in two years is interesting regardless of which
    heading it happens to live under. archive-filter.js moves the rows into
    one list and puts them back when "Category" is chosen again.
  {%- endcomment -%}
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

  <h2 id="{{ label | slugify }}">{{ label }} <span class="muted">{{ group.size }}</span></h2>

  <ul class="rows rows-archive" data-archive>
    {% for show in group.items %}
      {%- comment -%}
        The id has to be stringified before it will index the JSON object —
        Liquid will not match an integer against a string key, and the lookup
        silently returns nothing rather than complaining.
      {%- endcomment -%}
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

<script src="{{ '/assets/js/archive-filter.js' | relative_url }}?v={{ site.time | date: '%s' }}" defer></script>
