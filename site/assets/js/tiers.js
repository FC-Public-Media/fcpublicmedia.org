// see docs/inline/site/assets/js/tiers.js.md#1

const radios = [...document.querySelectorAll('.tiers input[name="tier"]')];
const next = document.getElementById('tier-next');
const chosen = document.getElementById('tier-chosen');
const go = document.getElementById('tier-continue');

function show(radio) {
  if (!radio) return;
  chosen.textContent = `${radio.dataset.name}, $${radio.dataset.price} a year`;
  go.dataset.sku = radio.value;          // what the passkey-then-checkout step will send
  next.hidden = false;
  const url = new URL(location.href);
  url.searchParams.set('tier', radio.dataset.name.toLowerCase());
  history.replaceState(null, '', url);
}

radios.forEach((r) => r.addEventListener('change', () => show(r)));

const asked = new URLSearchParams(location.search).get('tier');
const start = radios.find((r) => r.dataset.name.toLowerCase() === asked) || radios.find((r) => r.checked);
if (start) {
  start.checked = true;
  show(start);
}
