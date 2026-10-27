---
title: Reserve

booqable:
  snippet: '<script src="https://1463eea8-db0a-45d4-9801-176111dc06a5.assets.booqable.com/v2/booqable.js"></script>'

  # Booqable's script hydrates, in page order.
  components:
  - class: booqable-product-list
    attributes: 'data-per="24" data-show-search="true"'
---

<div class="halves" data-halves>
<div class="halves-tabs" role="tablist" hidden>
  <button type="button" role="tab" data-half="spaces" aria-selected="false">Spaces</button>
  <button type="button" role="tab" data-half="equipment" aria-selected="true">Equipment</button>
</div>

<section class="half" data-half="spaces" markdown="1">

## Studio

[{{ site.fcpm.email.bookings }}](mailto:{{ site.fcpm.email.bookings }})

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

<figure class="floor-plan">
  <img src="{{ '/assets/img/floor-plan.png' }}"
       alt="Floorplan of studio space, demonstrating the control room, video studio, podcasting room, and restroom."
       loading="lazy" decoding="async">
</figure>

</section>

<section class="half" data-half="equipment" markdown="1">

## Equipment

[{{ site.fcpm.email.equipment }}](mailto:{{ site.fcpm.email.equipment }})

{% include booqable.html config=page.booqable %}

</section>
</div>

<script type="module" src="{{ '/assets/js/halves.js' }}?v={{ site.time | date: '%s' }}"></script>
