// /join/: the membership tank, then Stripe for the tier picked. Answers never stand in the way of paying.

const { test, expect } = require('@playwright/test');

const WORKER = 'https://worker.test';
const STRIPE = 'https://checkout.stripe.test/session';

async function open(page, { worker = WORKER } = {}) {
  await page.goto('/join/');
  await page.locator('form[data-checkout]').evaluate((f, w) => { f.dataset.worker = w; }, worker);
}

async function pick(page, name) {
  await page.locator(`.tiers input[data-name="${name}"]`).check({ force: true });
}

test('the button keeps the words the page gives it', async ({ page }) => {
  await open(page);
  const words = await page.locator('[data-pay]').textContent();
  await pick(page, 'Creator');
  await expect(page.locator('[data-pay]')).toHaveText(words);
});

test('a tier in the address is picked on arrival, and picking one puts it there', async ({ page }) => {
  await page.goto('/join/?tier=producer');
  await expect(page.locator('.tiers input[data-name="Producer"]')).toBeChecked();
  await pick(page, 'Student');
  await expect(page).toHaveURL(/[?&]tier=student/);
});

test('no tier, no payment page', async ({ page }) => {
  await open(page);
  await page.locator('[name="agree_terms"]').check();
  await page.locator('[name="submit_terms"]').check();
  await page.locator('[data-pay]').click();
  await expect(page.locator('[data-say="pick-tier"]')).toBeVisible();
});

test('the terms are agreed before paying', async ({ page }) => {
  let calls = 0;
  await page.route(`${WORKER}/**`, (route) => { calls += 1; route.fulfill({ json: { ok: true } }); });
  await open(page);
  await pick(page, 'Supporter');
  await page.locator('[data-pay]').click();
  expect(calls).toBe(0);
});

test('answers, then checkout with the same reference, then Stripe', async ({ page }) => {
  const sent = {};
  await page.route(`${WORKER}/answers`, async (route) => {
    sent.answers = route.request().postDataJSON();
    await route.fulfill({ json: { ok: true } });
  });
  await page.route(`${WORKER}/checkout`, async (route) => {
    sent.checkout = route.request().postDataJSON();
    await route.fulfill({ json: { ok: true, url: STRIPE, id: 'cs_test' } });
  });
  await page.route(STRIPE, (route) => route.fulfill({ contentType: 'text/html', body: '<h1>Stripe</h1>' }));

  await open(page);
  await pick(page, 'Student');
  await page.locator('#first_name').fill('Ada');
  await page.locator('#email').fill('ada@example.org');
  await page.locator('[name="agree_terms"]').check();
  await page.locator('[name="submit_terms"]').check();
  await page.locator('[data-pay]').click();

  await expect(page).toHaveURL(STRIPE);
  expect(sent.answers).toMatchObject({
    form: 'membership', sku: 'membership:student',
    answers: { first_name: 'Ada', email: 'ada@example.org', agree_terms: true, submit_terms: true },
  });
  expect(sent.checkout).toMatchObject({
    sku: 'membership:student', email: 'ada@example.org', success_path: '/join/?joined', cancel_path: '/join/',
  });
  expect(sent.checkout.reference).toBe(sent.answers.reference);
});

test('answers that fail to keep still open the payment page', async ({ page }) => {
  await page.route(`${WORKER}/answers`, (route) => route.fulfill({ status: 503, json: { ok: false } }));
  await page.route(`${WORKER}/checkout`, (route) => route.fulfill({ json: { ok: true, url: STRIPE } }));
  await page.route(STRIPE, (route) => route.fulfill({ contentType: 'text/html', body: 'Stripe' }));
  await open(page);
  await pick(page, 'Supporter');
  await page.locator('[name="agree_terms"]').check();
  await page.locator('[name="submit_terms"]').check();
  await page.locator('[data-pay]').click();
  await expect(page).toHaveURL(STRIPE);
});

test('a payment page that will not open, with answers kept, says a person will write', async ({ page }) => {
  await page.route(`${WORKER}/answers`, (route) => route.fulfill({ json: { ok: true } }));
  await page.route(`${WORKER}/checkout`, (route) => route.fulfill({ status: 503, json: { ok: false } }));
  await open(page);
  await pick(page, 'Supporter');
  await page.locator('#email').fill('ada@example.org');
  await page.locator('[name="agree_terms"]').check();
  await page.locator('[name="submit_terms"]').check();
  await page.locator('[data-pay]').click();
  await expect(page.locator('[data-say="unpaid-kept"]')).toBeVisible();
});

test('"just send these" keeps the answers and the tier, without paying', async ({ page }) => {
  let body;
  await page.route(`${WORKER}/answers`, async (route) => {
    body = route.request().postDataJSON();
    await route.fulfill({ json: { ok: true } });
  });
  await open(page);
  await pick(page, 'Producer');
  await page.locator('#email').fill('ada@example.org');
  await page.locator('[data-keep]').click();
  await expect(page.locator('[data-receipt="sent"]')).toBeVisible();
  await expect(page.locator('[data-receipt="sent"] [data-reference]')).toHaveText(body.reference.slice(0, 8));
  expect(body).toMatchObject({ form: 'membership', sku: 'membership:producer', answers: { email: 'ada@example.org' } });
});

test('with no worker, joining becomes an email that names the tier', async ({ page }) => {
  await open(page, { worker: '' });
  await pick(page, 'Creator');
  await page.locator('#email').fill('ada@example.org');
  await page.locator('[name="agree_terms"]').check();
  await page.locator('[name="submit_terms"]').check();
  await page.locator('[data-pay]').click();
  await expect(page.locator('[data-say="unsent"]')).toBeVisible();
  const href = await page.locator('[data-say="unsent"] a[data-mailto]').getAttribute('href');
  expect(decodeURIComponent(href)).toContain('Tier: Creator, $70 a year');
});

test('back from Stripe, a thank-you instead of the form', async ({ page }) => {
  await page.goto('/join/?joined');
  await expect(page.locator('[data-receipt="joined"]')).toBeVisible();
  await expect(page.locator('form[data-checkout]')).toBeHidden();
});

test('the terms it asks you to agree to are there', async ({ page, request }) => {
  await page.goto('/join/');
  for (const href of await page.locator('[name="agree_terms"] + span a').evaluateAll((as) => as.map((a) => a.getAttribute('href')))) {
    const response = await request.get(href);
    expect(response.status(), href).toBe(200);
    expect(response.headers()['content-type']).toContain('pdf');
  }
});
