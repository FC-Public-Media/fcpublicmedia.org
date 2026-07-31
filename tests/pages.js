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
  { path: '/teach/', name: 'teach' },
  { path: '/policies/non-discrimination/', name: 'policy' },
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

module.exports = { PAGES, THIRD_PARTY, isThirdParty };
