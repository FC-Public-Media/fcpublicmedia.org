// Every spec's `test`: Playwright's, plus one guard. No test may reach the real site-worker. Its quota
// (KV writes above all: every /challenge is one) is shared with the public, and a test run that reaches
// it spent half a day's allowance on 2026-10-27. A request to it is blocked and fails the test.
// Tests that want a worker plant a fake one (brokerUrl, below; or a form's data-worker).

const base = require('@playwright/test');

const REAL_WORKER = [/^https:\/\/site-worker\.[^/]+\.workers\.dev\//, /^https:\/\/cloud\.fcpublicmedia\.org\//];

const test = base.test.extend({
  noRealWorker: [async ({ context }, use) => {
    const reached = [];
    await context.route((url) => REAL_WORKER.some((pattern) => pattern.test(url.href)), async (route) => {
      reached.push(`${route.request().method()} ${route.request().url()}`);
      await route.abort('blockedbyclient');
    });
    await use();
    base.expect(reached, 'a test reached the real site-worker; plant a fake one').toEqual([]);
  }, { auto: true }],
});

/** A page's HTML with its baked-in brokerUrl swapped for `broker` ("" for none). */
const withBroker = (html, broker = '') => html.replace(/"brokerUrl": "[^"]*"/, `"brokerUrl": ${JSON.stringify(broker)}`);

/** The page at `glob` with its brokerUrl swapped for `broker` ("" for none). */
async function brokerUrl(page, glob, broker) {
  await page.route(glob, async (route) => {
    const response = await route.fetch();
    await route.fulfill({ response, body: withBroker(await response.text(), broker) });
  });
}

module.exports = { test, expect: base.expect, brokerUrl, withBroker };
