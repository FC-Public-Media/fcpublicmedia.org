// /reserve/: spaces and equipment side by side on a wide screen, nothing hidden; tabs on a phone.

const { test, expect } = require('./fixtures');

const wide = (page) => page.viewportSize().width >= 896;

test('both halves show at once on a wide screen, and are tabs on a phone', async ({ page }) => {
  await page.goto('/reserve/');
  if (wide(page)) {
    await expect(page.locator('.half[data-half="spaces"]')).toBeVisible();
    await expect(page.locator('.half[data-half="equipment"]')).toBeVisible();
    await expect(page.locator('.halves-tabs')).toBeHidden();
    const spaces = await page.locator('.half[data-half="spaces"]').boundingBox();
    const equipment = await page.locator('.half[data-half="equipment"]').boundingBox();
    expect(equipment.x).toBeGreaterThan(spaces.x + spaces.width - 1);
  } else {
    await expect(page.locator('.halves-tabs')).toBeVisible();
    await expect(page.locator('.half[data-half="equipment"]')).toBeVisible();
    await expect(page.locator('.half[data-half="spaces"]')).toBeHidden();
    await page.locator('[role="tab"][data-half="spaces"]').click();
    await expect(page.locator('.half[data-half="spaces"]')).toBeVisible();
    await expect(page.locator('.half[data-half="equipment"]')).toBeHidden();
    const id = await page.locator('.half[data-half="spaces"] h2').getAttribute('id');
    expect(new URL(page.url()).hash).toBe(`#${id}`);
  }
});

test('the address can open a half, by its heading', async ({ page }) => {
  await page.goto('/reserve/');
  const id = await page.locator('.half[data-half="spaces"] h2').getAttribute('id');
  await page.goto(`/reserve/#${id}`);
  await page.reload();
  await expect(page.locator('.half[data-half="spaces"]')).toBeVisible();
  if (!wide(page)) await expect(page.locator('[role="tab"][data-half="spaces"]')).toHaveAttribute('aria-selected', 'true');
});

test('without JavaScript nothing is hidden', async ({ browser }) => {
  const context = await browser.newContext({ javaScriptEnabled: false, viewport: { width: 390, height: 844 } });
  const page = await context.newPage();
  await page.goto('/reserve/');
  await expect(page.locator('.half[data-half="spaces"]')).toBeVisible();
  await expect(page.locator('.half[data-half="equipment"]')).toBeVisible();
  await expect(page.locator('.halves-tabs')).toBeHidden();
  await context.close();
});

// The studio request: a week drawn from site/_data/hosts.yml, one week at a time. A Monday morning, so
// the whole of "this week" (Tuesday 3 to Saturday 7 November) is still ahead.
const WORKER = 'https://worker.test';
const MONDAY = new Date('2026-11-02T09:00:00');

async function openStudio(page) {
  await page.clock.setFixedTime(MONDAY);
  await page.goto('/reserve/#studio');
  await page.locator('#book').evaluate((form, worker) => { form.dataset.worker = worker; }, WORKER);
}

const picked = (page) => Promise.all(['#book-date', '#book-start', '#book-host'].map((s) => page.inputValue(s)));
const card = (page, name) => page.locator('.planner-host', { hasText: name });
const slot = (page, name, time) => page.locator(`.planner-slot[data-host="${name}"]`, { hasText: time });

test('the week is hosts.yml\'s days with hours, each with its host', async ({ page }) => {
  await openStudio(page);
  await expect(page.locator('.planner-date b')).toHaveText(['Tue', 'Wed', 'Thu', 'Fri', 'Sat']);
  await expect(page.locator('.planner-month')).toHaveText('November');
  await expect(page.locator('.planner-host > span')).toHaveText(['James', 'Morey', 'Nate', 'Chris', 'Autumn']); // first names; hosts.yml has the full ones
  // What each can help with is on their card; a slot is only its time.
  await expect(card(page, 'Morey').locator('small')).toHaveText('Audio · Video · Podcasting · Outreach'); // hosts.yml's supports, as written
  // Morey's 11–4 is two slots, with an hour between.
  await expect(page.locator('.planner-slot[data-host="Morey Hubin"]')).toHaveCount(2);
  await expect(page.locator('.planner-slot[data-host="Morey Hubin"]').first()).toHaveText('11–1');
  await expect(slot(page, 'Morey Hubin', '11–1')).toBeVisible();
  await expect(slot(page, 'Morey Hubin', '2–4')).toBeVisible();
});

test('picking a host picks their slot; picking a slot picks its host', async ({ page }) => {
  await openStudio(page);
  await card(page, 'Morey').click();
  expect(await picked(page)).toEqual(['2026-11-04', '11:00', 'Morey Hubin']);
  await expect(card(page, 'Morey')).toHaveClass(/is-picked/);

  await card(page, 'Morey').click(); // unpicked: the time stays, the host goes
  await slot(page, 'Autumn Ryan/Valenta', '2–4').click();
  expect(await picked(page)).toEqual(['2026-11-07', '14:00', 'Autumn Ryan/Valenta']);
});

test('a host picked by hand stays, and the day\'s own host is marked', async ({ page }) => {
  await openStudio(page);
  await card(page, 'Morey').click();
  await slot(page, 'Autumn Ryan/Valenta', '11–1').click();
  expect(await picked(page)).toEqual(['2026-11-07', '11:00', 'Morey Hubin']);
  await expect(card(page, 'Morey')).toHaveClass(/is-picked/);
  await expect(page.locator('.planner-seat.is-suggested')).toContainText('Autumn');
});

test('another week stops drawing the pick but keeps it in the form', async ({ page }) => {
  await openStudio(page);
  await slot(page, 'Nate Keen', '5–7').click();
  await expect(page.locator('.planner-slot.is-picked')).toHaveCount(1);
  await page.locator('[data-week="1"]').click();
  await expect(page.locator('.planner-date').first()).toContainText('10');
  await expect(page.locator('.planner-slot.is-picked')).toHaveCount(0);
  expect(await picked(page)).toEqual(['2026-11-05', '17:00', 'Nate Keen']);
});

test('above the day asks for earlier, and the start can be changed', async ({ page }) => {
  await openStudio(page);
  await page.locator('.planner-bumper', { hasText: 'Earlier' }).nth(1).click(); // Wednesday's
  expect(await picked(page)).toEqual(['2026-11-04', '09:00', '']);
  await expect(page.locator('#book-start')).toBeFocused();
  await expect(page.locator('.planner-bumper.is-picked')).toContainText('9–11');
});

test('no time, no request', async ({ page }) => {
  let calls = 0;
  await page.route(`${WORKER}/**`, (route) => { calls += 1; route.fulfill({ json: { ok: true } }); });
  await openStudio(page);
  await page.locator('#book button[type="submit"]').click();
  await expect(page.locator('#book [data-say="pick-time"]')).toBeVisible();
  expect(calls).toBe(0);
});

test('the request goes to the book tank, kept on the phone with check-in\'s name', async ({ page }) => {
  let sent = null;
  await page.route(`${WORKER}/answers`, async (route) => {
    sent = route.request().postDataJSON();
    await route.fulfill({ json: { ok: true } });
  });
  await page.addInitScript(() => {
    localStorage.setItem('fcpm.profile', JSON.stringify({ name: 'Jo Tester', email: 'jo@example.org', reason: '', note: '' }));
  });
  await openStudio(page);
  await expect(page.locator('#book-name')).toHaveValue('Jo Tester');
  await expect(page.locator('#book-email')).toHaveValue('jo@example.org');

  await page.locator('.book-picks label', { hasText: 'Podcast Studio' }).click();
  await expect(page.locator('[data-space="Podcast Studio"]')).toBeVisible();
  await expect(page.locator('[data-space="Video Studio"]')).toBeHidden();
  await slot(page, 'Autumn Ryan/Valenta', '11–1').click();
  await page.locator('#book-name').fill('Jo Q Tester');
  await page.locator('#book button[type="submit"]').click();

  await expect(page.locator('[data-receipt="sent"]')).toBeVisible();
  expect(sent.form).toBe('book');
  expect(sent.answers).toEqual({
    first_name: 'Jo', last_name: 'Q Tester', email: 'jo@example.org', space: 'Podcast Studio',
    when: 'Saturday, November 7, 2026, 11 am to 1 pm, with Autumn Ryan/Valenta',
  });
  await expect(page.locator('[data-receipt="sent"] [data-reference]')).toHaveText(sent.reference.slice(0, 8));
  await expect(page.locator('[data-mine-list] li')).toContainText('Podcast Studio');
  const profile = await page.evaluate(() => JSON.parse(localStorage.getItem('fcpm.profile')));
  expect(profile.name).toBe('Jo Q Tester');
});

test('a red line marks now on today, and the month changes with the week', async ({ page }) => {
  // Wednesday 28 October at 12:30: Wednesday's column, a little past the top of the day.
  await page.clock.setFixedTime(new Date('2026-10-28T12:30:00'));
  await page.goto('/reserve/#studio');
  await expect(page.locator('.planner-now')).toHaveCount(1);
  const wednesday = page.locator('.planner-track').nth(1);
  await expect(wednesday.locator('.planner-now')).toHaveCount(1);
  await expect(page.locator('.planner-month')).toHaveText('October');
  await page.locator('[data-week="1"]').click();
  await expect(page.locator('.planner-month')).toHaveText('November');
  await expect(page.locator('.planner-now')).toHaveCount(0);
});
