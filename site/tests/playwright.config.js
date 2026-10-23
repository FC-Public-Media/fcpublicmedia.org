// Playwright config: serves ../_site via http.server, or tests BASE_URL (`npm run test:live`).
// See docs/site.md.

const { defineConfig, devices } = require('@playwright/test');

const BASE_URL = process.env.BASE_URL;
const LOCAL_PORT = 4567;

module.exports = defineConfig({
  testDir: '.',
  fullyParallel: true,
  workers: process.env.CI ? '100%' : undefined,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  // CI's failure artifact is the html report.
  reporter: process.env.CI
    ? [['github'], ['list'], ['html', { open: 'never' }]]
    : [['list']],

  use: {
    // localhost, not 127.0.0.1: WebAuthn rejects an IP literal as an invalid domain.
    baseURL: BASE_URL || `http://localhost:${LOCAL_PORT}`,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    // Not `retain-on-failure`, which records every test; CI's retry is the run worth filming.
    video: 'on-first-retry',
  },

  projects: [
    { name: 'desktop', use: { ...devices['Desktop Chrome'] } },
    { name: 'mobile', use: { ...devices['Pixel 5'] } },
  ],

  webServer: BASE_URL
    ? undefined
    : {
        // All interfaces, so localhost answers whether it resolves to IPv4 or IPv6.
        command: `python3 -m http.server ${LOCAL_PORT} --directory ../_site`,
        url: `http://localhost:${LOCAL_PORT}/`,
        reuseExistingServer: !process.env.CI,
        timeout: 30_000,
      },
});
