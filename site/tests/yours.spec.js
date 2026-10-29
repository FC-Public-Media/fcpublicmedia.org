// /you/ and keep.js: every form's reply is kept on the device before it is sent, the contact card is
// noticed, and /you/ reads it back, sends it again, shows it to our camera, or deletes it.

const { test, expect } = require('./fixtures');

const WORKER = 'https://worker.test';

const readStore = (page, key, fallback = []) =>
  page.evaluate(([k, f]) => JSON.parse(localStorage.getItem(k) || JSON.stringify(f)), [key, fallback]);

async function fresh(page) {
  await page.goto('/you/');
  await page.evaluate(() => localStorage.clear());
}

async function submitProgram(page, { email = 'ada@example.org', phone = '', worker = WORKER } = {}) {
  await page.goto('/submit/');
  await page.locator('form[data-tank]').evaluate((f, w) => { if (w) f.dataset.worker = w; else delete f.dataset.worker; }, worker);
  await page.locator('[name="copyright"]').check();
  await page.locator('#first_name').fill('Ada');
  await page.locator('#email').fill(email);
  if (phone) await page.locator('[name="phone"]').fill(phone);
  await page.locator('#title').fill('Night Shift');
  await page.locator('#category').selectOption('Music');
  await page.getByRole('button', { name: 'Submit' }).click();
}

// Feeds the shown frames to the vendored composer, as the door's intake does.
const readFrames = (page) =>
  page.evaluate(async () => {
    const frames = JSON.parse(document.getElementById('show-code').dataset.frames || '[]');
    const { carrierSession } = await import('/assets/js/composer/carrier.mjs');
    const session = carrierSession({ friends: [] });
    let snap = null;
    for (const f of frames) snap = await session.feed(f);
    if (!snap?.complete) return null;
    const v = (await session.result()).transfers[0].verify;
    return v.bytes ? new TextDecoder().decode(v.bytes) : null;
  });

test.describe('kept replies', () => {
  test('a form keeps its reply before it sends, and marks it sent', async ({ page }) => {
    await fresh(page);
    let body;
    await page.route(`${WORKER}/answers`, async (route) => {
      body = route.request().postDataJSON();
      await route.fulfill({ json: { ok: true } });
    });
    await submitProgram(page);
    await expect(page.locator('[data-receipt="sent"]')).toBeVisible();

    const [kept] = await readStore(page, 'fcpm.replies');
    expect(kept.reference).toEqual(body.reference);
    expect(kept.tank).toEqual('program');
    expect(kept.sent.via).toEqual('tank');
    expect(kept.post.body).toEqual(body);
    expect(kept.lines).toContain('Title: Night Shift');
    const reply = JSON.parse(kept.reply);
    expect(Object.keys(reply)).toEqual(['schema', 'wizard', 'at', 'tank', 'reference', 'answers', 'issued', 'nonce', 'sig']);
    expect(reply).toMatchObject({ schema: 'fcpm.reply/v0', wizard: 'wizard:site+answers', tank: 'program', reference: body.reference });
    expect(reply.answers).toEqual(body.answers);
    expect(reply.at).toBeTruthy();
  });

  test('a send that fails loses nothing, and /you/ sends it again as it was', async ({ page }) => {
    await fresh(page);
    const bodies = [];
    let up = false;
    await page.route(`${WORKER}/answers`, async (route) => {
      bodies.push(route.request().postDataJSON());
      await route.fulfill({ json: up ? { ok: true } : { ok: false, detail: 'down' } });
    });
    await submitProgram(page);
    await expect(page.locator('[data-say="failed"]')).toBeVisible();
    await expect(page.locator('[data-say="failed"] a[href$="/you/"]')).toBeVisible();

    await page.goto('/you/');
    await expect(page.locator('#replies li')).toHaveCount(1);
    await expect(page.locator('#replies li')).toContainText('Program submission');
    await expect(page.locator('#replies li')).toContainText('kept, not sent');

    await page.locator('#replies li a').click();
    await expect(page.locator('[data-view="reply"]')).toBeVisible();
    await expect(page.locator('#reply-lines')).toContainText('Night Shift');
    up = true;
    await page.locator('#reply-send').click();
    await expect(page.locator('#reply-said')).toHaveText('Sent.');
    await expect(page.locator('#reply-send')).toBeHidden();

    expect(bodies).toHaveLength(2);
    expect(bodies[1]).toEqual(bodies[0]);
    expect((await readStore(page, 'fcpm.replies'))[0].sent.via).toEqual('tank');
  });

  test('a form that cannot send is still kept, with its email', async ({ page }) => {
    await fresh(page);
    await submitProgram(page, { worker: null });
    await expect(page.locator('[data-say="unsent"]')).toBeVisible();

    await page.goto('/you/');
    await page.locator('#replies li a').click();
    await expect(page.locator('#reply-send')).toBeHidden();
    await expect(page.locator('#reply-email')).toHaveAttribute('href', /^mailto:/);
  });

  test('Show it pours the kept reply as a bottle our camera reads', async ({ page }) => {
    await fresh(page);
    await page.route(`${WORKER}/answers`, (route) => route.fulfill({ json: { ok: true } }));
    await submitProgram(page);
    await expect(page.locator('[data-receipt="sent"]')).toBeVisible();

    await page.goto('/you/');
    await page.locator('#replies li a').click();
    await page.locator('#reply-show').click();
    await expect(page.locator('#show-read')).toContainText('signed');
    expect(await readFrames(page)).toEqual((await readStore(page, 'fcpm.replies'))[0].reply);

    await page.getByRole('link', { name: 'Back' }).click();
    await expect(page.locator('[data-view="reply"]')).toBeVisible();
  });

  test('deleting a reply takes it off this phone', async ({ page }) => {
    await fresh(page);
    await submitProgram(page, { worker: null });
    await page.goto('/you/');
    await page.locator('#replies li a').click();
    page.on('dialog', (dialog) => dialog.accept());
    await page.locator('#reply-drop').click();
    await expect(page.locator('[data-view="list"]')).toBeVisible();
    await expect(page.locator('#replies-empty')).toBeVisible();
    expect(await readStore(page, 'fcpm.replies')).toEqual([]);
  });

  test('opening /you/ sends nothing anywhere', async ({ page }) => {
    await fresh(page);
    await submitProgram(page, { worker: null });
    const outbound = [];
    page.on('request', (request) => { if (request.method() !== 'GET') outbound.push(request.url()); });
    await page.goto('/you/');
    await page.locator('#replies li a').click();
    await page.waitForTimeout(300);
    expect(outbound).toEqual([]);
  });
});

test.describe('contact cards', () => {
  test('a name, email and phone typed into a form become a card', async ({ page }) => {
    await fresh(page);
    await submitProgram(page, { worker: null, phone: '(970) 555-0100' });
    const [card] = await readStore(page, 'fcpm.cards');
    expect(card).toMatchObject({ name: 'Ada', email: 'ada@example.org', phone: '(970) 555-0100' });

    await page.goto('/you/');
    await expect(page.locator('#cards li')).toHaveCount(1);
    await expect(page.locator('#cards li')).toContainText('ada@example.org');
  });

  test('the same email is the same card; a new one is another card, never refused', async ({ page }) => {
    await fresh(page);
    await submitProgram(page, { worker: null });
    await submitProgram(page, { worker: null, phone: '970-555-0100' });
    let cards = await readStore(page, 'fcpm.cards');
    expect(cards).toHaveLength(1);
    expect(cards[0].phone).toEqual('970-555-0100');

    await submitProgram(page, { worker: null, email: 'ada.friend@example.org' });
    cards = await readStore(page, 'fcpm.cards');
    expect(cards).toHaveLength(2);
    expect(cards[0].email).toEqual('ada.friend@example.org');
  });

  test('a card can be removed', async ({ page }) => {
    await fresh(page);
    await submitProgram(page, { worker: null });
    await page.goto('/you/');
    await page.locator('#cards li').getByRole('button', { name: 'Remove' }).click();
    await expect(page.locator('#cards-empty')).toBeVisible();
    expect(await readStore(page, 'fcpm.cards')).toEqual([]);
  });

  test('checking in notices the card too', async ({ page }) => {
    await page.goto('/check-in/');
    await page.evaluate(() => localStorage.clear());
    await page.reload();
    await page.locator('#profile-name').fill('Sam Rivera');
    await page.locator('#profile-email').fill('sam@example.org').catch(() => {});
    await page.locator('[data-state="idle"] [data-action="check-in"]').click();
    await expect(page.locator('[data-state="done"]')).toBeVisible();
    const [card] = await readStore(page, 'fcpm.cards');
    expect(card.name).toEqual('Sam Rivera');
  });

  test('a form is never filled in from the cards', async ({ page }) => {
    await fresh(page);
    await submitProgram(page, { worker: null });
    await page.goto('/submit/');
    await expect(page.locator('#first_name')).toHaveValue('');
    await expect(page.locator('#email')).toHaveValue('');
  });
});
