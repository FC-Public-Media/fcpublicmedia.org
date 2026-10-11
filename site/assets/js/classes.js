// Class-window logic shared by the homepage and the check-in page, so they never disagree.
// Windows: soon (leadMinutes before), late (first lateMinutes), now (the rest of the class).
// See docs/programming.md.

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

// Stable key for an RSVP, independent of array order.
export const sessionKey = (session) => `${session.starts}|${session.title}`;

export function clockTime(ms) {
  return new Date(ms).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
}

// Re-evaluate on a timer while the tab is visible.
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
