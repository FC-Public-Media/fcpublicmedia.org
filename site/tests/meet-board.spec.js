// The board section of /meet/ (#the-board): it claims nothing FCPM isn't bound to, and shows no empty
// sections. See docs/site.md.

const { test, expect } = require('./fixtures');

test.describe('board and meetings', () => {
  test('does not claim a legal obligation it does not have', async ({ page }) => {
    // FCPM is a 501(c)(3); Colorado's Open Meetings Law does not reach its board.
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

  test('sections with nothing in them are absent, not empty', async ({ page }) => {
    await page.goto('/meet/');

    const headings = await page.$$eval('main h2, main h3', (hs) =>
      hs.map((h) => h.textContent.trim())
    );
    expect(headings).not.toContain('Coming up');
    expect(headings).not.toContain('Documents');
  });

  test('is reachable from the main menu', async ({ page }) => {
    await page.goto('/');

    await expect(page.locator('.site-nav a[href="/meet/"]')).toHaveCount(1);
  });

  test('the section anchor the links point at actually exists', async ({ page }) => {
    // Other pages link to #the-board; a missing anchor fails silently.
    await page.goto('/meet/');

    await expect(page.locator('#the-board')).toHaveCount(1);
  });
});
