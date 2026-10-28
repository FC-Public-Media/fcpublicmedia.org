// /submit/: the program form beside the rules on a wide screen, under them on a phone; it sends to the
// site-worker's `program` tank, and without one it hands the same answers to an email.

const { test, expect } = require('./fixtures');

const WORKER = 'https://worker.test';

async function fill(page) {
  await page.locator('[name="copyright"]').check();
  await page.locator('#first_name').fill('Ada');
  await page.locator('#email').fill('ada@example.org');
  await page.locator('#title').fill('Night Shift');
  await page.locator('#category').selectOption('Music');
}

test('Dropbox opens in a new tab and never blocks the form', async ({ page }) => {
  await page.goto('/submit/');
  const drop = page.locator('a.dropbox');
  await expect(drop).toHaveAttribute('target', '_blank');
  await expect(drop).toHaveAttribute('href', /dropbox\.com\/request\//);
  await expect(page.locator('[name="uploaded"]')).not.toHaveAttribute('required', '');
});

test('the form sits beside the rules when there is room', async ({ page }) => {
  await page.goto('/submit/');
  const main = await page.locator('.split-main').boundingBox();
  const side = await page.locator('.split-side').boundingBox();
  if (page.viewportSize().width >= 896) {
    expect(side.x).toBeGreaterThan(main.x + main.width - 1);
  } else {
    expect(side.y).toBeGreaterThan(main.y + main.height - 1);
  }
});

test('consent is required before anything is sent', async ({ page }) => {
  let sent = 0;
  await page.route(`${WORKER}/answers`, (route) => { sent += 1; route.fulfill({ json: { ok: true } }); });
  await page.goto('/submit/');
  await page.locator('form[data-tank]').evaluate((f, w) => { f.dataset.worker = w; }, WORKER);
  await page.locator('#email').fill('ada@example.org');
  await page.getByRole('button', { name: 'Submit' }).click();
  expect(sent).toBe(0);
});

test('sends the tank its own field names, and gives a reference', async ({ page }) => {
  let body;
  await page.route(`${WORKER}/answers`, async (route) => {
    body = route.request().postDataJSON();
    await route.fulfill({ json: { ok: true, reference: body.reference } });
  });
  await page.goto('/submit/');
  await page.locator('form[data-tank]').evaluate((f, w) => { f.dataset.worker = w; }, WORKER);
  await fill(page);
  await page.getByRole('button', { name: 'Submit' }).click();

  await expect(page.locator('[data-receipt="sent"]')).toBeVisible();
  await expect(page.locator('[data-receipt="sent"] [data-reference]')).toHaveText(body.reference.slice(0, 8));
  expect(body.form).toBe('program');
  expect(body.answers).toEqual({
    copyright: true, first_name: 'Ada', email: 'ada@example.org', title: 'Night Shift', category: 'Music',
  });
});

test('with no worker, the same answers become an email', async ({ page }) => {
  await page.goto('/submit/');
  await page.locator('form[data-tank]').evaluate((f) => { f.dataset.worker = ''; });
  await fill(page);
  await page.getByRole('button', { name: 'Submit' }).click();

  await expect(page.locator('[data-say="unsent"]')).toBeVisible();
  const href = await page.locator('[data-say="unsent"] a[data-mailto]').getAttribute('href');
  expect(href).toMatch(/^mailto:info@fcpublicmedia\.org\?subject=Program%20submission/);
  expect(decodeURIComponent(href)).toContain('Title: Night Shift');
});

test('a failed send still leaves the email way through', async ({ page }) => {
  await page.route(`${WORKER}/answers`, (route) => route.fulfill({ status: 403, json: { ok: false } }));
  await page.goto('/submit/');
  await page.locator('form[data-tank]').evaluate((f, w) => { f.dataset.worker = w; }, WORKER);
  await fill(page);
  await page.getByRole('button', { name: 'Submit' }).click();
  await expect(page.locator('[data-say="failed"] a[href^="mailto:"]')).toBeVisible();
  await expect(page.locator('form[data-tank]')).toBeVisible();
});
