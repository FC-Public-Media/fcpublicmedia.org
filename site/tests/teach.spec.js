// /learn/: the instructor application, beside the pitch on a wide screen. Only email is required.

const { test, expect } = require('./fixtures');

const WORKER = 'https://worker.test';
const form = (page) => page.locator('form[data-tank="instructor"]');

test('sends the instructor tank its own field names, ticked boxes as lists', async ({ page }) => {
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
  await page.locator('[name="in_person_virtual"][value="Online"]').check();
  await page.locator('#t-topics').fill('Lighting for small studios');
  await page.locator('[name="times"][value="Evening"]').check();
  await page.locator('[name="days"][value="Tuesday"]').check();
  await page.locator('[name="days"][value="Thursday"]').check();
  await form(page).getByRole('button').click();

  await expect(page.locator('[data-receipt="sent"]')).toBeVisible();
  expect(body).toMatchObject({
    form: 'instructor',
    answers: {
      first_name: 'Ada', email: 'ada@example.org', first_time: 'Yes', in_person_virtual: 'Online',
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
