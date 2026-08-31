---
title: Submit an episode
lede: Sign in with the device you set up, describe the episode, and tell us where the file is.
---

{%- assign up = site.data.upload -%}

<script type="application/json" id="upload-config">
{
  "rpId": {{ up.rp_id | jsonify }},
  "brokerUrl": {{ up.url | jsonify }},
  "programsPath": {{ up.programs_path | jsonify }},
  "destination": {{ up.destination | jsonify }},
  "timezone": {{ up.timezone | jsonify }},
  "defaultTime": {{ up.default_time | jsonify }}
}
</script>

<noscript>
  <p class="transaction transaction-todo">
    <b>This page needs JavaScript.</b>
    <span class="muted">Signing in with a passkey happens in your browser, so
    there is nothing for the page to do without it.
    <a href="/contact/">Get in touch</a> and we'll take the details
    directly.</span>
  </p>
</noscript>

{% comment %} ------------------------------------------------------- states {% endcomment %}

<div class="state" data-state="checking" hidden>
  <p class="lede">Checking this device&hellip;</p>
</div>

<div class="state" data-state="signed-out" hidden>
  <h2>Sign in with your device</h2>
  <p>
    Use the passkey you set up when we sent you a link. Your phone or laptop
    will ask you to confirm &mdash; there is nothing to type and no password.
  </p>
  <p>
    <button class="btn btn-primary btn-big" id="sign-in" type="button">Sign in</button>
  </p>
  <p class="muted">
    Never set one up, or using a new device? <a href="/contact/">Ask us</a> and
    we'll email a link that takes a minute.
  </p>
</div>

<div class="state" data-state="unsupported" hidden>
  <h2>This browser can't use passkeys</h2>
  <p>
    On a phone, opening this page in Safari or Chrome rather than inside
    another app's browser usually fixes it.
  </p>
  <p class="muted">
    Otherwise <a href="/contact/">tell us what you've got</a> and we'll take
    the details another way. Nothing here is mandatory.
  </p>
</div>

<div class="state" data-state="sign-in-failed" hidden>
  <h2>That didn't sign you in</h2>
  <p class="muted" id="sign-in-detail"></p>
  <p>
    <button class="btn" data-action="retry" type="button">Try again</button>
  </p>
  <p class="muted">
    If this device has never been set up, <a href="/contact/">ask us</a> for a
    link rather than fighting with it.
  </p>
</div>

{% comment %} --------------------------------------------------------- form {% endcomment %}

<div class="state" data-state="ready" hidden>
  <p class="eyebrow">Signed in</p>
  <h2 id="ready-site"></h2>
  <p class="muted">
    Submitting to your own site. <button class="btn-link" id="sign-out" type="button">Not you?</button>
  </p>

  <div class="field">
    <label for="ep-title">Title</label>
    <input type="text" id="ep-title" autocomplete="off" placeholder="What this episode is called">
  </div>

  <div class="field">
    <label for="ep-summary">What's it about</label>
    <textarea id="ep-summary" rows="3" placeholder="A few sentences."></textarea>
    <p class="muted">
      This is what a stranger reads before deciding whether to watch, so it's
      worth writing properly.
    </p>
  </div>

  <div class="field-row">
    <div class="field">
      <label for="ep-date">Drop date</label>
      <input type="date" id="ep-date">
    </div>
    <div class="field">
      <label for="ep-time">Time</label>
      <input type="time" id="ep-time">
    </div>
    <div class="field">
      <label for="ep-runtime">Runtime</label>
      <input type="text" id="ep-runtime" placeholder="24:10" inputmode="numeric">
    </div>
  </div>

  <p class="muted">
    {%- comment -%}
      The offset is computed for Colorado rather than for wherever the member
      is sitting, so a producer submitting from a hotel in another zone does
      not schedule their own episode an hour out. Shown so it is checkable.
    {%- endcomment -%}
    Saved as <code id="ep-iso">&mdash;</code>
  </p>

  <h3>The file</h3>

  {%- comment -%}
    There is nowhere to upload to yet, so the picker reads the file rather
    than sending it — name, size and type fill in the record, and the member
    is told plainly to send the file the way they already do. When a
    destination is configured this same control becomes the real upload.
  {%- endcomment -%}
  <div class="field">
    <label for="ep-file">Pick the finished file</label>
    <input type="file" id="ep-file" accept="video/*,audio/*">
    <p class="muted" id="ep-file-detail"></p>
  </div>

  <div class="field">
    <label for="ep-path">Or where it already is</label>
    <input type="text" id="ep-path" autocomplete="off"
           placeholder="/Programs/2026/my-episode.mov">
    <p class="muted">
      A path in the shared folder is enough. <b>Not a share link</b> &mdash; a
      path reaches nobody without our credentials, and a share link is a
      download anyone can use.
    </p>
  </div>

  <p class="transaction transaction-todo" data-no-destination hidden>
    <b>We can't take the file itself here yet.</b>
    <span class="muted">{{ up.fallback_note | strip_newlines | strip }}</span>
  </p>

  <p>
    <button class="btn btn-primary btn-big" id="ep-submit" type="button">Prepare submission</button>
  </p>
  <p class="muted" id="ep-error" role="status" aria-live="polite"></p>
</div>

{% comment %} ------------------------------------------------------- results {% endcomment %}

<div class="state" data-state="done" hidden>
  <p class="eyebrow">Sent</p>
  <h2>We've got it</h2>
  <p class="lede" id="done-detail"></p>
</div>

<div class="state" data-state="manual" hidden>
  <p class="eyebrow">Almost there</p>
  <h2>Send us this</h2>
  <p>
    This is your episode as an entry for your site. Copy it to us and we'll add
    it &mdash; and send the file itself however you normally do.
  </p>

  <p class="hero-actions">
    <button class="btn btn-primary" id="copy-entry" type="button">Copy it</button>
    <a class="btn" id="email-entry" href="#">Email it to us</a>
    <button class="btn" data-action="retry" type="button">Change something</button>
  </p>

  <p class="muted" id="copy-status" role="status" aria-live="polite"></p>

  <pre class="code-block"><code id="entry-yaml"></code></pre>

  <p class="muted">
    Once your site has this entry, it appears in your feed with its drop date
    &mdash; and that is what puts it on
    <a href="/meet/">the Meet page</a> as coming up.
  </p>
</div>

<script type="module" src="{{ '/assets/js/upload.js' | relative_url }}?v={{ site.time | date: '%s' }}"></script>
