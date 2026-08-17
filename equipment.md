---
title: Equipment
lede: Members can borrow cameras, audio, and lighting for their own projects.
---

## Browse and reserve online

Some of our gear can be booked directly. Pick your dates and the list below
shows what's actually free — availability is live, not a wish.

{% include booqable.html %}

<p class="muted">
  Not everything is here. Anything you can't find, or aren't sure about, goes
  through the email route below &mdash; which is also the better one if you'd
  rather describe the shoot than pick part numbers.
</p>

## How to borrow equipment

Email [{{ site.data.org.equipment_email }}](mailto:{{ site.data.org.equipment_email }})
and tell us:

- Your contact information
- What you're trying to make, and what you think you need
- When you need it, and for how long

Staff pull the gear and have it ready. You don't have to know exactly what to
ask for &mdash; describing the shoot is enough, and often better, since we may
have something more suitable than the thing you had in mind.

**Requests must be made at least one week before checkout.** Anything with
less notice than that can't be considered.

Every borrower agrees to the [Equipment Terms and Conditions](#terms).

Equipment can't be reserved through the studio booking calendar. Email is the
only way.

## What we have

{% for group in site.data.equipment.categories %}
- **{{ group.name }}** &mdash; {{ group.summary }}
{%- endfor %}

{% if site.data.equipment.highlights.size > 0 %}
Worth knowing about:

{% for item in site.data.equipment.highlights %}
- {{ item }}
{%- endfor %}
{% endif %}

<p class="muted">
  This is a summary, not a catalogue. The full inventory lives in our booking
  system, and staff work from it when they put your kit together &mdash; so
  tell us what you're making rather than picking part numbers.
</p>

## Not sure what you need?

That's the normal case. Members get help choosing gear, and we run
[classes]({{ '/classes/' | relative_url }}) on using it. If you're weighing
whether to join, [membership]({{ '/membership/' | relative_url }}) includes
both.

## Terms {#terms}

TODO &mdash; the current site links out to a separate Equipment Terms and
Conditions document. Decide whether to host it here as a page or keep it as a
downloadable PDF.
