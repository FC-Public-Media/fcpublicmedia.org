# `site/assets/js/checkin.js`

Moved out of the file. Unreviewed.

## 1

Above `import { readConfig, pickSession, sessionKey, clockTime, watch } from './classes.js';`

Check-in, recorded on the visitor's own device.

There is no server. Everything here reads and writes storage on the phone in
front of the person, and nothing leaves it.

The shape of the thing:

  1. Tap "Check in". The page asks for location once.
  2. If you are at the studio, you are checked in.
  3. If you are not, the check-in becomes *pending*: the page shows
     directions, and finishes by itself when you arrive. Leave it open,
     walk in, look down, it is done.

Re-checks happen every few minutes and only while the tab is visible, so a
page left open in a pocket costs nothing.

The device identifier is a random UUID generated on first visit. It is not
derived from anything about the device or the person, it is never sent
anywhere, and "Forget this device" deletes it.

## 2

Above `let session = null;`

The session currently in a window, or null. Re-read rather than cached, so
a page left open through the start of a class behaves correctly.

## 3

Above `function readStore(key, fallback) {`

Private browsing makes localStorage throw rather than return null, so every
access goes through these.

## 4

Above `async function requestPersistence() {`

Ask the browser to exempt this origin from routine eviction. Chrome decides
silently on engagement heuristics; Safari grants it largely when the site is
a Home Screen web app, which is why the page says so rather than relying on
this call alone.

## 5

Above `function metresBetween(lat1, lon1, lat2, lon2) {`

Haversine. Good to a few metres at these distances, which is far better
than a phone's own fix.

## 6

Above `enableHighAccuracy: false,`

Low accuracy on purpose: a coarse fix is plenty against a 200m
radius and costs far less battery than a GPS lock.

## 7

Above `maximumAge: fresh ? 0 : 120000,`

When someone taps "check again", they have almost certainly just
moved, so a cached fix is exactly the wrong answer — it would tell
a person standing in the doorway that they are still down the
street. Background polls reuse a recent fix instead, which is where
the battery saving actually comes from.

## 8

Above `const who = entry.email`

An unconfirmed address is marked in the list itself. Someone reading
their own history should be able to see which visits carry an address we
actually checked, without having to remember when they got the link.

## 9

Above `function deviceKind(ua = navigator.userAgent, model = '') {`

What to call this phone before anyone has said. Not a device fingerprint:
only the kind of thing it is, in words a person would use, so the default
is already useful ("iPhone", "Samsung", "Windows PC") and changing it is a
refinement rather than a chore. Chrome can say the model (Pixel 8, or a
Samsung's SM- number) when asked; nothing else is asked for.

## 10

Above `el('device-id').textContent = device.id.slice(0, 8);`

A fragment is enough to tell two devices apart. There is no reason to put
a full identifier on screen.

## 11

Above `email: el('profile-email').value.trim().toLowerCase(),`

Only meaningful while there is no claim; a confirmed address supersedes
it rather than overwriting it, so removing the claim leaves whatever the
visitor had typed before.

## 12

Above `function visitReason() {`

Nobody is asked why they came. The code they scanned says so — a QR aimed
at /check-in/?reason=Class does what it looks like it does — or a class
being on does. Only the reasons _data/checkin.yml lists are accepted, so a
made-up one in the URL is ignored rather than recorded.

## 13

Above `async function getAccessIdentity() {`

Three ways this page can know an email address, in descending order of how
much they are worth:

  claim   a signed token we minted and mailed. Verified, and the proof is
          kept so anyone downstream can check it themselves.
  access  Cloudflare Access authenticated the visitor at the edge. Verified,
          but only while the request is ours to make — nothing portable
          comes out of it.
  typed   the visitor told us. Unverified, and recorded as such.

A typed address is not treated as a failure. Most people will never have a
claim, and an address they typed still lines their visits up with the
membership list, which is the whole point.

## 14

Above `async function redeemClaim(token) {`

Take a claim from the URL, check it, and keep it if it holds.

The stored record includes the token itself, not just the address read out
of it. That is the part with any value: the address alone is a string this
device wrote, while the token is something we signed and anyone can re-check.

## 15

Above `email_verified: Boolean(email) && verified,`

Recorded rather than inferred. A row that says an address was
confirmed has to mean it, and a row that says otherwise is still a
perfectly good row.

## 16

Above `verified: Boolean(reading),`

Distance only — the coordinates themselves are not kept, even locally.
Knowing the check-in was verified is the useful part.

## 17

Above `el('done-detail').textContent = [`

The pass already says who. This says when, and whether the address on
the visit is one we checked.

## 18

Above `attempt({ silent: true });`

Coming back to the page is the strongest signal that something changed,
so check immediately as well as restarting the clock.

## 19

Above `function renderClass() {`

The same question the homepage asks, answered by the same function over the
same data. Neither page can drift from the other, and the QR on the door
stays a permanent link that carries no class information.

## 20

Above `const noted = getRsvps().includes(sessionKey(session));`

Before it starts, offer to note intent. Once it is running, the thing to
do is check in, so the offer goes away.

## 21

Above `renderReason();`

A class arrival is a check-in with the reason already known, unless the
code that was scanned said otherwise.

## 22

Above `claim: getClaim(),`

The whole token, so a restored backup is verified again rather than
trusted. Moving a file between devices must not be a way to manufacture
a confirmed address.

## 23

Above `const seen = new Set(getHistory().map((entry) => entry.at));`

Merge rather than replace, so importing a backup onto a device used
since does not discard the newer visits.

## 24

Above `let note = '';`

A claim in the file is re-checked from scratch. The file said it was
verified; that is not evidence, and the signature is.

## 25

Above `const VIEWS = ['visits', 'device'];`

The pass is one screen; the visits and this phone are screens of their own,
named by the address's # so Back and a bookmark both work. Anything else in
the # (a claim link, say) is the pass.

## 26

Above `function backToPass(event) {`

"Pass" goes back if that is where you came from, so the history does not
fill up with trips between screens. Opened straight at #visits, it replaces.

## 27

Above `const arriving = claimFromLocation();`

Before anything is rendered that depends on it: a claim arriving in the
URL is the reason this page was opened, and the history rows below should
already know about it.

## 28

Above `for (const id of ['profile-name', 'profile-email']) {`

Form state is written on every change, so closing the page mid-answer and
coming back later loses nothing.

## 29

Above `const contact = el('use-contact');`

A contact card, where the browser can offer one (Android Chrome's Contact
Picker). The person picks the card; nothing else in their contacts is
read. Elsewhere autocomplete="name" and "email" already let the keyboard
offer their own card, which is the same feeling without a button.

## 30

Above `if (classConfig) watch(renderClass);`

Re-evaluated on a timer while visible, so a page open through the start of
a class updates itself the same way the homepage does.

## 31

Above `if (getPending()) {`

A pending check-in survives a reload — pick it back up rather than making
someone start again.
