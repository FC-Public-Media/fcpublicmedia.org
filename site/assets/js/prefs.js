// This device's own choices (colours, language). Kept in localStorage for the page to read before it
// paints, and copied to the `fcpm-device` cache as /device.json, where the offline kit's worker can read
// them too. See docs/site.md#languages.

const CACHE = 'fcpm-device';
const PROFILE = '/device.json';
const NAMES = ['theme', 'lang'];
const inMemory = {};

export function read(name) {
  try {
    const stored = localStorage.getItem(name);
    if (stored) return stored;
  } catch (error) {
    // Storage blocked: only what this page was told.
  }
  return inMemory[name] || null;
}

async function mirror() {
  if (!self.caches) return;
  const profile = {};
  for (const name of NAMES) {
    const value = read(name);
    if (value) profile[name] = value;
  }
  try {
    const cache = await caches.open(CACHE);
    await cache.put(PROFILE, new Response(JSON.stringify(profile), {
      headers: { 'content-type': 'application/json' },
    }));
  } catch (error) {
    // No cache on this device (plain http, or blocked): the page still has localStorage.
  }
}

export function remember(name, value) {
  inMemory[name] = value;
  try {
    localStorage.setItem(name, value);
  } catch (error) {
    // Holds in memory for this page only.
  }
  mirror();
}
