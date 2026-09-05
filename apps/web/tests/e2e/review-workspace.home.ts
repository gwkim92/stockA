import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
test.beforeEach(async ({ request }) => { await request.post("http://127.0.0.1:18766/__scenario", { data: { scenario: "healthy" } }); });
for (const [path, title, file] of [["/portfolio/coverage", "보유 검토", "holdings"], ["/performance", "판단 성과", "performance"]]) {
  test(`${file} shows actual rendered review content and accessible navigation`, async ({ page }, info) => {
    const errors: string[] = []; page.on("pageerror", error => errors.push(error.message));
    await page.goto(path); const workspace = page.getByTestId("review-workspace");
    await expect(workspace.getByRole("heading", { name: title, exact: true, level: 1 })).toBeVisible();
    const firstRecord = workspace.getByRole("article").first();
    await expect(firstRecord).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
    const axe = await new AxeBuilder({ page }).analyze(); expect(axe.violations).toEqual([]); expect(errors).toEqual([]);
    const bounds = await firstRecord.boundingBox();
    expect(bounds!.y).toBeLessThan(info.project.name === "mobile" ? 780 : 900);
    await page.screenshot({ path: info.outputPath(`review-${file}-${info.project.name}.png`), fullPage: true, animations: "disabled" });
    await page.screenshot({ path: info.outputPath(`review-${file}-${info.project.name}-viewport.png`), animations: "disabled" });
  });
}
test("holding filters preserve date/history and never combine native currency values", async ({ page, request }) => {
  await page.goto("/portfolio/coverage?date=2025-01-15"); const list = page.getByTestId("holdings-review");
  const summary = page.getByRole("region", { name: "보고서 요약" });
  await expect(summary).toContainText("3,100"); await expect(summary).not.toContainText("500,000");
  await expect(summary).toContainText("2/4개");
  await list.getByRole("button", { name: "투자 논리 확인" }).click(); await expect(list.getByRole("article")).toHaveCount(2);
  await list.getByRole("textbox").fill("SPY"); await page.reload(); await expect(list.getByRole("article")).toHaveCount(1);
  await expect(page).toHaveURL(/date=2025-01-15/); await expect(list.getByRole("textbox")).toHaveValue("SPY");
  await list.getByRole("button", { name: "평가자료 확인" }).click(); await expect(list).toContainText("조건에 맞는 보유 종목이 없습니다");
  await page.goBack(); await expect(list.getByRole("article")).toHaveCount(1);
  await list.getByRole("button", { name: "필터 초기화" }).click(); await expect(list.getByRole("article")).toHaveCount(4);
  const requests = await (await request.get("http://127.0.0.1:18766/__requests")).json();
  expect(requests.some((r: { path: string }) => r.path === "/api/trading/readiness")).toBe(false);
  expect(requests.every((r: { method: string }) => r.method === "GET")).toBe(true);
});
test("performance filters separate horizons and retain report-level summary", async ({ page }) => {
  await page.goto("/performance"); const list = page.getByTestId("outcome-explorer");
  const summary = page.getByRole("region", { name: "보고서 요약" }); await expect(summary).toContainText("+2%p");
  await list.getByRole("combobox", { name: "관찰 기간" }).selectOption("90"); await expect(list.getByRole("article")).toHaveCount(1); await expect(list).toContainText("+6%p");
  await page.reload(); await expect(list.getByRole("combobox")).toHaveValue("90"); await expect(summary).toContainText("+2%p");
  await list.getByRole("button", { name: "필터 초기화" }).click(); await list.getByRole("button", { name: "초과수익 음수" }).click();
  await expect(list.getByRole("article")).toHaveCount(1); await expect(list).toContainText("-2%p");
  await expect(list.getByRole("link", { name: "당시 추천 →" })).toHaveAttribute("href", "/recommendations/recommendation-2");
  await expect(page.getByRole("region", { name: "관점별 기여도" })).toContainText("합산해 총수익률을 만들지 않습니다");
});
test("date form requests a new report, not merely a different label", async ({ page, request }) => {
  await page.goto("/performance"); await page.getByLabel("성과 종료 기준일").fill("2025-02-03");
  await page.getByRole("button", { name: "조회", exact: true }).click(); await expect(page).toHaveURL(/date=2025-02-03/);
  const requests = await (await request.get("http://127.0.0.1:18766/__requests")).json();
  expect(requests.some((r: { query: string }) => r.query.includes("measurementEndDate=2025-02-03"))).toBe(true);
});
for (const [scenario, path, expected] of [["empty", "/performance", "수신된 측정 결과가 없습니다"], ["summary-missing", "/performance", "미측정"], ["valuation-missing", "/portfolio/coverage", "0/4개"], ["feedback-mismatch", "/portfolio/coverage", "동일한 검토 기록을 참조한 사후 평가가 확인되지 않았습니다"], ["all-down", "/portfolio/coverage", "이 화면의 자료를 불러오지 못했습니다"], ["wrong-portfolio", "/performance", "자료의 계정 또는 형식을 확인해야 합니다"]]) {
  test(`${scenario} remains explicit, with no false healthy or zero return`, async ({ page, request }) => {
    await request.post("http://127.0.0.1:18766/__scenario", { data: { scenario } }); await page.goto(path);
    const workspace = page.getByTestId("review-workspace"); await expect(workspace).toContainText(expected);
    await expect(workspace).not.toContainText("do-not-expose-private-error");
    if (scenario === "feedback-mismatch") await expect(workspace).not.toContainText("999개");
    if (scenario === "empty") await expect(page.getByRole("region", { name: "보고서 요약" })).not.toContainText("100%");
  });
}
test("invalid date never calls the report backend", async ({ page, request }) => {
  await page.goto("/performance?date=2026-02-30"); await expect(page.getByTestId("review-workspace")).toContainText("조회 기준일을 확인해 주세요");
  const requests = await (await request.get("http://127.0.0.1:18766/__requests")).json();
  expect(requests.filter((r: { path: string }) => r.path.includes("outcomes"))).toHaveLength(0);
});
