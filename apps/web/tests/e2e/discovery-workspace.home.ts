import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
test.beforeEach(async ({ request }) => { await request.post("http://127.0.0.1:18765/__scenario", { data: { scenario: "healthy" } }); });
for (const [path, title, name] of [["/stocks", "종목 탐색", "stocks"], ["/cycles", "테마 사이클", "cycles"], ["/market-map", "시장 배경", "market"]]) {
  test(`${name} discovery renders, remains accessible and captures the actual screen`, async ({ page }, info) => {
    const errors: string[] = []; page.on("pageerror", error => errors.push(error.message));
    await page.goto(path); const workspace = page.getByTestId("discovery-workspace");
    await expect(workspace.getByRole("heading", { name: title, exact: true, level: 1 })).toBeVisible();
    await expect(workspace.getByRole("textbox")).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
    const axe = await new AxeBuilder({ page }).analyze(); expect(axe.violations).toEqual([]);
    expect(errors).toEqual([]);
    await page.screenshot({ path: info.outputPath(`discovery-${name}-${info.project.name}.png`), fullPage: true, animations: "disabled" });
    await page.screenshot({ path: info.outputPath(`discovery-${name}-${info.project.name}-viewport.png`), animations: "disabled" });
  });
}
test("stock search and relation filter survive refresh and history navigation", async ({ page }) => {
  await page.goto("/stocks"); const explorer = page.getByTestId("stock-explorer");
  await explorer.getByRole("textbox", { name: "종목 검색" }).fill("AAPL");
  await expect(explorer.getByRole("article")).toHaveCount(1); await expect(page).toHaveURL(/q=AAPL/);
  await explorer.getByRole("button", { name: /보유 연결/ }).click(); await expect(page).toHaveURL(/scope=held/);
  await page.reload(); await expect(explorer.getByRole("textbox")).toHaveValue("AAPL");
  await expect(explorer.getByRole("article")).toHaveCount(1);
  await explorer.getByRole("button", { name: /가격 확인/ }).click(); await expect(explorer).toContainText("조건에 맞는 결과가 없습니다");
  await page.goBack(); await expect(explorer.getByRole("article")).toHaveCount(1);
  await explorer.getByRole("button", { name: "필터 초기화" }).click(); await expect(explorer.getByRole("article")).toHaveCount(4);
  await expect(explorer).toContainText("가격 미확인"); await expect(explorer).toContainText("보유 연결 미확인");
  await expect(explorer).not.toContainText("오늘 가장 먼저 확인");
  await expect(explorer.getByRole("link", { name: "AAPL 종목 분석 열기" })).toHaveAttribute("href", "/stocks/AAPL");
});
test("cycle change and history filters keep unknown history out of observed changes", async ({ page }) => {
  await page.goto("/cycles"); const explorer = page.getByTestId("cycle-explorer");
  await explorer.getByRole("button", { name: /상태 전환/ }).click(); await expect(explorer.getByRole("article")).toHaveCount(2);
  await explorer.getByRole("button", { name: /이전 상태 미확인/ }).click(); await expect(explorer.getByRole("article")).toHaveCount(1);
  await expect(explorer.getByRole("heading", { name: "헬스케어" })).toBeVisible();
  await expect(explorer).toContainText("0%"); await expect(explorer).toContainText("미측정");
  await expect(page.getByTestId("discovery-workspace")).toContainText("중복 포함 · 고유 종목 수가 아님");
});
test("market group and lookback selections are real and retain source limitations", async ({ page }) => {
  await page.goto("/market-map"); const explorer = page.getByTestId("market-explorer");
  await explorer.getByRole("combobox", { name: "시장 영역" }).selectOption("metals"); await expect(explorer.getByRole("article")).toHaveCount(2);
  await expect(explorer).toContainText("현물 가격이 아닌 프록시 지수");
  await explorer.getByRole("combobox", { name: "시장 영역" }).selectOption("rates");
  await explorer.getByRole("combobox", { name: "변화율 기간" }).selectOption("60d");
  await expect(page).toHaveURL(/window=60d/); await page.reload();
  await expect(explorer.getByRole("combobox", { name: "시장 영역" })).toHaveValue("rates");
  await expect(explorer).toContainText("미측정");
  await explorer.getByRole("button", { name: "필터 초기화" }).click();
  await expect(explorer.getByRole("article")).toHaveCount(4);
  await expect(page.getByRole("table")).toHaveAccessibleName("저장된 상관관계 · 원래 반환 순서");
});
for (const [scenario, path, expected] of [["all-down", "/market-map", "이 화면의 자료를 불러오지 못했습니다"], ["empty", "/stocks", "수신된 목록이 비어 있습니다"], ["discovery-invalid", "/cycles", "이 화면의 자료를 불러오지 못했습니다"], ["discovery-unknown", "/market-map", "상관관계 자료 미제공"]]) {
  test(`${scenario} does not imply healthy or fabricate records`, async ({ page, request }) => {
    await request.post("http://127.0.0.1:18765/__scenario", { data: { scenario } });
    await page.goto(path); const workspace = page.getByTestId("discovery-workspace");
    await expect(workspace).toContainText(expected); await expect(workspace).not.toContainText("test-internal-token-must-not-render");
    await expect(workspace.getByRole("navigation", { name: "시장과 기업 탐색" })).toBeVisible();
    if (scenario === "discovery-unknown") { await expect(workspace).toContainText("기준일 미확인"); await expect(workspace).not.toContainText("수집 품질은 안정적"); }
  });
}
