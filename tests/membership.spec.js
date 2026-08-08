// Membership: the rules, and finding your own nonprofit.
//
// The feedback behind this page is that the pricing is hard to understand —
// and it is the rules that are hard, not the amounts. So the first tests here
// are about whether the rules are actually stated, which is the kind of thing
// that quietly rots when somebody rearranges a page.
//
// The rest are about the lookup, whose whole job is to stop being a gate. Most
// of what can go wrong with it — no matches, a failed download, no JavaScript
// — has to leave somebody a way through, because plenty of real organizations
// are legitimately not on the IRS list.

const { test, expect } = require('@playwright/test');

const DATA = '**/assets/nonprofits.json';

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

test.describe('the rules', () => {
  test('says the year starts when you join, not in January', async ({ page }) => {
    // The old site said both "January 1 – December 31" and "one year from
    // sign-up". This is the one that is true, and saying it is the whole point
    // of the section.
    await page.goto('/membership/');

    const rules = page.locator('h2', { hasText: 'How it works' }).locator('+ ul');
    await expect(rules).toContainText('A full year from the day you join');
    await expect(rules).toContainText('Not the calendar year');
  });

  test('says the two things that no longer exist', async ({ page }) => {
    // Both were real rules people remember. Leaving them unstated is how
    // somebody ends up arguing about a half-year price at the front desk.
    await page.goto('/membership/');

    const rules = page.locator('h2', { hasText: 'How it works' }).locator('+ ul');
    await expect(rules).toContainText('No half-year price');
    await expect(rules).toContainText('No monthly option');
  });

  test('the nonprofit rate is on every tier, not hidden in a paragraph', async ({ page }) => {
    // "Some of our people know that nonprofits pay half" is the failure being
    // fixed: a discount only the informed got.
    await page.goto('/membership/');

    const cards = page.locator('.grid-4 .card');
    await expect(cards).toHaveCount(4);

    for (const card of await cards.all()) {
      await expect(card).toContainText(/Nonprofits \$\d+/);
    }
    await expect(page.locator('.card', { hasText: 'Sponsor' })).toContainText('Nonprofits $20');
    await expect(page.locator('.card', { hasText: 'Producer' })).toContainText('Nonprofits $70');
  });
});

test.describe('finding your organization', () => {
  test('the list is not fetched until somebody needs it', async ({ page }) => {
    // A hundred and sixteen kilobytes that most visitors have no use for.
    let fetched = 0;
    await page.route(DATA, async (route) => {
      fetched += 1;
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(ORGS) });
    });

    await page.goto('/membership/');
    await expect(page.locator('#nonprofit-search')).toBeVisible();
    expect(fetched).toBe(0);

    await page.locator('#nonprofit-search').fill('poudre');
    await expect(page.locator('#nonprofit-results li')).toHaveCount(1);
    expect(fetched).toBe(1);
  });

  test('words in any order still find it', async ({ page }) => {
    // Nobody types the first two words of an organization's name. They type
    // the two they remember.
    await withList(page);
    await page.goto('/membership/');

    await page.locator('#nonprofit-search').fill('trust library');

    await expect(page.locator('#nonprofit-results li')).toContainText('POUDRE RIVER LIBRARY TRUST');
  });

  test('punctuation you would type does not stop a match', async ({ page }) => {
    // The IRS file has no apostrophes. People do.
    await withList(page);
    await page.goto('/membership/');

    await page.locator('#nonprofit-search').fill("st. mary's");

    await expect(page.locator('#nonprofit-results li')).toContainText('ST MARYS COMMUNITY KITCHEN');
  });

  test('choosing one hands over the EIN, which is the point', async ({ page }) => {
    await withList(page);
    await page.goto('/membership/');

    await page.locator('#nonprofit-search').fill('museum');
    await page.locator('#nonprofit-results button').first().click();

    await expect(page.locator('#nonprofit-chosen')).toBeVisible();
    await expect(page.locator('#nonprofit-ein')).toHaveText('841112223');

    const href = await page.locator('#nonprofit-email').getAttribute('href');
    expect(href).toMatch(/^mailto:/);
    expect(decodeURIComponent(href)).toContain('841112223');
    expect(decodeURIComponent(href)).toContain('FORT COLLINS MUSEUM OF DISCOVERY');
  });

  test('no match is not a refusal', async ({ page }) => {
    // The list is Larimer County 501(c)(3)s. A new organization, a chapter, or
    // one under a fiscal sponsor is legitimately absent, and being told "no"
    // would be the lookup doing harm.
    await withList(page);
    await page.goto('/membership/');

    await page.locator('#nonprofit-search').fill('an organization that is not there');

    await expect(page.locator('#nonprofit-status')).toContainText("aren't on the IRS list");
    await expect(page.locator('#nonprofit-results li')).toHaveCount(0);
  });

  test('a way through is always visible, not something you reach by failing', async ({ page }) => {
    await page.goto('/membership/');

    // Present before anybody has typed anything.
    const out = page.locator('a[href="/contact/"]', { hasText: 'Tell us who you are' });
    await expect(out).toBeVisible();
  });

  test('the list failing to load does not strand anybody', async ({ page }) => {
    await withList(page, { status: 500 });
    await page.goto('/membership/');

    await page.locator('#nonprofit-search').fill('poudre');

    await expect(page.locator('#nonprofit-status')).toContainText('Get in touch');
    await expect(page.locator('a[href="/contact/"]', { hasText: 'Tell us who you are' })).toBeVisible();
  });

  test('with no JavaScript the search box is not offered at all', async ({ browser }) => {
    // A search box that does nothing when typed into is worse than no search
    // box. The contact route is plain HTML and survives.
    const context = await browser.newContext({ javaScriptEnabled: false });
    const page = await context.newPage();
    await page.goto('/membership/');

    await expect(page.locator('#nonprofit-search')).toBeHidden();
    await expect(page.locator('a[href="/contact/"]', { hasText: 'Tell us who you are' })).toBeVisible();

    await context.close();
  });
});

test.describe('the synced list', () => {
  test('is real, and shaped the way the page expects', async ({ page }) => {
    // Against the committed file rather than a stub: the sync script and this
    // page agree on a format, and nothing else would notice them diverging.
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
