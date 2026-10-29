---
title: Join
offline: true
---

{%- assign tiers = site.data.tiers.tiers -%}

## Don't Just View It. Do It.

Membership is a one-time cost for a year of membership, beginning today.
If you need a la carte reservations on the venue itself, please reach out to 
[{{ site.fcpm.email.info }}](mailto:{{ site.fcpm.email.info }}).

<fieldset class="tiers">
<legend class="visually-hidden">Choose a tier</legend>
<ul class="grid grid-4">
{% for tier in tiers %}
  {%- assign slug = tier.sku | remove_first: "membership:" -%}
  <li class="card tier">
    <input type="radio" name="tier" id="tier-{{ slug }}" value="{{ tier.sku }}"
           data-name="{{ tier.name }}" data-price="{{ tier.price }}"
           aria-labelledby="tier-{{ slug }}-name tier-{{ slug }}-price">
    <h3 id="tier-{{ slug }}-name">{{ tier.name }}</h3>
    <p class="price" id="tier-{{ slug }}-price">${{ tier.price }}</p>
    {%- if slug == "student" -%}
    <p class="student">Current Student ID required.</p>
    {%- endif -%}
    {%- if slug == "producer" -%}
    <p class="nonprofit">Nonprofits ${{
      tier.amount
        | times: site.fcpm.membership.nonprofit_rate
        | divided_by: 100
        | round
    }}.</p>
    {%- endif -%}
    <p class="muted">{{ site.fcpm.tiers[slug] | replace: ".", ".<br>" }}</p>
  </li>
{% endfor %}
</ul>
</fieldset>

{%- comment -%} Names are the site-worker's `membership` tank; join.js sends it, then Stripe's page for
  the tier picked above. See assets/js/join.js. {%- endcomment %}
<form class="join-form" data-tank="membership" data-checkout data-subject="Membership"
      data-worker="{{ site.data.site_worker.url }}" data-email="{{ site.fcpm.email.info }}">
  <div class="field-row">
    <div class="field"><label for="first_name">First</label><input id="first_name" name="first_name" autocomplete="given-name"></div>
    <div class="field"><label for="last_name">Last</label><input id="last_name" name="last_name" autocomplete="family-name"></div>
  </div>
  <div class="field-row">
    <div class="field"><label for="email">Email</label><input id="email" name="email" type="email" autocomplete="email"></div>
    <div class="field"><label for="phone">Phone</label><input id="phone" name="phone" type="tel" autocomplete="tel"></div>
  </div>
  <div class="field-row">
    <div class="field"><label for="address">Address</label><input id="address" name="address" autocomplete="street-address"></div>
    <div class="field" data-org-search data-list="{{ '/assets/nonprofits.json' }}">
      <label for="organization">Organization, if you're joining for one</label>
      <input id="organization" name="organization" autocomplete="organization" placeholder="Name search">
      <ul class="rows" data-org-results></ul>
      <p class="muted" data-org="many" hidden><span data-count></span> matches; keep typing to narrow it.</p>
      <p class="muted" data-org="chosen" hidden>Listed with the IRS as a 501(c)(3), EIN <span data-ein></span>.</p>
    </div>
  </div>
  <label class="check">
    <input type="checkbox" name="agree_terms" required>
    <span>I have read and agree to the <a href="{{ '/assets/docs/studio-terms.pdf' }}">Studio</a> and
      <a href="{{ '/assets/docs/equipment-terms.pdf' }}">Equipment</a> Terms and Conditions.</span>
  </label>
  <label class="check">
    <input type="checkbox" name="submit_terms" required>
    <span>I understand the public media <a href="/submit/">Submission</a> requirements.</span>
  </label>

  <!--<details class="join-more">
    <summary>Your production experience, if you like</summary>
    <fieldset class="checks">
      <legend>Any media production experience?</legend>
      <label class="check"><input type="checkbox" name="experience" value="Producing" data-list><span>Producing</span></label>
      <label class="check"><input type="checkbox" name="experience" value="Directing" data-list><span>Directing</span></label>
      <label class="check"><input type="checkbox" name="experience" value="Technical Directing" data-list><span>Technical Directing</span></label>
      <label class="check"><input type="checkbox" name="experience" value="Audio Board" data-list><span>Audio Board</span></label>
      <label class="check"><input type="checkbox" name="experience" value="Studio Camera" data-list><span>Studio Camera</span></label>
      <label class="check"><input type="checkbox" name="experience" value="Field Production" data-list><span>Field Production</span></label>
      <label class="check"><input type="checkbox" name="experience" value="Set Design" data-list><span>Set Design</span></label>
      <label class="check"><input type="checkbox" name="experience" value="Lighting" data-list><span>Lighting</span></label>
      <label class="check"><input type="checkbox" name="experience" value="Editing" data-list><span>Editing</span></label>
      <label class="check"><input type="checkbox" name="experience" value="On-Air Talent" data-list><span>On-Air Talent</span></label>
      <label class="check"><input type="checkbox" name="experience" value="Still Photography" data-list><span>Still Photography</span></label>
      <label class="check"><input type="checkbox" name="experience" value="Podcasting" data-list><span>Podcasting</span></label>
      <label class="check"><input type="checkbox" name="experience" value="Other" data-list><span>Other</span></label>
    </fieldset>
    <div class="field"><label for="experience_other">Other experience</label><input id="experience_other" name="experience_other"></div>
    <fieldset class="checks">
      <legend>Where?</legend>
      <label class="check"><input type="checkbox" name="experience_where" value="Home Equipment" data-list><span>Home Equipment</span></label>
      <label class="check"><input type="checkbox" name="experience_where" value="Other Access Facilities" data-list><span>Other Access Facilities</span></label>
      <label class="check"><input type="checkbox" name="experience_where" value="Corporate Communications Company" data-list><span>Corporate Communications Company</span></label>
      <label class="check"><input type="checkbox" name="experience_where" value="Video Production Company" data-list><span>Video Production Company</span></label>
      <label class="check"><input type="checkbox" name="experience_where" value="School and/or College" data-list><span>School and/or College</span></label>
      <label class="check"><input type="checkbox" name="experience_where" value="Other" data-list><span>Other</span></label>
    </fieldset>
    <div class="field"><label for="experience_where_other">Other places</label><input id="experience_where_other" name="experience_where_other"></div>
    <div class="field"><label for="heard_from">How did you hear about us?</label><input id="heard_from" name="heard_from"></div>
  </details>-->

  <div class="trap" aria-hidden="true"><label for="website">Website</label><input id="website" name="website" tabindex="-1" autocomplete="off"></div>

  <p class="hero-actions">
    <button class="btn btn-primary" type="submit" data-pay>Join and pay with Stripe</button>
    <button class="btn" type="button" data-keep>I represent a nonprofit or cannot complete payment in advance</button>
  </p>
  <div class="muted" role="status" aria-live="polite">
    <p data-say="pick-tier" hidden>Pick a tier first.</p>
    <p data-say="opening" hidden>Opening the payment page…</p>
    <p data-say="sending" hidden>Sending…</p>
    <p data-say="empty" hidden>Nothing is filled in yet.</p>
    <p data-say="unsent" hidden>Joining can't take payment online yet. <a data-mailto href="#">Email this to us</a>; it's all filled in, and a person will sort out paying with you. It's kept on this phone too, under <a href="{{ '/you/' | relative_url }}">Yours</a>.</p>
    <p data-say="unpaid-kept" hidden>The payment page couldn't open. We have your answers and the tier you picked, and a person will write to you about paying.</p>
    <p data-say="unpaid" hidden>The payment page couldn't open. <a data-mailto href="#">Email this to us</a>; it's all filled in. It's kept on this phone too, under <a href="{{ '/you/' | relative_url }}">Yours</a>.</p>
    <p data-say="failed" hidden>That didn't send. <a data-mailto href="#">Email this to us</a>; it's all filled in. It's kept on this phone too, under <a href="{{ '/you/' | relative_url }}">Yours</a>.</p>
  </div>
</form>
<div data-receipt="sent" tabindex="-1" hidden>
  <p><b>Received.</b> Reference <code data-reference></code>. A person will write to you about paying.</p>
</div>
<div data-receipt="joined" tabindex="-1" hidden>
  <p><b>Thank you for joining.</b> Your payment went through, and Stripe is emailing you a receipt. A person will be in touch about your membership.</p>
</div>

<script type="module" src="{{ '/assets/js/nonprofit.js' }}?v={{ site.time | date: '%s' }}"></script>
<script type="module" src="{{ '/assets/js/tiers.js' }}?v={{ site.time | date: '%s' }}"></script>
<script type="module" src="{{ '/assets/js/join.js' }}?v={{ site.time | date: '%s' }}"></script>
