// see docs/inline/site/tests/playwright.config.js.md#1

const { defineConfig, devices } = require('@playwright/test');

const BASE_URL = process.env.BASE_URL;
const LOCAL_PORT = 4567;

module.exports = defineConfig({
  testDir: '.',
  fullyParallel: true,
  // see docs/inline/site/tests/playwright.config.js.md#2
  workers: process.env.CI ? '100%' : undefined,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  // see docs/inline/site/tests/playwright.config.js.md#3
  reporter: process.env.CI
    ? [['github'], ['list'], ['html', { open: 'never' }]]
    : [['list']],

  use: {
    // see docs/inline/site/tests/playwright.config.js.md#4
    baseURL: BASE_URL || `http://localhost:${LOCAL_PORT}`,
    // see docs/inline/site/tests/playwright.config.js.md#5
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    // see docs/inline/site/tests/playwright.config.js.md#6
    video: 'on-first-retry',
  },

  projects: [
    { name: 'desktop', use: { ...devices['Desktop Chrome'] } },
    { name: 'mobile', use: { ...devices['Pixel 5'] } },
  ],

  // Only start a server when testing locally.
  webServer: BASE_URL
    ? undefined
    : {
        // see docs/inline/site/tests/playwright.config.js.md#7
        command: `python3 -m http.server ${LOCAL_PORT} --directory ../_site`,
        url: `http://localhost:${LOCAL_PORT}/`,
        reuseExistingServer: !process.env.CI,
        timeout: 30_000,
      },
});
