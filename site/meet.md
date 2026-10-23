---
title: Meet
---

{%- assign com = site.data.community -%}
{%- assign now = site.time | date: "%s" -%}

{%- comment -%}
  Classes, board meetings and community events merged into one list: rows are "%%"-delimited
  strings keyed by epoch seconds (DST-safe), sorted, split back. Past events are dropped here.
{%- endcomment -%}

{%- assign rows = "" | split: "" -%}

{%- for s in site.data.classes.sessions -%}
  {%- assign at = s.starts | date: "%s" -%}
  {%- if at >= now -%}
    {%- capture row -%}
      {{ at }}%%Class%%{{ s.title }}%%{{ s.starts }}%%{{ s.room }}%%/classes/%%{{ s.note }}
    {%- endcapture -%}
    {%- assign rows = rows | push: row -%}
  {%- endif -%}
{%- endfor -%}

{%- for meeting in site.data.governance.meetings.upcoming -%}
  {%- assign at = meeting.starts | date: "%s" -%}
  {%- if at >= now -%}
    {%- capture row -%}
      {{ at }}%%Board meeting%%Board meeting%%{{ meeting.starts }}%%%%#the-board%%{{ meeting.note }}
    {%- endcapture -%}
    {%- assign rows = rows | push: row -%}
  {%- endif -%}
{%- endfor -%}

{%- for e in com.events -%}
  {%- assign at = e.starts | date: "%s" -%}
  {%- if at >= now -%}
    {%- capture row -%}
      {{ at }}%%{{ e.kind | default: "Event" }}%%{{ e.title }}%%{{ e.starts }}%%{{ e.where }}%%{{ e.url }}%%{{ e.note }}
    {%- endcapture -%}
    {%- assign rows = rows | push: row -%}
  {%- endif -%}
{%- endfor -%}

{%- assign upcoming = rows | sort -%}

## What's on

{% if upcoming.size > 0 %}

<ul class="rows rows-events">
{% for row in upcoming %}
  {%- assign f = row | strip | split: "%%" -%}
  <li>
    <b>
      <time datetime="{{ f[3] }}">{{ f[3] | date: "%a %-d %b" }}</time>
      <span class="muted">{{ f[3] | date: "%-l:%M%P" }}</span>
    </b>
    <span>
      {% if f[5] and f[5] != "" %}
        <a href="{{ f[5] }}">{{ f[2] }}</a>
      {% else %}
        {{ f[2] }}
      {% endif %}
      <span class="muted">
        {{ f[1] }}{% if f[4] and f[4] != "" %} &middot; {{ f[4] }}{% endif %}
      </span>
      {% if f[6] and f[6] != "" %}<span class="muted">{{ f[6] }}</span>{% endif %}
    </span>
  </li>
{% endfor %}
</ul>

{% else %}

<p class="lede">Nothing on the calendar right now.</p>

<p>
  That happens &mdash; we're small, and things go up when they're ready. The
  studio is still open by appointment, and the
  <a href="/classes/">classes page</a> is the first place a new session
  appears.
</p>

{% endif %}

<p class="muted">
  Classes, board meetings, and everything else, in one list. Sessions also
  show on the <a href="/classes/">classes page</a>; board meetings are
  <a href="#the-board">further down</a>, and anyone can come to one.
</p>

{% comment %} ------------------------------------------------ where we talk {% endcomment %}

## {{ com.heading }}

<p class="lede">{{ com.blurb | strip_newlines | strip }}</p>

{%- comment -%} Channels with no url are skipped; `primary` is the one to try first. {%- endcomment -%}

{%- assign live = com.channels | where_exp: "c", "c.url != ''" -%}
{%- assign primary = live | where: "primary", true | first -%}

{% if live.size > 0 %}

{% if primary %}
  <p>
    The main place is <a href="{{ primary.url }}">{{ primary.name }}</a> &mdash;
    {{ primary.detail | downcase }}
  </p>
{% endif %}

<ul class="rows rows-connect">
{% for channel in live %}
  <li>
    <b><a href="{{ channel.url }}">{{ channel.name }}</a></b>
    <span>{{ channel.detail }}</span>
  </li>
{% endfor %}
</ul>

{% else %}

<p class="transaction transaction-todo">
  <b>No channels are linked yet.</b>
  <span class="muted">Every entry in <code>_data/community.yml</code> is
  missing a URL, so this section is empty. The Slack invite is the one to
  add first &mdash; use a link that doesn't expire.</span>
</p>

{% endif %}

<p class="muted">
  Somewhere else you think people should be? <a href="/contact/">Tell us</a>.
  This list is short on purpose &mdash; a channel nobody reads is worse than
  no channel.
</p>

{% comment %} ------------------------------------------------ made by members {% endcomment %}

{%- comment -%} From _data/member_programs.json (sync-feeds.py). Strings are members': keep `| escape`. {%- endcomment -%}

{%- assign made = site.data.member_programs -%}

{%- comment -%}
  A future pubDate is a member's scheduled drop: listed under "Coming up", not "Made by members".
  `plus: 0` makes integers; `now` above is a string, and mixing the two raises.
{%- endcomment -%}
{%- assign nowsec = site.time | date: "%s" | plus: 0 -%}
{%- assign coming = "" | split: "" -%}
{%- assign published = "" | split: "" -%}

{%- for item in made.items -%}
  {%- if item.published -%}
    {%- assign at = item.published | date: "%s" | plus: 0 -%}
    {%- if at > nowsec -%}
      {%- assign coming = coming | push: item -%}
    {%- else -%}
      {%- assign published = published | push: item -%}
    {%- endif -%}
  {%- else -%}
    {%- comment -%} Undated counts as published, not forthcoming. {%- endcomment -%}
    {%- assign published = published | push: item -%}
  {%- endif -%}
{%- endfor -%}

{% if coming.size > 0 %}

## Coming up from members

<p class="lede">
  Announced by members on their own channels, not yet out.
</p>

{%- comment -%} No artifact link: the feed's pointer to the master file is not for publishing. {%- endcomment -%}
<ul class="feed">
{% for item in coming %}
  <li>
    {% if item.image and item.image != "" %}
      <div class="feed-thumb">
        <img src="{{ item.image | escape }}" alt="" loading="lazy"
             decoding="async" referrerpolicy="no-referrer">
      </div>
    {% endif %}
    <div class="feed-body">
      <b>
        {% if item.link and item.link != "" %}
          <a href="{{ item.link | escape }}" rel="noopener">{{ item.title | escape }}</a>
        {% else %}
          {{ item.title | escape }}
        {% endif %}
      </b>
      <p class="feed-meta muted">
        <b class="coming">{{ item.published | date: "%-d %b" }}</b>
        &middot; {{ item.source | escape }}{% if item.owner and item.owner != "" %} &middot; {{ item.owner | escape }}{% endif %}
      </p>
      {% if item.summary and item.summary != "" %}
        <p class="feed-summary muted">{{ item.summary | escape }}</p>
      {% endif %}
    </div>
  </li>
{% endfor %}
</ul>

{% endif %}

{% if published.size > 0 %}

## Made by members

<p class="lede">
  Published by members on their own channels. We read the feeds &mdash; follow
  the source for everything.
</p>

<ul class="feed">
{% for item in published %}
  <li>
    {% if item.image and item.image != "" %}
      <div class="feed-thumb">
        <img src="{{ item.image | escape }}" alt="" loading="lazy"
             decoding="async" referrerpolicy="no-referrer">
      </div>
    {% endif %}

    <div class="feed-body">
      <b>
        {% if item.link and item.link != "" %}
          <a href="{{ item.link | escape }}" rel="noopener">{{ item.title | escape }}</a>
        {% else %}
          {{ item.title | escape }}
        {% endif %}
      </b>

      <p class="feed-meta muted">
        {{ item.source | escape }}{% if item.owner and item.owner != "" %} &middot; {{ item.owner | escape }}{% endif %}
        {% if item.published %}
          &middot; <time datetime="{{ item.published | escape }}">{{ item.published | date: "%-d %b %Y" }}</time>
        {% endif %}
      </p>

      {% if item.summary and item.summary != "" %}
        <p class="feed-summary muted">{{ item.summary | escape }}</p>
      {% endif %}
    </div>
  </li>
{% endfor %}
</ul>

<p class="muted">
  Publish something you'd like listed here? <a href="/contact/">Send us the
  feed</a> &mdash; a podcast RSS URL, a YouTube channel, a blog. You keep the
  work wherever it already lives.
</p>

{% else %}

## Made by members

<p>
  If you publish a podcast, a channel, or a blog, we can list what you put out
  here &mdash; you keep it wherever it already lives and we just read the feed.
  <a href="/contact/">Send us the link</a> and it starts showing up.
</p>

{% endif %}

{% comment %} ----------------------------------------------------- taking part {% endcomment %}

## Taking part

<ul class="rows">
  <li>
    <b><a href="/membership/">Become a member</a></b>
    <span>Access to gear, studios, and the rest of it.</span>
  </li>
  <li>
    <b><a href="/classes/">Take a class</a></b>
    <span>Most people start here, member or not.</span>
  </li>
  <li>
    <b><a href="/teach/">Teach one</a></b>
    <span>If you know a thing, there's someone here who wants to learn it.</span>
  </li>
  <li>
    <b><a href="/submit/">Submit a program</a></b>
    <span>Made something? It can go out on the channel.</span>
  </li>
  <li>
    <b><a href="#the-board">Come to a board meeting</a></b>
    <span>They're open. You don't need to be on the agenda.</span>
  </li>
</ul>

{% comment %} --------------------------------------------------- the board {% endcomment %}

{%- assign gov = site.data.governance -%}
{%- assign m = gov.meetings -%}
{%- assign org = site.data.org -%}

## The board

{% if m.open %}

### Meetings are open

Board meetings are open to anyone who wants to come. You don't need to be a
member, you don't need to be on the agenda, and you don't need to tell us
first &mdash; though it's a small room, so it's kind to.

{% if m.schedule and m.schedule != "" %}
  <p class="lede">{{ m.schedule }}</p>
{% else %}
  <p class="transaction transaction-todo">
    <b>The meeting schedule isn't filled in yet.</b>
    <span class="muted">Someone who wants to attend can't act on this page
    until it is. Set <code>meetings.schedule</code> in
    <code>_data/governance.yml</code> &mdash; plain language, like "the third
    Tuesday of the month, 6:30pm".</span>
  </p>
{% endif %}

<ul class="rows">
  <li>
    <b>Where</b>
    <span>
      {% if m.location and m.location != "" %}
        {{ m.location }}
      {% else %}
        {{ org.address.venue }}, {{ org.address.street }},
        {{ org.address.city }}, {{ org.address.state }} {{ org.address.zip }}
      {% endif %}
    </span>
  </li>
  {% unless m.recorded %}
    <li>
      <b>Recording</b>
      <span>Meetings aren't recorded. The minutes are the record.</span>
    </li>
  {% endunless %}
</ul>

{% if m.what_to_expect and m.what_to_expect != "" %}
  <p>{{ m.what_to_expect | strip_newlines | strip }}</p>
{% endif %}

<p>
  If you want to raise something, <a href="/contact/">get in touch</a> ahead of
  time and we'll make room for it.
</p>

{% else %}

### Meetings

Board meetings are not currently open to the public. <a href="/contact/">Get in
touch</a> if there's something you'd like the board to consider.

{% endif %}

### Minutes

{% if gov.minutes.url and gov.minutes.url != "" %}
  <p>
    Minutes from past meetings are
    <a href="{{ gov.minutes.url }}" rel="noopener">available to look through</a>
    if you're interested.
    {% if gov.minutes.note %}<span class="muted">{{ gov.minutes.note | strip_newlines | strip }}</span>{% endif %}
  </p>
{% else %}
  <p>
    We keep minutes of every meeting. There's no folder linked here yet, so
    email
    {% assign to = gov.minutes.request_email | default: org.email %}
    <a href="mailto:{{ to }}?subject=Board%20minutes">{{ to }}</a>
    and we'll send them over.
    {% if gov.minutes.note %}<span class="muted">{{ gov.minutes.note | strip_newlines | strip }}</span>{% endif %}
  </p>
{% endif %}

### Who's on it

{%- comment -%} Office hours are per person and render before the bio. {%- endcomment -%}

{% assign roster = site.data.board | where_exp: "p", "p.name" %}
{% if roster.size > 0 %}
<ul class="grid">
{% for person in roster %}
  <li class="card">
    {% if person.photo and person.photo != "" %}
      <div class="card-portrait">
        <img src="{{ person.photo | escape }}" alt="" loading="lazy"
             decoding="async">
      </div>
    {% endif %}
    <h4>{{ person.name }}</h4>
    {% if person.role %}<p class="muted">{{ person.role }}</p>{% endif %}
    {% if person.office_hours and person.office_hours != "" %}
      <p class="office-hours">
        <b>Office hours</b>
        <span>{{ person.office_hours | strip_newlines | strip }}</span>
      </p>
    {% endif %}
    {% if person.bio %}<p>{{ person.bio }}</p>{% endif %}
  </li>
{% endfor %}
</ul>
{% else %}
  <p class="transaction transaction-todo">
    <b>The roster isn't filled in yet.</b>
    <span class="muted">Add entries to <code>_data/board.yml</code>. A name and
    a role is enough to start; bios, photos and
    <code>office_hours</code> can follow. Board members also host studio
    sessions, so this is worth getting right &mdash; and the office hours Bryan
    asked to see on this page are per-person, so they appear here or nowhere.</span>
  </p>
{% endif %}

{% assign docs = site.data.governance.documents | where_exp: "d", "d.url" %}
{% if docs.size > 0 %}
### Documents

<ul class="rows">
{% for doc in docs %}
  <li><b><a href="{{ doc.url }}" rel="noopener">{{ doc.name }}</a></b></li>
{% endfor %}
</ul>
{% endif %}
