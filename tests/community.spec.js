// The community page.
//
// Its job is to answer "when can I turn up" and "where is everyone" without
// making a visitor know which data file a thing lives in. Three sources merge
// into one list, so the tests below are mostly about that merge behaving —
// chronological, forward-looking, and not lying when it is empty.

const { test, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');

const REPO = path.resolve(__dirname, '..');

/** Class sessions as the build sees them, for comparing against the page. */
function classSessions() {
  const raw = fs.readFileSync(path.join(REPO, '_data', 'classes.yml'), 'utf8');
  return [...raw.matchAll(/^\s+-?\s*title:\s*(.+)$/gm)].map((m) =>
    m[1].trim().replace(/^["']|["']$/g, '')
  );
}

test.describe('community', () => {
  test('shows what is coming up', async ({ page }) => {
    await page.goto('/community/');

    const items = page.locator('.rows-events li');
    expect(await items.count(), 'nothing in the merged list').toBeGreaterThan(0);
  });

  test('pulls class sessions in without them being re-entered', async ({ page }) => {
    // The merge exists so a class is listed here by virtue of being a class.
    // If this breaks, the fix people reach for is to copy the session into
    // community.yml, and then the two quietly disagree forever.
    await page.goto('/community/');

    const listed = await page.locator('.rows-events').innerText();
    for (const title of classSessions()) {
      expect(listed, `${title} is in classes.yml but not on /community/`).toContain(title);
    }
  });

  test('is in chronological order', async ({ page }) => {
    // The sort key is epoch seconds rather than the ISO string, because two
    // events either side of a DST change carry different offsets.
    await page.goto('/community/');

    const stamps = await page.$$eval('.rows-events time', (ts) =>
      ts.map((t) => new Date(t.getAttribute('datetime')).getTime())
    );

    expect(stamps.length).toBeGreaterThan(0);
    expect(stamps, 'events are out of order').toEqual([...stamps].sort((a, b) => a - b));
  });

  test('shows nothing that has already happened', async ({ page }) => {
    // A calendar full of last spring is worse than an empty one — it reads as
    // abandoned rather than quiet.
    await page.goto('/community/');

    const stamps = await page.$$eval('.rows-events time', (ts) =>
      ts.map((t) => new Date(t.getAttribute('datetime')).getTime())
    );

    for (const stamp of stamps) {
      expect(stamp, 'a past event is still listed').toBeGreaterThan(Date.now() - 86400000);
    }
  });

  test('says what kind of thing each entry is', async ({ page }) => {
    // Merging sources means losing the context a single-purpose page would
    // have given for free, so each row has to carry it.
    await page.goto('/community/');

    await expect(page.locator('.rows-events')).toContainText('Class');
  });

  test('every listed date is real', async ({ page }) => {
    // A malformed offset in a data file renders as "Invalid Date" rather than
    // failing the build, which is exactly the kind of thing nobody notices.
    await page.goto('/community/');

    const text = await page.locator('.rows-events').innerText();
    expect(text).not.toContain('Invalid');
    expect(text).not.toContain('NaN');
  });
});

test.describe('community channels', () => {
  test('lists somewhere to go, and skips what has no link', async ({ page }) => {
    // Slack has no invite URL yet, so it must not render as a dead entry.
    await page.goto('/community/');

    const links = await page.$$eval('.rows-connect a[href]', (as) =>
      as.map((a) => a.getAttribute('href'))
    );

    expect(links.length, 'no channels linked').toBeGreaterThan(0);
    for (const href of links) {
      expect(href, 'a channel rendered without a real link').not.toBe('');
    }
  });

  test('does not name a chat platform it cannot link to', async ({ page }) => {
    // The chat platform is unsettled — Slack today, possibly Teams. Naming one
    // without a working link invites "where is it, then?", which is the one
    // question this section exists to prevent. Entries with no URL are meant
    // to be skipped entirely, and this is what proves it.
    await page.goto('/community/');

    const body = await page.locator('.rows-connect').innerText();
    const linked = await page.$$eval('.rows-connect a', (as) =>
      as.map((a) => a.textContent.trim())
    );

    for (const name of ['Slack', 'Teams', 'Discord']) {
      if (body.includes(name)) {
        expect(linked, `${name} is named but not linked`).toContain(name);
      }
    }
  });
});

test.describe('community wayfinding', () => {
  test('the homepage band leads here', async ({ page }) => {
    await page.goto('/');

    await expect(page.locator('main a[href="/community/"]').first()).toBeVisible();
  });

  test('offers concrete ways to take part', async ({ page }) => {
    // The page should not just describe a community; it should be possible to
    // act from it. Membership, classes, and the open board meeting are the
    // three that cost a newcomer the least.
    await page.goto('/community/');

    for (const href of ['/membership/', '/classes/', '/board/']) {
      await expect(
        page.locator(`main a[href="${href}"]`).first(),
        `no route to ${href}`
      ).toBeVisible();
    }
  });
});
