// see docs/inline/site/tests/contrast.spec.js.md#1

const { test, expect } = require('@playwright/test');

/** Relative luminance, straight from the WCAG definition. */
function luminance([r, g, b]) {
  const channel = (c) => {
    const v = c / 255;
    return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4;
  };
  return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b);
}

function ratio(a, b) {
  const [high, low] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (high + 0.05) / (low + 0.05);
}

// see docs/inline/site/tests/contrast.spec.js.md#2
async function sample(page, selector) {
  return page.$$eval(selector, (nodes) =>
    nodes
      .filter((node) => node.textContent.trim() && node.offsetParent !== null)
      .map((node) => {
        // see docs/inline/site/tests/contrast.spec.js.md#3
        const parse = (value) => {
          const parts = (value.match(/[\d.]+/g) || []).map(Number);
          const rgb = value.startsWith("color(") ? parts.slice(0, 3) : parts.slice(0, 3);
          return value.startsWith("color(") ? rgb.map((c) => Math.round(c * 255)) : rgb;
        };

        const style = getComputedStyle(node);
        let behind = null;
        for (let el = node; el; el = el.parentElement) {
          const bg = getComputedStyle(el).backgroundColor;
          const parts = (bg.match(/[\d.]+/g) || []).map(Number);
          const alpha = parts.length > 3 ? parts[3] : 1;
          if (parts.length >= 3 && alpha > 0.5) {
            behind = parse(bg);
            break;
          }
        }

        return {
          text: node.textContent.trim().slice(0, 40),
          colour: parse(style.color),
          background: behind,
          size: parseFloat(style.fontSize),
          weight: Number(style.fontWeight) || 400,
        };
      })
      .filter((s) => s.background)
  );
}

/** WCAG's own threshold: large text is allowed 3:1, everything else 4.5:1. */
const needed = ({ size, weight }) =>
  size >= 24 || (size >= 18.66 && weight >= 700) ? 3 : 4.5;

// see docs/inline/site/tests/contrast.spec.js.md#4
const CHECKED = [
  { path: '/', what: 'the masthead', selector: '.site-head a, .nav-group-label, .wordmark-text span' },
  { path: '/', what: 'the home page', selector: 'h1, h2, p, .lede, .muted, .eyebrow' },
  { path: '/watch/', what: 'listings', selector: 'h2, h3, .show-meta, .muted, .tag' },
  { path: '/membership/', what: 'membership', selector: 'h2, h3, p, .muted, .price' },
  { path: '/meet/', what: 'the calendar', selector: 'h2, .rows li, .muted, .coming' },
];

test.describe('contrast', () => {
  for (const { path, what, selector } of CHECKED) {
    test(`${what} is readable`, async ({ page }) => {
      await page.goto(path);

      const samples = await sample(page, selector);
      expect(samples.length, `nothing matched on ${path}`).toBeGreaterThan(0);

      const failures = samples
        .map((s) => ({ ...s, got: ratio(s.colour, s.background), want: needed(s) }))
        .filter((s) => s.got < s.want)
        .map(
          (s) =>
            `${s.got.toFixed(2)}:1 (needs ${s.want}) — rgb(${s.colour}) on ` +
            `rgb(${s.background}) — "${s.text}"`
        );

      expect(failures, `unreadable text on ${path}:\n${failures.join('\n')}`).toEqual([]);
    });
  }

  test('the navigation is visible, including behind the toggle', async ({ page }) => {
    // see docs/inline/site/tests/contrast.spec.js.md#5
    for (const [path, name] of [['/', 'home'], ['/watch/', 'watch'], ['/membership/', 'membership']]) {
      await page.goto(path);

      // see docs/inline/site/tests/contrast.spec.js.md#6
      const toggle = page.locator('.nav-toggle');
      if (await toggle.isVisible()) {
        await toggle.click();
        await expect(page.locator('.site-nav a').first()).toBeVisible();
      }

      const links = await sample(page, '.site-nav a');
      expect(links.length, `no navigation on ${name}`).toBeGreaterThan(0);

      for (const link of links) {
        const got = ratio(link.colour, link.background);
        expect(
          got,
          `${name}: "${link.text}" is ${got.toFixed(2)}:1 against the masthead`
        ).toBeGreaterThanOrEqual(4.5);
      }
    }
  });
});
