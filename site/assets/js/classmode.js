// Class mode on the homepage: decorates the check-in panel. See docs/programming.md.

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

  // No ?reason=Class: check-in decides from the same data, and a shared link outlives the class.
  el('[data-class-join]').textContent = session.running
    ? "I'm here for the class"
    : 'Check in for this class';

  el('[data-class-price]').hidden = !config.dropin?.public || config.dropin.public === 'TODO';
}
