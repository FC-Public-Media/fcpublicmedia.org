# `worker/src/enroll.js`

Moved out of the file. Unreviewed.

## 1

Above `/** Devices that still count. A revoked record stays for the audit, inert. */`

Who is on the list, and what they may do.

Pure functions over the array in .auth/devices.json. No network, no crypto,
no opinions about who asked — by the time anything here runs, the asking has
already been settled. Kept separate because the rules below are the ones
worth being able to read in one screen.

THE RULE THIS FILE EXISTS TO ENCODE
-----------------------------------
Enrollment and authority are different things (DESIGN-NOTES, "Enrollment and
authority are two different things"). Being listed is enrollment. Being
allowed to publish is authority. A claim link can be forwarded, and that is
survivable precisely because forwarding it can only get somebody listed.

  1. The FIRST device to bind is trusted. Nobody is there to approve it, the
     owner is the one who asked for the site, and a site with no publisher
     is a site nobody can use.
  2. Every device after that arrives listed and not allowed, and an existing
     publisher flips it. The owner approves a co-producer's phone from their
     own phone; staff are not in the loop.

A forwarded link is worthless the moment the owner has enrolled — which they
will have, because they are the one who asked.

## 2

Above `export function addDevice(devices, record) {`

Add a device.

Returns { ok: true, devices, granted } or { ok: false, detail }. `granted`
says whether it arrived able to publish, which is the one thing the page
needs to tell the person in front of it: "you're set up" versus "ask whoever
runs the site to approve this".

## 3

Above `const granted = !anyPublisher(devices);`

The first one is trusted; everything after waits for a person. Note this
asks whether a PUBLISHER exists, not whether the list is empty — a site
whose only devices are listed-but-not-allowed still has nobody who could
approve, so the next to arrive is the first that counts.

## 4

Above `export function revokeDevice(devices, credentialId) {`

Revoke a device.

Marked rather than deleted, so the record of what was once trusted survives.
The one thing this refuses is removing the last publisher — a site with
nobody able to publish cannot grant anybody, and the way back is staff
editing the file by hand. Better to say no than to strand somebody.

## 5

Above `export const serialize = (devices) => ${JSON.stringify({ version: 1, devices }, null, 2)}\n;`

The file as it should be written.

Two spaces and a trailing newline, so a diff of somebody being added is one
readable block rather than one very long line. This file is meant to be
looked at — it is the record of who can touch a site.
