// see docs/inline/site/tests/theme.spec.js.md#1

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
    // see docs/inline/site/tests/theme.spec.js.md#2
    await expect(page.locator('[data-theme-input]')).not.toBeChecked();
    await context.close();
  });

  test('follows the system once asked to, and remembers', async ({ browser }) => {
    const context = await browser.newContext({ colorScheme: 'dark' });
    const page = await context.newPage();
    await page.goto('/');

    await page.locator('[data-theme-input]').check();
    expect(await background(page)).toBe(INK);

    // see docs/inline/site/tests/theme.spec.js.md#3
    await page.goto('/watch/');
    expect(await background(page)).toBe(INK);
    await expect(page.locator('[data-theme-input]')).toBeChecked();
    await context.close();
  });

  test('turning it back off returns to light, and that sticks too', async ({ browser }) => {
    // see docs/inline/site/tests/theme.spec.js.md#4
    const context = await browser.newContext({ colorScheme: 'dark' });
    const page = await context.newPage();
    await page.goto('/');

    await page.locator('[data-theme-input]').check();
    await page.locator('[data-theme-input]').uncheck();
    expect(await background(page)).toBe(PAPER);

    await page.goto('/watch/');
    expect(await background(page)).toBe(PAPER);
    await context.close();
  });

  test('is not offered to somebody it cannot help', async ({ browser }) => {
    // see docs/inline/site/tests/theme.spec.js.md#5
    const context = await browser.newContext({ colorScheme: 'light' });
    const page = await context.newPage();
    await page.goto('/');

    await expect(page.locator('[data-theme-toggle]')).toBeHidden();
    expect(await background(page)).toBe(PAPER);
    await context.close();
  });

  test('appears when the machine goes dark, without a reload', async ({ browser }) => {
    // see docs/inline/site/tests/theme.spec.js.md#6
    const context = await browser.newContext({ colorScheme: 'light' });
    const page = await context.newPage();
    await page.goto('/');
    await expect(page.locator('[data-theme-toggle]')).toBeHidden();

    await page.emulateMedia({ colorScheme: 'dark' });

    await expect(page.locator('[data-theme-toggle]')).toBeVisible();
    expect(await background(page), 'the page changed without being asked').toBe(PAPER);
    await context.close();
  });

  test('reads a leftover "dark" as following the system', async ({ browser }) => {
    // see docs/inline/site/tests/theme.spec.js.md#7
    const context = await browser.newContext({ colorScheme: 'dark' });
    await context.addInitScript(() => {
      try {
        localStorage.setItem('theme', 'dark');
      } catch (error) {
        /* storage blocked; the test below still holds */
      }
    });
    const page = await context.newPage();
    await page.goto('/');

    expect(await background(page)).toBe(INK);
    await expect(page.locator('[data-theme-input]')).toBeChecked();
    await context.close();
  });

  test('survives storage being blocked, and says nothing about it', async ({ browser }) => {
    // see docs/inline/site/tests/theme.spec.js.md#8
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

    // see docs/inline/site/tests/theme.spec.js.md#9
    await page.locator('[data-theme-input]').check();
    expect(await background(page)).toBe(INK);

    // And nothing anywhere tells them to change their settings.
    const text = (await page.locator('body').innerText()).toLowerCase();
    for (const nag of ['enable javascript', 'enable cookies', 'local storage', 'turn on']) {
      expect(text, `the page nags about "${nag}"`).not.toContain(nag);
    }
    await context.close();
  });

  test('hides the control rather than offering a dead checkbox without scripting', async ({ browser }) => {
    const context = await browser.newContext({
      javaScriptEnabled: false,
      colorScheme: 'dark',
    });
    const page = await context.newPage();
    await page.goto('/');

    await expect(page.locator('[data-theme-toggle]')).toBeHidden();

    // And the page they get is the default one, which is the one we want.
    await expect(page.locator('.site-foot')).toBeVisible();
    await context.close();
  });
});
