// GENERATED FILE — do not edit. The YAML beside it is canonical.
//
//   python3 bin/build-kiosk.py
//
// WHY THIS FILE EXISTS, AND IT IS NOT A PREFERENCE
// -----------------------------------------------
// The panel opens `brand/idle/index.html` as a local file, from a clone, with
// no server behind it. Measured in Chrome 2026-09-24:
//
//   file:// + fetch('welcome.yml')        -> TypeError: Failed to fetch
//   file:// + <script src="welcome.js">   -> works, repeatedly, with a
//                                           cache-buster on the src
//
// A `file://` page has an opaque origin, so fetch and XHR are both refused
// and no header can permit it. That makes the YAML unreadable by the one
// consumer this artifact has — which is why the same content is emitted a
// second time as an assignment a script tag can carry.
//
// This is TRANSPORT, not a second source of truth. It is generated from the
// same `kiosk/content.yml` in the same run and carries the SAME `revision`,
// copied rather than recomputed, so the two cannot disagree about what they
// describe. Read `welcome.yml` if you have a choice; read this if you are a
// browser looking at a file path.
//
// One assignment and nothing else. No logic, no fetch, no side effects.
window.FCPM_KIOSK = {
  "revision": "803f8df90221",
  "place": "Fort Collins Public Media",
  "room": "the welcome desk",
  "greeting": "Welcome in. Scan the code to check in, and help yourself to the guest Wi-Fi — there is nothing to sign up for.",
  "panels": [
    {
      "panel": "Checking in",
      "say": "new.fcpublicmedia.org/check-in/",
      "qr": {
        "image": "site/assets/img/check-in-qr.svg",
        "encodes": "https://new.fcpublicmedia.org/check-in/",
        "alt": "QR code linking to the check-in page"
      },
      "note": "Scan it with your own phone. Your visits stay on your phone — we don't make you an account."
    },
    {
      "panel": "Guest Wi-Fi",
      "say": "FC Public Media Guest",
      "note": "Open Wi-Fi settings and pick this network. The password is on the printed card by the desk, or ask and we'll tell you."
    },
    {
      "panel": "Need a hand?",
      "say": "Ask whoever is at the desk.",
      "note": "If nobody is about, the studio phone and email are on the contact page."
    }
  ]
};
