---
title: Yours
layout: pass
theme_color: "#121417"
permalink: /you/
sitemap: false
---

{%- comment -%} What this device keeps for its person: every form's reply (kept before it is sent) and the contact
cards noticed in them. Nothing here is sent unless they say so. assets/js/yours.js; docs/identity.md#yours.
Views by #: (none) the list, #reply-<reference>, #show-<reference>. {%- endcomment %}

<noscript>
  <p class="transaction transaction-todo"><b>This page needs JavaScript.</b>
  <span class="muted">Everything on it is kept by your browser, not by us.</span></p>
</noscript>

{% comment %} ---------------------------------------------------------- list {% endcomment %}

<section class="pass-view" data-view="list" aria-labelledby="yours-title">
  <header class="pass-top">
    <a class="pass-back" href="{{ '/check-in/' | relative_url }}">Pass</a>
    <h2 id="yours-title">Yours</h2>
  </header>
  <div class="pass-scroll">
    <h3>Sent and kept</h3>
    <p class="muted" id="replies-empty" hidden>Nothing yet. Anything you send from a form here is kept on this
      phone first, and stays here.</p>
    <ul class="rows rows-yours" id="replies"></ul>

    <h3>Contact cards</h3>
    <p class="muted" id="cards-empty" hidden>None yet. A name, email or phone you type into one of our forms
      is noticed here, for you. It goes nowhere.</p>
    <ul class="rows rows-yours" id="cards"></ul>

    <p class="pass-actions">
      <a class="btn" href="{{ '/check-in/#visits' | relative_url }}">Visits</a>
      <a class="btn" href="{{ '/check-in/#device' | relative_url }}">This phone</a>
    </p>
  </div>
</section>

{% comment %} --------------------------------------------------------- reply {% endcomment %}

<section class="pass-view" data-view="reply" aria-labelledby="reply-title" hidden>
  <header class="pass-top">
    <a class="pass-back" href="#" data-back>Yours</a>
    <h2 id="reply-title"></h2>
  </header>
  <div class="pass-scroll">
    <p class="muted" id="reply-state"></p>
    <ul class="rows" id="reply-lines"></ul>
    <p class="pass-actions">
      <a class="btn btn-primary" id="reply-show" href="#">Show it</a>
      <button class="btn" id="reply-send" type="button" hidden>Send it</button>
      <a class="btn" id="reply-email" href="#" hidden>Email it</a>
      <button class="btn" id="reply-drop" type="button">Delete</button>
    </p>
    <p class="muted" id="reply-said" role="status" aria-live="polite"></p>
  </div>
</section>

{% comment %} ---------------------------------------------------------- show {% endcomment %}

<section class="pass-view" data-view="show" aria-labelledby="show-title" hidden>
  <header class="pass-top">
    <a class="pass-back" href="#" data-back>Back</a>
    <h2 id="show-title">Show it</h2>
  </header>
  <div class="pass-show">
    <div class="pass-code"><canvas id="show-code" role="img" aria-label="Your reply, as a moving code for our camera"></canvas></div>
    <p id="show-what"></p>
    <p class="pass-read" id="show-read"></p>
  </div>
</section>

<script type="module" src="{{ '/assets/js/yours.js' }}?v={{ site.time | date: '%s' }}"></script>
