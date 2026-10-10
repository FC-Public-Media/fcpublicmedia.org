// see docs/inline/worker/src/challenges.js.md#1

const PREFIX = 'challenge:';
const BYTES = 32;

const toBase64Url = (bytes) => {
  let binary = '';
  for (const byte of new Uint8Array(bytes)) binary += String.fromCharCode(byte);
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
};

// see docs/inline/worker/src/challenges.js.md#2
export function challengeStore(kv, { ttl = 300, now = () => Date.now() } = {}) {
  return {
    ttl,

    async issue(intent) {
      const challenge = toBase64Url(crypto.getRandomValues(new Uint8Array(BYTES)));
      const record = { intent, issued: now(), expires: now() + ttl * 1000 };
      await kv.put(PREFIX + challenge, JSON.stringify(record), { expirationTtl: ttl });
      return { challenge, expiresIn: ttl };
    },

    // see docs/inline/worker/src/challenges.js.md#3
    async take(challenge) {
      if (typeof challenge !== 'string' || !challenge) return null;

      const key = PREFIX + challenge;
      const raw = await kv.get(key);
      if (raw === null || raw === undefined) return null;
      await kv.delete(key);

      let record;
      try {
        record = JSON.parse(raw);
      } catch (error) {
        return null;
      }

      if (!record?.expires || record.expires <= now()) return null;
      return record.intent ?? null;
    },
  };
}
