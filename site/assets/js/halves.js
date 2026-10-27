// Two halves of a page (/reserve/): side by side on a wide screen, where nothing is hidden; tabs on a
// phone. The tab marked aria-selected in the page opens first, unless the address names something in a
// half (#equipment, its heading).

const halves = document.querySelector('[data-halves]');
const tabs = [...halves.querySelectorAll('[role="tab"]')];
const parts = [...halves.querySelectorAll('.half')];

function open(name) {
  for (const tab of tabs) tab.setAttribute('aria-selected', String(tab.dataset.half === name));
  // .is-away only hides on a phone; the wide layout ignores it.
  for (const part of parts) part.classList.toggle('is-away', part.dataset.half !== name);
}

tabs.forEach((tab) => tab.addEventListener('click', () => {
  open(tab.dataset.half);
  history.replaceState(null, '', `#${tab.dataset.half}`);
}));

const named = location.hash.length > 1 && document.getElementById(decodeURIComponent(location.hash.slice(1)));
const asked = named && parts.find((part) => part.contains(named));
open(asked ? asked.dataset.half : tabs.find((tab) => tab.getAttribute('aria-selected') === 'true').dataset.half);
halves.querySelector('.halves-tabs').hidden = false;
