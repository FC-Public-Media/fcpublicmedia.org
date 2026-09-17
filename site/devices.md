---
title: Devices
lede: See which phones and laptops can manage your site, and approve or remove them.
---

{%- assign az = site.data.authorize -%}

{%- comment -%}
  The page that makes "approve once, publish every week" a thing somebody can
  actually do. Without it, adding a co-producer's phone means asking staff,
  which is the loop the whole design is trying to leave.

  Deliberately reachable without a link. Someone who already manages a site
  should be able to come here and look, and the sign-in tells the page which
  site they mean — the passkey carries it.
{%- endcomment -%}

<script type="application/json" id="devices-config">
{
  "rpId": {{ az.rp_id | jsonify }},
  "brokerUrl": {{ az.url | jsonify }},
  "devicesPath": {{ az.devices_path | jsonify }}
}
</script>

<noscript>
  <p class="transaction transaction-todo">
    <b>This page needs JavaScript.</b>
    <span class="muted">Signing in with a passkey happens in your browser.
    <a href="/contact/">Ask us</a> and we'll make the change for you.</span>
  </p>
</noscript>

<div class="state" data-state="signed-out" hidden>
  <h2>Sign in with your device</h2>
  <p>Use the passkey you already set up. Nothing to type.</p>
  <p><button class="btn btn-primary btn-big" id="sign-in" type="button">Sign in</button></p>
  <p class="muted">
    Setting up a new device instead? That starts from the link we email you
    &mdash; <a href="/contact/">ask us</a> for one.
  </p>
</div>

<div class="state" data-state="unsupported" hidden>
  <h2>This browser can't use passkeys</h2>
  <p>On a phone, opening this in Safari or Chrome rather than inside another
  app's browser usually fixes it.</p>
  <p class="muted"><a href="/contact/">Tell us</a> and we'll make the change for you.</p>
</div>

<div class="state" data-state="sign-in-failed" hidden>
  <h2>That didn't sign you in</h2>
  <p class="muted" id="sign-in-detail"></p>
  <p><button class="btn" data-action="retry" type="button">Try again</button></p>
</div>

<div class="state" data-state="loading" hidden>
  <p class="lede">Fetching your devices&hellip;</p>
</div>

<div class="state" data-state="load-failed" hidden>
  <h2>Couldn't read your device list</h2>
  <p class="muted" id="load-detail"></p>
  <p><button class="btn" data-action="reload" type="button">Try again</button></p>
</div>

<div class="state" data-state="listing" hidden>
  <p class="eyebrow">Signed in</p>
  <h2 id="devices-site"></h2>

  {%- comment -%}
    Two lists rather than one, because "waiting for you" is a job and
    "already fine" is not. A single list sorted by status buries the only row
    anybody came here to act on.
  {%- endcomment -%}
  <div id="waiting-section" hidden>
    <h3>Waiting for you</h3>
    <p class="muted">
      These devices are registered but can't change anything yet. Approving one
      means it can publish to this site from now on &mdash; that's the point of
      doing it once rather than every week.
    </p>
    <ul class="rows" id="waiting-list"></ul>
  </div>

  <h3>Can publish</h3>
  <ul class="rows" id="allowed-list"></ul>
  {%- comment -%}
    A property of the list, not a result of anything you did — so it has its
    own line. Sharing one with the status below meant a redraw wiped the
    confirmation of whatever you had just done.
  {%- endcomment -%}
  <p class="muted" id="allowed-note"></p>

  <p class="muted" id="devices-status" role="status" aria-live="polite"></p>

  <p class="muted">
    Adding someone? Send them the link we email you and they can set their own
    device up &mdash; it'll appear here for you to approve.
  </p>
</div>

<div class="state" data-state="manual" hidden>
  <p class="eyebrow">Almost there</p>
  <h2>Ask us to make this change</h2>
  <p>We can't do it for you from here yet.</p>
  <p class="muted" id="manual-detail"></p>
  <p class="hero-actions">
    <a class="btn btn-primary" id="email-change" href="#">Email us</a>
    <button class="btn" data-action="reload" type="button">Back</button>
  </p>
</div>

<script type="module" src="{{ '/assets/js/devices.js' | relative_url }}?v={{ site.time | date: '%s' }}"></script>
