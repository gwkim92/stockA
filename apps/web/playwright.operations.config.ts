import { defineConfig, devices } from '@playwright/test';
export default defineConfig({
  testDir: './tests/e2e', testMatch: 'research-operations.home.ts', workers: 1,
  timeout: 30_000, reporter: 'list', outputDir: 'test-results/operations',
  use: { baseURL: 'http://127.0.0.1:13012', trace: 'retain-on-failure' },
  projects: [
    { name: 'desktop', use: { ...devices['Desktop Chrome'], viewport: { width: 1440, height: 1000 } } },
    { name: 'mobile', use: { ...devices['Desktop Chrome'], viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true } },
  ],
  webServer: [
    { command: 'node tests/e2e/research-operations-api.mjs', url: 'http://127.0.0.1:18773/__health', reuseExistingServer: false },
    { command: 'npm run start -- -p 13012', url: 'http://127.0.0.1:13012/data-health', reuseExistingServer: false,
      env: { STOCKANALYSIS_FRONTEND_API_BASE_URL: 'http://127.0.0.1:18773', STOCKANALYSIS_FRONTEND_API_READ_TOKEN: 'operations-fixture-only', NEXT_TELEMETRY_DISABLED: '1' } },
  ],
});
