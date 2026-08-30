// Follow the system, or don't. That is the whole setting.
//
// LIGHT IS THE DEFAULT AND IT IS NOT A CHOICE ANYBODY HAS TO MAKE. The palette
// reads well in light and the dark scheme was called drab, so following the
// system by default was handing most visitors the weaker of the two without
// asking. Off means light. On means whatever their machine says, which for
// almost everybody who goes looking for this is dark.
//
// WHY NOT A THIRD "DARK" OPTION. It only differs from "follow" for somebody
// whose system is light but who wants a dark site anyway, and that is a small
// group who mostly own a dark system already. One toggle is a state you can
// read at a glance; three radios is a decision.
//
// THE TOGGLE LOOKS INERT ON A LIGHT SYSTEM, and that is expected rather than
// broken. Switching it on changes nothing until the machine goes dark, which
// is exactly what "match my system" promises. The label says match, not dark,
// for that reason.
//
// STORAGE IS BEST-EFFORT AND NEVER MENTIONED. Reading localStorage THROWS when
// storage is blocked rather than returning null, and blocking it is a real
// setting real people turn on. Every access is wrapped; when it fails the
// choice lives in a variable for as long as the page does. That visitor gets a
// toggle that works and forgets on the next navigation, which is a smaller
// loss than being told about it. Nothing here ever asks anybody to change
// their settings.

const STORE = 'theme';
const FOLLOW = 'system';
const FIXED = 'light';

/** Set when storage is refused, so the choice still holds for this page. */
let inMemory = null;

function read() {
  let stored = null;
  try {
    stored = localStorage.getItem(STORE);
  } catch (error) {
    stored = null;
  }
  const pref = stored || inMemory || FIXED;
  // Anything that is not an explicit `light` counts as following — including
  // `dark` left over from the three-way this replaced.
  return pref === FIXED ? FIXED : FOLLOW;
}

function write(value) {
  inMemory = value;
  try {
    localStorage.setItem(STORE, value);
  } catch (error) {
    // Held in memory above. Not worth telling anybody about.
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

if (control && input) {
  const current = read();
  apply(current);
  input.checked = current === FOLLOW;

  control.hidden = false;

  input.addEventListener('change', () => {
    const pref = input.checked ? FOLLOW : FIXED;
    write(pref);
    apply(pref);
  });

  // Somebody following their system who flips the laptop to dark at sunset
  // should not have to reload to see it.
  if (window.matchMedia) {
    window
      .matchMedia('(prefers-color-scheme: dark)')
      .addEventListener('change', () => {
        if (read() === FOLLOW) apply(FOLLOW);
      });
  }
}
