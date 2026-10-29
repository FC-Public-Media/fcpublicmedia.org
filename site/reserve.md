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

The _{{ site.fcpm.address.venue }}_ studio at **{{ site.fcpm.address.street }}** shares a block with Old Town Library. Our equipment and software are yours to use while on-site.

{%- comment -%} A request to the site-worker's `book` tank (assets/js/book.js). The week below is drawn
  from site/_data/hosts.yml as it is: each person's day keys are their hosting hours. Every word shown
  is here; book.js only picks which, and draws the week. {%- endcomment %}
<form class="book" id="book" data-tank="book" data-sends data-subject="Studio request"
      data-worker="{{ site.data.site_worker.url }}" data-email="{{ site.fcpm.email.bookings }}">

  <div class="field-row">
    <div class="field"><label for="book-name">Name</label><input id="book-name" name="name" autocomplete="name"></div>
    <div class="field"><label for="book-email">Email</label><input id="book-email" name="email" type="email" autocomplete="email"></div>
  </div>

  {%- comment -%} The week: one at a time, Tuesday to Saturday (the days in hosts.yml with hours).
    A host's hours are cut into two-hour slots with an hour between, so 11–4 is 11–1 and 2–4.
    The day is picked on the week, so it has no box of its own. Two rows of picks, alike on purpose:
    the week shown with the start time, then the space with the host. {%- endcomment %}
  <div class="book-row">
    <div class="book-picks" role="group" aria-label="Week" data-weeks hidden>
      <button type="button" data-week="0" aria-pressed="true">This week</button>
      <button type="button" data-week="1" aria-pressed="false">Next week</button>
      <button type="button" data-week="2" aria-pressed="false">Week after</button>
    </div>
    <div class="field"><label for="book-start">Time</label><input id="book-start" name="start" type="time" step="900"></div>
  </div>
  <input type="hidden" id="book-date" name="date">

  <fieldset class="book-spaces">
    <legend class="visually-hidden">Which space</legend>
    <div class="book-row">
      <div class="book-picks">
        <label><input type="radio" name="space" value="Video Studio" checked><span>Video Studio</span></label>
        <label><input type="radio" name="space" value="Podcast Studio"><span>Podcast Studio</span></label>
        <label><input type="radio" name="space" value="Editing Bays"><span>Editing Bays</span></label>
      </div>
      <div class="field"><label for="book-host">With</label>
        <select id="book-host" name="host">
          <option value="">No preference</option>
          {%- for person in site.data.hosts.people %}
          {%- assign _name = person.name | split: " " -%}
          <option value="{{ person.name | escape }}">{{ _name[0] }}</option>
          {%- endfor %}
        </select>
      </div>
    </div>
    <div class="book-space" data-space="Video Studio">
      <p><b>635 sq ft.</b> An adaptable space perfect for nearly every project. Includes a state-of-the-art RGB light system, live editing board, acoustic treatment, and a massive green screen to make your vision real.</p>
    </div>
    <div class="book-space" data-space="Podcast Studio">
      <p><b>113 sq ft.</b> Room for up to four in-person guests. Acoustically treated, with professional audio equipment to make your podcast sound great.</p>
    </div>
    <div class="book-space" data-space="Editing Bays">
      <p><b>318 sq ft.</b> The entire Adobe Suite for video and audio projects. These are state-of-the-art machines — you can edit 4K footage and above. Two stations, both dual-monitor, and a window straight into the video studio.</p>
    </div>
  </fieldset>

  <div class="planner" data-planner hidden>
    <div class="planner-scroll">
      <div class="planner-grid" data-planner-grid></div>
    </div>
    <p class="muted planner-hint">Pick a host, or a time. Above and below the day ask for earlier or later.</p>
    <template data-words>
      <span data-word="earlier">Earlier</span>
      <span data-word="later">Later</span>
      <span data-word="you">You</span>
    </template>
  </div>
  <script type="application/json" id="hosts">{{ site.data.hosts | jsonify }}</script>

  <div class="trap" aria-hidden="true"><label for="book-website">Website</label><input id="book-website" name="website" tabindex="-1" autocomplete="off"></div>

  <p class="hero-actions"><button class="btn btn-primary" type="submit">Ask for this time</button></p>
  <div class="muted" role="status" aria-live="polite">
    <p data-say="pick-time" hidden>Pick a time on the week first.</p>
    <p data-say="sending" hidden>Sending…</p>
    <p data-say="unsent" hidden>Requests can't be sent from here yet. <a data-mailto href="#">Email this to us</a>; it's all filled in. It's kept on this phone too, under <a href="{{ '/you/' | relative_url }}">Yours</a>.</p>
    <p data-say="failed" hidden>That didn't send. <a data-mailto href="#">Email this to us</a>; it's all filled in. It's kept on this phone too, under <a href="{{ '/you/' | relative_url }}">Yours</a>.</p>
  </div>
</form>
<div data-receipt="sent" tabindex="-1" hidden>
  <p><b>Asked.</b> Reference <code data-reference></code>. Nothing is booked until a person checks the
    room is free and a host can be there; we'll email you. If it's soon, call {{ site.fcpm.phone }}.</p>
  <p><button class="btn" type="button" data-again>Ask for another time</button></p>
</div>

<div class="book-mine" data-mine hidden>
  <h3>Asked from this phone</h3>
  <ul class="rows" data-mine-list></ul>
</div>

</section>

<section class="half" data-half="equipment" markdown="1">

## Equipment rental

[{{ site.fcpm.email.equipment }}](mailto:{{ site.fcpm.email.equipment }})

We offer ready-to-go kits for home and field work. Booqable and Stripe will handle your reservation.
Come for pickup when it's time.

{% include booqable.html config=page.booqable %}

</section>
</div>

<script type="module" src="{{ '/assets/js/halves.js' }}?v={{ site.time | date: '%s' }}"></script>
<script type="module" src="{{ '/assets/js/book.js' }}?v={{ site.time | date: '%s' }}"></script>
