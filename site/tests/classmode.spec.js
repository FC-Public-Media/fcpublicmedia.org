// The clock is mocked. Podcasting 101 (site/_data/classes.yml) runs 2026-08-12 00:00–02:00 UTC.

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

    // The QR shows whether or not a class is on.
    await expect(page.locator('.hero-qr img')).toBeVisible();
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

  test('puts a running class above the fold', async ({ page }) => {
    // Position, not just presence: someone in the doorway should not scroll to find the class.
    await visitAt(page, at(20));

    const box = await slot(page).boundingBox();
    expect(box, 'the class card has no box').not.toBeNull();

    const fold = page.viewportSize().height;
    expect(box.y, 'the class card starts below the fold').toBeLessThan(fold);
    expect(
      box.y + box.height,
      'the class card runs past the fold',
    ).toBeLessThanOrEqual(fold);

    // On a phone the class displaces the headline, not the QR.
    const qr = await page.locator('a.hero-qr').boundingBox();
    expect(qr, 'the QR has no box').not.toBeNull();
    expect(qr.y + qr.height, 'the QR fell below the fold').toBeLessThanOrEqual(fold);
  });

  test('the join link carries no class information', async ({ page }) => {
    await visitAt(page, at(20));

    // A bare link: check-in decides from the same data, and a shared link outlives the class.
    const join = page.locator('[data-class-join]');
    await expect(join).toBeVisible();
    await expect(join).toHaveAttribute('href', '/check-in/');
    await expect(join).toHaveText("I'm here for the class");
  });

  test('the join link invites rather than announces before the start', async ({ page }) => {
    await visitAt(page, at(-60));
    await expect(page.locator('[data-class-join]')).toHaveText('Check in for this class');
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
    // Main frame only: the Cablecast player iframe loads its own third-party scripts.
    const requests = [];
    page.on('request', (request) => {
      let ownFrame = false;
      try {
        ownFrame = request.frame() === page.mainFrame();
      } catch (error) {
        return; // service worker or a frame already gone
      }
      if (!ownFrame) return;

      // The page's own document is not a fetch.
      if (request.isNavigationRequest()) return;

      const url = request.url();
      // The on-air strip calls Cablecast from this frame; that is another feature.
      if (isThirdParty(url)) return;
      if (url.includes('/assets/')) return;
      requests.push(url);
    });

    await visitAt(page, at(20));
    await expect(slot(page)).toBeVisible();

    expect(requests, 'class mode fetched something').toEqual([]);

    // And the schedule really is inline rather than loaded.
    const inline = await page.locator('#class-config').textContent();
    expect(JSON.parse(inline).sessions.length).toBeGreaterThan(0);
  });
});
