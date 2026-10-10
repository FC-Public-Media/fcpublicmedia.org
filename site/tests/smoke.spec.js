// Every page in pages.js loads cleanly, plus navigation, the archive and the hosted-form pages.
// Needs no network. See docs/site.md.

const { test, expect } = require('@playwright/test');
const { PAGES, isThirdParty, isThirdPartyConsole } = require('./pages');

// Attach before navigating; third-party failures are collected apart from our own.
function watch(page) {
  const consoleErrors = [];
  const pageErrors = [];
  const ownFailures = [];
  const thirdPartyFailures = [];

  page.on('console', (message) => {
    if (message.type() !== 'error') return;

    // Iframe errors reach this console; headless Chromium lacks HLS, so VIDEOJS logs errors.
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

// A trimming Liquid comment can fuse a heading and HTML into one escaped line; <pre> is skipped.
test('no page shows its own markup as text', async ({ page }) => {
  const escaped = /&lt;\/?(?:ul|ol|li|div|p|table|section|nav|span|a|h[1-6])[\s>]/;
  const leaked = [];

  for (const { path, name } of PAGES) {
    await page.goto(path);

    const suspects = await page.$$eval('h1, h2, h3, h4, main > p, li', (nodes) =>
      nodes.map((node) => node.innerHTML)
    );

    for (const html of suspects) {
      if (escaped.test(html)) leaked.push(`${name}: ${html.slice(0, 80)}`);
    }
  }

  expect(
    leaked,
    'escaped markup is being displayed as words — a Liquid comment has ' +
      'probably eaten the newline between a heading and the HTML under it:\n' +
      leaked.join('\n')
  ).toEqual([]);
});

for (const { path, name } of PAGES) {
  test.describe(name, () => {
    test(`${name} loads cleanly`, async ({ page }) => {
      const problems = watch(page);

      const response = await page.goto(path, { waitUntil: 'domcontentloaded' });
      expect(response, `no response for ${path}`).toBeTruthy();
      expect(response.status(), `${path} returned HTTP ${response.status()}`).toBeLessThan(400);

      // Give deferred scripts a moment to run and fail if they are going to.
      await page.waitForTimeout(500);

      // Third-party trouble is a `third-party` annotation, not a failure.
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

      // No leading or trailing separator: an empty string is truthy in Liquid.
      await expect(page).toHaveTitle(/^[^\s—|-].*[^\s—|-]$/);

      // At most one h1: pages on site/_layouts/page.html have none.
      const headings = page.locator('h1');
      expect(await headings.count(), `more than one h1 on ${path}`).toBeLessThanOrEqual(1);
      if (await headings.count()) await expect(headings).not.toBeEmpty();

      // Catches e.g. a catalog record with no title rendering as an invisible link.
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

    // Visible only once archive-filter.js has run.
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

// /book/ and /register/ frame a hosted form; both are unconfigured.
test.describe('hosted forms', () => {
  for (const path of ['/book/', '/register/']) {
    test(`${path} says plainly that it is not set up yet`, async ({ page }) => {
      await page.goto(path);

      const notice = page.locator('.transaction-todo');
      await expect(notice).toBeVisible();
      await expect(notice).toContainText('not set up yet');

      // The setup instruction that keeps the form working on iPhones.
      await expect(notice).toContainText('Anyone can respond');
    });

    test(`${path} still offers somewhere to go`, async ({ page }) => {
      await page.goto(path);

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

test.describe('archive airing history', () => {
  test('shows how often programs have aired', async ({ page }) => {
    // The Liquid join keys airings by stringified id; a wrong key type zeroes every row.
    await page.goto('/watch/archive/');

    const withAirings = await page.$$eval(
      '[data-archive] li[data-airings]',
      (rows) => rows.filter((r) => Number(r.dataset.airings) > 0).length
    );

    expect(withAirings, 'no program has any airing history').toBeGreaterThan(0);
    await expect(page.locator('.airings').first()).toBeVisible();
  });

  test('sorting by least aired puts unaired programs first', async ({ page }) => {
    await page.goto('/watch/archive/');

    await page.locator('#archive-sort').selectOption('least');

    const first = await page.$$eval('[data-archive] li:not([hidden])', (rows) =>
      rows.slice(0, 5).map((r) => Number(r.dataset.airings))
    );
    expect(first.every((n) => n === 0), `got ${first}`).toBe(true);
  });

  test('sorting by most aired puts the heaviest rotation first', async ({ page }) => {
    await page.goto('/watch/archive/');

    await page.locator('#archive-sort').selectOption('most');

    const counts = await page.$$eval('[data-archive] li:not([hidden])', (rows) =>
      rows.slice(0, 10).map((r) => Number(r.dataset.airings))
    );
    expect(counts[0]).toBeGreaterThan(0);
    expect(counts, 'not in descending order').toEqual([...counts].sort((a, b) => b - a));
  });

  test('sorting flattens the category headings', async ({ page }) => {
    await page.goto('/watch/archive/');

    const before = await page.locator('h2[id]:not([hidden])').count();
    expect(before).toBeGreaterThan(1);

    await page.locator('#archive-sort').selectOption('title');
    await expect(page.locator('h2[id]:not([hidden])')).toHaveCount(0);
  });

  test('returning to category puts every row back', async ({ page }) => {
    await page.goto('/watch/archive/');

    const total = await page.locator('[data-archive] li').count();
    const firstTitle = await page.locator('[data-archive] li').first().getAttribute('data-title');

    await page.locator('#archive-sort').selectOption('most');
    await page.locator('#archive-sort').selectOption('category');

    await expect(page.locator('[data-archive] li')).toHaveCount(total);
    expect(await page.locator('[data-archive] li').first().getAttribute('data-title'))
      .toBe(firstTitle);
    expect(await page.locator('h2[id]:not([hidden])').count()).toBeGreaterThan(1);
  });

  test('filtering still works while sorted', async ({ page }) => {
    await page.goto('/watch/archive/');

    await page.locator('#archive-sort').selectOption('least');
    await page.locator('#archive-filter').fill('zzzzzznotathing');

    await expect(page.locator('[data-archive] li:not([hidden])')).toHaveCount(0);
  });
});
