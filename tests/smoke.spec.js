// Smoke tests: does every page load without anything visibly broken?
//
// These run against local output by default and need no network. They are the
// ones that should stay green all the time.
//
// The point of these is to surface failures that are invisible in normal use —
// especially on a phone, where there is no console to look at.

const { test, expect } = require('@playwright/test');
const { PAGES, isThirdParty, isThirdPartyConsole } = require('./pages');

/**
 * Attach listeners before navigating and return the collected problems.
 * Third-party failures are kept separate: an outage at Cablecast is not the
 * same event as a link we got wrong, and conflating them makes the suite
 * flaky enough that people stop trusting it.
 */
function watch(page) {
  const consoleErrors = [];
  const pageErrors = [];
  const ownFailures = [];
  const thirdPartyFailures = [];

  page.on('console', (message) => {
    if (message.type() !== 'error') return;

    // Console messages from inside an embedded iframe surface on the parent
    // page's console, so a third-party player's internal errors would
    // otherwise fail an assertion about our own code.
    //
    // The concrete case: headless Chromium ships without the codecs for HLS,
    // so the Cablecast player reliably logs
    // "VIDEOJS: ERROR: (CODE:4 MEDIA_ERR_SRC_NOT_SUPPORTED)" on any runner
    // that can reach the network. That is a property of the test browser, not
    // a broken embed — whether the player actually mounts is asserted in
    // embeds.spec.js, where it belongs.
    const source = message.location()?.url || '';
    const text = message.text();

    if (isThirdParty(source) || isThirdPartyConsole(text)) {
      thirdPartyFailures.push(`console: ${text}`);
    } else {
      consoleErrors.push(text);
    }
  });

  page.on('pageerror', (error) => {
    pageErrors.push(`${error.name}: ${error.message}`);
  });

  page.on('requestfailed', (request) => {
    const entry = `${request.url()} (${request.failure()?.errorText || 'failed'})`;
    (isThirdParty(request.url()) ? thirdPartyFailures : ownFailures).push(entry);
  });

  page.on('response', (response) => {
    if (response.status() < 400) return;
    const entry = `${response.url()} -> HTTP ${response.status()}`;
    (isThirdParty(response.url()) ? thirdPartyFailures : ownFailures).push(entry);
  });

  return { consoleErrors, pageErrors, ownFailures, thirdPartyFailures };
}

for (const { path, name } of PAGES) {
  test.describe(name, () => {
    test(`${name} loads cleanly`, async ({ page }) => {
      const problems = watch(page);

      const response = await page.goto(path, { waitUntil: 'domcontentloaded' });
      expect(response, `no response for ${path}`).toBeTruthy();
      expect(response.status(), `${path} returned HTTP ${response.status()}`).toBeLessThan(400);

      // Give deferred scripts a moment to run and fail if they are going to.
      await page.waitForTimeout(500);

      // Third-party trouble is recorded on the test rather than asserted on,
      // so it shows up in the report without turning the run red because
      // someone else's server had a bad minute.
      if (problems.thirdPartyFailures.length) {
        test.info().annotations.push({
          type: 'third-party',
          description: problems.thirdPartyFailures.join('\n'),
        });
      }

      expect(problems.pageErrors, `uncaught JavaScript errors on ${path}`).toEqual([]);
      expect(problems.consoleErrors, `console errors on ${path}`).toEqual([]);
      expect(problems.ownFailures, `failed same-origin requests on ${path}`).toEqual([]);
    });

    test(`${name} has real content`, async ({ page }) => {
      await page.goto(path, { waitUntil: 'domcontentloaded' });

      // Not just "has a title" — a title must not begin or end with a
      // separator. The homepage rendered as " — Fort Collins Public Media"
      // because an empty string is truthy in Liquid, and a bare /\S/ check
      // was happy with it.
      await expect(page).toHaveTitle(/^[^\s—|-].*[^\s—|-]$/);
      await expect(page.locator('h1')).toHaveCount(1);
      await expect(page.locator('h1')).not.toBeEmpty();

      // Every link needs something clickable in it. This is what catches
      // data problems like a catalog record with no title rendering as an
      // invisible link.
      const blankLinks = await page.$$eval('a', (links) =>
        links
          .filter((a) => {
            const hasText = a.textContent.trim().length > 0;
            const hasImage = a.querySelector('img');
            const hasLabel = a.getAttribute('aria-label');
            return !hasText && !hasImage && !hasLabel;
          })
          .map((a) => a.getAttribute('href'))
      );
      expect(blankLinks, `links with no visible label on ${path}`).toEqual([]);
    });

    test(`${name} internal links resolve`, async ({ page, request }) => {
      await page.goto(path, { waitUntil: 'domcontentloaded' });

      const origin = new URL(page.url()).origin;
      const links = await page.$$eval('a[href]', (as) => as.map((a) => a.href));

      const internal = [...new Set(links)].filter(
        (href) => href.startsWith(origin) && !href.includes('#')
      );

      const broken = [];
      for (const href of internal) {
        const response = await request.get(href, { failOnStatusCode: false });
        if (response.status() >= 400) broken.push(`${href} -> ${response.status()}`);
      }

      expect(broken, `broken internal links on ${path}`).toEqual([]);
    });

    test(`${name} does not scroll sideways`, async ({ page }) => {
      await page.goto(path, { waitUntil: 'domcontentloaded' });
      await page.waitForTimeout(300);

      // The classic mobile bug: something a few pixels too wide makes the
      // whole page pan, and it is easy to miss unless you look for it.
      const overflow = await page.evaluate(() => {
        const doc = document.documentElement;
        return doc.scrollWidth - doc.clientWidth;
      });

      expect(overflow, `page scrolls horizontally by ${overflow}px`).toBeLessThanOrEqual(1);
    });
  });
}

test.describe('navigation', () => {
  test('mobile menu opens and closes', async ({ page }, testInfo) => {
    test.skip(testInfo.project.name !== 'mobile', 'mobile viewport only');

    await page.goto('/');

    const toggle = page.locator('.nav-toggle');
    const nav = page.locator('#site-nav');

    await expect(toggle).toBeVisible();
    await expect(nav).toBeHidden();

    await toggle.click();
    await expect(nav).toBeVisible();
    await expect(toggle).toHaveAttribute('aria-expanded', 'true');

    await toggle.click();
    await expect(nav).toBeHidden();
  });

  test('every header link is reachable', async ({ page, request }) => {
    await page.goto('/');

    const hrefs = await page.$$eval('.site-nav a[href]', (as) => as.map((a) => a.href));
    expect(hrefs.length).toBeGreaterThan(3);

    for (const href of hrefs) {
      const response = await request.get(href, { failOnStatusCode: false });
      expect(response.status(), `${href} is not reachable`).toBeLessThan(400);
    }
  });
});

test.describe('archive', () => {
  test('lists programs and filters them', async ({ page }) => {
    await page.goto('/watch/archive/');

    const rows = page.locator('[data-archive] li');
    const total = await rows.count();
    expect(total, 'archive is empty').toBeGreaterThan(100);

    // The filter box is hidden until its script runs, so its visibility is
    // itself the assertion that the script loaded.
    const filter = page.locator('#archive-filter');
    await expect(filter).toBeVisible();

    await filter.fill('zzzzzznotathing');
    await expect(rows.filter({ visible: true })).toHaveCount(0);

    await filter.fill('');
    await expect(rows.filter({ visible: true })).toHaveCount(total);
  });

  test('every program links somewhere', async ({ page }) => {
    await page.goto('/watch/archive/');

    const bad = await page.$$eval('[data-archive] li a', (links) =>
      links
        .filter((a) => !a.getAttribute('href') || a.textContent.trim() === '')
        .map((a) => a.outerHTML.slice(0, 120))
    );

    expect(bad, 'archive rows with no link or no label').toEqual([]);
  });
});

// ---------------------------------------------------------------------------
// The two pages that frame a hosted form. Nothing is configured yet, so what
// matters is that the unconfigured state is visible rather than a blank space,
// and that the page never leaves someone with no way forward.

test.describe('hosted forms', () => {
  for (const path of ['/book/', '/register/']) {
    test(`${path} says plainly that it is not set up yet`, async ({ page }) => {
      await page.goto(path);

      const notice = page.locator('.transaction-todo');
      await expect(notice).toBeVisible();
      await expect(notice).toContainText('not set up yet');

      // The instruction that stops someone shipping a form that breaks on
      // iPhones has to survive edits to this page.
      await expect(notice).toContainText('Anyone can respond');
    });

    test(`${path} still offers somewhere to go`, async ({ page }) => {
      await page.goto(path);

      // An unconfigured form page must not be a dead end. Two specific things
      // rather than a link count, which would only measure how chatty the
      // copy happens to be: somewhere else on the site to go, and a way to
      // reach a human.
      const onward = await page.$$eval('main a[href^="/"]', (as) => as.length);
      expect(onward, 'no links onward into the site').toBeGreaterThan(0);

      const contact = await page.$$eval(
        'main a[href^="mailto:"], main a[href^="tel:"]',
        (as) => as.length
      );
      expect(contact, 'no way to reach a person').toBeGreaterThan(0);
    });

    test(`${path} does not frame anything before it is configured`, async ({ page }) => {
      await page.goto(path);
      await expect(page.locator('.hosted-form iframe')).toHaveCount(0);
    });
  }
});
