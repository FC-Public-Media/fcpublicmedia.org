// see docs/inline/worker/src/devices.js.md#1

const RAW_HOST = 'https://raw.githubusercontent.com';

// see docs/inline/worker/src/devices.js.md#2
export function deviceList({ fetchImpl = fetch, read = null, path = '.auth/devices.json', ref = 'HEAD' } = {}) {
  return {
    // see docs/inline/worker/src/devices.js.md#3
    async find(repo, credentialId) {
      if (typeof credentialId !== 'string' || !credentialId) {
        return { ok: false, reason: 'unknown-device', detail: 'No credential was named.' };
      }

      let text;
      if (read) {
        const found = await read({ repo, path });
        if (!found.ok) {
          // see docs/inline/worker/src/devices.js.md#4
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

/** Listed is not the same as allowed. See site/_data/authorize.yml. */
export const mayPublish = (device) => device?.may_publish === true;
