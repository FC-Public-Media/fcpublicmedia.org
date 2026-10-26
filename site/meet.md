---
title: Meet
---

## The board

<ul class="grid" style="gap: 0; padding: 0; margin: 0">
{%- assign _people = site.data.hosts.people | where_exp: "p", "p.role != nil" -%}
{% for person in _people %}
  <li class="card" style="margin: 0; border: 0;">
    {% if person.photo and person.photo != "" %}
      <div class="card-portrait">
        <img src="{{ person.photo | escape }}" alt="" loading="lazy"
             decoding="async">
      </div>
    {% endif %}
    <h4>
      {{ person.name }}
    </h4>
    {% for day_info in site.data.hosts.days %}
      {% assign _info = day_info[0] %}
      {% if person[_info] %}
        <p class="office-hours">
          <span>
            {{ site.data.hosts.labels[_info] }}:
            {{ person[_info][0] | modulo: 12 }}-{{ person[_info][1] | modulo: 12 }}</span>
        </p>
      {% endif %}
    {% endfor %}
    {% if person.role %}<p><b>{{ person.role }}</b></p>{% endif %}
    <span class="supports">{% for _sup in person.supports %}<b>{{ _sup }}</b>{% unless forloop.last %}<span> • </span>{% endunless %}{% endfor %}</span>
    {% if person.bio %}<p>{{ person.bio }}</p>{% endif %}
  </li>
{% endfor %}
</ul>
