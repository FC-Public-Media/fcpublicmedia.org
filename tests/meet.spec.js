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

/**
 * Class sessions as the build sees them, with when they start.
 *
 * The start time is read as well as the title, and that is the whole point of
 * this helper. The page shows only what has not happened yet — deliberately,
 * and there is a test below for it — so a version of this that returned every
 * title asserted that history is on display, and passed only until the first
 * session went by. It did exactly that: "Podcasting 101" was on a Tuesday and
 * this went red on the Wednesday, in CI, on a change about colours.
 */
function classSessions() {
  const raw = fs.readFileSync(path.join(REPO, '_data', 'classes.yml'), 'utf8');
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

test.describe('community', () => {
  test('shows what is coming up', async ({ page }) => {
    await page.goto('/meet/');

    const items = page.locator('.rows-events li');
    expect(await items.count(), 'nothing in the merged list').toBeGreaterThan(0);
  });

  test('pulls class sessions in without them being re-entered', async ({ page }) => {
    // The merge exists so a class is listed here by virtue of being a class.
    // If this breaks, the fix people reach for is to copy the session into
    // community.yml, and then the two quietly disagree forever.
    await page.goto('/meet/');

    const sessions = upcoming();

    // Not a vacuous pass when everything has gone by. A calendar with no
    // future classes in it is a real thing to know about — it means the sync
    // has stopped or nobody has scheduled anything — and a test that went
    // quietly green on it would be hiding exactly that.
    expect(
      sessions.length,
      'every session in classes.yml is in the past — the calendar needs refreshing'
    ).toBeGreaterThan(0);

    const listed = await page.locator('.rows-events').innerText();
    for (const { title } of sessions) {
      expect(listed, `${title} is in classes.yml but not on /meet/`).toContain(title);
    }
  });

  test('is in chronological order', async ({ page }) => {
    // The sort key is epoch seconds rather than the ISO string, because two
    // events either side of a DST change carry different offsets.
    await page.goto('/meet/');

    const stamps = await page.$$eval('.rows-events time', (ts) =>
      ts.map((t) => new Date(t.getAttribute('datetime')).getTime())
    );

    expect(stamps.length).toBeGreaterThan(0);
    expect(stamps, 'events are out of order').toEqual([...stamps].sort((a, b) => a - b));
  });

  test('shows nothing that has already happened', async ({ page }) => {
    // A calendar full of last spring is worse than an empty one — it reads as
    // abandoned rather than quiet.
    await page.goto('/meet/');

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
    await page.goto('/meet/');

    await expect(page.locator('.rows-events')).toContainText('Class');
  });

  test('every listed date is real', async ({ page }) => {
    // A malformed offset in a data file renders as "Invalid Date" rather than
    // failing the build, which is exactly the kind of thing nobody notices.
    await page.goto('/meet/');

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
    // The chat platform is unsettled — Slack today, possibly Teams. Naming one
    // without a working link invites "where is it, then?", which is the one
    // question this section exists to prevent. Entries with no URL are meant
    // to be skipped entirely, and this is what proves it.
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
    // The shipped state, and the one that has to do the work: nobody has sent
    // a feed yet, so the section's whole job is to ask for one. An empty
    // heading with nothing under it would ask for nothing.
    await page.goto('/meet/');

    const section = page.locator('main');
    await expect(section).toContainText('Made by members');
    await expect(section).toContainText('feed');
  });

  test('every member item would be escaped and safely linked', async ({ page }) => {
    // Feed content is third-party. If items are present, none of them may
    // introduce a script, an event handler, or a non-http link — the two
    // halves of the defence are stripping in sync-feeds.py and | escape in
    // the template, and this checks the result rather than either half.
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
    const raw = fs.readFileSync(path.join(REPO, '_data', 'member_programs.json'), 'utf8');
    return JSON.parse(raw).items || [];
  }

  test('nothing under "Made by members" is dated in the future', async ({ page }) => {
    // A member site marks a program `scheduled` with a future drop date, and
    // that date rides into the feed as its pubDate. Before the split, those
    // arrived here announcing something as published on the day it was still
    // being finished.
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
    // A feed entry carries where the finished file lives. That is for us — a
    // page announcing something is coming has no business publishing the path
    // to an unreleased master.
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
    // Plenty of feeds are sloppy about dates, and guessing that undated means
    // upcoming would put a whole back catalogue under "coming up".
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
    // The page should not just describe a community; it should be possible to
    // act from it. Membership, classes, and the open board meeting are the
    // three that cost a newcomer the least.
    await page.goto('/meet/');

    for (const href of ['/membership/', '/classes/', '#the-board']) {
      await expect(
        page.locator(`main a[href="${href}"]`).first(),
        `no route to ${href}`
      ).toBeVisible();
    }
  });
});
