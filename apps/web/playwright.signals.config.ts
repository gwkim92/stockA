import { defineConfig, devices } from '@playwright/test';
export default defineConfig({
  testDir: './tests/e2e', testMatch: 'news-theme.home.ts', workers: 1, fullyParallel: false,
  timeout: 30_000, expect: { timeout: 10_000 },
  reporter: [['list'], ['html', { outputFolder: 'playwright-signals-report', open: 'never' }]], outputDir: 'test-results/signals',
  use: { baseURL: 'http://127.0.0.1:13008', trace: 'retain-on-failure', screenshot: 'only-on-failure' },
  projects: [
    { name: 'desktop', use: { ...devices['Desktop Chrome'], viewport: { width: 1440, height: 1000 } } },
    { name: 'mobile', use: { ...devices['Desktop Chrome'], viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true } },
  ],
  webServer: [
    { command: 'node tests/e2e/news-theme-api.mjs', url: 'http://127.0.0.1:18769/__health', reuseExistingServer: false },
    { command: 'npm run start -- -p 13008', url: 'http://127.0.0.1:13008/events', reuseExistingServer: false, env: { STOCKANALYSIS_FRONTEND_API_BASE_URL: 'http://127.0.0.1:18769', STOCKANALYSIS_FRONTEND_API_READ_TOKEN: 'news-theme-fixture', NEXT_TELEMETRY_DISABLED: '1' } },
  ],
});
