// see docs/inline/site/tests/meet.spec.js.md#1

const { test, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');

// `site/tests/` is inside the Jekyll source, so one level up is the site.
const SITE_DIR = path.resolve(__dirname, '..');

// see docs/inline/site/tests/meet.spec.js.md#2
function classSessions() {
  const raw = fs.readFileSync(path.join(SITE_DIR, '_data', 'classes.yml'), 'utf8');
  const sessions = [];

  for (const block of raw.split(/^\s+- (?=title:)/m).slice(1)) {
    const title = block.match(/^title:\s*(.+)$/m);
    const starts = block.match(/^\s*starts:\s*(\S+)/m);
    if (title && starts) {
      sessions.push({
        title: title[1].trim().replace(/^["']|["']$/g, ''),
        starts: new Date(starts[1]),
      });
    }
  }
  return sessions;
}

/** The ones the page is actually claiming to show. */
const upcoming = () => classSessions().filter((s) => s.starts.getTime() > Date.now());

// see docs/inline/site/tests/meet.spec.js.md#3
const notice = (message) => test.info().annotations.push({ type: 'stale-content', description: message });

test.describe('the calendar on /meet/', () => {
  test('shows what is coming up, or says there is nothing', async ({ page }) => {
    await page.goto('/meet/');

    const items = await page.locator('.rows-events li').count();
    if (items > 0) return;

    notice('no upcoming events — classes.yml, governance.yml and community.yml are all in the past');

    // see docs/inline/site/tests/meet.spec.js.md#4
    await expect(page.locator('main')).toContainText('Nothing on the calendar right now');
    await expect(page.locator('.rows-events')).toHaveCount(0);
  });

  test('pulls class sessions in without them being re-entered', async ({ page }) => {
    // see docs/inline/site/tests/meet.spec.js.md#5
    await page.goto('/meet/');

    const sessions = upcoming();
    if (sessions.length === 0) {
      notice('every session in classes.yml is in the past — nothing to check the merge against');
      return;
    }

    const listed = await page.locator('.rows-events').innerText();
    for (const { title } of sessions) {
      expect(listed, `${title} is in classes.yml but not on /meet/`).toContain(title);
    }
  });

  test('is in chronological order', async ({ page }) => {
    // see docs/inline/site/tests/meet.spec.js.md#6
    await page.goto('/meet/');

    const stamps = await page.$$eval('.rows-events time', (ts) =>
      ts.map((t) => new Date(t.getAttribute('datetime')).getTime())
    );

    expect(stamps, 'events are out of order').toEqual([...stamps].sort((a, b) => a - b));
  });

  test('shows nothing that has already happened', async ({ page }) => {
    // see docs/inline/site/tests/meet.spec.js.md#7
    await page.goto('/meet/');

    const stamps = await page.$$eval('.rows-events time', (ts) =>
      ts.map((t) => new Date(t.getAttribute('datetime')).getTime())
    );

    for (const stamp of stamps) {
      expect(stamp, 'a past event is still listed').toBeGreaterThan(Date.now() - 86400000);
    }
  });

  test('says what kind of thing each entry is', async ({ page }) => {
    // see docs/inline/site/tests/meet.spec.js.md#8
    await page.goto('/meet/');

    if (upcoming().length === 0) {
      notice('no upcoming classes — cannot check that rows are labelled');
      return;
    }
    await expect(page.locator('.rows-events')).toContainText('Class');
  });

  test('every listed date is real', async ({ page }) => {
    // see docs/inline/site/tests/meet.spec.js.md#9
    await page.goto('/meet/');

    if ((await page.locator('.rows-events').count()) === 0) return;

    const text = await page.locator('.rows-events').innerText();
    expect(text).not.toContain('Invalid');
    expect(text).not.toContain('NaN');
  });
});

test.describe('community channels', () => {
  test('lists somewhere to go, and skips what has no link', async ({ page }) => {
    // Slack has no invite URL yet, so it must not render as a dead entry.
    await page.goto('/meet/');

    const links = await page.$$eval('.rows-connect a[href]', (as) =>
      as.map((a) => a.getAttribute('href'))
    );

    expect(links.length, 'no channels linked').toBeGreaterThan(0);
    for (const href of links) {
      expect(href, 'a channel rendered without a real link').not.toBe('');
    }
  });

  test('does not name a chat platform it cannot link to', async ({ page }) => {
    // see docs/inline/site/tests/meet.spec.js.md#10
    await page.goto('/meet/');

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

test.describe('member programs', () => {
  test('invites feeds even with none configured', async ({ page }) => {
    // see docs/inline/site/tests/meet.spec.js.md#11
    await page.goto('/meet/');

    const section = page.locator('main');
    await expect(section).toContainText('Made by members');
    await expect(section).toContainText('feed');
  });

  test('every member item would be escaped and safely linked', async ({ page }) => {
    // see docs/inline/site/tests/meet.spec.js.md#12
    await page.goto('/meet/');

    const items = page.locator('.rows-feed li');
    if ((await items.count()) === 0) return;

    const html = await page.locator('main').innerHTML();
    expect(html).not.toMatch(/<\s*script/i);
    expect(html).not.toMatch(/\son\w+\s*=/i);

    const hrefs = await page.$$eval('main a[href]', (as) =>
      as.map((a) => a.getAttribute('href'))
    );
    for (const href of hrefs) {
      expect(href, `${href} is not a safe link`).toMatch(/^(https?:\/\/|\/|mailto:|tel:|#)/);
    }
  });
});

test.describe('member submissions', () => {
  /** The data the page was built from. */
  function programs() {
    const raw = fs.readFileSync(path.join(SITE_DIR, '_data', 'member_programs.json'), 'utf8');
    return JSON.parse(raw).items || [];
  }

  test('nothing under "Made by members" is dated in the future', async ({ page }) => {
    // see docs/inline/site/tests/meet.spec.js.md#13
    await page.goto('/meet/');

    const heading = page.locator('h2', { hasText: 'Made by members' });
    if ((await heading.count()) === 0) return;

    const dates = await page.$$eval('h2', (hs) => {
      const made = hs.find((h) => h.textContent.includes('Made by members'));
      if (!made) return [];
      const out = [];
      for (let el = made.nextElementSibling; el && el.tagName !== 'H2'; el = el.nextElementSibling) {
        el.querySelectorAll('time[datetime]').forEach((t) => out.push(t.getAttribute('datetime')));
      }
      return out;
    });

    for (const when of dates) {
      expect(new Date(when).getTime(), `${when} has not happened yet`)
        .toBeLessThanOrEqual(Date.now());
    }
  });

  test('the artifact pointer never reaches the page', async ({ page }) => {
    // see docs/inline/site/tests/meet.spec.js.md#14
    await page.goto('/meet/');

    const html = await page.content();
    const pointers = programs()
      .map((item) => item.enclosure && item.enclosure.url)
      .filter(Boolean);

    for (const pointer of pointers) {
      expect(html, `${pointer} was rendered onto the page`).not.toContain(pointer);
    }
  });

  test('an undated item is treated as published, not as forthcoming', async ({ page }) => {
    // see docs/inline/site/tests/meet.spec.js.md#15
    await page.goto('/meet/');

    const undated = programs().filter((item) => !item.published);
    if (!undated.length) return;

    const coming = page.locator('h2', { hasText: 'Coming up from members' });
    if ((await coming.count()) === 0) return;

    const comingText = await page.$$eval('h2', (hs) => {
      const head = hs.find((h) => h.textContent.includes('Coming up from members'));
      if (!head) return '';
      let text = '';
      for (let el = head.nextElementSibling; el && el.tagName !== 'H2'; el = el.nextElementSibling) {
        text += el.textContent;
      }
      return text;
    });

    for (const item of undated) {
      expect(comingText, `undated "${item.title}" was listed as coming up`)
        .not.toContain(item.title);
    }
  });
});

test.describe('community wayfinding', () => {
  test('the homepage band leads here', async ({ page }) => {
    await page.goto('/');

    await expect(page.locator('main a[href="/meet/"]').first()).toBeVisible();
  });

  test('offers concrete ways to take part', async ({ page }) => {
    // see docs/inline/site/tests/meet.spec.js.md#16
    await page.goto('/meet/');

    for (const href of ['/membership/', '/classes/', '#the-board']) {
      await expect(
        page.locator(`main a[href="${href}"]`).first(),
        `no route to ${href}`
      ).toBeVisible();
    }
  });
});
