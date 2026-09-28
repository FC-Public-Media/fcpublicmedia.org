/* dim.js -- every studio screen falls to dim when nobody is meant to be here.

   docs/SCREENS-DIM.md is the plan. In short:

   AWAKE comes from the door. window.FCPM_AWAKE is [[startMs, endMs], ...]:
   host shifts and classes, each from an hour before, for a week ahead.
   page() bakes it in; the kiosk and depot pages hand in fresh ones through
   window.fcpmAwake(), which fires `fcpm:awake`. This file only compares the
   page's own clock with that list. It never guesses a schedule, and it has no
   idle timer.

   AWAKE ANYWAY:
     - <html class="fcpm-awake">, set by a page that must not dim (the wall
       while held, or a class taking a screen over);
     - an hour after any touch, click, key or real pointer movement, and
       each one starts the hour again. Nobody should watch a room's screen
       dim on them because the schedule didn't know they were there;
     - no list, an empty list, or past the list's last end. A screen that
       doesn't know fails awake.

   DIM is pure black over the page, the page at 10%, and the three squares:
   a split clock (hour hand at the top, a seconds tick in the middle, minute
   hand at the bottom), the lit square walking the column, the column gliding
   slowly across the black and bouncing off the edges, against burn-in.
   The first touch on a dim screen only wakes it.

   PROOFS, on the top page's URL: ?at=HH:MM or ?at=<ISO time> pretends it is
   then (as the wall and class mode do), ?awake and ?dim pin either state.

   window.FCPMDim = { isDim(), tally(el) }. The wall asks isDim() every frame
   and stops turning while it is true. tally() draws the mark into any
   element; the idle screen uses it.

   Only the top window runs it. The wall's modules are pages in iframes that
   carry this file too, and there must be one layer, the shell's.

   No build step, no network, ES5-ish: it has to run inlined into a page
   read over file:// on a panel that has been off for a month. */
(function () {
  'use strict';
  var top;
  try { top = window === window.top; } catch (e) { top = false; }
  if (!top || window.FCPMDim) return;

  var HOUR = 3600e3, STEP = 4000;
  var html = document.documentElement;
  var still = window.matchMedia ? window.matchMedia('(prefers-reduced-motion: reduce)') : { matches: false };
  var q = new URLSearchParams(location.search);

  // ?at=: HH:MM today, or anything Date can read. The clock then runs on
  // from there.
  var skew = 0, at = q.get('at');
  if (at) {
    var t = NaN, hm = /^(\d{1,2}):(\d{2})$/.exec(at);
    if (hm) { var d = new Date(); d.setHours(+hm[1], +hm[2], 0, 0); t = d.getTime(); }
    else t = Date.parse(at);
    if (!isNaN(t)) skew = t - Date.now();
  }
  function now() { return Date.now() + skew; }

  // --- the verdict ---------------------------------------------------------

  var wokeUntil = 0;
  function scheduled(t) {
    var w = window.FCPM_AWAKE;
    if (!Array.isArray(w) || !w.length) return true;
    var last = 0;
    for (var i = 0; i < w.length; i++) {
      var s = +w[i][0], e = +w[i][1];
      if (t >= s && t < e) return true;
      if (e > last) last = e;
    }
    return t >= last;
  }
  function awake() {
    if (q.has('awake')) return true;
    if (q.has('dim')) return false;
    if (html.classList.contains('fcpm-awake')) return true;
    var t = now();
    return t < wokeUntil || scheduled(t);
  }

  // --- the mark ------------------------------------------------------------

  var NS = 'http://www.w3.org/2000/svg';
  function svg(tag, attrs, parent) {
    var n = document.createElementNS(NS, tag);
    for (var k in attrs) n.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(n);
    return n;
  }
  function hand(parent, y1, y2, w) {
    var g = svg('g', { 'stroke-linecap': 'square' }, parent);
    svg('line', { x1: 50, y1: y1, x2: 50, y2: y2, stroke: 'currentColor', 'stroke-width': w }, g);
    return g;
  }
  var tallies = [];
  function tally(el) {
    el.classList.add('fcpm-tally');
    el.setAttribute('aria-hidden', 'true');
    el.textContent = '';
    var parts = [];
    for (var i = 0; i < 3; i++) {
      var m = document.createElement('div');
      m.className = 'fcpm-mark' + (i === 1 ? ' lit' : '');
      var s = svg('svg', { viewBox: '0 0 100 100' }, m);
      if (i === 0) parts.push(hand(s, 54, 29, 6));                 // hours
      if (i === 2) parts.push(hand(s, 55, 17, 4));                 // minutes
      if (i === 1) {                                               // seconds
        var ticks = svg('g', { 'class': 'ticks', stroke: 'currentColor', 'stroke-linecap': 'square' }, s);
        for (var h = 0; h < 12; h++)
          svg('line', { x1: 50, y1: 11, x2: 50, y2: 15, 'stroke-width': h % 3 ? 1.6 : 3,
                        transform: 'rotate(' + h * 30 + ' 50 50)' }, ticks);
        parts.push(hand(s, 8, 18, 4));
      }
      el.appendChild(m);
    }
    var t = { el: el, marks: el.children, hh: parts[0], ss: parts[1], mm: parts[2], at: 1, dir: 1 };
    tallies.push(t);
    tick(t);
    return el;
  }
  function tick(t) {
    var d = new Date(now()), s = d.getSeconds(), m = d.getMinutes() + s / 60, h = d.getHours() % 12 + m / 60;
    t.hh.setAttribute('transform', 'rotate(' + h * 30 + ' 50 50)');
    t.mm.setAttribute('transform', 'rotate(' + m * 6 + ' 50 50)');
    t.ss.setAttribute('transform', 'rotate(' + s * 6 + ' 50 50)');
  }
  // Down the column and back up, never wrapping: a level meter, not a
  // progress bar. Reduced motion keeps it on the middle square.
  function walk(t) {
    if (still.matches) { t.at = 1; }
    else {
      t.at += t.dir;
      if (t.at <= 0 || t.at >= t.marks.length - 1) t.dir = -t.dir;
    }
    for (var i = 0; i < t.marks.length; i++) t.marks[i].classList.toggle('lit', i === t.at);
  }

  // --- the layer -----------------------------------------------------------

  var layer, mark, dim = false;
  function build() {
    layer = document.createElement('div');
    layer.id = 'fcpm-dim';
    // Findable by role and name, like everything an attendant presses.
    layer.setAttribute('role', 'button');
    layer.setAttribute('aria-label', 'Wake the screen');
    mark = tally(document.createElement('div'));
    layer.appendChild(mark);
    document.body.appendChild(layer);
    // The first touch only wakes: it never reaches what is underneath.
    ['pointerdown', 'pointerup', 'mousedown', 'mouseup', 'click', 'touchstart', 'touchend', 'contextmenu']
      .forEach(function (type) {
        layer.addEventListener(type, function (ev) {
          if (!dim && !html.classList.contains('fcpm-waking')) return;
          ev.preventDefault(); ev.stopPropagation();
          if (type === 'pointerdown' || type === 'touchstart' || type === 'click') woke();
        }, { capture: true, passive: false });
      });
    layer.addEventListener('keydown', function (ev) { if (dim) { ev.preventDefault(); woke(); } });
  }

  function set(d) {
    if (d === dim) return;
    dim = d;
    html.classList.toggle('fcpm-dim', d);
    layer.setAttribute('aria-hidden', d ? 'false' : 'true');
    layer.tabIndex = d ? 0 : -1;
    if (d) { place(true); glide(); }
    try { window.dispatchEvent(new CustomEvent('fcpm:dim', { detail: { dim: d } })); } catch (e) {}
  }
  function judge() { if (layer) set(!awake()); }

  // --- the glide -----------------------------------------------------------

  // A disc on a frictionless table: a straight line at a calm, constant
  // speed, bouncing off the edges. About a minute to cross a portrait panel.
  // Reduced motion: no glide; it moves to a new place once an hour instead.
  var x = 0, y = 0, vx = 1, vy = 1, last = 0, movedHour = -1;
  function bounds() {
    return { w: Math.max(0, window.innerWidth - mark.offsetWidth - 40),
             h: Math.max(0, window.innerHeight - mark.offsetHeight - 40) };
  }
  function draw() { mark.style.transform = 'translate(' + (x + 20) + 'px,' + (y + 20) + 'px)'; }
  function place(random) {
    var b = bounds();
    if (random) {
      x = Math.random() * b.w; y = Math.random() * b.h;
      var a = Math.PI / 6 + Math.random() * Math.PI / 6;           // never flat, never steep
      vx = Math.cos(a) * (Math.random() < 0.5 ? -1 : 1);
      vy = Math.sin(a) * (Math.random() < 0.5 ? -1 : 1);
    }
    x = Math.min(Math.max(x, 0), b.w); y = Math.min(Math.max(y, 0), b.h);
    draw();
  }
  function glide(ts) {
    if (!dim) { last = 0; return; }
    if (still.matches) {
      var hr = Math.floor(now() / HOUR);
      if (hr !== movedHour) { movedHour = hr; place(true); }
      last = 0;
      return setTimeout(glide, 60e3);
    }
    if (ts && last) {
      var b = bounds(), speed = Math.min(window.innerWidth, window.innerHeight) / 60;   // px per second
      var dt = Math.min(ts - last, 250) / 1000;
      x += vx * speed * dt; y += vy * speed * dt;
      if (x <= 0 || x >= b.w) { vx = -vx; x = Math.min(Math.max(x, 0), b.w); }
      if (y <= 0 || y >= b.h) { vy = -vy; y = Math.min(Math.max(y, 0), b.h); }
      draw();
    }
    last = ts || 0;
    requestAnimationFrame(glide);
  }

  // --- waking --------------------------------------------------------------

  // Waking keeps the layer catching for a moment after it starts to go, so
  // the rest of the touch that woke it (the click a tap ends in) lands on
  // the layer and not on a button that has just appeared under it.
  var waking = 0;
  function woke() {
    wokeUntil = now() + HOUR;
    if (dim) {
      html.classList.add('fcpm-waking');
      clearTimeout(waking);
      waking = setTimeout(function () { html.classList.remove('fcpm-waking'); }, 700);
    }
    judge();
  }
  // A pointer that hasn't moved is not a person: browsers send a mousemove
  // when the page changes under a resting cursor, and the layer appearing is
  // exactly that. Count only real movement.
  var px = null, py = null;
  function moved(ev) {
    if (px !== null && (Math.abs(ev.screenX - px) > 2 || Math.abs(ev.screenY - py) > 2)) woke();
    px = ev.screenX; py = ev.screenY;
  }
  function start() {
    build();
    window.addEventListener('pointermove', moved, true);
    ['pointerdown', 'keydown', 'wheel', 'touchstart'].forEach(function (type) {
      window.addEventListener(type, woke, { capture: true, passive: true });
    });
    window.addEventListener('fcpm:awake', judge);
    window.addEventListener('resize', function () { if (dim) place(false); });
    new MutationObserver(judge).observe(html, { attributes: true, attributeFilter: ['class'] });
    judge();
    setInterval(function () {
      for (var i = 0; i < tallies.length; i++) tick(tallies[i]);
      judge();
    }, 1000);
    setInterval(function () { for (var i = 0; i < tallies.length; i++) walk(tallies[i]); }, STEP);
  }

  window.FCPMDim = { isDim: function () { return dim; }, tally: tally };
  if (document.body) start();
  else document.addEventListener('DOMContentLoaded', start);
})();
