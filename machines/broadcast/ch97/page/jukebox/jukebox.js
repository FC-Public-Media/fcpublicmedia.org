// jukebox.js -- the floor's jukebox (../../../jukebox) as its list, from /floor/now.json: every track in the folder
// in the order it plays, the one playing lit with how far in it is, the ones played this time round dimmed. The
// folder is read again after every track, so a file added, taken out or renamed shows here at the next one.
// The hands (POST /floor/jukebox): stop or play, skip, and a row pressed plays that track, the order going on from it.
(function () {
  "use strict";
  var list = document.getElementById("order");
  var folder = document.querySelector("footer .folder"), round = document.querySelector("footer .round");
  var playing = null, heardAt = 0, drawn = "", lit = null, state = "";
  var toggle = document.querySelector('#hands [data-do="stop"]'), skip = document.querySelector('#hands [data-do="skip"]');

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }
  function mmss(s) {
    s = Math.max(0, Math.round(s));
    var h = Math.floor(s / 3600), m = Math.floor(s / 60) % 60, ss = String(s % 60).padStart(2, "0");
    return h ? h + ":" + String(m).padStart(2, "0") + ":" + ss : m + ":" + ss;
  }
  function hours(s) {
    var m = Math.round(s / 60);
    return m < 60 ? m + " min" : Math.floor(m / 60) + " h " + (m % 60) + " min";
  }

  function draw(now) {
    folder.textContent = now.folder || "";
    playing = now.playing;
    heardAt = Date.now();
    state = now.state || (playing ? "playing" : "");
    toggle.textContent = state === "stopped" ? "play" : "stop";
    toggle.dataset.do = state === "stopped" ? "play" : "stop";
    toggle.disabled = state !== "playing" && state !== "stopped";
    skip.disabled = state !== "playing";
    var here = playing || now.stopped;
    if (!here) { list.textContent = ""; round.textContent = ""; drawn = ""; lit = null; return; }
    var all = [here].concat(now.next || []), n = all.length, at = now.at || 0, order = [];
    for (var i = 0; i < n; i++) order.push(all[(i - at + n) % n]);
    var key = order.map(function (t) { return t.id; }).join("\n") + "\n" + here.id + "\n" + state;
    if (key !== drawn) {
      drawn = key;
      list.textContent = "";
      order.forEach(function (t, i) {
        var li = el("li", i < at ? "then" : i === at && playing ? "on" : "");
        li.dataset.file = t.id;
        li.appendChild(el("span", "title", t.artist ? t.title + " · " + t.artist : t.title));
        li.appendChild(el("span", "file", t.id));
        li.appendChild(el("span", "len", mmss(t.length)));
        list.appendChild(li);
        if (i === at) lit = li;
      });
      var total = order.reduce(function (s, t) { return s + (t.length || 0); }, 0);
      round.textContent = n + " tracks · " + hours(total) + " round";
      list.scrollTop = Math.max(0, lit.offsetTop - list.offsetTop - 2 * lit.offsetHeight);   // two played ones above it
    }
    tick();
  }

  function tick() {
    if (!playing || !lit) return;
    var pos = Math.min(playing.length, playing.position + (Date.now() - heardAt) / 1000);
    lit.querySelector(".len").textContent = mmss(pos) + " / " + mmss(playing.length);
  }

  function say(body) {
    return fetch("/floor/jukebox", { method: "POST", headers: { "Content-Type": "application/json" },
                                     body: JSON.stringify(body) }).then(function () { setTimeout(ask, 800); }, function () {});
  }
  document.getElementById("hands").addEventListener("click", function (e) {
    var b = e.target.closest("button");
    if (b && !b.disabled) say({ do: b.dataset.do });
  });
  list.addEventListener("click", function (e) {
    var li = e.target.closest("li");
    if (!li || li.classList.contains("on")) return;
    li.classList.add("asked");
    say({ do: "play", file: li.dataset.file });
  });

  function ask() {
    fetch("/floor/now.json", { cache: "no-store" }).then(function (r) { return r.ok ? r.json() : null; })
      .then(function (now) { if (now) draw(now); }, function () {});
  }
  ask();
  setInterval(ask, 5000);
  setInterval(tick, 1000);
})();
