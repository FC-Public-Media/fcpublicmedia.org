---
title: Your site's settings
lede: Sign in with the device you set up, and edit your settings file directly.
---

{%- assign st = site.data.settings -%}

<script type="application/json" id="settings-config">
{
  "rpId": {{ st.rp_id | jsonify }},
  "brokerUrl": {{ st.url | jsonify }},
  "path": {{ st.path | jsonify }}
}
</script>

<noscript>
  <p class="transaction transaction-todo">
    <b>This page needs JavaScript.</b>
    <span class="muted">Signing in with a passkey happens in your browser.
    You can also edit the file directly on GitHub if you have an account
    there, which does the same thing.</span>
  </p>
</noscript>

{% comment %} ------------------------------------------------------- states {% endcomment %}

<div class="state" data-state="signed-out" hidden>
  <h2>Sign in with your device</h2>
  <p>
    Use the passkey you set up when we sent you a link. Nothing to type.
  </p>
  <p>
    <button class="btn btn-primary btn-big" id="sign-in" type="button">Sign in</button>
  </p>
  <p class="muted">
    Never set one up, or on a new device? <a href="/contact/">Ask us</a> for a
    link.
  </p>
</div>

<div class="state" data-state="unsupported" hidden>
  <h2>This browser can't use passkeys</h2>
  <p>
    On a phone, opening this in Safari or Chrome rather than inside another
    app's browser usually fixes it.
  </p>
  <p class="muted"><a href="/contact/">Tell us</a> and we'll make the change for you.</p>
</div>

<div class="state" data-state="sign-in-failed" hidden>
  <h2>That didn't sign you in</h2>
  <p class="muted" id="sign-in-detail"></p>
  <p><button class="btn" data-action="retry" type="button">Try again</button></p>
  <p class="muted"><a href="/contact/">Ask us</a> if this device has never been set up.</p>
</div>

<div class="state" data-state="loading" hidden>
  <p class="lede">Fetching your settings&hellip;</p>
</div>

<div class="state" data-state="load-failed" hidden>
  <h2>Couldn't read your settings</h2>
  <p class="muted" id="load-detail"></p>
  <p><button class="btn" data-action="reload" type="button">Try again</button></p>
</div>

{% comment %} -------------------------------------------------------- editor {% endcomment %}

<div class="state" data-state="editing" hidden>
  <p class="eyebrow">Signed in</p>
  <h2 id="editing-site"></h2>

  {%- comment -%}
    The file is shown whole, comments and all, because those comments are the
    only documentation a member has for what these settings do. A form would
    strip them on the first save. See _data/settings.yml.
  {%- endcomment -%}
  <p>
    This is your <code id="editing-path"></code>, exactly as it is on your
    site. The lines starting with <code>#</code> are notes explaining what each
    setting does &mdash; they're part of the file, so leave them in unless
    they've stopped being true.
  </p>

  <div class="field">
    <label for="settings-text">Settings file</label>
    <textarea id="settings-text" rows="24" spellcheck="false"
              autocapitalize="none" autocomplete="off" wrap="off"></textarea>
  </div>

  <p class="muted" id="settings-checks" role="status" aria-live="polite"></p>

  <p class="hero-actions">
    <button class="btn btn-primary btn-big" id="settings-save" type="button">Save changes</button>
    <button class="btn" id="settings-revert" type="button">Undo my edits</button>
  </p>

  <p class="muted" id="settings-status" role="status" aria-live="polite"></p>

  <p class="muted">
    Indentation matters in this format, and tabs aren't allowed &mdash; use
    spaces. If something's wrong we'll tell you rather than publishing it.
  </p>
</div>

{% comment %} ------------------------------------------------------- results {% endcomment %}

<div class="state" data-state="saved" hidden>
  <p class="eyebrow">Saved</p>
  <h2>That's gone through</h2>
  <p class="lede" id="saved-detail"></p>
  <p class="hero-actions">
    <button class="btn" data-action="reload" type="button">Keep editing</button>
    {%- comment -%}
      Where the change went. On the default branch mode that is a pull request
      with the checks running on it — worth being able to look at, because "we
      are checking it" is easier to believe when you can see the thing.
    {%- endcomment -%}
    <a class="btn" id="saved-link" href="#" hidden>See the change</a>
  </p>
</div>

<div class="state" data-state="manual" hidden>
  <p class="eyebrow">Almost there</p>
  <h2>Send us this</h2>
  <p>
    We can't save it for you from here yet. Copy the file below and send it
    over &mdash; we'll put it in place.
  </p>

  <p class="hero-actions">
    <button class="btn btn-primary" id="copy-settings" type="button">Copy it</button>
    <a class="btn" id="email-settings" href="#">Email it to us</a>
    <button class="btn" data-action="retry" type="button">Back to editing</button>
  </p>

  <p class="muted" id="copy-status" role="status" aria-live="polite"></p>

  <pre class="code-block"><code id="settings-output"></code></pre>
</div>

<script type="module" src="{{ '/assets/js/settings.js' | relative_url }}?v={{ site.time | date: '%s' }}"></script>
