// Which colours, and remembering it if we are allowed to.
//
// Light is the default and is what the stylesheet does on its own. This file
// exists for two things: honouring a stored preference of `dark` or `system`,
// and drawing the control that sets one. The head carries a copy of the first
// half inline, because doing it here would mean painting light and correcting
// it — a flash on every navigation for exactly the people who asked for dark.
//
// STORAGE IS BEST-EFFORT AND NEVER MENTIONED.
//
// Reading or writing localStorage THROWS when storage is blocked, rather than
// returning null, and blocking it is a real setting real people turn on. So
// every access is wrapped, and when it fails the choice is held in a variable
// for the life of the page instead. That visitor gets a working control that
// forgets between navigations, which is a smaller loss than being told about
// it. Nothing here ever asks anybody to change their settings.

const STORE = 'theme';
const DEFAULT = 'light';

/** Set when storage is refused, so the choice still holds for this page. */
let inMemory = null;

function read() {
  try {
    return localStorage.getItem(STORE) || inMemory || DEFAULT;
  } catch (error) {
    return inMemory || DEFAULT;
  }
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

/** The attribute the stylesheet actually reads. Only ever `dark` or absent. */
function apply(pref) {
  const dark = pref === 'dark' || (pref === 'system' && systemIsDark());
  if (dark) {
    document.documentElement.setAttribute('data-theme', 'dark');
  } else {
    document.documentElement.removeAttribute('data-theme');
  }
}

const picker = document.querySelector('[data-theme-picker]');

if (picker) {
  const current = read();
  apply(current);

  const chosen = picker.querySelector(`input[value="${current}"]`);
  if (chosen) chosen.checked = true;

  picker.hidden = false;

  picker.addEventListener('change', (event) => {
    const value = event.target.value;
    write(value);
    apply(value);
  });

  // Somebody on `system` who flips their laptop to dark at sunset should not
  // have to reload to see it.
  if (window.matchMedia) {
    window
      .matchMedia('(prefers-color-scheme: dark)')
      .addEventListener('change', () => {
        if (read() === 'system') apply('system');
      });
  }
}
