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

// The studio request: a week drawn from site/_data/hosts.yml. These tests name no host, day or hour: they take
// whatever the file holds, so changing it never turns them red. A Sunday just after midnight: weeks run Sunday
// to Saturday, so the whole of "this week" is still ahead.
const WORKER = 'https://worker.test';
const SUNDAY = new Date('2026-11-01T00:01:00');

async function openStudio(page) {
  await page.clock.setFixedTime(SUNDAY);
  await page.goto('/reserve/#studio');
  await page.locator('#book').evaluate((form, worker) => { form.dataset.worker = worker; }, WORKER);
}

const picked = (page) => Promise.all(['#book-date', '#book-start', '#book-host'].map((s) => page.inputValue(s)));
const hostOf = (locator) => locator.getAttribute('data-host');

test('the week has a column per day with hours, and a card for each host whose slots it shows', async ({ page }) => {
  await openStudio(page);
  expect(await page.locator('.planner-date').count()).toBeGreaterThan(0);
  await expect(page.locator('.planner-month')).not.toHaveText('');
  const cards = await page.locator('.planner-host').evaluateAll((all) => all.map((c) => [c.dataset.host, c.querySelector('span').textContent]));
  for (const [name, shown] of cards) expect(shown).toBe(name.split(' ')[0]); // first names; hosts.yml has the full ones
  const slotHosts = await page.locator('.planner-slot').evaluateAll((all) => all.map((s) => s.dataset.host));
  expect(new Set(slotHosts)).toEqual(new Set(cards.map(([name]) => name)));
});

test('picking a host picks their slot; picking a slot picks its host', async ({ page }) => {
  await openStudio(page);
  const card = page.locator('.planner-host').first();
  const name = await hostOf(card);
  await card.click();
  const [date, start, host] = await picked(page);
  expect(host).toBe(name);
  expect(date && start).toBeTruthy();
  await expect(card).toHaveClass(/is-picked/);
  expect(await page.locator('.planner-slot.is-picked').evaluateAll((all) => all.map((s) => s.dataset.host))).toContain(name);

  await card.click(); // unpicked: the time stays, the host goes
  expect(await picked(page)).toEqual([date, start, '']);
  const slot = page.locator('.planner-slot').last();
  await slot.click();
  expect((await picked(page))[2]).toBe(await hostOf(slot));
  await expect(slot).toHaveClass(/is-picked/);
});

test('a host picked by hand stays, and the day\'s own host is marked', async ({ page }) => {
  await openStudio(page);
  const card = page.locator('.planner-host').first();
  const name = await hostOf(card);
  const other = page.locator(`.planner-slot:not([data-host="${name}"])`).first();
  test.skip(!(await other.count()), 'hosts.yml has one host');
  await card.click();
  await other.click();
  expect((await picked(page))[2]).toBe(name);
  await expect(card).toHaveClass(/is-picked/);
  await expect(page.locator('.planner-seat.is-suggested').first()).toBeVisible();
});

test('another week stops drawing the pick but keeps it in the form', async ({ page }) => {
  await openStudio(page);
  const slot = page.locator('.planner-slot').first();
  await slot.click();
  const before = await picked(page);
  const first = await page.locator('.planner-date').first().textContent();
  await expect(slot).toHaveClass(/is-picked/);
  await page.locator('[data-week="1"]').click();
  await expect(page.locator('.planner-date').first()).not.toHaveText(first);
  await expect(page.locator('.planner-slot.is-picked')).toHaveCount(0);
  expect(await picked(page)).toEqual(before);
});

test('above the day asks for earlier, and the start can be changed', async ({ page }) => {
  await openStudio(page);
  await page.locator('.planner-bumper', { hasText: 'Earlier' }).first().click();
  const [date, start, host] = await picked(page);
  expect(date && start).toBeTruthy();
  expect(host).toBe('');
  await expect(page.locator('#book-start')).toBeFocused();
  await expect(page.locator('.planner-bumper.is-picked')).toHaveCount(1);
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
  const slot = page.locator('.planner-slot').first();
  const host = await hostOf(slot);
  await slot.click();
  await page.locator('#book-name').fill('Jo Q Tester');
  await page.locator('#book button[type="submit"]').click();

  await expect(page.locator('[data-receipt="sent"]')).toBeVisible();
  expect(sent.form).toBe('book');
  const { when, ...rest } = sent.answers;
  expect(rest).toEqual({ first_name: 'Jo', last_name: 'Q Tester', email: 'jo@example.org', space: 'Podcast Studio' });
  expect(when).toMatch(new RegExp(`^\\w+day, \\w+ \\d+, \\d{4}, \\d+(:\\d\\d)? [ap]m to \\d+(:\\d\\d)? [ap]m, with ${host.replace(/[.*+?^${}()|[\]\\/]/g, '\\$&')}$`));
  await expect(page.locator('[data-receipt="sent"] [data-reference]')).toHaveText(sent.reference.slice(0, 8));
  await expect(page.locator('[data-mine-list] li')).toContainText('Podcast Studio');
  const profile = await page.evaluate(() => JSON.parse(localStorage.getItem('fcpm.profile')));
  expect(profile.name).toBe('Jo Q Tester');
});

test('a red line marks now on today, and not on another week', async ({ page }) => {
  await openStudio(page);
  const day = Number((await page.locator('.planner-date').first().textContent()).match(/\d+/)[0]);
  await page.clock.setFixedTime(new Date(SUNDAY.getFullYear(), SUNDAY.getMonth(), day, 12, 30));
  await page.reload();
  await expect(page.locator('.planner-track').first().locator('.planner-now')).toHaveCount(1);
  await page.locator('[data-week="1"]').click();
  await expect(page.locator('.planner-now')).toHaveCount(0);
});
