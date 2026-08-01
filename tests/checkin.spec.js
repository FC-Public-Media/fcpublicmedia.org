// The check-in page is the one part of this site with real client-side state
// and real conditional behaviour, so it gets real tests.
//
// Geolocation is mocked through Playwright's context permissions and
// setGeolocation, which is the only way to exercise "you are not here yet"
// without standing in a car park.

const { test, expect } = require('@playwright/test');

const PATH = '/check-in/';

// Carnegie Center for Creativity, from _data/checkin.yml.
const STUDIO = { latitude: 40.5849119, longitude: -105.0735292 };
// Old Town Square, roughly 700m away — outside the 200m radius, close enough
// to be a realistic "on my way" position.
const NEARBY = { latitude: 40.5892, longitude: -105.0768 };
// Denver.
const FAR = { latitude: 39.7392, longitude: -104.9903 };

const readHistory = (page) =>
  page.evaluate(() => JSON.parse(localStorage.getItem('fcpm.checkins') || '[]'));
const readDevice = (page) =>
  page.evaluate(() => JSON.parse(localStorage.getItem('fcpm.device') || 'null'));
const readPending = (page) =>
  page.evaluate(() => JSON.parse(localStorage.getItem('fcpm.pending') || 'null'));

const panel = (page, state) => page.locator(`[data-state="${state}"]`);

async function fresh(page, context, coords) {
  if (coords) {
    await context.grantPermissions(['geolocation']);
    await context.setGeolocation(coords);
  }
  await page.goto(PATH);
  await page.evaluate(() => localStorage.clear());
  await page.reload();
}

test.describe('check-in', () => {
  test('offers a check-in button on arrival at the page', async ({ page, context }) => {
    await fresh(page, context, STUDIO);
    await expect(panel(page, 'idle')).toBeVisible();
    await expect(page.locator('[data-action="check-in"]').first()).toBeVisible();
  });

  test('checks in when you are at the studio', async ({ page, context }) => {
    await fresh(page, context, STUDIO);

    await page.locator('[data-state="idle"] [data-action="check-in"]').click();

    await expect(panel(page, 'done')).toBeVisible();
    await expect(page.locator('h2', { hasText: 'Welcome' })).toBeVisible();

    const history = await readHistory(page);
    expect(history).toHaveLength(1);
    expect(history[0].verified).toBe(true);
    expect(history[0].device).toEqual((await readDevice(page)).id);
    // Distance is kept; coordinates are not.
    expect(history[0].distance_m).toBeLessThan(200);
    expect(history[0]).not.toHaveProperty('latitude');
    expect(history[0]).not.toHaveProperty('longitude');

    expect(await readPending(page)).toBeNull();
  });

  test('holds the check-in as pending when you are not there yet', async ({ page, context }) => {
    await fresh(page, context, NEARBY);

    await page.locator('[data-state="idle"] [data-action="check-in"]').click();

    await expect(panel(page, 'far')).toBeVisible();
    await expect(page.locator('#far-distance')).toContainText(/\d/);
    await expect(page.locator('#venue-directions')).toHaveAttribute(
      'href',
      /google\.com\/maps\/dir/
    );

    expect(await readHistory(page)).toEqual([]);
    expect(await readPending(page)).not.toBeNull();
  });

  test('a long way away is still just pending, not an error', async ({ page, context }) => {
    await fresh(page, context, FAR);
    await page.locator('[data-state="idle"] [data-action="check-in"]').click();

    await expect(panel(page, 'far')).toBeVisible();
    await expect(page.locator('#far-distance')).toContainText('km');
  });

  test('completes by itself once you arrive', async ({ page, context }) => {
    await fresh(page, context, NEARBY);
    await page.locator('[data-state="idle"] [data-action="check-in"]').click();
    await expect(panel(page, 'far')).toBeVisible();

    // Walk in.
    await context.setGeolocation(STUDIO);
    await page.locator('[data-state="far"] [data-action="check-in"]').click();

    await expect(panel(page, 'done')).toBeVisible();
    expect(await readHistory(page)).toHaveLength(1);
    expect(await readPending(page)).toBeNull();
  });

  test('a pending check-in survives closing the page', async ({ page, context }) => {
    await fresh(page, context, NEARBY);
    await page.locator('[data-state="idle"] [data-action="check-in"]').click();
    await expect(panel(page, 'far')).toBeVisible();

    await page.reload();

    // Picked back up rather than starting over.
    await expect(panel(page, 'far')).toBeVisible();
    expect(await readPending(page)).not.toBeNull();
  });

  test('cancelling a pending check-in clears it', async ({ page, context }) => {
    await fresh(page, context, NEARBY);
    await page.locator('[data-state="idle"] [data-action="check-in"]').click();
    await expect(panel(page, 'far')).toBeVisible();

    await page.locator('#cancel-pending').click();

    await expect(panel(page, 'idle')).toBeVisible();
    expect(await readPending(page)).toBeNull();
  });

  test('explains itself when location is refused', async ({ page, context }) => {
    await context.clearPermissions();
    await page.goto(PATH);
    await page.evaluate(() => localStorage.clear());
    await page.reload();

    await page.locator('[data-state="idle"] [data-action="check-in"]').click();

    await expect(panel(page, 'denied')).toBeVisible();
    expect(await readHistory(page)).toEqual([]);
  });

  test('the device identifier is random, not derived from the device', async ({ browser }) => {
    const ids = [];
    for (let i = 0; i < 2; i += 1) {
      const context = await browser.newContext();
      const page = await context.newPage();
      await page.goto(PATH);
      ids.push((await readDevice(page)).id);
      await context.close();
    }
    expect(ids[0]).not.toEqual(ids[1]);
  });

  test('details are remembered and restored', async ({ page, context }) => {
    await fresh(page, context, STUDIO);

    await page.locator('#profile-name').fill('Sam Rivera');
    await page.locator('#profile-reason').selectOption('Class');
    await page.locator('#profile-note').fill('Podcasting 101');

    await page.reload();

    await expect(page.locator('#profile-name')).toHaveValue('Sam Rivera');
    await expect(page.locator('#profile-reason')).toHaveValue('Class');
    await expect(page.locator('#profile-note')).toHaveValue('Podcasting 101');
  });

  test('details are attached to the check-in', async ({ page, context }) => {
    await fresh(page, context, STUDIO);

    await page.locator('#profile-name').fill('Sam Rivera');
    await page.locator('#profile-reason').selectOption('Class');
    await page.locator('[data-state="idle"] [data-action="check-in"]').click();

    await expect(panel(page, 'done')).toBeVisible();
    const [entry] = await readHistory(page);
    expect(entry.name).toEqual('Sam Rivera');
    expect(entry.reason).toEqual('Class');
  });

  test('a reason can be primed from the URL', async ({ page, context }) => {
    await fresh(page, context, STUDIO);
    await page.goto(`${PATH}?reason=Class`);

    await expect(page.locator('#profile-reason')).toHaveValue('Class');
  });

  test('a nonsense reason in the URL is ignored', async ({ page, context }) => {
    await fresh(page, context, STUDIO);
    await page.goto(`${PATH}?reason=%3Cscript%3E`);

    // Falls back to the stored value rather than injecting an option.
    await expect(page.locator('#profile-reason')).toHaveValue('');
  });

  test('history shows the reason', async ({ page, context }) => {
    await fresh(page, context, STUDIO);
    await page.locator('#profile-reason').selectOption('Volunteering or crew');
    await page.locator('[data-state="idle"] [data-action="check-in"]').click();

    await expect(page.locator('#checkin-history li')).toHaveCount(1);
    await expect(page.locator('#checkin-history li')).toContainText('Volunteering or crew');
    await expect(page.locator('#checkin-count')).toContainText('1 visit');
  });

  test('history survives a reload', async ({ page, context }) => {
    await fresh(page, context, STUDIO);
    await page.locator('[data-state="idle"] [data-action="check-in"]').click();
    await expect(page.locator('#checkin-history li')).toHaveCount(1);

    await page.reload();
    await expect(page.locator('#checkin-history li')).toHaveCount(1);
  });

  test('forgetting the device clears everything', async ({ page, context }) => {
    await fresh(page, context, STUDIO);
    await page.locator('#profile-name').fill('Sam Rivera');
    await page.locator('[data-state="idle"] [data-action="check-in"]').click();
    await expect(panel(page, 'done')).toBeVisible();

    const before = (await readDevice(page)).id;

    page.once('dialog', (dialog) => dialog.accept());
    await page.locator('#forget-button').click();

    expect(await readHistory(page)).toEqual([]);
    expect((await readDevice(page)).id).not.toEqual(before);
    await expect(page.locator('#profile-name')).toHaveValue('');
    await expect(panel(page, 'idle')).toBeVisible();
  });

  test('exporting produces a file with the history in it', async ({ page, context }) => {
    await fresh(page, context, STUDIO);
    await page.locator('[data-state="idle"] [data-action="check-in"]').click();
    await expect(panel(page, 'done')).toBeVisible();

    const download = await Promise.all([
      page.waitForEvent('download'),
      page.locator('#export-button').click(),
    ]).then(([event]) => event);

    const stream = await download.createReadStream();
    const chunks = [];
    for await (const chunk of stream) chunks.push(chunk);
    const payload = JSON.parse(Buffer.concat(chunks).toString());

    expect(payload.checkins).toHaveLength(1);
    expect(payload.device.id).toBeTruthy();
  });

  test('importing merges rather than replacing', async ({ page, context }) => {
    await fresh(page, context, STUDIO);
    await page.locator('[data-state="idle"] [data-action="check-in"]').click();
    await expect(panel(page, 'done')).toBeVisible();

    await page.locator('#import-input').setInputFiles({
      name: 'backup.json',
      mimeType: 'application/json',
      buffer: Buffer.from(
        JSON.stringify({
          checkins: [
            { at: '2024-01-01T10:00:00.000Z', device: 'old', verified: true },
            { at: '2024-02-01T10:00:00.000Z', device: 'old', verified: true },
          ],
        })
      ),
    });

    await expect(page.locator('#checkin-history li')).toHaveCount(3);
    await expect(page.locator('#storage-status')).toContainText('Restored 2 visits');
  });

  test('a bad import file reports rather than throwing', async ({ page, context }) => {
    await fresh(page, context, STUDIO);
    await page.locator('#import-input').setInputFiles({
      name: 'nonsense.json',
      mimeType: 'application/json',
      buffer: Buffer.from('not json at all'),
    });

    await expect(page.locator('#storage-status')).toContainText('could not be read');
    expect(await readHistory(page)).toEqual([]);
  });

  test('nothing is sent anywhere when checking in', async ({ page, context }) => {
    await fresh(page, context, STUDIO);

    // The promise of this page is that the visit stays on the device. If a
    // future change starts posting somewhere, this fails.
    const outbound = [];
    page.on('request', (request) => {
      const url = request.url();
      const own = url.includes('/check-in/') || url.includes('/assets/');
      if (!own && request.method() !== 'GET') outbound.push(`${request.method()} ${url}`);
    });

    await page.locator('[data-state="idle"] [data-action="check-in"]').click();
    await expect(panel(page, 'done')).toBeVisible();
    await page.waitForTimeout(500);

    expect(outbound, 'check-in made a network request').toEqual([]);
  });
});

test.describe('check-in entry points', () => {
  test('the homepage offers one tap to check in', async ({ page }) => {
    await page.goto('/');

    const card = page.locator('.checkin-card');
    await expect(card).toBeVisible();

    const button = card.locator('a.btn-primary');
    await expect(button).toHaveAttribute('href', /\/check-in\/$/);

    // Same code as the printed poster, and it has to actually load. It is
    // lazy-loaded and below the fold on a phone, so scroll to it first and
    // wait — asserting immediately would only be testing the viewport height.
    const qr = card.locator('.checkin-card-qr img');
    await qr.scrollIntoViewIfNeeded();
    await expect
      .poll(() => qr.evaluate((img) => img.complete && img.naturalWidth > 0), {
        message: 'the QR image did not load',
      })
      .toBe(true);
  });

  test('the poster shows a QR and the URL it encodes', async ({ page }) => {
    await page.goto('/check-in/poster/');

    const qr = page.locator('.poster-qr');
    await expect(qr).toBeVisible();
    const loaded = await qr.evaluate((img) => img.complete && img.naturalWidth > 0);
    expect(loaded, 'the QR image did not load').toBe(true);

    await expect(page.locator('.poster-url')).toContainText('fcpublicmedia.org/check-in/');
  });
});
