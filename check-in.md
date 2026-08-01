---
title: Check In
lede: Scan, tap once, and your visit is recorded on your own phone.
---

{%- assign ci = site.data.checkin -%}

<script type="application/json" id="checkin-config">
{
  "identityMode": {{ ci.identity.mode | jsonify }},
  "historyLimit": {{ ci.history_limit | default: 200 }}
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

<p class="transaction transaction-todo" id="checkin-unavailable" hidden>
  <b>Your browser is not allowing this page to save anything.</b>
  <span class="muted">That usually means private browsing. Check-ins are
  stored on your device, so there is nowhere to put them. Please use the
  paper log.</span>
</p>

<div id="checkin-app" hidden>

  <p>
    <button class="btn btn-primary" id="checkin-button" type="button">I'm here</button>
  </p>
  <p class="muted" id="checkin-status" role="status" aria-live="polite"></p>

  {% if ci.identity.mode == "none" %}
    <p class="muted">{{ ci.identity.anonymous_note | strip_newlines | strip }}</p>
  {% endif %}

  <h2>Your visits</h2>
  <p class="muted" id="checkin-count"></p>
  <p class="muted" id="checkin-empty" hidden>No visits recorded on this device yet.</p>
  <ul class="rows rows-checkin" id="checkin-history"></ul>

  <h2>This device</h2>

  <p>
    This page keeps a list for you, on this device. Nothing is sent to us and
    there is no account. The identifier below is a random number generated the
    first time you opened this page — it is not derived from your phone or from
    you, and deleting it deletes the list with it.
  </p>

  <ul class="rows">
    <li><b>Name</b> <span><input type="text" id="device-label" placeholder="My phone" autocomplete="off"></span></li>
    <li><b>Identifier</b> <span><code id="device-id"></code></span></li>
    <li><b>First used</b> <span id="device-since"></span></li>
  </ul>

  <h2>Keeping your history</h2>

  <p>
    <b>Browsers delete this.</b> Safari removes stored data after about a week
    without a visit unless this page has been added to your Home Screen, and
    clearing your browsing data clears this too. If your visit history matters
    to you, save a copy.
  </p>

  <p class="hero-actions">
    <button class="btn" id="export-button" type="button">Save a copy</button>
    <label class="btn" for="import-input">Restore from a file</label>
    <input type="file" id="import-input" accept="application/json,.json" hidden>
  </p>

  <p>
    <button class="btn" id="forget-button" type="button">Forget this device</button>
  </p>

</div>

<script src="{{ '/assets/js/checkin.js' | relative_url }}" defer></script>
