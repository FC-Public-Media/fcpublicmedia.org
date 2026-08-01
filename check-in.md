---
title: Check In
lede: One tap when you get here. Your visits stay on your own phone.
---

{%- assign ci = site.data.checkin -%}
{%- assign loc = ci.location -%}

<script type="application/json" id="checkin-config">
{
  "identityMode": {{ ci.identity.mode | jsonify }},
  "historyLimit": {{ ci.history_limit | default: 200 }},
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

{% comment %} ---------------------------------------------------- states {% endcomment %}

<div class="state" data-state="blocked" hidden>
  <p class="transaction transaction-todo">
    <b>Your browser is not allowing this page to save anything.</b>
    <span class="muted">That usually means private browsing. Check-ins are
    stored on your device, so there is nowhere to put them. Please use the
    paper log.</span>
  </p>
</div>

<div class="state" data-state="idle" hidden>
  <p>
    <button class="btn btn-primary btn-big" data-action="check-in" type="button">Check in</button>
  </p>
  {% if loc.required %}
    <p class="muted">
      We'll check that you're at {{ loc.name }}. If you're not there yet, we'll
      hold your check-in and finish it when you arrive.
    </p>
  {% endif %}
  {% if ci.identity.mode == "none" %}
    <p class="muted">{{ ci.identity.anonymous_note | strip_newlines | strip }}</p>
  {% endif %}
</div>

<div class="state" data-state="locating" hidden>
  <p class="lede">Checking where you are&hellip;</p>
</div>

<div class="state" data-state="far" hidden>
  <p class="eyebrow">Not yet</p>
  <h2>You're not at the studio yet</h2>
  <p class="lede" id="far-distance"></p>

  <p>
    Your check-in is held and will finish by itself when you get here.
    <b>Leave this page open</b> &mdash; look down when you walk in and it will
    be done.
  </p>

  <p class="hero-actions">
    <a class="btn btn-primary" id="venue-directions" href="#" target="_blank" rel="noopener">Directions</a>
    <button class="btn" data-action="check-in" type="button">Check again now</button>
  </p>

  <p class="muted">
    {{ loc.name }}<br>{{ loc.address }}
  </p>

  <p>
    <button class="btn" id="cancel-pending" type="button">Cancel</button>
  </p>
</div>

<div class="state" data-state="denied" hidden>
  <p class="eyebrow">Location needed</p>
  <h2>We couldn't check where you are</h2>
  <p>
    Checking in needs your location, because it is what tells us you actually
    arrived. Your position is never sent anywhere &mdash; the page compares it
    to the studio's address on your own phone, and keeps only the distance.
  </p>
  <p class="muted">
    Turn location back on for this site in your browser settings, then try
    again. Or use the paper log by the door.
  </p>
  <p>
    <button class="btn" data-action="check-in" type="button">Try again</button>
  </p>
</div>

<div class="state" data-state="error" hidden>
  <h2>That didn't work</h2>
  <p class="muted" id="error-detail"></p>
  <p>
    <button class="btn" data-action="check-in" type="button">Try again</button>
  </p>
</div>

<div class="state" data-state="done" hidden>
  <p class="eyebrow">Checked in</p>
  <h2>Welcome.</h2>
  <p class="lede" id="done-detail"></p>
  <p class="muted">
    Anything you add below is saved for next time, and stays on this phone.
  </p>
  <p>
    <button class="btn" id="again-button" type="button">Check in again</button>
  </p>
</div>

{% comment %} ------------------------------------------------ your details {% endcomment %}

<h2>Your details</h2>

<p class="muted">
  Optional, kept on this device, and remembered next time. Nothing here is
  sent to us.
</p>

<div class="field">
  <label for="profile-name">Name</label>
  <input type="text" id="profile-name" autocomplete="name" placeholder="Optional">
</div>

<div class="field">
  <label for="profile-reason">What brings you in?</label>
  <select id="profile-reason">
    <option value="">Not saying</option>
    {% for reason in ci.reasons %}
      <option value="{{ reason }}">{{ reason }}</option>
    {% endfor %}
  </select>
</div>

<div class="field">
  <label for="profile-note">Anything else</label>
  <input type="text" id="profile-note" placeholder="Optional">
</div>

{% comment %} ----------------------------------------------------- history {% endcomment %}

<h2>Your visits</h2>
<p class="muted" id="checkin-count"></p>
<p class="muted" id="checkin-empty" hidden>No visits recorded on this device yet.</p>
<ul class="rows rows-checkin" id="checkin-history"></ul>

<h2>This device</h2>

<p>
  This page keeps a list for you, on this device. There is no account and
  nothing is sent to us. The identifier below is a random number generated the
  first time you opened this page &mdash; it is not derived from your phone or
  from you, and deleting it deletes the list with it.
</p>

<p class="muted">
  Your list lives on this device only. Open the site on a different phone and
  it starts a fresh list; the two do not know about each other.
</p>

<ul class="rows">
  <li><b>Name</b> <span><input type="text" id="device-label" placeholder="My phone" autocomplete="off"></span></li>
  <li><b>Identifier</b> <span><code id="device-id"></code></span></li>
  <li><b>First used</b> <span id="device-since"></span></li>
</ul>

<h2>Keeping your history</h2>

<p class="muted" id="persist-state"></p>

<p>
  Browsers clear stored data. Safari does it after a stretch without a visit
  unless this page is on your Home Screen, and clearing your browsing data
  clears this too. If your visit history matters to you, save a copy.
</p>

<p class="hero-actions">
  <button class="btn" id="export-button" type="button">Save a copy</button>
  <label class="btn" for="import-input">Restore from a file</label>
  <input type="file" id="import-input" accept="application/json,.json" hidden>
</p>

<p class="muted" id="storage-status" role="status" aria-live="polite"></p>

<p>
  <button class="btn" id="forget-button" type="button">Forget this device</button>
</p>

<script src="{{ '/assets/js/checkin.js' | relative_url }}" defer></script>
