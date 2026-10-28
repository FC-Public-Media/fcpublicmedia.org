// Two halves of a page (/reserve/): side by side on a wide screen, where nothing is hidden; tabs on a
// phone. The tab marked aria-selected in the page opens first, unless the address names something in a
// half (#equipment, its heading).

const halves = document.querySelector('[data-halves]');
// Its own tab bar only: a half can have tabs of its own (the studio's weeks).
const tabs = [...halves.querySelectorAll('.halves-tabs [role="tab"]')];
const parts = [...halves.querySelectorAll('.half')];

function open(name) {
  for (const tab of tabs) tab.setAttribute('aria-selected', String(tab.dataset.half === name));
  // .is-away only hides on a phone; the wide layout ignores it.
  for (const part of parts) part.classList.toggle('is-away', part.dataset.half !== name);
}

// The address takes the half's heading id, so it opens the same half again whatever the heading says.
tabs.forEach((tab) => tab.addEventListener('click', () => {
  open(tab.dataset.half);
  const heading = parts.find((part) => part.dataset.half === tab.dataset.half).querySelector('h2[id]');
  history.replaceState(null, '', `#${heading ? heading.id : tab.dataset.half}`);
}));

const named = location.hash.length > 1 && document.getElementById(decodeURIComponent(location.hash.slice(1)));
const asked = named && parts.find((part) => part.contains(named));
open(asked ? asked.dataset.half : tabs.find((tab) => tab.getAttribute('aria-selected') === 'true').dataset.half);
halves.querySelector('.halves-tabs').hidden = false;
