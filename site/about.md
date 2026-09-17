---
title: About
lede: Who we are and what the place is for.
---

{%- comment -%}
  Kept on one line on purpose. Wrapped, `{{ site.data.org.founded }}` expands
  to "2004." at the start of a line, and Markdown reads that as an ordered
  list marker — which split this sentence in half and turned the legal line
  into item 1.
{%- endcomment -%}
Fort Collins Public Media has been a community media resource since {{ site.data.org.founded }}. {{ site.data.org.legal }}

<p class="transaction transaction-todo">
  <b>Mission statement and history &mdash; not written yet.</b>
  <span class="muted">The current Wix site has no about page at all, which is
  unusual for a nonprofit and is the gap this page exists to close. A few
  paragraphs on what FCPM is for, who it serves, and how it started would do
  it.</span>
</p>

## The board

The board meets in the open &mdash; anyone can come and sit in.
<a href="/meet/#the-board">Who's on it, when they meet, and how to attend</a> is on its
own page, along with the minutes.

## Financials and governance

<p class="transaction transaction-todo">
  <b>Not decided yet.</b>
  <span class="muted">Nonprofits are commonly asked for an EIN, a Form 990,
  and an annual report. What belongs here is a board decision rather than a
  technical one. Anything published goes in <code>documents</code> in
  <code>_data/governance.yml</code> and appears on the board page.</span>
</p>

## Getting in touch

{{ site.data.org.name }} is at {{ site.data.org.address.street }},
{{ site.data.org.address.city }}. The
<a href="/contact/">contact page</a> has hours, a phone number, and the right
address for each kind of question.
