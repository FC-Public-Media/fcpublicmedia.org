// The check-in page is the one part of this site with real client-side state,
// so it gets real tests. Everything it does happens in localStorage on the
// visitor's device, which means the failure modes are all invisible: a check
// that silently does not save, a history that vanishes, a "forget" button that
// forgets only half of it.

const { test, expect } = require('@playwright/test');

const PATH = '/check-in/';

const readHistory = (page) =>
  page.evaluate(() => JSON.parse(localStorage.getItem('fcpm.checkins') || '[]'));

const readDevice = (page) =>
  page.evaluate(() => JSON.parse(localStorage.getItem('fcpm.device') || 'null'));

test.describe('check-in', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(PATH);
    await page.evaluate(() => localStorage.clear());
    await page.reload();
    await expect(page.locator('#checkin-app')).toBeVisible();
  });

  test('generates a device identifier on first visit', async ({ page }) => {
    const device = await readDevice(page);

    expect(device).toBeTruthy();
    expect(device.id).toMatch(/^[0-9a-f-]{16,}$/);
    expect(device.created).toBeTruthy();

    // Only a fragment of the identifier is shown. There is no reason to put a
    // full identifier on screen where it can be photographed.
    const shown = await page.locator('#device-id').textContent();
    expect(shown.length).toBeLessThan(device.id.length);
    expect(device.id.startsWith(shown)).toBe(true);
  });

  test('the identifier is random, not derived from the device', async ({ browser }) => {
    // Two fresh contexts on the same browser and OS must not collide.
    const ids = [];
    for (let i = 0; i < 2; i += 1) {
      const context = await browser.newContext();
      const page = await context.newPage();
      await page.goto(PATH);
      await expect(page.locator('#checkin-app')).toBeVisible();
      ids.push((await readDevice(page)).id);
      await context.close();
    }

    expect(ids[0]).not.toEqual(ids[1]);
  });

  test('records a visit and shows it', async ({ page }) => {
    await expect(page.locator('#checkin-empty')).toBeVisible();

    await page.locator('#checkin-button').click();

    await expect(page.locator('#checkin-status')).toContainText('Checked in');
    await expect(page.locator('#checkin-history li')).toHaveCount(1);
    await expect(page.locator('#checkin-count')).toContainText('1 visit');
    await expect(page.locator('#checkin-empty')).toBeHidden();

    const history = await readHistory(page);
    expect(history).toHaveLength(1);
    expect(history[0].at).toBeTruthy();
    expect(history[0].device).toEqual((await readDevice(page)).id);
  });

  test('history survives a reload', async ({ page }) => {
    await page.locator('#checkin-button').click();
    await expect(page.locator('#checkin-history li')).toHaveCount(1);

    await page.reload();

    await expect(page.locator('#checkin-history li')).toHaveCount(1);
    await expect(page.locator('#checkin-count')).toContainText('1 visit');
  });

  test('newest visit is listed first', async ({ page }) => {
    await page.locator('#checkin-button').click();
    await expect(page.locator('#checkin-history li')).toHaveCount(1);

    // Push the first entry into the past so ordering is unambiguous.
    await page.evaluate(() => {
      const history = JSON.parse(localStorage.getItem('fcpm.checkins'));
      history[0].at = '2020-01-01T00:00:00.000Z';
      localStorage.setItem('fcpm.checkins', JSON.stringify(history));
    });
    await page.reload();

    await page.locator('#checkin-button').click();
    await expect(page.locator('#checkin-history li')).toHaveCount(2);

    const history = await readHistory(page);
    expect(new Date(history[0].at).getTime()).toBeGreaterThan(new Date(history[1].at).getTime());
  });

  test('the device name is editable and persists', async ({ page }) => {
    await page.locator('#device-label').fill('Front desk iPad');
    await page.locator('#device-label').blur();

    await page.reload();

    await expect(page.locator('#device-label')).toHaveValue('Front desk iPad');
    expect((await readDevice(page)).label).toEqual('Front desk iPad');
  });

  test('forgetting the device clears the identifier and the history', async ({ page }) => {
    await page.locator('#checkin-button').click();
    await expect(page.locator('#checkin-history li')).toHaveCount(1);

    const before = (await readDevice(page)).id;

    page.once('dialog', (dialog) => dialog.accept());
    await page.locator('#forget-button').click();

    await expect(page.locator('#checkin-history li')).toHaveCount(0);
    await expect(page.locator('#checkin-empty')).toBeVisible();

    expect(await readHistory(page)).toEqual([]);
    // A new identifier, not the old one lingering.
    expect((await readDevice(page)).id).not.toEqual(before);
  });

  test('cancelling forget keeps everything', async ({ page }) => {
    await page.locator('#checkin-button').click();
    const before = (await readDevice(page)).id;

    page.once('dialog', (dialog) => dialog.dismiss());
    await page.locator('#forget-button').click();

    await expect(page.locator('#checkin-history li')).toHaveCount(1);
    expect((await readDevice(page)).id).toEqual(before);
  });

  test('history is capped so storage cannot grow forever', async ({ page }) => {
    const limit = await page.evaluate(
      () => JSON.parse(document.getElementById('checkin-config').textContent).historyLimit
    );

    await page.evaluate((n) => {
      const history = Array.from({ length: n + 25 }, (_, i) => ({
        at: new Date(Date.now() - i * 60000).toISOString(),
        device: 'test',
        email: null,
      }));
      localStorage.setItem('fcpm.checkins', JSON.stringify(history));
    }, limit);

    await page.reload();
    await page.locator('#checkin-button').click();

    expect((await readHistory(page)).length).toBeLessThanOrEqual(limit);
  });

  test('exporting produces a file with the history in it', async ({ page }) => {
    await page.locator('#checkin-button').click();
    await expect(page.locator('#checkin-history li')).toHaveCount(1);

    const download = await Promise.all([
      page.waitForEvent('download'),
      page.locator('#export-button').click(),
    ]).then(([event]) => event);

    expect(download.suggestedFilename()).toMatch(/^fcpm-checkins-\d{4}-\d{2}-\d{2}\.json$/);

    const stream = await download.createReadStream();
    const chunks = [];
    for await (const chunk of stream) chunks.push(chunk);
    const payload = JSON.parse(Buffer.concat(chunks).toString());

    expect(payload.checkins).toHaveLength(1);
    expect(payload.device.id).toBeTruthy();
    expect(payload.exported).toBeTruthy();
  });

  test('importing merges rather than replacing', async ({ page }) => {
    // One visit already on the device.
    await page.locator('#checkin-button').click();
    await expect(page.locator('#checkin-history li')).toHaveCount(1);

    const backup = JSON.stringify({
      exported: '2024-01-01T00:00:00.000Z',
      device: { id: 'old-device', label: '', created: '2024-01-01T00:00:00.000Z' },
      checkins: [
        { at: '2024-01-01T10:00:00.000Z', device: 'old-device', email: null },
        { at: '2024-02-01T10:00:00.000Z', device: 'old-device', email: null },
      ],
    });

    await page.locator('#import-input').setInputFiles({
      name: 'backup.json',
      mimeType: 'application/json',
      buffer: Buffer.from(backup),
    });

    // The visit made a moment ago must still be there alongside the restored
    // two — importing a backup should never lose newer visits.
    await expect(page.locator('#checkin-history li')).toHaveCount(3);
    await expect(page.locator('#checkin-status')).toContainText('Restored 2 visits');
  });

  test('a bad import file reports rather than throwing', async ({ page }) => {
    await page.locator('#import-input').setInputFiles({
      name: 'nonsense.json',
      mimeType: 'application/json',
      buffer: Buffer.from('this is not json'),
    });

    await expect(page.locator('#checkin-status')).toContainText('could not be read');
    expect(await readHistory(page)).toEqual([]);
  });

  test('nothing is sent anywhere when checking in', async ({ page }) => {
    // The promise of this page is that the visit stays on the device. If a
    // future change starts posting somewhere, this fails.
    const outbound = [];
    page.on('request', (request) => {
      const url = request.url();
      const sameDocument = url.includes('/check-in/') || url.includes('/assets/');
      if (!sameDocument && request.method() !== 'GET') outbound.push(`${request.method()} ${url}`);
    });

    await page.locator('#checkin-button').click();
    await expect(page.locator('#checkin-status')).toContainText('Checked in');
    await page.waitForTimeout(500);

    expect(outbound, 'check-in made a network request').toEqual([]);
  });
});

test.describe('check-in poster', () => {
  test('shows a QR code and the URL it encodes', async ({ page }) => {
    await page.goto('/check-in/poster/');

    const qr = page.locator('.poster-qr');
    await expect(qr).toBeVisible();

    // A broken image here means a printed poster with a blank square on it.
    const loaded = await qr.evaluate((img) => img.complete && img.naturalWidth > 0);
    expect(loaded, 'the QR image did not load').toBe(true);

    await expect(page.locator('.poster-url')).toContainText('fcpublicmedia.org/check-in/');
  });
});
