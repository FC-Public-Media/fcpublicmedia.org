// Which colours, and who decides.
//
// TWO RULES THIS FILE EXISTS TO HOLD.
//
// 1. LIGHT IS THE DEFAULT, including for a visitor whose system is dark. That
//    is a deliberate reversal — the site used to follow the system — and it is
//    exactly the kind of thing somebody "helpfully" restores later on the
//    assumption that following the system is always correct. It is not correct
//    here: the dark scheme reads as drab and most visitors were being handed
//    the weaker of the two without being asked.
//
// 2. THE SETTING IS A TOGGLE, not a palette picker. Follow the system, or do
//    not. There is deliberately no explicit "dark", because it differs from
//    "follow" only for somebody whose system is light but who wants a dark
//    site anyway — a small group who mostly own a dark system already.

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
    // And the control says so, rather than showing an unset state on a page
    // that plainly has a colour.
    await expect(page.locator('[data-theme-input]')).not.toBeChecked();
    await context.close();
  });

  test('follows the system once asked to, and remembers', async ({ browser }) => {
    const context = await browser.newContext({ colorScheme: 'dark' });
    const page = await context.newPage();
    await page.goto('/');

    await page.locator('[data-theme-input]').check();
    expect(await background(page)).toBe(INK);

    // Across a navigation, and without a flash — the head sets the attribute
    // before anything paints, which is why that script is inline rather than
    // in theme.js.
    await page.goto('/watch/');
    expect(await background(page)).toBe(INK);
    await expect(page.locator('[data-theme-input]')).toBeChecked();
    await context.close();
  });

  test('turning it back off returns to light, and that sticks too', async ({ browser }) => {
    // The way back matters: without it, somebody on a dark machine who tried
    // the toggle would have no route to the default.
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

  test('does nothing visible on a light system, which is the promise', async ({ browser }) => {
    // Not a bug. "Match my system" on a light system means light, and it
    // starts mattering the day that machine goes dark. The label says match
    // rather than dark for exactly this reason.
    const context = await browser.newContext({ colorScheme: 'light' });
    const page = await context.newPage();
    await page.goto('/');

    await page.locator('[data-theme-input]').check();
    expect(await background(page)).toBe(PAPER);
    await context.close();
  });

  test('reads a leftover "dark" as following the system', async ({ browser }) => {
    // The three-way this replaced could store `dark`. Anything that is not an
    // explicit `light` counts as following, which is the closest surviving
    // intent for somebody who had chosen dark.
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

    // The toggle still works for the life of the page. It forgets on the next
    // navigation, which is a smaller loss than being nagged about it.
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
