import { test, expect } from '@playwright/test';

const routePaths = [
  '/', '/projects', '/projects/new', '/flags', '/scanner', '/dependencies',
  '/chaos', '/monitor', '/guardian', '/incidents', '/cleanup', '/integrations',
  '/policies', '/settings', '/organizations/new', '/login', '/register',
];

test('registers, persists, navigates, validates integrations, and runs synthetic Staging workflow', async ({ page }) => {
  test.setTimeout(90000);
  const pageErrors: string[] = [];
  const failedRequests: string[] = [];
  const serverErrors: string[] = [];
  page.on('pageerror', error => pageErrors.push(error.message));
  page.on('requestfailed', request => failedRequests.push(`${request.method()} ${request.url()}: ${request.failure()?.errorText}`));
  page.on('response', response => {
    if (response.status() >= 500) serverErrors.push(`${response.status()} ${response.url()}`);
  });

  const unique = `${Date.now()}-${Math.random().toString(16).slice(2, 8)}`;
  const email = `flagforge.qa.${unique}@example.com`;
  const password = `FfQa!${unique.slice(-8)}bZ#`;
  await page.goto('/register');
  await page.getByPlaceholder('Alex Rivera').fill('FlagForge QA Runner');
  const emailField = page.getByPlaceholder('alex@company.com');
  await emailField.fill('not-an-email');
  await page.getByPlaceholder('At least 8 characters').fill('short');
  await page.getByRole('button', { name: 'Get Started' }).click();
  await expect(page).toHaveURL(/\/register$/);
  expect(await emailField.evaluate((element: HTMLInputElement) => element.validity.valid)).toBe(false);

  await page.getByPlaceholder('Alex Rivera').fill('FlagForge QA Runner');
  await emailField.fill(email);
  await page.getByPlaceholder('At least 8 characters').fill(password);
  await page.getByRole('button', { name: 'Get Started' }).click();
  await expect(page).toHaveURL(/\/organizations\/new$/);
  await page.getByPlaceholder('Acme Global Inc').fill(`FlagForge QA ${unique}`);
  await page.getByRole('button', { name: 'Create Organization' }).click();
  await expect(page).toHaveURL(/\/projects$/);
  await page.reload();
  await expect(page.getByText(`FlagForge QA ${unique}`, { exact: true }).first()).toBeVisible();

  await page.goto('/projects/new');
  await page.getByPlaceholder('e.g. Core Commerce Storefront').fill(`QA Project ${unique}`);
  await page.getByPlaceholder('e.g. core-commerce-storefront').fill(`qa-project-${unique.replace(/[^a-z0-9-]/gi, '-')}`);
  await page.getByRole('button', { name: 'Create Project' }).click();
  await expect(page).toHaveURL(/\/projects\/[0-9a-f-]{36}$/i, { timeout: 15000 });
  await expect(page.getByRole('heading', { name: new RegExp(`QA Project ${unique}`) })).toBeVisible();
  await expect(page.getByText('Production', { exact: true })).toBeVisible();
  await page.getByPlaceholder('e.g. QA Sandbox').fill(`Isolated QA ${unique}`);
  await page.getByRole('button', { name: 'Add Environment' }).click();
  await expect(page.getByText(`Isolated QA ${unique}`, { exact: true })).toBeVisible();

  // Seed content is clearly labelled synthetic and confined to this disposable QA organization.
  await page.goto('/');
  await page.waitForLoadState('networkidle');
  await expect(page.getByRole('button', { name: /sign out/i })).toBeVisible();
  // Allow the production App Router client handlers to hydrate before interaction.
  await page.waitForTimeout(500);
  const seedResponse = page.waitForResponse(response =>
    response.url().includes('/seed-demo') && response.request().method() === 'POST'
  );
  await page.getByRole('button', { name: 'Seed Synthetic Demo Data' }).click();
  const seeded = await seedResponse;
  expect(seeded.status()).toBe(200);
  await expect(page.getByText(/Synthetic demo fixtures seeded locally/i)).toBeVisible();

  for (const route of routePaths) {
    await page.goto(route);
    await expect(page.locator('main')).toBeVisible();
    await expect(page.locator('main').getByText(/Loading[^.]*…/)).toHaveCount(0, { timeout: 10000 }).catch(() => {});
    const mainText = (await page.locator('main').innerText()).trim();
    expect(mainText.length, `route rendered empty main: ${route}`).toBeGreaterThan(20);
    await page.screenshot({ path: `test-results/routes-${route.replace(/[^a-z0-9]+/gi, '-') || 'home'}.png`, fullPage: true });
  }

  // The route sweep intentionally visits public auth pages, so restore the
  // authenticated QA session before exercising protected workflows again.
  await page.goto('/login');
  await page.getByPlaceholder('alex@company.com').fill(email);
  await page.getByPlaceholder('••••••••••••').fill(password);
  await page.getByRole('button', { name: 'Continue' }).click();
  await expect(page).toHaveURL(/\/projects$/);

  await page.goto('/chaos');
  await page.getByRole('button', { name: 'Run Synthetic Test' }).first().click();
  await expect(page.getByText(/Synthetic staging simulation completed/i)).toBeVisible();
  await expect(page.getByText(/no remote flag changed/i)).toBeVisible();

  await page.goto('/flags');
  const search = page.getByPlaceholder('Search flags by key, name, or description (press Enter)...');
  await search.fill(`no-such-qa-flag-${unique}`);
  await search.press('Enter');
  await expect(page.getByText(new RegExp(`No flags matched "no-such-qa-flag-${unique}"`))).toBeVisible();
  await page.locator('select').selectOption({ label: `QA Project ${unique}` });
  await expect(page.locator('select')).not.toHaveValue('');

  await page.goto('/scanner');
  const scannerSearch = page.getByPlaceholder('Search by flag key or file...');
  await scannerSearch.fill(`no-such-reference-${unique}`);
  await expect(page.getByText('No code references discovered yet. Click "Run AST Scan" to analyze your repository.')).toBeVisible();
  await scannerSearch.fill('checkout_v2_redesign');
  await expect(page.getByText('checkout_v2_redesign', { exact: true }).first()).toBeVisible();

  await page.goto('/dependencies');
  await page.getByRole('button', { name: 'Refresh Map' }).click();
  await expect(page.locator('main')).toContainText(/Topology Graph/i);

  await page.goto('/monitor');
  await page.locator('select').selectOption({ label: 'Staging' });
  await page.getByRole('button', { name: 'Refresh Metrics' }).click();
  await expect(page.locator('main')).toContainText('No telemetry received');

  await page.goto('/guardian');
  await expect(page.locator('main')).toContainText('MANUAL_APPROVAL_REQUIRED');
  await expect(page.locator('main')).toContainText('Rollback unavailable');
  await expect(page.locator('main')).toContainText('No remote flag change will be attempted');

  await page.goto('/incidents');
  await expect(page.locator('main')).toContainText('No active incidents recorded');
  await expect(page.locator('main')).toContainText('No rollback actions executed');

  await page.goto('/cleanup');
  await page.getByRole('button', { name: 'Load actual source for review' }).first().click();
  await expect(page.locator('main')).toContainText('Connect GitHub and select an authorized repository');
  await expect(page.locator('main')).toContainText('No repository diff prepared');

  await page.goto('/integrations');
  await expect(page.getByText(/GitHub/i).first()).toBeVisible();
  await expect(page.getByText(/not configured|connect GitHub/i).first()).toBeVisible();
  await page.getByRole('button', { name: 'Add Flagsmith Connection' }).click();
  await page.getByRole('button', { name: 'Test Connection' }).click();
  await expect(page.getByText('Please provide API URL and Management Token to test.')).toBeVisible();
  await page.getByRole('button', { name: 'Cancel' }).click();
  await page.screenshot({ path: 'test-results/integrations-desktop.png', fullPage: true });

  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/integrations');
  await expect(page.locator('main')).toBeVisible();
  const dimensions = await page.evaluate(() => ({ viewport: document.documentElement.clientWidth, page: document.documentElement.scrollWidth }));
  expect(dimensions.page, `mobile horizontal overflow: ${JSON.stringify(dimensions)}`).toBeLessThanOrEqual(dimensions.viewport + 1);
  await page.screenshot({ path: 'test-results/integrations-mobile-390.png', fullPage: true });

  await page.getByRole('button', { name: /sign out/i }).click();
  await expect(page).toHaveURL(/\/login$/);
  await page.getByPlaceholder('alex@company.com').fill(email);
  await page.getByPlaceholder('••••••••••••').fill(password);
  await page.getByRole('button', { name: 'Continue' }).click();
  await expect(page).toHaveURL(/\/projects$/);
  await expect(page.getByText(`FlagForge QA ${unique}`, { exact: true }).first()).toBeVisible();

  expect(pageErrors, 'uncaught JavaScript errors').toEqual([]);
  expect(serverErrors, 'HTTP 5xx responses').toEqual([]);
  const unexpectedFailedRequests = failedRequests.filter(request => !request.includes('ERR_ABORTED'));
  expect(unexpectedFailedRequests, 'unexpected failed network requests').toEqual([]);
  // Route-change cancellations are expected; unexpected failed requests fail the suite.
  test.info().annotations.push({ type: 'failed requests', description: JSON.stringify(failedRequests) });
});
