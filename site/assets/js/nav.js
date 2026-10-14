// Mobile menu toggle; the page works without it. See docs/site.md.

const toggle = document.querySelector('.nav-toggle');
const nav = document.getElementById('site-nav');

if (toggle && nav) {
  toggle.addEventListener('click', () => {
    const open = nav.dataset.open === 'true';
    nav.dataset.open = String(!open);
    toggle.setAttribute('aria-expanded', String(!open));
  });
}
