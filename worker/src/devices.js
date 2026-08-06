// Finding the public key a signature has to verify against.
//
// The device list lives in the member's own repository, not in a database
// here. That was decided in _data/authorize.yml and it holds up: the grants
// travel with the repo when it is handed over, and die with it when it is
// deleted. Nothing is orphaned in a service nobody remembers paying for.
//
// The file is public, and that is fine. It holds public keys, which are the
// half that is meant to be published, plus the labels people gave their own
// devices. Anyone can read who may edit a site. Nobody can become them.
//
// THE SHAPE
// ---------
//   {
//     "version": 1,
//     "devices": [
//       {
//         "credential_id": "…base64url…",
//         "public_key":    "…base64url SPKI…",
//         "algorithm":     -7,
//         "label":         "Jane's phone",
//         "added":         "2026-01-14T18:22:04.117Z",
//         "may_publish":   true
//       }
//     ]
//   }
//
// `may_publish` is the whole reason binding a device is safe to allow from a
// forwardable link. Being in this list means listed. Publishing is a separate
// property, and it is absent by default — a record that does not say so
// cannot write anything, it can only prove it exists.

const RAW_HOST = 'https://raw.githubusercontent.com';

/**
 * Reader for a repository's device list.
 *
 * `fetchImpl` is injectable so the tests never touch the network; everything
 * about how this behaves — a missing file, a corrupt one, a revoked device —
 * is worth testing and none of it should need GitHub to be having a good day.
 *
 * TWO WAYS TO READ IT, AND WHY
 * ----------------------------
 * `read` is the authenticated one, and it is used whenever the broker has a
 * credential. raw.githubusercontent is the fallback for a broker configured to
 * verify but not to write.
 *
 * The difference is not tidiness. raw serves this with cache headers measured
 * in minutes, so a broker reading it would answer from a stale copy — which
 * means a device revoked a minute ago still works, and, less obviously, an
 * owner who has just bound their own phone cannot approve anybody until the
 * cache catches up. The second one would look like the feature simply not
 * working. The authenticated read has neither problem.
 */
export function deviceList({ fetchImpl = fetch, read = null, path = '.auth/devices.json', ref = 'HEAD' } = {}) {
  return {
    /**
     * Returns { ok: true, device } or { ok: false, reason, detail }.
     *
     * `reason` distinguishes the three that mean different things to a person
     * standing there: the site has no list at all (nobody has ever been set
     * up), this credential is not on it (wrong site, or removed), and the
     * credential is on it but not allowed to do this.
     */
    async find(repo, credentialId) {
      if (typeof credentialId !== 'string' || !credentialId) {
        return { ok: false, reason: 'unknown-device', detail: 'No credential was named.' };
      }

      let text;
      if (read) {
        const found = await read({ repo, path });
        if (!found.ok) {
          // "The app is not installed here" must not arrive looking like
          // "GitHub is down". One is our setup and one is somebody else's
          // afternoon, and they need different answers.
          return {
            ok: false,
            reason: found.reason === 'credential' ? 'credential' : 'unreachable',
            detail: found.detail,
          };
        }
        if (found.content === null) {
          return { ok: false, reason: 'no-list', detail: `${repo} has no registered devices yet.` };
        }
        text = found.content;
      } else {
        const url = `${RAW_HOST}/${repo}/${ref}/${path}`;
        let response;
        try {
          response = await fetchImpl(url, { headers: { Accept: 'application/json' } });
        } catch (error) {
          return { ok: false, reason: 'unreachable', detail: 'GitHub could not be reached.' };
        }

        if (response.status === 404) {
          return {
            ok: false,
            reason: 'no-list',
            detail: `${repo} has no registered devices yet.`,
          };
        }
        if (!response.ok) {
          return { ok: false, reason: 'unreachable', detail: `GitHub returned ${response.status}.` };
        }
        text = await response.text();
      }

      let listed;
      try {
        listed = JSON.parse(text)?.devices;
      } catch (error) {
        return { ok: false, reason: 'unreadable', detail: 'The device list is not valid JSON.' };
      }
      if (!Array.isArray(listed)) {
        return { ok: false, reason: 'unreadable', detail: 'The device list has the wrong shape.' };
      }

      const device = listed.find(
        (entry) => entry?.credential_id === credentialId && entry?.revoked !== true
      );
      if (!device) {
        return {
          ok: false,
          reason: 'unknown-device',
          detail: `That device is not registered for ${repo}.`,
        };
      }
      if (typeof device.public_key !== 'string' || !device.public_key) {
        return { ok: false, reason: 'unreadable', detail: 'That device record has no public key.' };
      }

      return { ok: true, device };
    },
  };
}

/** Listed is not the same as allowed. See _data/authorize.yml. */
export const mayPublish = (device) => device?.may_publish === true;
