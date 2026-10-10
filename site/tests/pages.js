// The pages every smoke test visits, and the third-party hosts and console text it excuses.
// See docs/site.md.

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

// Embed hosts: their failures are reported apart from same-origin failures.
const THIRD_PARTY = [
  'cablecast.tv',
  'youtube.com',
  'youtu.be',
  'instagram.com',
  'facebook.com',
  'conta.cc',
  'booqable.com', // the /reserve/ embed renders inline, but its script loads from here
];

const isThirdParty = (url) => THIRD_PARTY.some((host) => url.includes(host));

// Embedded-player console text, matched by text since some messages carry no source URL.
const THIRD_PARTY_CONSOLE = [
  'VIDEOJS:', // the Cablecast player
];

const isThirdPartyConsole = (text) =>
  THIRD_PARTY_CONSOLE.some((prefix) => text.includes(prefix));

module.exports = { PAGES, THIRD_PARTY, isThirdParty, isThirdPartyConsole };
