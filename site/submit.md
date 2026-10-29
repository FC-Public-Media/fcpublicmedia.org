---
title: Submit
---

<div class="split">
<div class="split-main" markdown="1">

## Acceptance

Media will broadcast to **Comcast 97**, **Connexion 22**, **Roku**, **AppleTV**, **YouTube**, the **{{ site.title }} website** and associated **cablecast.tv** outlet.

Submissions must:

1. be accompanied by the completed form.
1. be released for broadcast by the copyright manager's permission.
2. be "HD" (720p or better).
3. be uploaded to our Dropbox.

## Disclaimers

Member-made media is not the opinion of staff or technology vendors.

Submissions must:

1. **not** be a vehicle for a <u>call to action</u>.
2. **not** be <u>primarily advertising</u>.
3. **not** be <u>paid political endorsement</u> in other media.
3. **not** be libelous, slanderous or defamatory, that is an unlawful invasion of privacy or violates state, federal or copyright laws.

Media that is offensive or inappropriate for unsolicited or underage viewing should present a discretion disclaimer, such as:

> The following program contains material that may be offensive to some viewers or inappropriate for viewing by children. Viewer discretion is advise.

</div>
<aside class="split-side" aria-labelledby="submit">
<h2 id="submit">Submit</h2>

<a class="dropbox" href="https://www.dropbox.com/request/ex9K5a8TvCI8SrFRy8Vz" target="_blank" rel="noopener">
  <b>Open our Dropbox</b>
</a>

{%- comment -%} Names are the site-worker's `program` tank. See assets/js/answers.js. {%- endcomment %}
<form data-tank="program" data-subject="Program submission"
      data-worker="{{ site.data.site_worker.url }}" data-email="{{ site.fcpm.email.info }}">
  <label class="check">
    <input type="checkbox" name="copyright" required>
    <span>I consent and am authorized to release this media for broadcast.</span>
  </label>
  <label class="check">
    <input type="checkbox" name="uploaded">
    <span>I have confirmed the success of my upload.</span>
  </label>

  <div class="field-row">
    <div class="field"><label for="first_name">First</label><input id="first_name" name="first_name" autocomplete="given-name"></div>
    <div class="field"><label for="last_name">Last</label><input id="last_name" name="last_name" autocomplete="family-name"></div>
  </div>
  <div class="field-row">
    <div class="field"><label for="email">Email</label><input id="email" name="email" type="email" autocomplete="email" required></div>
    <div class="field"><label for="phone">Phone</label><input id="phone" name="phone" type="tel" autocomplete="tel"></div>
  </div>
  <div class="field-row">
    <div class="field"><label for="title">Title</label><input id="title" name="title"></div>
    <div class="field">
      <label for="category">Category</label>
      <select id="category" name="category">
        <option value=""></option>
        <option>Art &amp; Literature</option>
        <option>Classic Films Show</option>
        <option>Comedy</option>
        <option>Film &amp; Animation</option>
        <option>Food &amp; Drink</option>
        <option>Gaming</option>
        <option>Music</option>
        <option>News &amp; Information</option>
        <option>Non-Profit Awareness</option>
        <option>Sports</option>
        <option>Theatre &amp; Dance</option>
        <option>Other</option>
      </select>
    </div>
  </div>
  <div class="field"><label for="description">Description &amp; credits</label><textarea id="description" name="description" rows="5"></textarea></div>
  <div class="field"><label for="schedule">Scheduling (optional)</label><textarea id="schedule" name="schedule" rows="3"></textarea></div>

  <div class="trap" aria-hidden="true"><label for="website">Website</label><input id="website" name="website" tabindex="-1" autocomplete="off"></div>

  <p><button class="btn btn-primary" type="submit">Submit</button></p>
  <div class="muted" role="status" aria-live="polite">
    <p data-say="sending" hidden>Sending…</p>
    <p data-say="unsent" hidden>This form can't send on its own yet. <a data-mailto href="#">Email it to us</a> instead; it's all filled in. It's kept on this phone too, under <a href="{{ '/you/' | relative_url }}">Yours</a>.</p>
    <p data-say="failed" hidden>That didn't send. <a data-mailto href="#">Email it to us</a> instead; it's all filled in. It's kept on this phone too, under <a href="{{ '/you/' | relative_url }}">Yours</a>.</p>
  </div>
</form>
<div data-receipt="sent" tabindex="-1" hidden>
  <p><b>Received.</b> Reference <code data-reference></code>.</p>
</div>
</aside>
</div>

<script type="module" src="{{ '/assets/js/answers.js' }}?v={{ site.time | date: '%s' }}"></script>
