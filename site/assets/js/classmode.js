// Class mode on the homepage.
//
// The homepage has no job here beyond decorating the panel that already holds
// the QR and the check-in link. It does not encode the class into anything —
// the link is the same permanent /check-in/ either way, and that page works
// out for itself that a class is on. One source of truth, in classes.js.

import { readConfig, pickSession, clockTime, watch } from './classes.js';

const config = readConfig();
const card = document.querySelector('[data-checkin-card]');
const slot = document.querySelector('[data-class-slot]');

if (config && card && slot) {
  watch(() => {
    const session = pickSession(config);

    if (!session) {
      slot.hidden = true;
      card.dataset.classMode = 'off';
      return;
    }

    slot.hidden = false;
    card.dataset.classMode = session.phase;
    paint(session);
  });
}

function paint(session) {
  const el = (sel) => slot.querySelector(sel);

  el('[data-class-title]').textContent = session.title;
  el('[data-class-room]').textContent = session.room || '';
  el('[data-class-summary]').textContent = (session.summary || '').trim();

  el('[data-class-eyebrow]').textContent =
    session.running ? 'Happening now' : 'Starting soon';

  el('[data-class-when]').textContent = session.running
    ? `On now until ${clockTime(session.ends)}`
    : `Starts at ${clockTime(session.starts)}`;

  el('[data-class-late]').hidden = session.phase !== 'late';

  // Deliberately not "?reason=Class". The check-in page reaches the same
  // conclusion from the same data, so putting it in the URL would create a
  // second place for the answer to live — and a link that could be shared
  // hours later still claiming a class is on.
  el('[data-class-join]').textContent = session.running
    ? "I'm here for the class"
    : 'Check in for this class';

  el('[data-class-price]').hidden = !config.dropin?.public || config.dropin.public === 'TODO';
}
