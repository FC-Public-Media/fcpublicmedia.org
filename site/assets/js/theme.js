// Footer "Match my system colours" toggle: light by default, dark when following a dark system.
// See docs/site.md.

const STORE = 'theme';
const FOLLOW = 'system';
const FIXED = 'light';

let inMemory = null;

function read() {
  let stored = null;
  try {
    stored = localStorage.getItem(STORE);
  } catch (error) {
    stored = null;
  }
  const pref = stored || inMemory || FIXED;
  // Anything but `light` (including a stored `dark`) means follow the system.
  return pref === FIXED ? FIXED : FOLLOW;
}

function write(value) {
  inMemory = value;
  try {
    localStorage.setItem(STORE, value);
  } catch (error) {
    // Storage blocked: the choice holds in memory for this page only.
  }
}

const systemIsDark = () =>
  window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;

/** The attribute the stylesheet reads. Only ever `dark`, or absent. */
function apply(pref) {
  if (pref === FOLLOW && systemIsDark()) {
    document.documentElement.setAttribute('data-theme', 'dark');
  } else {
    document.documentElement.removeAttribute('data-theme');
  }
}

const control = document.querySelector('[data-theme-toggle]');
const input = document.querySelector('[data-theme-input]');

/** Worth offering only when pressing it would do something, or already has. */
const worthShowing = () => systemIsDark() || read() === FOLLOW;

if (control && input) {
  const current = read();
  apply(current);
  input.checked = current === FOLLOW;
  control.hidden = !worthShowing();

  input.addEventListener('change', () => {
    const pref = input.checked ? FOLLOW : FIXED;
    write(pref);
    apply(pref);
  });

  // Re-apply and re-check visibility when the system scheme flips, without a reload.
  if (window.matchMedia) {
    window
      .matchMedia('(prefers-color-scheme: dark)')
      .addEventListener('change', () => {
        apply(read());
        control.hidden = !worthShowing();
      });
  }
}
