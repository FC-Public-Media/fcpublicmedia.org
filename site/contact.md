---
title: Contact
lede: We're glad to hear from you.
---

<ul class="rows">
  <li><b>Email</b> <span><a href="mailto:{{ site.data.org.email }}">{{ site.data.org.email }}</a></span></li>
  <li><b>Phone</b> <span><a href="tel:{{ site.data.org.phone | remove: '-' }}">{{ site.data.org.phone }}</a></span></li>
  <li><b>Equipment</b> <span><a href="mailto:{{ site.data.org.equipment_email }}">{{ site.data.org.equipment_email }}</a></span></li>
</ul>

## Visit

{{ site.data.org.address.venue }}
{{ site.data.org.address.street }}
{{ site.data.org.address.city }}, {{ site.data.org.address.state }} {{ site.data.org.address.zip }}

{{ site.data.org.address.note }}.

## Send a message

<p class="transaction transaction-todo">
  <b>Contact form.</b>
  <span class="muted">A static site can't accept form posts on its own. Two
  options: a small function in <code>/api</code> that relays to
  {{ site.data.org.email }} via Microsoft Graph, or a hosted form service. See
  README, "Forms".</span>
</p>

## Newsletter

[Sign up for our newsletter]({{ site.data.org.newsletter_url }}).
