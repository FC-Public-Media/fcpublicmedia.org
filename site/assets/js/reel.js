// The hero's background video.
//
// It is the first thing on screen, so "lazy" cannot mean "wait until it scrolls into view" — it
// means do not compete with first paint. The markup carries `preload="none"` and no `autoplay`, so
// nothing is fetched until this asks, and this waits until the page has gone idle. Until then the
// hero's own photograph (`hero_image`) is what is showing, which is also what shows if the video
// never arrives.
//
// The control is the pause button in the hero panel, on the brand plane. See _includes/reel.html.

const video = document.querySelector('[data-reel-video]');
const toggle = document.querySelector('[data-reel-toggle]');
const label = document.querySelector('[data-reel-label]');

// Asked for less motion: never start it. The still stays, and the button still works, so it is
// something you can choose rather than something moving at you.
const still = matchMedia('(prefers-reduced-motion: reduce)');

if (video) {
  // Only now is there a control worth showing: with no script the still is the whole story, and a
  // button that does nothing is worse than no button.
  if (toggle) toggle.hidden = false;

  let wanted = !still.matches;

  const state = () => {
    const playing = !video.paused && !video.ended;
    video.classList.toggle('is-playing', playing);
    if (toggle) toggle.setAttribute('aria-pressed', String(playing));
    if (label) label.textContent = playing ? 'Pause the background video' : 'Play the background video';
  };

  // play() rejects when the browser declines; a muted loop is usually allowed, but not always, and
  // either way the button should end up saying what the next click will do.
  const play = () => video.play().then(state, state);

  video.addEventListener('play', state);
  video.addEventListener('pause', state);

  if (toggle) {
    toggle.addEventListener('click', () => {
      wanted = video.paused;
      if (wanted) play();
      else video.pause();
    });
  }

  // Nothing to decode for a tab nobody is looking at.
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden') video.pause();
    else if (wanted) play();
  });

  const start = () => { if (wanted) play(); else state(); };

  if ('requestIdleCallback' in window) requestIdleCallback(start, { timeout: 3000 });
  else addEventListener('load', () => setTimeout(start, 400), { once: true });

  state();
}
