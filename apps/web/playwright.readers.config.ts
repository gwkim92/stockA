import { defineConfig, devices } from "@playwright/test";
export default defineConfig({
  testDir: "./tests/e2e", testMatch: "research-readers.home.ts", workers: 1, fullyParallel: false,
  timeout: 30_000, expect: { timeout: 10_000 },
  reporter: [["list"], ["html", { outputFolder: "playwright-readers-report", open: "never" }]],
  outputDir: "test-results/readers",
  use: { baseURL: "http://127.0.0.1:13006", trace: "retain-on-failure", screenshot: "only-on-failure" },
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"], viewport: { width: 1440, height: 1000 } } },
    { name: "mobile", use: { ...devices["Desktop Chrome"], viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true } },
  ],
  webServer: [
    { command: "node tests/e2e/readers-api.mjs", url: "http://127.0.0.1:18767/__health", reuseExistingServer: false },
    { command: "npm run start -- -p 13006", url: "http://127.0.0.1:13006/theses/thesis-1", reuseExistingServer: false,
      env: { STOCKANALYSIS_FRONTEND_API_BASE_URL: "http://127.0.0.1:18767", STOCKANALYSIS_FRONTEND_API_READ_TOKEN: "reader-test-only", NEXT_TELEMETRY_DISABLED: "1" } },
  ],
});
