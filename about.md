---
title: About & Board
lede: Who we are and who runs the place.
---

Fort Collins Public Media has been a community media resource since
{{ site.data.org.founded }}. {{ site.data.org.legal }}

TODO &mdash; mission statement and a short history. The current site has no
about page, which is unusual for a nonprofit and worth fixing.

## Board and staff

<ul class="grid">
{% for person in site.data.board %}
  <li class="card">
    <h3>{{ person.name }}</h3>
    <p class="muted">{{ person.role }}</p>
    <p>{{ person.bio }}</p>
  </li>
{% endfor %}
</ul>

<p class="transaction transaction-todo">
  <b>Roster is a placeholder.</b>
  <span class="muted">Fill in <code>_data/board.yml</code>. Board members also
  host studio sessions, so this page is worth getting right.</span>
</p>

## Financials and governance

TODO &mdash; nonprofits are generally expected to publish their EIN, Form 990,
and annual report. Decide what belongs here.
