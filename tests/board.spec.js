// The board page.
//
// Its one job is to make "you can come to a board meeting" actionable. The
// tests below are about that, plus the two states this page ships in — no
// schedule, no roster, no minutes link — which are what everyone will see
// until someone fills them in, and which must not read as a broken page.

const { test, expect } = require('@playwright/test');

test.describe('board and meetings', () => {
  test('says the meetings are open', async ({ page }) => {
    await page.goto('/board/');

    await expect(page.locator('main')).toContainText('open to anyone');
  });

  test('does not claim a legal obligation it does not have', async ({ page }) => {
    // FCPM is a 501(c)(3), not a public body. Colorado's Open Meetings Law
    // covers state and local government and does not reach a nonprofit board,
    // so language implying statutory compliance would be a misstatement — and
    // an easy one to introduce while editing copy that sounds civic.
    await page.goto('/board/');

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
    await page.goto('/board/');

    await expect(page.locator('main')).toContainText("aren't recorded");
  });

  test('always offers a way to get the minutes', async ({ page }) => {
    // With no folder linked — the shipped state — the page must still route
    // someone somewhere rather than mentioning minutes and stopping.
    await page.goto('/board/');

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
    await page.goto('/board/');

    await expect(page.locator('.transaction-todo').first()).toBeVisible();
    await expect(page.locator('main')).toContainText("schedule isn't filled in");
  });

  test('an empty roster shows a notice, not empty cards', async ({ page }) => {
    // The previous version of this rendered one card per placeholder, so a
    // live page displayed "TODO" three times.
    await page.goto('/board/');

    await expect(page.locator('main .card')).toHaveCount(0);
    await expect(page.locator('main')).not.toContainText('TODO');
    await expect(page.locator('main')).toContainText("roster isn't filled in");
  });

  test('sections with nothing in them are absent, not empty', async ({ page }) => {
    // A heading with no list under it reads as neglect and invites the exact
    // question it was meant to answer.
    await page.goto('/board/');

    const headings = await page.$$eval('main h2, main h3', (hs) =>
      hs.map((h) => h.textContent.trim())
    );
    expect(headings).not.toContain('Coming up');
    expect(headings).not.toContain('Documents');
  });

  test('the about page hands off to it', async ({ page }) => {
    // Splitting the old "About & Board" page must not strand the board
    // content — someone looking for governance will still start at /about/.
    await page.goto('/about/');

    await expect(page.locator('main a[href="/board/"]')).toHaveCount(1);
  });

  test('is reachable from the footer', async ({ page }) => {
    await page.goto('/');

    // Exact href, so /bulletin-board/ does not satisfy this by accident.
    await expect(page.locator('.site-foot a[href="/board/"]')).toHaveCount(1);
  });
});
