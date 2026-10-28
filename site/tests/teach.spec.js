// /learn/: the instructor application, beside the pitch on a wide screen. Only email is required.

const { test, expect } = require('./fixtures');

const WORKER = 'https://worker.test';
const form = (page) => page.locator('form[data-tank="instructor@2"]');

// The site-worker's `instructor@2` tank (its src/tanks.js). A name it doesn't list makes it refuse the whole reply.
const TANK = ['first_name', 'last_name', 'email', 'phone', 'first_time', 'method', 'times', 'days', 'topics', 'needs', 'audience'];

test('sends the instructor@2 tank its own field names, ticked boxes as lists', async ({ page }) => {
  let body;
  await page.route(`${WORKER}/answers`, async (route) => {
    body = route.request().postDataJSON();
    await route.fulfill({ json: { ok: true } });
  });
  await page.goto('/learn/');
  await form(page).evaluate((f, w) => { f.dataset.worker = w; }, WORKER);

  await page.locator('#t-first').fill('Ada');
  await page.locator('#t-email').fill('ada@example.org');
  await page.locator('#t-first-time').check();
  await page.locator('[name="method"][value="In person"]').check();
  await page.locator('[name="method"][value="Recorded"]').check();
  await page.locator('#t-topics').fill('Lighting for small studios');
  await page.locator('[name="times"][value="Evening"]').check();
  await page.locator('[name="days"][value="Tuesday"]').check();
  await page.locator('[name="days"][value="Thursday"]').check();
  await form(page).getByRole('button').click();

  await expect(page.locator('[data-receipt="sent"]')).toBeVisible();
  expect(body).toMatchObject({
    form: 'instructor@2',
    answers: {
      first_name: 'Ada', email: 'ada@example.org', first_time: 'Yes', method: ['In person', 'Recorded'],
      topics: 'Lighting for small studios',
      times: ['Evening'], days: ['Tuesday', 'Thursday'],
    },
  });
});

test('nothing but an email is required', async ({ page }) => {
  await page.goto('/learn/');
  const required = await form(page).locator('[required]').evaluateAll((els) => els.map((e) => e.name));
  expect(required).toEqual(['email']);
});

test('with no worker, the application becomes an email', async ({ page }) => {
  await page.goto('/learn/');
  await form(page).evaluate((f) => { f.dataset.worker = ''; });
  await page.locator('#t-email').fill('ada@example.org');
  await page.locator('[name="days"][value="Monday"]').check();
  await form(page).getByRole('button').click();
  await expect(page.locator('[data-say="unsent"]')).toBeVisible();
  const href = await page.locator('[data-say="unsent"] a[data-mailto]').getAttribute('href');
  expect(decodeURIComponent(href)).toContain('[x] Monday');
});

test('the form sends only fields the instructor@2 tank takes', async ({ page }) => {
  await page.goto('/learn/');
  const names = await form(page).locator('[name]').evaluateAll((els) => [...new Set(els.map((e) => e.name))]);
  const sent = names.filter((name) => name !== 'website');
  expect(sent.filter((name) => !TANK.includes(name)), 'fields the worker would refuse').toEqual([]);
});
