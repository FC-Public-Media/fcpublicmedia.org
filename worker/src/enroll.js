// Who is on the list, and what they may do.
//
// Pure functions over the array in .auth/devices.json. No network, no crypto,
// no opinions about who asked — by the time anything here runs, the asking has
// already been settled. Kept separate because the rules below are the ones
// worth being able to read in one screen.
//
// THE RULE THIS FILE EXISTS TO ENCODE
// -----------------------------------
// Enrollment and authority are different things (DESIGN-NOTES, "Enrollment and
// authority are two different things"). Being listed is enrollment. Being
// allowed to publish is authority. A claim link can be forwarded, and that is
// survivable precisely because forwarding it can only get somebody listed.
//
//   1. The FIRST device to bind is trusted. Nobody is there to approve it, the
//      owner is the one who asked for the site, and a site with no publisher
//      is a site nobody can use.
//   2. Every device after that arrives listed and not allowed, and an existing
//      publisher flips it. The owner approves a co-producer's phone from their
//      own phone; staff are not in the loop.
//
// A forwarded link is worthless the moment the owner has enrolled — which they
// will have, because they are the one who asked.

/** Devices that still count. A revoked record stays for the audit, inert. */
export const active = (devices) => devices.filter((device) => device?.revoked !== true);

/** Is there anybody who could approve a new device? */
export const anyPublisher = (devices) =>
  active(devices).some((device) => device.may_publish === true);

const find = (devices, credentialId) =>
  devices.findIndex((device) => device?.credential_id === credentialId);

/**
 * Add a device.
 *
 * Returns { ok: true, devices, granted } or { ok: false, detail }. `granted`
 * says whether it arrived able to publish, which is the one thing the page
 * needs to tell the person in front of it: "you're set up" versus "ask whoever
 * runs the site to approve this".
 */
export function addDevice(devices, record) {
  if (find(devices, record.credential_id) >= 0) {
    return { ok: false, detail: 'That device is already registered for this site.' };
  }

  // The first one is trusted; everything after waits for a person. Note this
  // asks whether a PUBLISHER exists, not whether the list is empty — a site
  // whose only devices are listed-but-not-allowed still has nobody who could
  // approve, so the next to arrive is the first that counts.
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

/**
 * Revoke a device.
 *
 * Marked rather than deleted, so the record of what was once trusted survives.
 * The one thing this refuses is removing the last publisher — a site with
 * nobody able to publish cannot grant anybody, and the way back is staff
 * editing the file by hand. Better to say no than to strand somebody.
 */
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

/**
 * The file as it should be written.
 *
 * Two spaces and a trailing newline, so a diff of somebody being added is one
 * readable block rather than one very long line. This file is meant to be
 * looked at — it is the record of who can touch a site.
 */
export const serialize = (devices) => `${JSON.stringify({ version: 1, devices }, null, 2)}\n`;
