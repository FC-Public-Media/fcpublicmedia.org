// Class mode is entirely a function of the wall clock, so the clock is mocked.
// Without that these tests would only pass in August 2026 between six and
// eight in the evening, which is not a test.
//
// Session times come from _data/classes.yml. Podcasting 101 runs
// 2026-08-11 18:00–20:00 in Denver, which is 2026-08-12 00:00–02:00 UTC.
// lead_minutes is 90, late_minutes is 45.

const { test, expect } = require('@playwright/test');
const { isThirdParty } = require('./pages');

const START = Date.parse('2026-08-12T00:00:00Z');
const MINUTE = 60000;

const at = (offsetMinutes) => new Date(START + offsetMinutes * MINUTE);

const slot = (page) => page.locator('[data-class-slot]');
const card = (page) => page.locator('[data-checkin-card]');

async function visitAt(page, when) {
  await page.clock.install({ time: when });
  await page.goto('/');
  // classmode.js runs on a deferred script; give it a turn.
  await page.waitForTimeout(200);
}

test.describe('class mode', () => {
  test('stays out of the way when no class is running', async ({ page }) => {
    await visitAt(page, at(-24 * 60)); // a day before

    await expect(slot(page)).toBeHidden();
    await expect(card(page)).toHaveAttribute('data-class-mode', 'off');

    // The ordinary check-in card is untouched.
    await expect(page.locator('.checkin-card')).toBeVisible();
  });

  test('announces a class that is about to start', async ({ page }) => {
    await visitAt(page, at(-60)); // inside the 90 minute lead

    await expect(slot(page)).toBeVisible();
    await expect(card(page)).toHaveAttribute('data-class-mode', 'soon');
    await expect(page.locator('[data-class-eyebrow]')).toHaveText('Starting soon');
    await expect(page.locator('[data-class-title]')).toHaveText('Podcasting 101');
    await expect(page.locator('[data-class-when]')).toContainText('Starts at');
    await expect(page.locator('[data-class-room]')).toHaveText('Podcast Studio');
  });

  test('is quiet before the lead window opens', async ({ page }) => {
    await visitAt(page, at(-120)); // 2 hours out, lead is 90 minutes
    await expect(slot(page)).toBeHidden();
  });

  test('says a class is happening, and that you can still join', async ({ page }) => {
    await visitAt(page, at(20)); // 20 minutes in, inside the 45 minute late window

    await expect(card(page)).toHaveAttribute('data-class-mode', 'late');
    await expect(page.locator('[data-class-eyebrow]')).toHaveText('Happening now');
    await expect(page.locator('[data-class-when]')).toContainText('On now until');
    await expect(page.locator('[data-class-late]')).toBeVisible();
  });

  test('stops inviting latecomers once it is too late', async ({ page }) => {
    await visitAt(page, at(90)); // well past the late window, class still running

    await expect(card(page)).toHaveAttribute('data-class-mode', 'now');
    await expect(slot(page)).toBeVisible();
    await expect(page.locator('[data-class-late]')).toBeHidden();
  });

  test('clears once the class has ended', async ({ page }) => {
    await visitAt(page, at(125)); // class ran 0–120

    await expect(slot(page)).toBeHidden();
    await expect(card(page)).toHaveAttribute('data-class-mode', 'off');
  });

  test('the join link primes the check-in reason', async ({ page }) => {
    await visitAt(page, at(20));

    const join = page.locator('[data-class-join]');
    await expect(join).toBeVisible();
    await expect(join).toHaveAttribute('href', '/check-in/?reason=Class');
  });

  test('offers other classes rather than only this one', async ({ page }) => {
    await visitAt(page, at(20));
    await expect(page.locator('[data-class-signup]')).toHaveAttribute('href', '/classes/');
  });

  test('switches on by itself as the class begins', async ({ page }) => {
    await visitAt(page, at(-100)); // before the lead window
    await expect(slot(page)).toBeHidden();

    // Someone leaves the page open while they wait.
    await page.clock.fastForward('45:00');
    await expect(slot(page)).toBeVisible();
    await expect(card(page)).toHaveAttribute('data-class-mode', 'soon');
  });

  test('switches off by itself when the class ends', async ({ page }) => {
    await visitAt(page, at(110)); // ten minutes from the end
    await expect(slot(page)).toBeVisible();

    await page.clock.fastForward('20:00');
    await expect(slot(page)).toBeHidden();
  });

  test('decides from the build, without fetching a schedule', async ({ page }) => {
    // The homepage does make third-party requests — the Cablecast on-air
    // strip, the live embed, archive thumbnails. Those are other features.
    // What class mode must not do is fetch a calendar.
    const requests = [];
    page.on('request', (request) => {
      const url = request.url();
      if (!isThirdParty(url) && !url.includes('/assets/')) requests.push(url);
    });

    await visitAt(page, at(20));
    await expect(slot(page)).toBeVisible();

    // Only the document itself.
    const extra = requests.filter((url) => !url.match(/127\.0\.0\.1:\d+\/$/));
    expect(extra, 'class mode fetched something').toEqual([]);

    // And the schedule really is inline rather than loaded.
    const inline = await page.locator('#class-config').textContent();
    expect(JSON.parse(inline).sessions.length).toBeGreaterThan(0);
  });
});
