// standby.js -- our page between programs: panels taking turns, the jukebox on the slant. Plain files.
//
//   ?jukebox=URL   a jukebox to show and play (bay 1's OBS: http://127.0.0.1:8095). Without it, the slant shows
//                  what the floor's own jukebox is playing (/floor/now.json); with no music at all, it invites
//   ?holder=NAME   inside OBS, while OBS streams: the name it takes the air under (POST /air, ../../standby)
//   ?listen        play the music here too (a person can also press listen, where there is a pointer)
//
// Panels: the bulletin board's slides (/slides/slides.json, their own seconds), what is next on 97 (the
// days we laid, /schedule/), and the invitation. See ../../../PROFILE.md, "The standby page".
(function () {
  "use strict";
  var q = new URLSearchParams(location.search);
  var JUKEBOX = (q.get("jukebox") || "").replace(/\/$/, "");
  var NOW = JUKEBOX ? JUKEBOX + "/now.json" : "/floor/now.json";
  var ROOM = "America/Denver", PILLS = 12, NEXT_EVERY = 4, PITCH_EVERY = 3;   // a pitch every third "next"
  var stage = document.getElementById("stage"), panels = document.getElementById("panels");
  var slant = document.getElementById("slant"), track = slant.querySelector(".track");

  function fit() {
    var s = Math.min(innerWidth / 1920, innerHeight / 1080);
    stage.style.transform = "scale(" + s + ")";
  }
  addEventListener("resize", fit);
  fit();

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }
  function getJSON(url) {
    return fetch(url, { cache: "no-store" }).then(function (r) { return r.ok ? r.json() : null; })
      .catch(function () { return null; });
  }
  function roomDay(d) {   // YYYY-MM-DD in the room
    return new Intl.DateTimeFormat("en-CA", { timeZone: ROOM, year: "numeric", month: "2-digit", day: "2-digit" }).format(d);
  }
  function roomTime(d) {
    return new Intl.DateTimeFormat("en-US", { timeZone: ROOM, hour: "numeric", minute: "2-digit" }).format(d);
  }
  function mmss(s) {
    s = Math.max(0, Math.round(s));
    return Math.floor(s / 60) + ":" + String(s % 60).padStart(2, "0");
  }

  // ---------------------------------------------------------------- the panels

  function slidePanel(s) {
    var p = el("div", "panel slide"), img = el("img");
    img.src = "/slides/" + s.file;
    img.alt = "";
    p.appendChild(img);
    return { node: p, seconds: s.seconds || 10 };
  }

  function nextPanel(airings) {
    var now = Date.now(), coming = airings.filter(function (a) { return Date.parse(a.at) + a.seconds * 1000 > now; });
    if (!coming.length) return null;
    var p = el("div", "panel text next"), ol = el("ol");
    p.appendChild(el("h2", null, Date.parse(coming[0].at) <= now ? "Now on 97" : "Next on 97"));
    coming.slice(0, 3).forEach(function (a) {
      var li = el("li"), show = a.show || {};
      li.appendChild(el("span", "at", Date.parse(a.at) <= now ? "now" : roomTime(new Date(a.at))));
      li.appendChild(el("span", "p", show.project || show.title || ""));
      if (show.project && show.title) li.appendChild(el("span", "t", show.title));
      ol.appendChild(li);
    });
    p.appendChild(ol);
    return { node: p, seconds: 12 };
  }

  function pitchPanel() {
    var p = el("div", "panel text pitch"), small = el("p", "small");
    p.appendChild(el("p", "big", "Your music here."));
    small.appendChild(document.createTextNode("Members put their music on this stream, on channel 97 and YouTube. "));
    small.appendChild(el("b", null, "fcpublicmedia.org/join"));
    p.appendChild(small);
    return { node: p, seconds: 12 };
  }

  function airings() {
    var today = new Date(), tomorrow = new Date(Date.now() + 864e5);
    return Promise.all([roomDay(today), roomDay(tomorrow)].map(function (d) {
      return getJSON("/schedule/" + d + ".json");
    })).then(function (days) {
      return days.reduce(function (all, d) { return all.concat((d && d.airings) || []); }, []);
    });
  }

  // One round: the slides in their order, "next on 97" after every NEXT_EVERY, now and then the invitation.
  function round() {
    return Promise.all([getJSON("/slides/slides.json"), airings()]).then(function (got) {
      var slides = got[0] || [], air = got[1], out = [], nexts = 0;
      slides.forEach(function (s, i) {
        out.push(function () { return slidePanel(s); });
        if ((i + 1) % NEXT_EVERY === 0) {
          nexts++;
          out.push(nexts % PITCH_EVERY === 0 ? pitchPanel : function () { return nextPanel(air); });
        }
      });
      if (!slides.length) out.push(function () { return nextPanel(air); }, pitchPanel);
      return out;
    });
  }

  var shown = null;
  function show(made) {
    panels.appendChild(made.node);
    made.node.getBoundingClientRect();     // laid out first, so the fade runs
    made.node.classList.add("on");
    var old = shown;
    shown = made.node;
    if (old) setTimeout(function () { old.remove(); }, 1000);
  }

  function turn(list, i) {
    if (i >= list.length) return round().then(function (l) { turn(l, 0); });
    var made = list[i]();
    if (!made) return turn(list, i + 1);
    show(made);
    setTimeout(function () { turn(list, i + 1); }, made.seconds * 1000);
  }
  round().then(function (l) { turn(l, 0); });

  // ---------------------------------------------------------------- the jukebox, on the slant

  var who = slant.querySelector(".who"), what = slant.querySelector(".what"), time = slant.querySelector(".time");
  var bar = slant.querySelector(".bar"), pills = [];
  for (var i = 0; i < PILLS; i++) pills.push(bar.appendChild(el("i")));
  var playing = null, heardAt = 0;

  function paint() {
    slant.classList.toggle("silent", !playing);
    track.classList.toggle("solo", !!playing && !playing.artist);
    if (!playing) {
      who.textContent = "Your music here.";
      what.textContent = "Members put their music on this stream";
      pills.forEach(function (p) { p.className = ""; });
      time.textContent = "";
      return;
    }
    var pos = Math.min(playing.length, playing.position + (Date.now() - heardAt) / 1000);
    var at = Math.min(PILLS - 1, Math.floor(pos / playing.length * PILLS));
    who.textContent = playing.artist || playing.title;
    what.textContent = playing.artist ? playing.title : "";
    pills.forEach(function (p, n) { p.className = n < at ? "then" : n === at ? "on" : ""; });
    time.textContent = mmss(pos) + " / " + mmss(playing.length);
  }

  function ask() {
    getJSON(NOW).then(function (now) {
      var next = now && now.playing;
      if (next && playing && next.id !== playing.id) {     // a new track: the slant turns over
        track.classList.add("quiet");
        setTimeout(function () { playing = next; heardAt = Date.now(); paint(); track.classList.remove("quiet"); }, 600);
        return;
      }
      playing = next || null;
      heardAt = Date.now();
    });
  }
  ask();
  setInterval(ask, 5000);
  setInterval(paint, 250);

  // ---------------------------------------------------------------- hands, for a person with a pointer

  var audio = null, still;
  function listen(on) {
    if (on && !audio) { audio = new Audio(JUKEBOX + "/stream.mp3"); audio.play().catch(function () {}); }
    if (!on && audio) { audio.pause(); audio.src = ""; audio = null; }
    document.querySelector('[data-do="listen"]').classList.toggle("on", !!audio);
  }
  document.getElementById("hands").addEventListener("click", function (e) {
    var b = e.target.closest("button");
    if (!b) return;
    if (!JUKEBOX) return;
    if (b.dataset.do === "listen") listen(!audio);
    if (b.dataset.do === "skip") fetch(JUKEBOX + "/skip", { method: "POST" }).then(ask, function () {});
  });
  addEventListener("mousemove", function () {
    document.body.classList.add("pointing");
    clearTimeout(still);
    still = setTimeout(function () { document.body.classList.remove("pointing"); }, 2500);
  });
  if (!JUKEBOX) document.getElementById("hands").hidden = true;   // the floor's music is the floor's to play
  if (q.has("listen") && JUKEBOX) listen(true);

  // ---------------------------------------------------------------- the air, from inside OBS

  // OBS's browser source gives the page window.obsstudio. While OBS streams, this page says it has the
  // air, so the floor (../../standby) steps off YouTube's backup; when OBS stops, the claim lapses.
  if (window.obsstudio && window.obsstudio.getStatus) {
    var holder = q.get("holder") || "obs";
    setInterval(function () {
      window.obsstudio.getStatus(function (s) {
        if (s && s.streaming) {
          fetch("/air", { method: "POST", headers: { "Content-Type": "application/json" },
                          body: JSON.stringify({ holder: holder }) }).catch(function () {});
        }
      });
    }, 5000);
  }
})();
