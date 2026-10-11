// Challenges in KV, keyed by the 32-byte challenge itself. See worker/README.md.
// take() reads then deletes; KV's eventual consistency can let the same intent replay once.

const PREFIX = 'challenge:';
const BYTES = 32;

const toBase64Url = (bytes) => {
  let binary = '';
  for (const byte of new Uint8Array(bytes)) binary += String.fromCharCode(byte);
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
};

/** `ttl` seconds sets KV expiry, and the stored deadline is checked too, since KV eviction lags. */
export function challengeStore(kv, { ttl = 300, now = () => Date.now() } = {}) {
  return {
    ttl,

    async issue(intent) {
      const challenge = toBase64Url(crypto.getRandomValues(new Uint8Array(BYTES)));
      const record = { intent, issued: now(), expires: now() + ttl * 1000 };
      await kv.put(PREFIX + challenge, JSON.stringify(record), { expirationTtl: ttl });
      return { challenge, expiresIn: ttl };
    },

    /** Spend a challenge (deleted whatever the outcome); returns its intent or null. */
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
