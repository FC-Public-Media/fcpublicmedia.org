---
title: Community
lede: What's coming up, and where to find everyone between visits.
---

{%- assign com = site.data.community -%}
{%- assign now = site.time | date: "%s" -%}

{%- comment -%}
  ONE LIST FROM THREE FILES

  Classes, board meetings, and everything else live in different data files
  for good reasons, but a visitor should not have to know that. So they are
  merged here into a single chronological list.

  Liquid cannot build objects, so each source is flattened into a delimited
  string, the strings are sorted, and each is split back apart to render. It
  is a well-worn Jekyll idiom and it is the only awkward part of this page.

  The sort key is epoch seconds via the `date` filter, which parses the
  UTC offset properly — sorting the ISO strings directly would be right by
  accident rather than on purpose, since two events on the same day always
  share an offset but two events either side of a DST change do not.

  Delimiter is "%%" because it does not occur in prose. A title containing it
  would split wrongly; nothing else would.

  Past events are dropped here rather than in the templates below, so the
  "nothing coming up" state is genuinely about emptiness and not about a list
  full of last spring.
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
      {{ at }}%%Board meeting%%Board meeting%%{{ meeting.starts }}%%%%/board/%%{{ meeting.note }}
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

{%- comment -%}
  Written to be true on a quiet month rather than to fill space. A small
  organization with nothing scheduled is not a broken one, and a page that
  implies otherwise is worse than a page that says so and offers the door.
{%- endcomment -%}

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
  show on the <a href="/classes/">classes page</a>; board meetings are on the
  <a href="/board/">board page</a>, and
  <a href="/board/">anyone can come to one</a>.
</p>

{% comment %} ------------------------------------------------ where we talk {% endcomment %}

## {{ com.heading }}

<p class="lede">{{ com.blurb | strip_newlines | strip }}</p>

{%- comment -%}
  Channels with no url are skipped, so a platform still being argued about can
  sit in the data file without appearing here. `primary` marks whichever one
  someone should actually try first — see the note in _data/community.yml
  about the chat platform being unsettled.
{%- endcomment -%}

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

{%- comment -%}
  Read from _data/member_programs.json, which script/sync-feeds.py builds from
  the feeds listed in _data/feeds.yml. Nothing is fetched in the browser.

  EVERY STRING BELOW WAS WRITTEN BY SOMEBODY ELSE. The sync already strips
  markup and rejects any link that is not http(s); `| escape` here is the
  second half of that, and removing it would put a member's blog getting
  hijacked directly into our pages. Do not "tidy" it away.
{%- endcomment -%}

{%- assign made = site.data.member_programs -%}
{% if made and made.items.size > 0 %}

## Made by members

<p class="lede">
  Published by members on their own channels. We read the feeds &mdash; follow
  the source for everything.
</p>

<ul class="rows rows-events">
{% for item in made.items %}
  <li>
    <b>
      {% if item.published %}
        <time datetime="{{ item.published | escape }}">{{ item.published | date: "%a %-d %b" }}</time>
      {% else %}
        <span class="muted">Undated</span>
      {% endif %}
    </b>
    <span>
      {% if item.link and item.link != "" %}
        <a href="{{ item.link | escape }}" rel="noopener">{{ item.title | escape }}</a>
      {% else %}
        {{ item.title | escape }}
      {% endif %}
      <span class="muted">
        {{ item.source | escape }}{% if item.owner and item.owner != "" %} &middot; {{ item.owner | escape }}{% endif %}
      </span>
      {% if item.summary and item.summary != "" %}
        <span class="muted">{{ item.summary | escape }}</span>
      {% endif %}
    </span>
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
    <b><a href="/board/">Come to a board meeting</a></b>
    <span>They're open. You don't need to be on the agenda.</span>
  </li>
</ul>
