// /join/: the rules are stated, and the nonprofit lookup always leaves a way through.

const { test, expect } = require('./fixtures');

const DATA = '**/assets/nonprofits.json';

// The tiers as sync-tiers.py last pulled them from Stripe; none until it has run.
const TIERS = (() => {
  try {
    return require('../_data/tiers.json').tiers || [];
  } catch {
    return [];
  }
})();

/** A small stand-in, so matching is tested rather than the size of the file. */
const ORGS = {
  county: 'Larimer',
  orgs: [
    ['840123456', 'POUDRE RIVER LIBRARY TRUST', 'Fort Collins'],
    ['840987654', 'ST MARYS COMMUNITY KITCHEN', 'Loveland'],
    ['841112223', 'FORT COLLINS MUSEUM OF DISCOVERY', 'Fort Collins'],
    ['842223334', 'NORTHERN COLORADO KIDS THRIVE', 'Fort Collins'],
  ],
};

async function withList(page, { status = 200, body = ORGS } = {}) {
  await page.route(DATA, async (route) => {
    if (status !== 200) {
      await route.fulfill({ status, contentType: 'text/plain', body: 'no' });
      return;
    }
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body) });
  });
}

test.describe('the tiers', () => {
  test('the nonprofit rate is on every tier, not hidden in a paragraph', async ({ page }) => {
    // The nonprofit rate is on the page for everyone: half, to the dollar.
    test.skip(!TIERS.length, 'site/_data/tiers.json has no tiers; run sync-tiers.py');
    await page.goto('/join/');

    const cards = page.locator('.grid-4 .card');
    await expect(cards).toHaveCount(TIERS.length);

    for (const tier of TIERS) {
      const card = page.locator('.card', { hasText: tier.name });
      await expect(card).toContainText(`$${tier.price}`);
      await expect(card).toContainText(`Nonprofits $${Math.round(tier.amount / 200)}`);
    }
  });

  test('with no tiers pulled, no empty grid', async ({ page }) => {
    test.skip(TIERS.length > 0, 'tiers are pulled');
    await page.goto('/join/');
    await expect(page.locator('.tiers')).toHaveCount(0);
  });
});

test.describe('finding your organization', () => {
  const field = (page) => page.locator('#organization');
  const results = (page) => page.locator('[data-org-results] li');

  test('the list is not fetched until somebody types there', async ({ page }) => {
    // A hundred and sixteen kilobytes that most visitors have no use for.
    let fetched = 0;
    await page.route(DATA, async (route) => {
      fetched += 1;
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(ORGS) });
    });

    await page.goto('/join/');
    await expect(field(page)).toBeVisible();
    expect(fetched).toBe(0);

    await field(page).fill('poudre');
    await expect(results(page)).toHaveCount(1);
    expect(fetched).toBe(1);
  });

  test('words in any order still find it', async ({ page }) => {
    await withList(page);
    await page.goto('/join/');
    await field(page).fill('trust library');
    await expect(results(page)).toContainText('POUDRE RIVER LIBRARY TRUST');
  });

  test('punctuation you would type does not stop a match', async ({ page }) => {
    // The IRS file has no apostrophes. People do.
    await withList(page);
    await page.goto('/join/');
    await field(page).fill("st. mary's");
    await expect(results(page)).toContainText('ST MARYS COMMUNITY KITCHEN');
  });

  test('choosing one fills the field with its name and EIN, which is the point', async ({ page }) => {
    await withList(page);
    await page.goto('/join/');
    await field(page).fill('museum');
    await page.locator('[data-org-results] button').first().click();

    await expect(field(page)).toHaveValue('FORT COLLINS MUSEUM OF DISCOVERY (EIN 841112223)');
    await expect(page.locator('[data-org="chosen"]')).toBeVisible();
    await expect(page.locator('[data-org="chosen"] [data-ein]')).toHaveText('841112223');
    await expect(results(page)).toHaveCount(0);
  });

  test('an organization not on the list is kept as typed', async ({ page }) => {
    // Plenty of organizations, and every business, are not on it; nothing says no.
    await withList(page);
    await page.goto('/join/');
    await field(page).fill('Acme Video Cooperative');
    await expect(results(page)).toHaveCount(0);
    await expect(field(page)).toHaveValue('Acme Video Cooperative');
  });

  test('the list failing to load leaves an ordinary field', async ({ page }) => {
    await withList(page, { status: 500 });
    await page.goto('/join/');
    await field(page).fill('poudre');
    await expect(results(page)).toHaveCount(0);
    await expect(field(page)).toHaveValue('poudre');
  });
});

test.describe('the synced list', () => {
  test('is real, and shaped the way the page expects', async ({ page }) => {
    // Against the committed file, so the sync script's format is checked too.
    const response = await page.request.get('/assets/nonprofits.json');
    expect(response.status()).toBe(200);

    const payload = await response.json();
    expect(payload.county).toBe('Larimer');
    expect(payload.orgs.length).toBeGreaterThan(500);

    for (const [ein, name, city] of payload.orgs.slice(0, 50)) {
      expect(ein).toMatch(/^\d{9}$/);
      expect(name.length).toBeGreaterThan(0);
      expect(city.length).toBeGreaterThan(0);
    }
  });
});
