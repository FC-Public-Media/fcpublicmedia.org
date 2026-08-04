---
title: Authorize this device
lede: Set up the phone or laptop you'll use to manage your site.
---

{%- assign az = site.data.authorize -%}
{%- assign id = site.data.identity -%}

<script type="application/json" id="authorize-config">
{
  "issuer": {{ id.issuer | jsonify }},
  "keys": [
    {%- for key in id.keys -%}
      {"id": {{ key.id | jsonify }}, "x": {{ key.x | jsonify }}, "y": {{ key.y | jsonify }}}
      {%- unless forloop.last %},{% endunless -%}
    {%- endfor -%}
  ],
  "rpId": {{ az.rp_id | jsonify }},
  "brokerUrl": {{ az.url | jsonify }},
  "devicesPath": {{ az.devices_path | jsonify }},
  "writeMode": {{ az.write_mode | jsonify }}
}
</script>

<noscript>
  <p class="transaction transaction-todo">
    <b>This page needs JavaScript.</b>
    <span class="muted">Setting up a passkey happens entirely in your browser,
    so there is nothing for the page to do without it.</span>
  </p>
</noscript>

{% comment %} ------------------------------------------------------- states {% endcomment %}

{%- comment -%}
  Every state is a sibling panel toggled by authorize.js, the same pattern as
  the check-in page. Nothing is hidden behind a reload.
{%- endcomment -%}

<div class="state" data-state="checking" hidden>
  <p class="lede">Checking your link&hellip;</p>
</div>

{%- comment -%}
  Landing here with no link at all is the most likely wrong turn — someone
  finds the page in a footer or a search result. It should explain itself
  rather than look broken.
{%- endcomment -%}
<div class="state" data-state="no-link" hidden>
  <h2>You'll need the link we emailed you</h2>
  <p>
    This page sets up a device to manage a member site. It only works from the
    link we send &mdash; that link is what says which site you're setting up.
  </p>
  <p class="muted">
    Haven't got one, or it's expired? <a href="/contact/">Ask us</a> and we'll
    send another.
  </p>
</div>

<div class="state" data-state="bad-link" hidden>
  <h2>That link didn't work</h2>
  <p class="lede" id="bad-link-detail"></p>
  <p class="muted">
    <a href="/contact/">Ask us</a> for a new one &mdash; they're quick to send
    and they expire on purpose.
  </p>
</div>

<div class="state" data-state="ready" hidden>
  <p class="eyebrow">Setting up</p>
  <h2 id="ready-site"></h2>
  <p class="lede">
    Sent to <b id="ready-email"></b>.
  </p>

  <p>
    You're about to create a <b>passkey</b> on this device. Your phone or
    laptop keeps the private half in its own secure storage &mdash; we never
    see it, and it survives your browser clearing site data, which is the
    problem it solves.
  </p>

  <div class="field">
    <label for="device-name">Name this device</label>
    <input type="text" id="device-name" placeholder="My phone" autocomplete="off">
    <p class="muted">
      So you can tell it apart later. Anyone else set up on this site will see
      this name.
    </p>
  </div>

  <p>
    <button class="btn btn-primary btn-big" id="create-passkey" type="button">Create the passkey</button>
  </p>

  <p class="muted">
    Doing this on more than one device is fine and expected &mdash; open the
    same email on each. You can forward it to someone who works on the site
    with you, and they can set up their own.
  </p>
</div>

<div class="state" data-state="working" hidden>
  <p class="lede">Waiting for your device&hellip;</p>
  <p class="muted">Your phone or laptop should be asking you to confirm.</p>
</div>

<div class="state" data-state="cancelled" hidden>
  <h2>Nothing was set up</h2>
  <p>That's fine &mdash; the request was cancelled and nothing changed.</p>
  <p>
    <button class="btn" data-action="retry" type="button">Try again</button>
  </p>
</div>

<div class="state" data-state="unsupported" hidden>
  <h2>This browser can't make a passkey</h2>
  <p>
    Passkeys need a reasonably current browser. On a phone, opening the link in
    Safari or Chrome rather than inside another app's browser usually fixes it.
  </p>
  <p class="muted">
    Still stuck? <a href="/contact/">Tell us</a> and we'll sort it another way.
  </p>
</div>

<div class="state" data-state="error" hidden>
  <h2>That didn't work</h2>
  <p class="muted" id="error-detail"></p>
  <p>
    <button class="btn" data-action="retry" type="button">Try again</button>
  </p>
</div>

{%- comment -%}
  Sent — the broker took it. This is the state that does not exist yet.
{%- endcomment -%}
<div class="state" data-state="done" hidden>
  <p class="eyebrow">Done</p>
  <h2>This device is set up</h2>
  <p class="lede" id="done-detail"></p>
  <p class="muted">
    Next time you come to change something on your site, this device is how
    you'll prove it's you. Nothing to remember and nothing to type.
  </p>
</div>

{%- comment -%}
  No broker configured, which is the shipped state. The passkey is real and
  already made; what is missing is only the delivery. Showing the record and
  asking someone to send it is a genuine workflow for the first few members
  rather than a placeholder — so it is written as an instruction, not an
  apology.
{%- endcomment -%}
<div class="state" data-state="manual" hidden>
  <p class="eyebrow">Almost there</p>
  <h2>Send us this and you're done</h2>
  <p>
    Your passkey is made and stays on this device. We just need the public
    half, which is the text below. It's safe to send by email &mdash; it
    can't be used to pretend to be you.
  </p>

  <p class="hero-actions">
    <button class="btn btn-primary" id="copy-record" type="button">Copy it</button>
    <a class="btn" id="email-record" href="#">Email it to us</a>
  </p>

  <p class="muted" id="copy-status" role="status" aria-live="polite"></p>

  <pre class="code-block"><code id="device-record"></code></pre>

  <p class="muted">
    Keep this page open until you've sent it. Closing it doesn't delete the
    passkey, but you'd need a new link to see this text again.
  </p>
</div>

<script type="module" src="{{ '/assets/js/authorize.js' | relative_url }}"></script>
