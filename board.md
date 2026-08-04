---
title: Board & Meetings
lede: Who governs FC Public Media, when they meet, and how to come to one.
---

{%- assign gov = site.data.governance -%}
{%- assign m = gov.meetings -%}
{%- assign org = site.data.org -%}

{% comment %} ------------------------------------------------ open meetings {% endcomment %}

{%- comment -%}
  The lead, because it is the only thing on this page that asks something of
  the reader. Everything below is reference material.

  FCPM is a nonprofit, not a public body — Colorado's Open Meetings Law does
  not apply. Saying "you are welcome" rather than "as required by law" is both
  accurate and the better sentence.
{%- endcomment -%}

{% if m.open %}

## Our meetings are open

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

{%- comment -%}
  Specific dates only appear when there are some. An empty "Upcoming" heading
  reads as neglect, which is worse than not having the section.
{%- endcomment -%}
{% if m.upcoming and m.upcoming.size > 0 %}
### Coming up

<ul class="rows">
{% for meeting in m.upcoming %}
  <li>
    <b>{{ meeting.starts | date: "%A, %-d %B" }}</b>
    <span>
      {{ meeting.starts | date: "%-l:%M%P" }}
      {% if meeting.note %}<span class="muted">{{ meeting.note }}</span>{% endif %}
    </span>
  </li>
{% endfor %}
</ul>
{% endif %}

<p>
  If you want to raise something, <a href="/contact/">get in touch</a> ahead of
  time and we'll make room for it.
</p>

{% else %}

## Board meetings

Board meetings are not currently open to the public. <a href="/contact/">Get in
touch</a> if there's something you'd like the board to consider.

{% endif %}

{% comment %} ------------------------------------------------------ minutes {% endcomment %}

## Minutes

{%- comment -%}
  Deliberately understated. Minutes being available is not the same as minutes
  being published, and the difference is the whole reason this section is a
  paragraph near the bottom rather than a feature.
{%- endcomment -%}

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

{% comment %} ----------------------------------------------------- the board {% endcomment %}

## Who's on the board

{% assign roster = site.data.board | where_exp: "p", "p.name" %}
{% if roster.size > 0 %}
<ul class="grid">
{% for person in roster %}
  <li class="card">
    <h3>{{ person.name }}</h3>
    {% if person.role %}<p class="muted">{{ person.role }}</p>{% endif %}
    {% if person.bio %}<p>{{ person.bio }}</p>{% endif %}
  </li>
{% endfor %}
</ul>
{% else %}
  <p class="transaction transaction-todo">
    <b>The roster isn't filled in yet.</b>
    <span class="muted">Add entries to <code>_data/board.yml</code>. A name and
    a role is enough to start; bios can follow. Board members also host studio
    sessions, so this is worth getting right.</span>
  </p>
{% endif %}

{% comment %} --------------------------------------------------- documents {% endcomment %}

{%- comment -%}
  Only rendered when there is something to render. A nonprofit governance
  section listing three headings and no documents invites exactly the question
  it was meant to answer.
{%- endcomment -%}
{% assign docs = site.data.governance.documents | where_exp: "d", "d.url" %}
{% if docs.size > 0 %}
## Documents

<ul class="rows">
{% for doc in docs %}
  <li><b><a href="{{ doc.url }}" rel="noopener">{{ doc.name }}</a></b></li>
{% endfor %}
</ul>
{% endif %}

<p class="muted">
  {{ org.legal }} More about the organization is on the
  <a href="/about/">about page</a>.
</p>
