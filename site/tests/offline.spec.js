// The offline kit (sw.js): a page marked `offline: true` installs it; with no network, the check-in and
// /you/ still open, a check-in is still kept, and Show it still pours. Other pages install nothing.

const { test, expect } = require('./fixtures');

const kitReady = (page) =>
  page.evaluate(async () => {
    await navigator.serviceWorker.ready;
    const names = await caches.keys();
    const kit = names.find((n) => n.startsWith('fcpm-kit-'));
    if (!kit) return [];
    // Install adds the kit's files one by one; wait until the last ones are in.
    for (let i = 0; i < 50; i += 1) {
      const keys = (await (await caches.open(kit)).keys()).map((r) => new URL(r.url).pathname);
      if (keys.includes('/assets/js/composer/carrier.mjs') && keys.includes('/you/')) return keys;
      await new Promise((ok) => setTimeout(ok, 100));
    }
    return (await (await caches.open(kit)).keys()).map((r) => new URL(r.url).pathname);
  });

test.describe('offline kit', () => {
  test('a kit page installs the kit: its pages, scripts and the composer', async ({ page }) => {
    await page.goto('/check-in/');
    const kept = await kitReady(page);
    for (const path of ['/check-in/', '/you/', '/submit/', '/assets/js/checkin.js', '/assets/js/bottle.js',
      '/assets/js/composer/carrier.mjs', '/assets/css/site.css', '/manifest.webmanifest']) {
      expect(kept, path).toContain(path);
    }
  });

  test('with no network, a check-in is still made, kept and shown', async ({ page, context }) => {
    await page.goto('/check-in/');
    await kitReady(page);
    await page.evaluate(() => localStorage.clear());

    await context.setOffline(true);
    await page.goto('/check-in/');
    await page.locator('#profile-name').fill('Sam Rivera');
    await page.locator('[data-state="idle"] [data-action="check-in"]').click();
    await expect(page.locator('[data-state="done"]')).toBeVisible();
    await page.getByRole('link', { name: 'Show it' }).click();
    await expect(page.locator('#show-read')).toContainText('signed');

    await page.goto('/you/');
    await expect(page.locator('#cards li')).toContainText('Sam Rivera');
    await context.setOffline(false);
  });

  test('a page from the kit carries the manifest for the Home Screen', async ({ page }) => {
    await page.goto('/check-in/');
    const href = await page.locator('link[rel="manifest"]').getAttribute('href');
    const manifest = await (await page.request.get(href)).json();
    expect(manifest).toMatchObject({ start_url: '/check-in/', display: 'standalone' });
    expect(manifest.icons.map((i) => i.sizes)).toContain('512x512');
  });

  test('a page outside the kit installs nothing', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(300);
    expect(await page.evaluate(async () => (await navigator.serviceWorker.getRegistrations()).length)).toBe(0);
    await expect(page.locator('link[rel="manifest"]')).toHaveCount(0);
  });
});
