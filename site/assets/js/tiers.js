// Membership tiles: keeps ?tier= in the address (replaced, never pushed), and picks it again on arrival.

const radios = [...document.querySelectorAll('.tiers input[name="tier"]')];
const slug = (radio) => radio.value.replace(/^membership:/, '');

radios.forEach((radio) => radio.addEventListener('change', () => {
  const url = new URL(location.href);
  url.searchParams.set('tier', slug(radio));
  history.replaceState(null, '', url);
}));

const asked = new URLSearchParams(location.search).get('tier');
const start = radios.find((radio) => slug(radio) === asked);
if (start) start.checked = true;
