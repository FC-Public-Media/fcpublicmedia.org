// Issuing challenges, and spending them exactly once.
//
// The challenge is its own lookup key. There is no separate ID: the broker
// generates 32 random bytes, stores the intent under them, and finds the
// intent again by reading the challenge back out of the signed client data. A
// challenge nobody was issued matches nothing, and guessing one is guessing a
// 256-bit number.
//
// SINGLE USE, AND WHERE THAT IS ONLY NEARLY TRUE
// ----------------------------------------------
// take() reads and then deletes. Between those two calls KV is eventually
// consistent, so two requests arriving within the propagation window can both
// read the same challenge before either delete lands.
//
// That window is worth being precise about rather than hand-waving:
//
//   * KV never invents a value, so eventual consistency cannot make a
//     challenge appear that was not issued. The failure it can cause in the
//     other direction — issue in one location, verify in another, no value yet
//     — is an availability failure. The page says try again.
//   * A duplicate spend is a replay of the SAME intent, because the intent is
//     what the challenge is bound to. It cannot be redirected at a different
//     file or different content. And for a write, the second one carries the
//     same blob SHA, which GitHub has already moved past, so it is refused
//     anyway.
//
// If that stops being good enough — a non-idempotent action, money, anything
// that must happen once — the fix is a Durable Object rather than a tighter
// loop here. Its storage is strongly consistent and single-threaded per key,
// which is exactly the guarantee this comment is explaining the absence of.

const PREFIX = 'challenge:';
const BYTES = 32;

const toBase64Url = (bytes) => {
  let binary = '';
  for (const byte of new Uint8Array(bytes)) binary += String.fromCharCode(byte);
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
};

/**
 * A challenge store over a KV namespace.
 *
 * `ttl` is in seconds and is also KV's own expiry, so an abandoned challenge
 * costs nothing and cleans itself up. The stored expiry is checked as well:
 * KV's expiry is a promise about eviction, not about what a read returns the
 * instant afterwards, and a challenge one second past its deadline should be
 * refused by us rather than by a garbage collector.
 */
export function challengeStore(kv, { ttl = 300, now = () => Date.now() } = {}) {
  return {
    ttl,

    async issue(intent) {
      const challenge = toBase64Url(crypto.getRandomValues(new Uint8Array(BYTES)));
      const record = { intent, issued: now(), expires: now() + ttl * 1000 };
      await kv.put(PREFIX + challenge, JSON.stringify(record), { expirationTtl: ttl });
      return { challenge, expiresIn: ttl };
    },

    /**
     * Spend a challenge. Returns the intent it was issued for, or null.
     *
     * The delete happens whatever the outcome, including for an expired one:
     * a challenge that has been presented is finished, and leaving it there
     * would only give somebody another go at it.
     */
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
