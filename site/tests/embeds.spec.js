// see docs/inline/site/tests/embeds.spec.js.md#1

const { test, expect } = require('@playwright/test');

const CABLECAST = 'https://reflect-fcpublicmedia.cablecast.tv';
const LIVE_EMBED = `${CABLECAST}/internetchannel/watch-live-embed?streamId=1`;

test.describe('embeds @external', () => {
  test('the live player embed mounts a video element @external', async ({ page }) => {
    await page.goto(LIVE_EMBED, { waitUntil: 'domcontentloaded' });

    // see docs/inline/site/tests/embeds.spec.js.md#2
    await expect(page.locator('video')).toBeAttached({ timeout: 30_000 });
  });

  test('the homepage live embed is pointed at the right place @external', async ({ page }) => {
    await page.goto('/');

    const frame = page.locator('iframe[src*="watch-live-embed"]');
    await expect(frame).toHaveCount(1);
    await expect(frame).toHaveAttribute('src', LIVE_EMBED);

    // see docs/inline/site/tests/embeds.spec.js.md#3
    const content = page.frameLocator('iframe[src*="watch-live-embed"]');
    await expect(content.locator('body')).toBeAttached({ timeout: 30_000 });
  });

  test('archive links open a real show page @external', async ({ page }) => {
    await page.goto('/watch/archive/');

    const hrefs = await page.$$eval('[data-archive] li a', (links) =>
      links.map((a) => a.href).filter((href) => href.includes('/internetchannel/show/'))
    );
    expect(hrefs.length, 'no show links found in the archive').toBeGreaterThan(0);

    // see docs/inline/site/tests/embeds.spec.js.md#4
    const sample = [hrefs[0], hrefs[Math.floor(hrefs.length / 2)], hrefs[hrefs.length - 1]];

    for (const href of sample) {
      await page.goto(href, { waitUntil: 'domcontentloaded' });
      // see docs/inline/site/tests/embeds.spec.js.md#5
      await expect(
        page.locator('video, h1, .show-title').first(),
        `${href} did not render a show`
      ).toBeAttached({ timeout: 30_000 });
    }
  });

  test('thumbnails load rather than showing broken images @external', async ({ page }) => {
    await page.goto('/watch/');
    await page.waitForLoadState('networkidle');

    const broken = await page.$$eval('img', (images) =>
      images
        .filter((img) => img.complete && img.naturalWidth === 0)
        .map((img) => img.src)
    );

    expect(broken, 'images that failed to load').toEqual([]);
  });
});

test.describe('outbound links @external', () => {
  test('every external link in the footer resolves @external', async ({ page, request }) => {
    await page.goto('/');

    const origin = new URL(page.url()).origin;
    const external = await page.$$eval('.site-foot a[href]', (as) => as.map((a) => a.href));

    const offsite = [...new Set(external)].filter(
      (href) => href.startsWith('http') && !href.startsWith(origin)
    );

    const broken = [];
    for (const href of offsite) {
      try {
        const response = await request.get(href, {
          failOnStatusCode: false,
          timeout: 20_000,
        });
        // see docs/inline/site/tests/embeds.spec.js.md#6
        if (response.status() >= 400 && ![403, 405, 429].includes(response.status())) {
          broken.push(`${href} -> ${response.status()}`);
        }
      } catch (error) {
        broken.push(`${href} -> ${error.message.split('\n')[0]}`);
      }
    }

    expect(broken, 'broken outbound links').toEqual([]);
  });
});
