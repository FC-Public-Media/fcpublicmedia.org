// Class mode.
//
// The build bakes the schedule into the page. This decides, from the wall
// clock on the device, whether a class is happening right now — and if so
// rearranges the check-in card around it.
//
// No request is made. A page built last night already knows about tonight's
// class, because the times came with it. The trade is staleness: a session
// added after the last build is not here. See _data/classes.yml.
//
// Three windows:
//
//   soon    lead_minutes before the start   "starting soon, here's where"
//   now     start to end                    "in progress, you can still come in"
//   late    the first late_minutes of it    adds "you can join late"
//
// Outside all of them the card stays as it was and this file does nothing.

const source = document.getElementById('class-config');
if (source) run(JSON.parse(source.textContent));

function run(config) {
  const card = document.querySelector('[data-checkin-card]');
  const slot = document.querySelector('[data-class-slot]');
  if (!card || !slot) return;

  const render = () => {
    const session = currentSession(config);

    if (!session) {
      slot.hidden = true;
      card.dataset.classMode = 'off';
      return;
    }

    slot.hidden = false;
    card.dataset.classMode = session.phase;
    paint(slot, session, config);
  };

  render();

  // A class starts or ends while someone is looking at the page. Re-checking
  // each minute is cheap — it is arithmetic on numbers already in memory —
  // and only runs while the tab is visible.
  let timer = null;
  const start = () => {
    stop();
    if (document.visibilityState === 'visible') timer = window.setInterval(render, 60000);
  };
  const stop = () => {
    if (timer) window.clearInterval(timer);
    timer = null;
  };

  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') {
      render();
      start();
    } else {
      stop();
    }
  });

  start();
}

function currentSession(config) {
  const now = Date.now();
  const lead = config.leadMinutes * 60000;
  const late = config.lateMinutes * 60000;

  for (const session of config.sessions) {
    const starts = Date.parse(session.starts);
    const ends = Date.parse(session.ends);
    if (Number.isNaN(starts) || Number.isNaN(ends)) continue;

    if (now >= starts && now <= ends) {
      return { ...session, phase: now <= starts + late ? 'late' : 'now', starts, ends };
    }
    if (now >= starts - lead && now < starts) {
      return { ...session, phase: 'soon', starts, ends };
    }
  }

  return null;
}

function clockTime(ms) {
  return new Date(ms).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
}

function paint(slot, session, config) {
  const el = (sel) => slot.querySelector(sel);

  el('[data-class-title]').textContent = session.title;
  el('[data-class-room]').textContent = session.room || '';
  el('[data-class-summary]').textContent = (session.summary || '').trim();

  const when = el('[data-class-when]');
  if (session.phase === 'soon') {
    when.textContent = `Starts at ${clockTime(session.starts)}`;
  } else {
    when.textContent = `On now until ${clockTime(session.ends)}`;
  }

  el('[data-class-eyebrow]').textContent =
    session.phase === 'soon' ? 'Starting soon' : 'Happening now';

  // "You can still come in" only while it is genuinely still worth walking in.
  el('[data-class-late]').hidden = session.phase !== 'late';

  const join = el('[data-class-join]');
  join.href = `/check-in/?reason=${encodeURIComponent('Class')}`;

  const signup = el('[data-class-signup]');
  if (session.signup) {
    signup.href = session.signup;
    signup.hidden = false;
  } else {
    signup.hidden = true;
  }

  // Pricing is shown plainly rather than gated. Someone who balks at the
  // drop-in rate is exactly the person for whom membership is the better
  // deal, so the membership link sits right next to it rather than behind a
  // wall.
  const price = el('[data-class-price]');
  price.hidden = !config.dropin.public;
}
