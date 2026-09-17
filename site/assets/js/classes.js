// Shared class-window logic.
//
// Two pages ask the same question — "is a class happening right now?" — and
// they must never disagree. The homepage uses it to decorate the check-in
// panel; the check-in page uses it to preload itself for a class arrival.
//
// So the answer lives here, once, and both import it. The QR on the door
// carries no class information at all: it is a permanent link to /check-in/,
// and the page works out the rest. Nothing to reprint, nothing to rotate,
// nothing that can be stale in someone's pocket.
//
// Windows:
//
//   soon   the leadMinutes before the start — visible on the way in
//   late   the first lateMinutes after it starts — still worth walking in
//   now    running, past the point of joining late
//
// `late` is a sub-case of the class being on, not a separate phase of the
// day; both mean "the class is happening".

export function readConfig(elementId = 'class-config') {
  const source = document.getElementById(elementId);
  if (!source) return null;
  try {
    return JSON.parse(source.textContent);
  } catch (error) {
    return null;
  }
}

export function pickSession(config, now = Date.now()) {
  if (!config?.sessions?.length) return null;

  const lead = (config.leadMinutes ?? 90) * 60000;
  const late = (config.lateMinutes ?? 45) * 60000;

  for (const session of config.sessions) {
    const starts = Date.parse(session.starts);
    const ends = Date.parse(session.ends);
    if (Number.isNaN(starts) || Number.isNaN(ends)) continue;

    if (now >= starts && now <= ends) {
      return {
        ...session,
        starts,
        ends,
        phase: now <= starts + late ? 'late' : 'now',
        running: true,
      };
    }

    if (now >= starts - lead && now < starts) {
      return { ...session, starts, ends, phase: 'soon', running: false };
    }
  }

  return null;
}

// Stable identity for a session, so an RSVP can be matched back to it without
// depending on array order or on a field the calendar may not provide.
export const sessionKey = (session) => `${session.starts}|${session.title}`;

export function clockTime(ms) {
  return new Date(ms).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
}

// Re-evaluate on a timer, but only while the tab is visible. Both callers want
// exactly this, and both would otherwise get it slightly wrong.
export function watch(render, intervalMs = 60000) {
  let timer = null;

  const start = () => {
    stop();
    if (document.visibilityState === 'visible') timer = window.setInterval(render, intervalMs);
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

  render();
  start();
  return stop;
}
