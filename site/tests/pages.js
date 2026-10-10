// see docs/inline/site/tests/pages.js.md#1

const PAGES = [
  { path: '/', name: 'home' },
  { path: '/watch/', name: 'watch' },
  { path: '/watch/archive/', name: 'archive' },
  { path: '/watch/under-the-marquee/', name: 'show' },
  { path: '/classes/', name: 'classes' },
  { path: '/membership/', name: 'membership' },
  { path: '/reserve/', name: 'reserve' },
  { path: '/podcasts/', name: 'podcasts' },
  { path: '/podcasts/lcsnapshotnews/', name: 'podcast-detail' },
  { path: '/submit/', name: 'submit' },
  { path: '/bulletin-board/', name: 'bulletin-board' },
  { path: '/donate/', name: 'donate' },
  { path: '/nonprofits/', name: 'nonprofits' },
  { path: '/contact/', name: 'contact' },
  { path: '/about/', name: 'about' },
  { path: '/meet/', name: 'meet' },
  { path: '/teach/', name: 'teach' },
  { path: '/policies/non-discrimination/', name: 'policy' },
  { path: '/book/', name: 'book' },
  { path: '/register/', name: 'register' },
  { path: '/authorize/', name: 'authorize' },
  { path: '/upload/', name: 'upload' },
  { path: '/settings/', name: 'settings' },
  { path: '/devices/', name: 'devices' },
  { path: '/check-in/', name: 'check-in' },
  { path: '/check-in/poster/', name: 'check-in-poster' },
];

// see docs/inline/site/tests/pages.js.md#2
const THIRD_PARTY = [
  'cablecast.tv',
  'youtube.com',
  'youtu.be',
  'instagram.com',
  'facebook.com',
  'conta.cc',
  // see docs/inline/site/tests/pages.js.md#3
  'booqable.com',
];

const isThirdParty = (url) => THIRD_PARTY.some((host) => url.includes(host));

// see docs/inline/site/tests/pages.js.md#4
const THIRD_PARTY_CONSOLE = [
  'VIDEOJS:', // the Cablecast player
];

const isThirdPartyConsole = (text) =>
  THIRD_PARTY_CONSOLE.some((prefix) => text.includes(prefix));

module.exports = { PAGES, THIRD_PARTY, isThirdParty, isThirdPartyConsole };
