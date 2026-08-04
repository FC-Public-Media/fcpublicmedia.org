// Every page the smoke tests visit. Add a page here and it is covered by all
// of them at once.

const PAGES = [
  { path: '/', name: 'home' },
  { path: '/watch/', name: 'watch' },
  { path: '/watch/archive/', name: 'archive' },
  { path: '/classes/', name: 'classes' },
  { path: '/equipment/', name: 'equipment' },
  { path: '/membership/', name: 'membership' },
  { path: '/reservations/', name: 'reservations' },
  { path: '/podcasts/', name: 'podcasts' },
  { path: '/podcasts/lcsnapshotnews/', name: 'podcast-detail' },
  { path: '/submit/', name: 'submit' },
  { path: '/bulletin-board/', name: 'bulletin-board' },
  { path: '/donate/', name: 'donate' },
  { path: '/nonprofits/', name: 'nonprofits' },
  { path: '/contact/', name: 'contact' },
  { path: '/about/', name: 'about' },
  { path: '/board/', name: 'board' },
  { path: '/teach/', name: 'teach' },
  { path: '/policies/non-discrimination/', name: 'policy' },
  { path: '/book/', name: 'book' },
  { path: '/register/', name: 'register' },
  { path: '/check-in/', name: 'check-in' },
  { path: '/check-in/poster/', name: 'check-in-poster' },
];

// Hosts we embed from. Requests to these are expected and are reported
// separately from same-origin failures, because "Cablecast is down" and "we
// shipped a broken link" need different responses.
const THIRD_PARTY = [
  'cablecast.tv',
  'youtube.com',
  'youtu.be',
  'instagram.com',
  'facebook.com',
  'conta.cc',
];

const isThirdParty = (url) => THIRD_PARTY.some((host) => url.includes(host));

// Console output we know comes from an embedded player rather than our code.
// Matched by text as a backstop, because not every console message carries a
// usable source URL — an iframe error with an empty location would otherwise
// be blamed on this site.
const THIRD_PARTY_CONSOLE = [
  'VIDEOJS:', // the Cablecast player
];

const isThirdPartyConsole = (text) =>
  THIRD_PARTY_CONSOLE.some((prefix) => text.includes(prefix));

module.exports = { PAGES, THIRD_PARTY, isThirdParty, isThirdPartyConsole };
