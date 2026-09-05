import { defineConfig, devices } from '@playwright/test';
export default defineConfig({
  testDir: './tests/e2e', testMatch: 'company-evidence.home.ts', workers: 1, fullyParallel: false,
  timeout: 30_000, expect: { timeout: 10_000 },
  reporter: [['list'], ['html', { outputFolder: 'playwright-company-report', open: 'never' }]], outputDir: 'test-results/company',
  use: { baseURL: 'http://127.0.0.1:13007', trace: 'retain-on-failure', screenshot: 'only-on-failure' },
  projects: [
    { name: 'desktop', use: { ...devices['Desktop Chrome'], viewport: { width: 1440, height: 1000 } } },
    { name: 'mobile', use: { ...devices['Desktop Chrome'], viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true } },
  ],
  webServer: [
    { command: 'node tests/e2e/company-evidence-api.mjs', url: 'http://127.0.0.1:18768/__health', reuseExistingServer: false },
    { command: 'npm run start -- -p 13007', url: 'http://127.0.0.1:13007/stocks/AAPL', reuseExistingServer: false, env: { STOCKANALYSIS_FRONTEND_API_BASE_URL: 'http://127.0.0.1:18768', STOCKANALYSIS_FRONTEND_API_READ_TOKEN: 'company-fixture-only', NEXT_TELEMETRY_DISABLED: '1' } },
  ],
});
