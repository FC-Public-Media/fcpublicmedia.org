// see docs/inline/site/assets/js/classes.js.md#1

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

// see docs/inline/site/assets/js/classes.js.md#2
export const sessionKey = (session) => `${session.starts}|${session.title}`;

export function clockTime(ms) {
  return new Date(ms).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
}

// see docs/inline/site/assets/js/classes.js.md#3
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
