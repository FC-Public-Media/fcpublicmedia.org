// Tilt stack videos (_includes/tilt-slot.html): play while on screen, never when less motion is asked for.

const videos = document.querySelectorAll('[data-tilt-video]');
const still = matchMedia('(prefers-reduced-motion: reduce)');

if (videos.length && !still.matches && 'IntersectionObserver' in window) {
  const seen = new IntersectionObserver((entries) => {
    for (const { target, isIntersecting } of entries) {
      if (isIntersecting) target.play().then(() => target.classList.add('is-playing'), () => {});
      else target.pause();
    }
  }, { rootMargin: '200px 0px' });
  videos.forEach((v) => seen.observe(v));
}
