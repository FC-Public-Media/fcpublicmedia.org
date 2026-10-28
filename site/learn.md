---
title: Learn
---

{%- comment -%} The page's reading on the left; teaching, and its application, on the right from the top. {%- endcomment %}
<div class="split">
<div class="split-main" markdown="1">

## Classes

[{{ site.fcpm.email.education }}](mailto:{{ site.fcpm.email.education }})

**Next:** _TBD_

## Before Now

If you missed a prior topic, let's do it again!

- Digital Cinematography
- Camera Operation Basics
- Audio Training 101
- Lighting Basics
- Social Media Marketing
- Introductory Screenwriting
- Adobe Premiere for Beginners
- Adobe Photoshop for Beginners
- Adobe Lightroom for Beginners
- Podcasting Basics
- Podcasting Development
- Podcasting Production

</div>
<aside class="split-side" aria-labelledby="teaching-at-fc-public-media">
<h2 id="teaching-at-fc-public-media">Teaching at FC Public Media</h2>
<div markdown="1">

Do you know things that others should too? We are able to pay {{ site.fcpm.classes.rate }} for about 2 hours. We can provide copies of printouts and a portrait roller screen with your materials.

Got a LOT to teach? Starting a student or youth series? Want it recorded? Reach out to [{{ site.fcpm.email.info }}](mailto:{{ site.fcpm.email.info }}) to discuss how we can bring in your audience!

</div>

{%- comment -%} Names are the site-worker's `instructor` tank; assets/js/answers.js sends it. Only email is
  required: it is how we write back. Who someone is gets sorted out on our side, never theirs. {%- endcomment %}
<form data-tank="instructor" data-subject="Instructor application"
      data-worker="{{ site.data.site_worker.url }}" data-email="{{ site.fcpm.email.info }}">
  <div class="field-row">
    <div class="field"><label for="t-first">First</label><input id="t-first" name="first_name" autocomplete="given-name"></div>
    <div class="field"><label for="t-last">Last</label><input id="t-last" name="last_name" autocomplete="family-name"></div>
  </div>
  <div class="field-row">
    <div class="field"><label for="t-email">Email</label><input id="t-email" name="email" type="email" autocomplete="email" required></div>
    <div class="field"><label for="t-phone">Phone</label><input id="t-phone" name="phone" type="tel" autocomplete="tel"></div>
  </div>
  <div class="field-row">
    <fieldset class="checks checks-inline">
      <legend>Teaching so far</legend>
      <label class="check"><input type="checkbox" id="t-first-time" name="first_time" value="Yes"><span>This would be my first time</span></label>
    </fieldset>
    <fieldset class="checks checks-inline">
      <legend>In person or online?</legend>
      <label class="check"><input type="radio" name="in_person_virtual" value="In person"><span>In person</span></label>
      <label class="check"><input type="radio" name="in_person_virtual" value="Online"><span>Online</span></label>
      <label class="check"><input type="radio" name="in_person_virtual" value="Both"><span>Both</span></label>
    </fieldset>
  </div>
  <div class="field-row">
    <div class="field"><label for="t-topics">What you'd teach</label><textarea id="t-topics" name="topics" rows="3"></textarea></div>
    <div class="field"><label for="t-why">Why FCPM?</label><textarea id="t-why" name="why" rows="3"></textarea></div>
  </div>
  <div class="field-row">
    <div class="field"><label for="t-years">Years teaching</label><textarea id="t-years" name="years_experience" rows="3"></textarea></div>
    <div class="field"><label for="t-where">Where you've taught</label><textarea id="t-where" name="taught_where" rows="3"></textarea></div>
  </div>
  <div class="field-row">
    <fieldset class="checks checks-inline">
      <legend>Times</legend>
        <label class="check"><input type="checkbox" name="times" value="Morning" data-list><span>Morning</span></label>
        <label class="check"><input type="checkbox" name="times" value="Afternoon" data-list><span>Afternoon</span></label>
        <label class="check"><input type="checkbox" name="times" value="Evening" data-list><span>Evening</span></label>
    </fieldset>
    <fieldset class="checks checks-inline">
      <legend>Days</legend>
        <label class="check"><input type="checkbox" name="days" value="Monday" data-list><span>Monday</span></label>
        <label class="check"><input type="checkbox" name="days" value="Tuesday" data-list><span>Tuesday</span></label>
        <label class="check"><input type="checkbox" name="days" value="Wednesday" data-list><span>Wednesday</span></label>
        <label class="check"><input type="checkbox" name="days" value="Thursday" data-list><span>Thursday</span></label>
        <label class="check"><input type="checkbox" name="days" value="Friday" data-list><span>Friday</span></label>
        <label class="check"><input type="checkbox" name="days" value="Saturday" data-list><span>Saturday</span></label>
        <label class="check"><input type="checkbox" name="days" value="Sunday" data-list><span>Sunday</span></label>
    </fieldset>
  </div>
  <div class="field"><label for="t-notes">Anything else?</label><textarea id="t-notes" name="notes" rows="2"></textarea></div>

  <div class="trap" aria-hidden="true"><label for="t-website">Website</label><input id="t-website" name="website" tabindex="-1" autocomplete="off"></div>

  <p><button class="btn btn-primary" type="submit">Apply to teach</button></p>
  <div class="muted" role="status" aria-live="polite">
    <p data-say="sending" hidden>Sending…</p>
    <p data-say="unsent" hidden>This form can't send on its own yet. <a data-mailto href="#">Email it to us</a> instead; it's all filled in.</p>
    <p data-say="failed" hidden>That didn't send. <a data-mailto href="#">Email it to us</a> instead; it's all filled in.</p>
  </div>
</form>
<div data-receipt="sent" tabindex="-1" hidden>
  <p><b>Received.</b> Reference <code data-reference></code>. We'll write back.</p>
</div>
</aside>
</div>

<script type="module" src="{{ '/assets/js/answers.js' }}?v={{ site.time | date: '%s' }}"></script>
