import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  testMatch: ["research-home.home.ts", "recommendation-memo.home.ts", "workspace-redesign.home.ts", "discovery-workspace.home.ts"],
  fullyParallel: false,
  workers: 1,
  timeout: 30_000,
  expect: { timeout: 10_000 },
  reporter: [["list"], ["html", { outputFolder: "playwright-home-report", open: "never" }]],
  outputDir: "test-results/home",
  use: { baseURL: "http://127.0.0.1:13004", trace: "retain-on-failure", screenshot: "only-on-failure" },
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"], viewport: { width: 1440, height: 1000 } } },
    { name: "mobile", use: { ...devices["Desktop Chrome"], viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true } },
  ],
  webServer: [
    { command: "node tests/e2e/research-home-api.mjs", url: "http://127.0.0.1:18765/__health", reuseExistingServer: false },
    {
      command: "npm run start -- -p 13004", url: "http://127.0.0.1:13004", reuseExistingServer: false,
      env: { STOCKANALYSIS_FRONTEND_API_BASE_URL: "http://127.0.0.1:18765", STOCKANALYSIS_FRONTEND_API_READ_TOKEN: "ci-only-read-token", NEXT_TELEMETRY_DISABLED: "1" },
    },
  ],
});
