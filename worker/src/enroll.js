// see docs/inline/worker/src/enroll.js.md#1

/** Devices that still count. A revoked record stays for the audit, inert. */
export const active = (devices) => devices.filter((device) => device?.revoked !== true);

/** Is there anybody who could approve a new device? */
export const anyPublisher = (devices) =>
  active(devices).some((device) => device.may_publish === true);

const find = (devices, credentialId) =>
  devices.findIndex((device) => device?.credential_id === credentialId);

// see docs/inline/worker/src/enroll.js.md#2
export function addDevice(devices, record) {
  if (find(devices, record.credential_id) >= 0) {
    return { ok: false, detail: 'That device is already registered for this site.' };
  }

  // see docs/inline/worker/src/enroll.js.md#3
  const granted = !anyPublisher(devices);

  return {
    ok: true,
    granted,
    devices: [...devices, { ...record, may_publish: granted }],
  };
}

/** Flip a listed device to being allowed to publish. */
export function allowDevice(devices, credentialId) {
  const at = find(devices, credentialId);
  if (at < 0) return { ok: false, detail: 'That device is not registered for this site.' };
  if (devices[at].revoked === true) {
    return { ok: false, detail: 'That device was revoked. It has to be added again.' };
  }
  if (devices[at].may_publish === true) {
    return { ok: false, detail: 'That device is already allowed.', already: true };
  }

  const next = [...devices];
  next[at] = { ...next[at], may_publish: true };
  return { ok: true, devices: next };
}

// see docs/inline/worker/src/enroll.js.md#4
export function revokeDevice(devices, credentialId) {
  const at = find(devices, credentialId);
  if (at < 0) return { ok: false, detail: 'That device is not registered for this site.' };
  if (devices[at].revoked === true) return { ok: true, devices, already: true };

  const next = [...devices];
  next[at] = { ...next[at], revoked: true };

  if (devices[at].may_publish === true && !anyPublisher(next)) {
    return {
      ok: false,
      detail:
        'That is the only device that can publish to this site. Add and approve ' +
        'another one first, or nobody will be able to change anything.',
    };
  }

  return { ok: true, devices: next };
}

// see docs/inline/worker/src/enroll.js.md#5
export const serialize = (devices) => `${JSON.stringify({ version: 1, devices }, null, 2)}\n`;
