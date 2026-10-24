// Tiles | List for the Booqable store on /reserve/: one class on .booqable-store, remembered per browser.
// Tiles are Booqable's own; list is site.css under .is-list. See docs/payments.md#booqable.

const KEY = 'fcpm.booqable.view';
const store = document.querySelector('.booqable-store');
const picker = document.querySelector('.booqable-view');

// Private browsing makes localStorage throw.
function read() {
  try { return window.localStorage.getItem(KEY); } catch (error) { return null; }
}
function write(view) {
  try { window.localStorage.setItem(KEY, view); } catch (error) { /* the choice lasts this page only */ }
}

function show(view) {
  store.classList.toggle('is-list', view === 'list');
  for (const button of picker.querySelectorAll('button')) {
    button.setAttribute('aria-pressed', String(button.dataset.view === view));
  }
}

if (store && picker) {
  show(read() === 'tiles' ? 'tiles' : 'list');
  picker.addEventListener('click', (event) => {
    const button = event.target.closest('button[data-view]');
    if (!button) return;
    show(button.dataset.view);
    write(button.dataset.view);
  });
  picker.hidden = false;
}
