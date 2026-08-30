// Which colours, and who decides.
//
// The rule this file exists to hold: LIGHT IS THE DEFAULT, including for a
// visitor whose system is set to dark. That is a deliberate reversal — the
// site used to follow the system — and it is exactly the kind of thing that
// gets "helpfully" restored by somebody who assumes following the system is
// always correct. It is not correct here: the dark scheme reads as drab and
// most visitors were being handed the weaker of the two without asking.

const { test, expect } = require('@playwright/test');

const PAPER = 'rgb(244, 241, 234)';
const INK = 'rgb(18, 20, 23)';

const background = (page) =>
  page.evaluate(() => getComputedStyle(document.body).backgroundColor);

test.describe('colour scheme', () => {
  test('is light by default even when the system is dark', async ({ browser }) => {
    const context = await browser.newContext({ colorScheme: 'dark' });
    const page = await context.newPage();
    await page.goto('/');

    expect(await background(page)).toBe(PAPER);
    await context.close();
  });

  test('remembers dark once it is chosen', async ({ browser }) => {
    const context = await browser.newContext({ colorScheme: 'light' });
    const page = await context.newPage();
    await page.goto('/');

    await page.locator('[data-theme-picker] input[value="dark"]').check();
    expect(await background(page)).toBe(INK);

    // Across a navigation, and without a flash — the head sets the attribute
    // before anything paints, which is why that script is inline and not in
    // theme.js.
    await page.goto('/watch/');
    expect(await background(page)).toBe(INK);
    await context.close();
  });

  test('follows the system only when asked to', async ({ browser }) => {
    for (const [scheme, expected] of [['dark', INK], ['light', PAPER]]) {
      const context = await browser.newContext({ colorScheme: scheme });
      const page = await context.newPage();
      await page.goto('/');

      await page.locator('[data-theme-picker] input[value="system"]').check();
      expect(await background(page), `system=${scheme}`).toBe(expected);
      await context.close();
    }
  });

  test('survives storage being blocked, and says nothing about it', async ({ browser }) => {
    // Reading localStorage THROWS when storage is blocked rather than
    // returning null, and blocking it is a real setting real people turn on.
    const context = await browser.newContext({ colorScheme: 'dark' });
    await context.addInitScript(() => {
      Object.defineProperty(window, 'localStorage', {
        get() {
          throw new DOMException('The operation is insecure.', 'SecurityError');
        },
      });
    });
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', (error) => errors.push(error.message));

    await page.goto('/');
    expect(errors, 'blocked storage threw').toEqual([]);
    expect(await background(page)).toBe(PAPER);

    // The control still works for the life of the page. It forgets on the
    // next navigation, which is a smaller loss than being nagged about it.
    await page.locator('[data-theme-picker] input[value="dark"]').check();
    expect(await background(page)).toBe(INK);

    // And nothing anywhere tells them to change their settings.
    const text = (await page.locator('body').innerText()).toLowerCase();
    for (const nag of ['enable javascript', 'enable cookies', 'local storage', 'turn on']) {
      expect(text, `the page nags about "${nag}"`).not.toContain(nag);
    }
    await context.close();
  });

  test('hides the control rather than offering dead buttons without scripting', async ({ browser }) => {
    const context = await browser.newContext({
      javaScriptEnabled: false,
      colorScheme: 'dark',
    });
    const page = await context.newPage();
    await page.goto('/');

    // Three radios that cannot do anything are worse than no control at all —
    // the visitor is left wondering what they broke.
    await expect(page.locator('[data-theme-picker]')).toBeHidden();

    // And the page they get is the default one, which is the one we want.
    await expect(page.locator('.site-foot')).toBeVisible();
    await context.close();
  });
});
