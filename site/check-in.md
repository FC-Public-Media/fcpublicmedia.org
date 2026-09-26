---
title: Check In
layout: pass
lede: One tap when you get here. Your visits stay on your own phone.
---

{%- assign ci = site.data.checkin -%}
{%- assign loc = ci.location -%}
{%- assign cl = site.data.classes -%}

{%- comment -%}
  The same schedule the homepage gets. Both pages run the same function over
  it (assets/js/classes.js), so they cannot disagree about whether a class is
  on — and the QR on the door stays a permanent link to this page, carrying no
  class information that could go stale in someone's pocket.
{%- endcomment -%}
{% include class-config.html %}

{%- assign id = site.data.identity -%}

<script type="application/json" id="checkin-config">
{
  "identityMode": {{ ci.identity.mode | jsonify }},
  {%- comment -%}
    Public halves only. These are safe to serve to everyone — that is the
    point of them. See _data/identity.yml.
  {%- endcomment -%}
  "identity": {
    "issuer": {{ id.issuer | jsonify }},
    "keys": [
      {%- for key in id.keys -%}
        {"id": {{ key.id | jsonify }}, "x": {{ key.x | jsonify }}, "y": {{ key.y | jsonify }}}
        {%- unless forloop.last %},{% endunless -%}
      {%- endfor -%}
    ]
  },
  "historyLimit": {{ ci.history_limit | default: 200 }},
  "reasons": {{ ci.reasons | jsonify }},
  "location": {
    "required": {{ loc.required | default: false }},
    "latitude": {{ loc.latitude }},
    "longitude": {{ loc.longitude }},
    "radius": {{ loc.radius_m }},
    "accuracySlack": {{ loc.accuracy_slack_m }},
    "recheckSeconds": {{ loc.recheck_seconds }}
  }
}
</script>

<noscript>
  <p class="transaction transaction-todo">
    <b>This page needs JavaScript.</b>
    <span class="muted">Your visit is recorded by your browser rather than by
    us, so there is nothing for the page to do without it. The paper log by
    the door works fine.</span>
  </p>
</noscript>


{%- comment -%}
  THE PASS. Autumn, 2026-09-26: this is the page a member sees most, on their
  own phone. It is their pass, it has their name on it, and it does not scroll.
  So it is three views of one screen each, switched by the address's #:

    (none)    the pass: who you are, and checking in
    #visits   your visits, as a list
    #device   this phone: its identifier, and keeping or forgetting the list

  No explanatory text. The reason for a visit is not asked for: it comes from
  the code that was scanned (/check-in/?reason=Class) or from a class being
  on, and the pass shows it.
{%- endcomment -%}

{% comment %} ------------------------------------------------------ the pass {% endcomment %}

<section class="pass-view pass" data-view="pass" aria-label="Your pass">

  <div class="pass-card">
    <span class="pass-mark" aria-hidden="true"></span>
    <label class="visually-hidden" for="profile-name">Name</label>
    <input class="pass-name" type="text" id="profile-name" autocomplete="name"
           placeholder="Your name" spellcheck="false">

    <div class="pass-email" data-claim="none" hidden>
      <label class="visually-hidden" for="profile-email">Email</label>
      <input type="email" id="profile-email" autocomplete="email" placeholder="Email"
             inputmode="email" autocapitalize="none" spellcheck="false">
    </div>
    <p class="pass-email" data-claim="verified" hidden>
      <span id="claim-email"></span> <span class="pass-chip">Confirmed</span>
    </p>

    <label class="visually-hidden" for="device-label">This phone's name</label>
    <input class="pass-device" type="text" id="device-label" placeholder="This phone"
           autocomplete="off" spellcheck="false">
  </div>

  <div class="pass-now">
    <p class="pass-status" id="claim-status" role="status" aria-live="polite" hidden></p>

    <div class="class-banner" id="class-banner-root" data-class-banner hidden>
      <p class="eyebrow" data-class-eyebrow></p>
      <h2 data-class-title></h2>
      <p><span data-class-when></span> <span class="muted" data-class-room></span></p>
      <p data-class-late hidden>Running late? Come anyway.</p>
      <p data-rsvp-offer hidden>
        <button class="btn" id="rsvp-button" type="button">I'm planning to come</button>
      </p>
      <p class="rsvp-noted" data-rsvp-noted hidden>You're coming. Check in when you get here.</p>
    </div>

    <div class="state" data-state="blocked" hidden>
      <h2>This browser won't save anything</h2>
      <p class="muted">Private browsing? Use the paper log by the door.</p>
    </div>

    <div class="state" data-state="idle" hidden>
      <p class="pass-reason" id="visit-reason" hidden></p>
      <button class="btn btn-primary btn-big" data-action="check-in" type="button">Check in</button>
    </div>

    <div class="state" data-state="locating" hidden>
      <p class="lede">Checking where you are&hellip;</p>
    </div>

    <div class="state" data-state="far" hidden>
      <h2>Not at the studio yet</h2>
      <p class="muted" id="far-distance"></p>
      <p class="muted">Held. Leave this open and it finishes when you arrive.</p>
      <p class="pass-actions">
        <a class="btn btn-primary" id="venue-directions" href="#" target="_blank" rel="noopener">Directions</a>
        <button class="btn" data-action="check-in" type="button">Check again</button>
        <button class="btn" id="cancel-pending" type="button">Cancel</button>
      </p>
    </div>

    <div class="state" data-state="denied" hidden>
      <h2>Location is off</h2>
      <p class="muted">Turn it on for this site, or use the paper log.</p>
      <button class="btn" data-action="check-in" type="button">Try again</button>
    </div>

    <div class="state" data-state="error" hidden>
      <h2>That didn't work</h2>
      <p class="muted" id="error-detail"></p>
      <button class="btn" data-action="check-in" type="button">Try again</button>
    </div>

    <div class="state" data-state="done" hidden>
      <h2>Welcome.</h2>
      <p class="muted" id="done-detail"></p>
      <button class="btn" id="again-button" type="button">Check in again</button>
    </div>
  </div>

  <nav class="pass-nav" aria-label="More">
    <a href="#visits">Visits <span id="checkin-count"></span></a>
    <a href="#device">This phone</a>
  </nav>
</section>

{% comment %} -------------------------------------------------------- visits {% endcomment %}

<section class="pass-view" data-view="visits" aria-labelledby="visits-title" hidden>
  <header class="pass-top">
    <a class="pass-back" href="#" data-back>Pass</a>
    <h2 id="visits-title">Visits</h2>
  </header>
  <div class="pass-scroll">
    <p class="muted" id="checkin-empty" hidden>No visits yet.</p>
    <ul class="rows rows-checkin" id="checkin-history"></ul>
  </div>
</section>

{% comment %} -------------------------------------------------------- device {% endcomment %}

<section class="pass-view" data-view="device" aria-labelledby="device-title" hidden>
  <header class="pass-top">
    <a class="pass-back" href="#" data-back>Pass</a>
    <h2 id="device-title">This phone</h2>
  </header>
  <div class="pass-scroll">
    <ul class="rows">
      <li><b>Identifier</b> <span><code id="device-id"></code></span></li>
      <li><b>First used</b> <span id="device-since"></span></li>
      <li><b>Kept</b> <span id="persist-state"></span></li>
    </ul>

    <p class="pass-actions">
      <button class="btn" id="export-button" type="button">Save a copy</button>
      <label class="btn" for="import-input">Restore from a file</label>
      <input type="file" id="import-input" accept="application/json,.json" hidden>
    </p>
    <p class="muted" id="storage-status" role="status" aria-live="polite"></p>

    <div data-claim="verified" hidden>
      <ul class="rows">
        <li><b>Email confirmed until</b> <span id="claim-expires"></span></li>
      </ul>
      <p class="pass-actions">
        <button class="btn" id="claim-forget" type="button">Remove confirmed email</button>
      </p>
    </div>
    <p class="muted" data-claim="none" hidden>
      <a href="/contact/">Ask us</a> to confirm your email.
    </p>

    <p class="pass-actions">
      <button class="btn" id="forget-button" type="button">Forget this phone</button>
    </p>
  </div>
</section>

<script type="module" src="{{ '/assets/js/checkin.js' | relative_url }}?v={{ site.time | date: '%s' }}"></script>
