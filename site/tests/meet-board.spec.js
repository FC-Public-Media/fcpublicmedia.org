// see docs/inline/site/tests/meet-board.spec.js.md#1

const { test, expect } = require('@playwright/test');

test.describe('board and meetings', () => {
  test('says the meetings are open', async ({ page }) => {
    await page.goto('/meet/');

    await expect(page.locator('main')).toContainText('open to anyone');
  });

  test('does not claim a legal obligation it does not have', async ({ page }) => {
    // see docs/inline/site/tests/meet-board.spec.js.md#2
    await page.goto('/meet/');

    const text = await page.locator('main').innerText();
    for (const phrase of [
      'required by law',
      'as required',
      'open meetings law',
      'sunshine law',
      'in compliance',
    ]) {
      expect(
        text.toLowerCase(),
        `"${phrase}" claims an obligation FCPM does not have`
      ).not.toContain(phrase);
    }
  });

  test('says meetings are not recorded', async ({ page }) => {
    // see docs/inline/site/tests/meet-board.spec.js.md#3
    await page.goto('/meet/');

    await expect(page.locator('main')).toContainText("aren't recorded");
  });

  test('always offers a way to get the minutes', async ({ page }) => {
    // see docs/inline/site/tests/meet-board.spec.js.md#4
    await page.goto('/meet/');

    const minutes = page.locator('main');
    await expect(minutes).toContainText('minutes');

    const contactable = await page.$$eval(
      'main a[href^="mailto:"], main a[href^="/contact/"]',
      (as) => as.length
    );
    expect(contactable, 'no way to ask for the minutes').toBeGreaterThan(0);
  });

  test('a missing schedule is called out rather than left blank', async ({ page }) => {
    // see docs/inline/site/tests/meet-board.spec.js.md#5
    await page.goto('/meet/');

    await expect(page.locator('.transaction-todo').first()).toBeVisible();
    await expect(page.locator('main')).toContainText("schedule isn't filled in");
  });

  test('an empty roster shows a notice, not empty cards', async ({ page }) => {
    // see docs/inline/site/tests/meet-board.spec.js.md#6
    await page.goto('/meet/');

    await expect(page.locator('main .card')).toHaveCount(0);
    await expect(page.locator('main')).not.toContainText('TODO');
    await expect(page.locator('main')).toContainText("roster isn't filled in");
  });

  test('sections with nothing in them are absent, not empty', async ({ page }) => {
    // see docs/inline/site/tests/meet-board.spec.js.md#7
    await page.goto('/meet/');

    const headings = await page.$$eval('main h2, main h3', (hs) =>
      hs.map((h) => h.textContent.trim())
    );
    expect(headings).not.toContain('Coming up');
    expect(headings).not.toContain('Documents');
  });

  test('the about page hands off to it', async ({ page }) => {
    // see docs/inline/site/tests/meet-board.spec.js.md#8
    await page.goto('/about/');

    await expect(page.locator('main a[href="/meet/#the-board"]')).toHaveCount(1);
  });

  test('is reachable from the main menu', async ({ page }) => {
    await page.goto('/');

    // see docs/inline/site/tests/meet-board.spec.js.md#9
    await expect(page.locator('.site-nav a[href="/meet/"]')).toHaveCount(1);
  });

  test('the section anchor the links point at actually exists', async ({ page }) => {
    // see docs/inline/site/tests/meet-board.spec.js.md#10
    await page.goto('/meet/');

    await expect(page.locator('#the-board')).toHaveCount(1);
  });
});
