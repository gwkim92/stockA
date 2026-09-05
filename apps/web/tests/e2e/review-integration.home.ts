import { expect, test } from "@playwright/test";

type LoggedRequest = { path: string; query: string; method: string };

test.beforeEach(async ({ request }) => {
  await request.post("http://127.0.0.1:18766/__scenario", { data: { scenario: "healthy" } });
});

test("tab navigation preserves the selected report date", async ({ page, request }) => {
  await page.goto("/portfolio/coverage?date=2025-01-15");
  const tabs = page.getByRole("navigation", { name: "보유와 성과" });
  await tabs.getByRole("link", { name: "판단 성과", exact: true }).click();
  await expect(page).toHaveURL(/\/performance\?date=2025-01-15$/);
  await expect(page.getByLabel("성과 종료 기준일")).toHaveValue("2025-01-15");
  await tabs.getByRole("link", { name: "보유 검토", exact: true }).click();
  await expect(page).toHaveURL(/\/portfolio\/coverage\?date=2025-01-15$/);
  const requests: LoggedRequest[] = await (await request.get("http://127.0.0.1:18766/__requests")).json();
  expect(requests.some(row => row.query.includes("measurementEndDate=2025-01-15"))).toBe(true);
});

test("scrolling and hovering both detail links do not request trading readiness", async ({ page, request }, info) => {
  await page.goto("/portfolio/coverage");
  const detailLinks = page.getByTestId("review-workspace").locator('a[href="/portfolio/coverage/details"]');
  await expect(detailLinks).toHaveCount(2);
  for (const link of await detailLinks.all()) {
    await link.scrollIntoViewIfNeeded();
    if (info.project.name === "desktop") await link.hover();
  }
  // Allow the production router's viewport/hover prefetch queue to settle.
  await page.waitForTimeout(600);
  const requests: LoggedRequest[] = await (await request.get("http://127.0.0.1:18766/__requests")).json();
  expect(requests.some(row => row.path.includes("trading-readiness"))).toBe(false);
});

test("the preserved policy page still renders when deliberately opened", async ({ page, request }) => {
  await request.post("http://127.0.0.1:18766/__scenario", { data: { scenario: "legacy" } });
  const response = await page.goto("/portfolio/coverage/details");
  expect(response?.status()).toBe(200);
  await expect(page.locator("#portfolio-coverage-title")).toBeVisible();
  await expect(page.getByText("최신 정책·운영 상세입니다.", { exact: false })).toBeVisible();
  const requests: LoggedRequest[] = await (await request.get("http://127.0.0.1:18766/__requests")).json();
  expect(requests.some(row => row.path.includes("trading-readiness"))).toBe(true);
  await page.getByRole("link", { name: "← 보유 검토로 돌아가기", exact: true }).click();
  await expect(page.getByTestId("holdings-review")).toBeVisible();
});

test("future and duplicate date parameters never query the outcomes endpoint", async ({ page, request }) => {
  for (const query of ["date=2999-01-01", "date=2025-01-01&date=2025-01-02"]) {
    await page.goto(`/performance?${query}`);
    await expect(page.getByTestId("review-workspace")).toContainText("조회 기준일을 확인해 주세요");
  }
  const requests: LoggedRequest[] = await (await request.get("http://127.0.0.1:18766/__requests")).json();
  expect(requests.filter(row => row.path.includes("outcomes"))).toHaveLength(0);
});
