---
title: Podcasts
lede: Shows produced in our studios by people from around Larimer County.
---

{% assign shows = site.podcasts | sort: "title" %}
<ul class="grid">
{% for show in shows %}
  <li class="card">
    <h3><a href="{{ show.url | relative_url }}">{{ show.title }}</a></h3>
    {% if show.explicit %}<p><span class="tag tag-warn">Explicit language</span></p>{% endif %}
    <p>{{ show.lede }}</p>
  </li>
{% endfor %}
</ul>

## Archives

TODO &mdash; the current site keeps a separate podcast archive page. Decide
whether retired shows get their own entries above or a single archive listing.

## Start your own

The podcast studio is available to members.
[See membership]({{ '/membership/' | relative_url }}) or
[book a session]({{ '/reserve/' | relative_url }}).
