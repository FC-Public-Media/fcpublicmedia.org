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

{%- comment -%} A request to the site-worker's `book` tank (assets/js/book.js). The week below is drawn
  from site/_data/hosts.yml as it is: each person's day keys are their hosting hours. Every word shown
  is here; book.js only picks which, and draws the week. {%- endcomment %}
<form class="book" id="book" data-tank="book" data-sends data-subject="Studio request"
      data-worker="{{ site.data.site_worker.url }}" data-email="{{ site.fcpm.email.bookings }}">

  <fieldset class="book-spaces">
    <legend class="visually-hidden">Which space</legend>
    <div class="book-space-picks">
      <label><input type="radio" name="space" value="Video Studio" checked><span>Video Studio</span></label>
      <label><input type="radio" name="space" value="Podcast Studio"><span>Podcast Studio</span></label>
      <label><input type="radio" name="space" value="Editing Bays"><span>Editing Bays</span></label>
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

  <div class="field-row">
    <div class="field"><label for="book-name">Name</label><input id="book-name" name="name" autocomplete="name"></div>
    <div class="field"><label for="book-email">Email</label><input id="book-email" name="email" type="email" autocomplete="email"></div>
  </div>

  <div class="field-row book-when">
    <div class="field"><label for="book-date">Day</label><input id="book-date" name="date" type="date"></div>
    <div class="field"><label for="book-start">Start, for two hours</label><input id="book-start" name="start" type="time" step="900"></div>
    <div class="field"><label for="book-host">With</label>
      <select id="book-host" name="host">
        <option value="">Whoever is hosting</option>
        {%- for person in site.data.hosts.people %}
        <option value="{{ person.name | escape }}">{{ person.name }}</option>
        {%- endfor %}
      </select>
    </div>
  </div>

  {%- comment -%} The week: one at a time, Tuesday to Saturday (the days in hosts.yml with hours).
    A host's hours are cut into two-hour slots with an hour between, so 11–4 is 11–1 and 2–4. {%- endcomment %}
  <div class="planner" data-planner hidden>
    <div class="planner-weeks" role="tablist" aria-label="Week">
      <button type="button" role="tab" data-week="0" aria-selected="true">This week</button>
      <button type="button" role="tab" data-week="1" aria-selected="false">Next week</button>
      <button type="button" role="tab" data-week="2" aria-selected="false">Week after</button>
    </div>
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

  <div class="field"><label for="book-notes">What you're making, if you like</label><textarea id="book-notes" name="notes" rows="3"></textarea></div>

  <div class="trap" aria-hidden="true"><label for="book-website">Website</label><input id="book-website" name="website" tabindex="-1" autocomplete="off"></div>

  <p class="hero-actions"><button class="btn btn-primary" type="submit">Ask for this time</button></p>
  <div class="muted" role="status" aria-live="polite">
    <p data-say="pick-time" hidden>Pick a day and a start time first.</p>
    <p data-say="sending" hidden>Sending…</p>
    <p data-say="unsent" hidden>Requests can't be sent from here yet. <a data-mailto href="#">Email this to us</a>; it's all filled in.</p>
    <p data-say="failed" hidden>That didn't send. <a data-mailto href="#">Email this to us</a>; it's all filled in.</p>
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
<script type="module" src="{{ '/assets/js/book.js' }}?v={{ site.time | date: '%s' }}"></script>
