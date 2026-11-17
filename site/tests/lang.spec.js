// Languages: English is the page as built; another is its strings file put over it, chosen in the footer
// or, with no choice made, by the device's own languages. See docs/site.md#languages.

const { test, expect } = require('./fixtures');
const { PAGES } = require('./pages.js');

const filesOf = async (request) => (await request.get('/strings.json')).json();

/** The first language that has a strings file, and its table. */
async function other(request) {
  const files = await filesOf(request);
  const [code, file] = Object.entries(files)[0];
  return { code, file, strings: file.strings || {} };
}

const navWords = (page) => page.locator('.site-nav .nav-word').allTextContents();
const said = (strings, english) => english.map((w) => strings[w.trim()] ?? w.trim());

test.describe('languages', () => {
  test('offers English and every strings file, each in its own words', async ({ page, request }) => {
    const files = await filesOf(request);
    await page.goto('/');
    const choice = page.locator('[data-lang-choice]');
    await expect(choice).toBeVisible();
    await expect(choice.locator('[data-lang="en"]')).toHaveText('English');
    for (const [code, file] of Object.entries(files)) {
      await expect(choice.locator(`[data-lang="${code}"]`)).toHaveText(file.name);
    }
  });

  test('an English device gets the page as built, and asks for no strings', async ({ browser }) => {
    const context = await browser.newContext({ locale: 'en-US' });
    const page = await context.newPage();
    const asked = [];
    page.on('request', (r) => { if (r.url().includes('/strings.json')) asked.push(r.url()); });
    await page.goto('/');
    await expect(page.locator('html')).toHaveAttribute('lang', 'en');
    await expect(page.locator('[data-lang="en"]')).toHaveAttribute('aria-pressed', 'true');
    expect(asked).toEqual([]);
    await context.close();
  });

  test('a device that prefers another language gets it with no choice made', async ({ browser, request }) => {
    const { code, strings } = await other(request);
    const english = await browser.newContext({ locale: 'en-US' });
    const englishWords = await navWords(await (async () => { const p = await english.newPage(); await p.goto('/'); return p; })());
    await english.close();

    const context = await browser.newContext({ locale: code });
    const page = await context.newPage();
    await page.goto('/');
    await expect(page.locator('html')).toHaveAttribute('lang', code);
    await expect(page.locator('html')).not.toHaveAttribute('data-lang-pending', /.*/);
    expect((await navWords(page)).map((w) => w.trim())).toEqual(said(strings, englishWords));
    await context.close();
  });

  test('a choice sticks from page to page, and English brings back the page as built', async ({ browser, request }) => {
    const { code, strings } = await other(request);
    const context = await browser.newContext({ locale: 'en-US' });
    const page = await context.newPage();
    await page.goto('/');
    const english = await navWords(page);

    await page.locator(`[data-lang="${code}"]`).click();
    await expect(page.locator('html')).toHaveAttribute('lang', code);
    expect((await navWords(page)).map((w) => w.trim())).toEqual(said(strings, english));

    await page.goto('/meet/');
    await expect(page.locator('html')).toHaveAttribute('lang', code);
    await expect(page.locator(`[data-lang="${code}"]`)).toHaveAttribute('aria-pressed', 'true');

    await Promise.all([page.waitForEvent('load'), page.locator('[data-lang="en"]').click()]);
    await expect(page.locator('html')).toHaveAttribute('lang', 'en');
    expect(await navWords(page)).toEqual(english);
    await context.close();
  });

  test('what says translate="no" is left as it is', async ({ browser, request }) => {
    const { code } = await other(request);
    const read = async (locale) => {
      const context = await browser.newContext({ locale });
      const page = await context.newPage();
      await page.goto('/');
      await expect(page.locator('html')).toHaveAttribute('lang', locale);
      const words = await page.locator('[translate="no"]').allTextContents();
      await context.close();
      return words;
    };
    expect(await read(code)).toEqual(await read('en'));
  });

  test('the choice is kept where the offline kit can read it', async ({ page, request }) => {
    const { code } = await other(request);
    await page.goto('/');
    await page.locator(`[data-lang="${code}"]`).click();
    await expect(page.locator('html')).toHaveAttribute('lang', code);
    const profile = await page.evaluate(async () => {
      for (let i = 0; i < 20; i += 1) {
        const kept = await (await caches.open('fcpm-device')).match('/device.json');
        if (kept) return kept.json();
        await new Promise((ok) => setTimeout(ok, 50));
      }
      return null;
    });
    expect(profile).toMatchObject({ lang: code });
  });

  test('with no network, a kit page still comes in the chosen language', async ({ browser, request }) => {
    const { code } = await other(request);
    const context = await browser.newContext({ locale: code });
    const page = await context.newPage();
    await page.goto('/check-in/');
    await page.evaluate(async () => {
      await navigator.serviceWorker.ready;
      for (let i = 0; i < 50; i += 1) {
        const kit = (await caches.keys()).find((n) => n.startsWith('fcpm-kit-'));
        if (kit && await (await caches.open(kit)).match('/strings.json')) return;
        await new Promise((ok) => setTimeout(ok, 100));
      }
    });
    await context.setOffline(true);
    await page.reload();
    await expect(page.locator('html')).toHaveAttribute('lang', code);
    await context.close();
  });

  test('survives storage being blocked', async ({ browser, request }) => {
    const { code } = await other(request);
    const context = await browser.newContext({ locale: code });
    await context.addInitScript(() => {
      Object.defineProperty(window, 'localStorage', {
        get() { throw new DOMException('The operation is insecure.', 'SecurityError'); },
      });
    });
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', (error) => errors.push(error.message));
    await page.goto('/');
    await expect(page.locator('html')).toHaveAttribute('lang', code);
    // Nothing can keep a choice across the reload, so the device decides again; it must not throw.
    await Promise.all([page.waitForEvent('load'), page.locator('[data-lang="en"]').click()]);
    expect(errors).toEqual([]);
    await context.close();
  });

  test('hides the choice without scripting', async ({ browser }) => {
    const context = await browser.newContext({ javaScriptEnabled: false });
    const page = await context.newPage();
    await page.goto('/');
    await expect(page.locator('[data-lang-choice]')).toBeHidden();
    await context.close();
  });

  for (const { path, name } of PAGES) {
    test(`${name} does not scroll sideways in another language`, async ({ browser, request }) => {
      const { code } = await other(request);
      const context = await browser.newContext({ locale: code, viewport: { width: 360, height: 740 } });
      const page = await context.newPage();
      await page.goto(path);
      await expect(page.locator('html')).toHaveAttribute('lang', code);
      const over = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
      expect(over).toBeLessThanOrEqual(0);
      await context.close();
    });
  }
});
