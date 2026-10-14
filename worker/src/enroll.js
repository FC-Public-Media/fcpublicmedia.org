// Enrolment rules as pure functions over the devices array: listed is not allowed, the first
// device is trusted, a publisher approves the rest. See docs/identity.md#passkeys-and-devices.

/** Devices that still count. A revoked record stays for the audit, inert. */
export const active = (devices) => devices.filter((device) => device?.revoked !== true);

/** Is there anybody who could approve a new device? */
export const anyPublisher = (devices) =>
  active(devices).some((device) => device.may_publish === true);

const find = (devices, credentialId) =>
  devices.findIndex((device) => device?.credential_id === credentialId);

/** Add a device: { ok, devices, granted } where `granted` means it may publish already. */
export function addDevice(devices, record) {
  if (find(devices, record.credential_id) >= 0) {
    return { ok: false, detail: 'That device is already registered for this site.' };
  }

  // Asks whether a publisher exists, not whether the list is empty.
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

/** Revoke a device by marking it; refuses to remove the last publisher. */
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

/** The file as written: indented, trailing newline, so additions diff readably. */
export const serialize = (devices) => `${JSON.stringify({ version: 1, devices }, null, 2)}\n`;
