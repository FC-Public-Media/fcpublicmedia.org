// Tests for things hosted by someone else: the Cablecast player, show pages,
// and thumbnails.
//
// These need network access and will fail if Cablecast is down, which is why
// they are separated from smoke.spec.js. Skip them with:
//
//     npx playwright test --grep-invert @external
//
// Why these exist at all: Cablecast's viewer is a single-page app. Requesting
// a show that does not exist still returns HTTP 200 and a full HTML shell —
// verified with /internetchannel/show/999999. So checking status codes proves
// nothing about whether a link works. The only way to know is to render the
// page and look for the player.

const { test, expect } = require('@playwright/test');

const CABLECAST = 'https://reflect-fcpublicmedia.cablecast.tv';
const LIVE_EMBED = `${CABLECAST}/internetchannel/watch-live-embed?streamId=1`;

test.describe('embeds @external', () => {
  test('the live player embed mounts a video element @external', async ({ page }) => {
    await page.goto(LIVE_EMBED, { waitUntil: 'domcontentloaded' });

    // The player is injected by the SPA, so wait for the element rather than
    // trusting the response.
    await expect(page.locator('video')).toBeAttached({ timeout: 30_000 });
  });

  test('the homepage live embed is pointed at the right place @external', async ({ page }) => {
    await page.goto('/');

    const frame = page.locator('iframe[src*="watch-live-embed"]');
    await expect(frame).toHaveCount(1);
    await expect(frame).toHaveAttribute('src', LIVE_EMBED);

    // Confirm the iframe actually produced a document rather than a blocked
    // or errored frame.
    const content = page.frameLocator('iframe[src*="watch-live-embed"]');
    await expect(content.locator('body')).toBeAttached({ timeout: 30_000 });
  });

  test('archive links open a real show page @external', async ({ page }) => {
    await page.goto('/watch/archive/');

    const hrefs = await page.$$eval('[data-archive] li a', (links) =>
      links.map((a) => a.href).filter((href) => href.includes('/internetchannel/show/'))
    );
    expect(hrefs.length, 'no show links found in the archive').toBeGreaterThan(0);

    // A sample, not all 1,060 — enough to catch a wrong URL shape, which is
    // the failure mode that matters. A per-show data problem is Cablecast's
    // to fix, not this site's.
    const sample = [hrefs[0], hrefs[Math.floor(hrefs.length / 2)], hrefs[hrefs.length - 1]];

    for (const href of sample) {
      await page.goto(href, { waitUntil: 'domcontentloaded' });
      // The SPA renders something show-shaped: a heading or a player. If the
      // URL pattern were wrong we would get the shell and nothing else.
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
        // 403 and 429 are what social networks return to automated clients;
        // they mean "we saw you", not "this link is wrong".
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
