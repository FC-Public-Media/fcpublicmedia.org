// Playwright configuration for the smoke tests.
//
// Two ways to run:
//
//   npm test                 build _site first, serve it locally, test that
//   npm run test:live        test the deployed site instead
//
// The local server is Python's http.server because it needs no dependency and
// serves directory index files, which is all Jekyll output requires. It does
// not do custom 404 pages or redirects — those are host behavior, so the
// tests that cover them only run against a real deployment.

const { defineConfig, devices } = require('@playwright/test');

const BASE_URL = process.env.BASE_URL;
const LOCAL_PORT = 4567;

module.exports = defineConfig({
  testDir: '.',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  // The html reporter is what the failure artifact in CI is made of — without
  // it the upload step finds nothing to upload, which is the situation you
  // least want when a test only fails on the runner.
  reporter: process.env.CI
    ? [['github'], ['list'], ['html', { open: 'never' }]]
    : [['list']],

  use: {
    baseURL: BASE_URL || `http://127.0.0.1:${LOCAL_PORT}`,
    // On failure, keep enough to diagnose without re-running — which is the
    // whole point when the thing that broke only breaks on a phone.
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },

  projects: [
    { name: 'desktop', use: { ...devices['Desktop Chrome'] } },
    { name: 'mobile', use: { ...devices['Pixel 5'] } },
  ],

  // Only start a server when testing locally.
  webServer: BASE_URL
    ? undefined
    : {
        command: `python3 -m http.server ${LOCAL_PORT} --bind 127.0.0.1 --directory ../_site`,
        url: `http://127.0.0.1:${LOCAL_PORT}/`,
        reuseExistingServer: !process.env.CI,
        timeout: 30_000,
      },
});
