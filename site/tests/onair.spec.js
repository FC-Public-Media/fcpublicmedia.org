// What's on Channel 97, in the masthead: two lines like the wordmark (the programme, its slot), and on a
// narrow screen not at all: it gives up its room before any menu item gives up a word. /watch/ keeps its own bar.

const { test, expect } = require('./fixtures');

const SCHEDULE = {
  scheduleItems: [
    { show: 1, runDateTime: '2026-10-28T19:00:00-06:00' },
    { show: 2, runDateTime: '2026-10-28T20:30:00-06:00' },
  ],
  shows: [{ id: 1, title: 'Night Shift' }, { id: 2, title: 'Morning Show' }],
};

async function at(page, when) {
  await page.route('https://reflect-fcpublicmedia.cablecast.tv/**', (route) => route.fulfill({ json: SCHEDULE }));
  await page.clock.install({ time: new Date(when) });
}

const wide = (page) => page.viewportSize().width > 960;

test('the masthead says what is on and when it runs, or gives the room up', async ({ page }) => {
  await at(page, '2026-10-28T19:30:00-06:00');
  await page.goto('/join/');
  const bar = page.locator('.site-head-brand [data-onair]');
  if (wide(page)) {
    await expect(bar.locator('.onair-label')).toHaveText('Night Shift');
    await expect(bar.locator('.onair-slot')).toHaveText('7:00–8:30 PM');
  } else {
    await expect(bar).toBeHidden();
    await expect(page.locator('.site-nav a[aria-current="page"] .nav-word')).toHaveText('Join');
    await expect(page.locator('.site-nav a[aria-current="page"] .nav-word')).toBeVisible();
  }
});

test('/watch/ keeps its own bar at any width', async ({ page }) => {
  await at(page, '2026-10-28T19:30:00-06:00');
  await page.goto('/watch/');
  const bar = page.locator('.onair-inline');
  await expect(bar.locator('.onair-label')).toHaveText('Night Shift');
  await expect(bar.locator('.onair-slot')).toHaveText('7:00–8:30 PM');
});
