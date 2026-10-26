// The pages every smoke test visits, and the third-party hosts and console text it excuses.
// See docs/site.md.

const PAGES = [
  { path: '/', name: 'home' },
  { path: '/watch/', name: 'watch' },
  { path: '/learn/', name: 'learn' },
  { path: '/join/', name: 'join' },
  { path: '/reserve/', name: 'reserve' },
  { path: '/submit/', name: 'submit' },
  { path: '/meet/', name: 'meet' },
  { path: '/check-in/', name: 'check-in' },
  { path: '/check-in/poster/', name: 'check-in-poster' },
  { path: '/authorize/', name: 'authorize' },
  { path: '/you/upload/', name: 'upload' },
  { path: '/you/settings/', name: 'settings' },
  { path: '/you/devices/', name: 'devices' },
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

// The class the site bakes in (site/_includes/class-config.html): calendar.json's first session when
// it has one, else classes.yml's, Podcasting 101. Class tests set their clock by it.
function bakedClass() {
  const cal = JSON.parse(require('fs').readFileSync(require('path').join(__dirname, '..', '_data', 'calendar.json'), 'utf8'));
  const s = (cal.sessions || [])[0];
  return s ? { start: Date.parse(s.starts), title: s.title, room: s.room }
           : { start: Date.parse('2026-08-12T00:00:00Z'), title: 'Podcasting 101', room: 'Podcast Studio' };
}

module.exports = { PAGES, THIRD_PARTY, isThirdParty, isThirdPartyConsole, bakedClass };
