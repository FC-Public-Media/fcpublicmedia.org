---
title: Reserve

booqable:
  snippet: '<script src="https://1463eea8-db0a-45d4-9801-176111dc06a5.assets.booqable.com/v2/booqable.js"></script>'

  # Booqable's script hydrates, in page order.
  components:
  - class: booqable-datepicker
    what: Pick the dates first, so everything below shows real availability.
  - class: booqable-product-list
    attributes: 'data-per="24" data-show-search="true"'
    what: Every product with the search field built in.
---

At any tier of
[FC Public Media Membership]({{ '/join/' }})
you can reserve both the video and podcast studios, edit with the full Adobe
Creative Suite, and check out production equipment.

## Spaces

By email: [{{ site.fcpm.email.info }}](mailto:{{ site.fcpm.email.info }})
By phone: {{ site.fcpm.phone }}

{%- comment -%} The descriptions are the board's wording, verbatim: do not rewrite them.
{%- endcomment %}
<ul class="rows rows-spaces">
  <li>
    <b>Video Studio</b>
    <span>635 sq ft</span>
    <p>An adaptable space perfect for nearly every project. Includes a state-of-the-art RGB light system, live editing board, acoustic treatment, and a massive green screen to make your vision real.</p>
  </li>
  <li>
    <b>Podcast Studio</b>
    <span>113 sq ft</span>
    <p>Room for up to four in-person guests. Acoustically treated, with professional audio equipment to make your podcast sound great.</p>
  </li>
  <li>
    <b>Editing Bays</b>
    <span>318 sq ft</span>
    <p>The entire Adobe Suite for video and audio projects. These are state-of-the-art machines — you can edit 4K footage and above. Two stations, both dual-monitor, and a window straight into the video studio.</p>
  </li>
  <li>
    <b>Equipment Checkout</b>
    <p>Booked and checked out online, further down this page.</p>
  </li>
</ul>
{% include transaction.html key="booking" text="Check availability"
   todo="Email or call and we'll check the room and a host for you." %}

A room isn't confirmed straight away: someone has to check it is free and that a host can be
there, so expect a reply rather than an instant booking. We'll email once it's confirmed &mdash;
if you need it sooner than that, call.

## Equipment

Pick your dates, add what you need, and check out. Checkout asks you to
accept FC Public Media's Equipment Terms and Conditions and takes a
refundable security deposit.

Anything unusual, or would rather not book online? Email
[{{ site.fcpm.equipment_email }}](mailto:{{ site.fcpm.equipment_email }}).

{% include booqable.html config=page.booqable %}

{%- comment -%} Floor plan at the bottom, per the board president's review; `plan_label` maps its room names. {%- endcomment %}
<figure class="floor-plan">
  <img src="{{ '/assets/img/floor-plan.png' }}"
       alt="Floor plan. The video studio is the large room at the centre, with
            the editing bays along its left wall and the podcast studio below,
            off the corner."
       width="381" height="381" loading="lazy" decoding="async">
  <figcaption>
    The plan uses the building's labels: <b>studio</b> is the video studio,
    <b>office</b> is the podcast studio, <b>control room</b> is the editing bays.
  </figcaption>
</figure>
