// The board — a section of /meet/, not a page.
//
// It stopped being its own page because it is one of the ways you meet this
// place, not a destination beside it. Its one job is unchanged: make "you can
// come to a board meeting" actionable. The tests below are about that, plus
// the three states it ships in — no schedule, no roster, no minutes link —
// which are what everyone will see until someone fills them in, and which
// must not read as a broken page.

const { test, expect } = require('@playwright/test');

test.describe('board and meetings', () => {
  test('says the meetings are open', async ({ page }) => {
    await page.goto('/meet/');

    await expect(page.locator('main')).toContainText('open to anyone');
  });

  test('does not claim a legal obligation it does not have', async ({ page }) => {
    // FCPM is a 501(c)(3), not a public body. Colorado's Open Meetings Law
    // covers state and local government and does not reach a nonprofit board,
    // so language implying statutory compliance would be a misstatement — and
    // an easy one to introduce while editing copy that sounds civic.
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
    // Someone who assumes a recording exists may speak differently in the
    // room, and it is why the minutes are the only record.
    await page.goto('/meet/');

    await expect(page.locator('main')).toContainText("aren't recorded");
  });

  test('always offers a way to get the minutes', async ({ page }) => {
    // With no folder linked — the shipped state — the page must still route
    // someone somewhere rather than mentioning minutes and stopping.
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
    // An invitation with no date is not an invitation. This is the state the
    // page ships in, so the gap has to be loud enough that someone closes it.
    await page.goto('/meet/');

    await expect(page.locator('.transaction-todo').first()).toBeVisible();
    await expect(page.locator('main')).toContainText("schedule isn't filled in");
  });

  test('an empty roster shows a notice, not empty cards', async ({ page }) => {
    // The previous version of this rendered one card per placeholder, so a
    // live page displayed "TODO" three times.
    await page.goto('/meet/');

    await expect(page.locator('main .card')).toHaveCount(0);
    await expect(page.locator('main')).not.toContainText('TODO');
    await expect(page.locator('main')).toContainText("roster isn't filled in");
  });

  test('sections with nothing in them are absent, not empty', async ({ page }) => {
    // A heading with no list under it reads as neglect and invites the exact
    // question it was meant to answer.
    await page.goto('/meet/');

    const headings = await page.$$eval('main h2, main h3', (hs) =>
      hs.map((h) => h.textContent.trim())
    );
    expect(headings).not.toContain('Coming up');
    expect(headings).not.toContain('Documents');
  });

  test('the about page hands off to it', async ({ page }) => {
    // Merging it into /meet/ must not strand the board content — someone
    // looking for governance will still start at /about/, and the link has to
    // land on the section rather than on a page that no longer exists.
    await page.goto('/about/');

    await expect(page.locator('main a[href="/meet/#the-board"]')).toHaveCount(1);
  });

  test('is reachable from the main menu', async ({ page }) => {
    await page.goto('/');

    // In the header now, not the footer. Meet is a section of the site, and
    // the board is a heading inside it.
    await expect(page.locator('.site-nav a[href="/meet/"]')).toHaveCount(1);
  });

  test('the section anchor the links point at actually exists', async ({ page }) => {
    // Three places link to #the-board. An anchor is silently broken in a way
    // a 404 is not — the page loads, it just does not go anywhere.
    await page.goto('/meet/');

    await expect(page.locator('#the-board')).toHaveCount(1);
  });
});
