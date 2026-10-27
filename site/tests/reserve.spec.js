// /reserve/: spaces and equipment side by side on a wide screen, nothing hidden; tabs on a phone.

const { test, expect } = require('@playwright/test');

const wide = (page) => page.viewportSize().width >= 896;

test('both halves show at once on a wide screen, and are tabs on a phone', async ({ page }) => {
  await page.goto('/reserve/');
  if (wide(page)) {
    await expect(page.locator('.half[data-half="spaces"]')).toBeVisible();
    await expect(page.locator('.half[data-half="equipment"]')).toBeVisible();
    await expect(page.locator('.halves-tabs')).toBeHidden();
    const spaces = await page.locator('.half[data-half="spaces"]').boundingBox();
    const equipment = await page.locator('.half[data-half="equipment"]').boundingBox();
    expect(equipment.x).toBeGreaterThan(spaces.x + spaces.width - 1);
  } else {
    await expect(page.locator('.halves-tabs')).toBeVisible();
    await expect(page.locator('.half[data-half="equipment"]')).toBeVisible();
    await expect(page.locator('.half[data-half="spaces"]')).toBeHidden();
    await page.getByRole('tab', { name: 'Spaces' }).click();
    await expect(page.locator('.half[data-half="spaces"]')).toBeVisible();
    await expect(page.locator('.half[data-half="equipment"]')).toBeHidden();
    await expect(page).toHaveURL(/#spaces$/);
  }
});

test('the address can open a half', async ({ page }) => {
  await page.goto('/reserve/#spaces');
  await expect(page.locator('.half[data-half="spaces"]')).toBeVisible();
  if (!wide(page)) await expect(page.getByRole('tab', { name: 'Spaces' })).toHaveAttribute('aria-selected', 'true');
});

test('without JavaScript nothing is hidden', async ({ browser }) => {
  const context = await browser.newContext({ javaScriptEnabled: false, viewport: { width: 390, height: 844 } });
  const page = await context.newPage();
  await page.goto('/reserve/');
  await expect(page.locator('.half[data-half="spaces"]')).toBeVisible();
  await expect(page.locator('.half[data-half="equipment"]')).toBeVisible();
  await expect(page.locator('.halves-tabs')).toBeHidden();
  await context.close();
});
