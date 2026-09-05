import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test.beforeEach(async ({ request }) => { await request.post("http://127.0.0.1:18765/__scenario", { data: { scenario: "healthy" } }); });

test("company memo connects investment claim, source, assumption and review", async ({ page }, info) => {
  const errors: string[] = []; page.on("pageerror", error => errors.push(error.message));
  await page.goto("/recommendations/recommendation-1");
  const memo = page.getByTestId("investment-memo");
  await expect(memo.getByRole("heading", { name: "투자 논리와 판단 조건" })).toBeVisible();
  await expect(memo).toContainText("반복 매출과 현금흐름이 장기 투자 논리를 지탱한다.");
  await expect(memo).toContainText("연속 두 분기"); await expect(memo).toContainText("2026-10-30");
  await expect(memo.getByRole("link", { name: "연결 원문 1" })).toHaveAttribute("href", "/source-documents/source-document-1");
  await memo.getByText("모형별 핵심 가정", { exact: true }).click();
  await expect(memo.getByText(/매출 성장률: 5%/)).toBeVisible();
  expect((await new AxeBuilder({ page }).include('[data-testid="investment-memo"]').analyze()).violations).toEqual([]);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
  expect(errors).toEqual([]);
  await memo.screenshot({ path: info.outputPath(`investment-memo-${info.project.name}.png`) });
});

for (const scenario of ["memo-thesis-down", "memo-thesis-mismatch", "memo-thesis-slow"]) {
  test(`optional thesis cannot erase recommendation: ${scenario}`, async ({ page, request }) => {
    await request.post("http://127.0.0.1:18765/__scenario", { data: { scenario } });
    await page.goto("/recommendations/recommendation-1");
    const memo = page.getByTestId("investment-memo");
    await expect(memo).toContainText("서비스 매출과 현금흐름을 함께 검토합니다.");
    await expect(memo).not.toContainText("ALIEN-CLAIM"); await expect(memo).not.toContainText("secret-thesis-password");
    await expect(memo).toContainText(scenario === "memo-thesis-slow" ? "응답이 지연" : scenario === "memo-thesis-mismatch" ? "연결이 달라" : "불러오지 못했습니다");
    await expect(memo).toContainText("미지정");
  });
}

test("unknown evidence and holdings never become zero-complete or non-held", async ({ page, request }) => {
  await request.post("http://127.0.0.1:18765/__scenario", { data: { scenario: "memo-unknown" } });
  await page.goto("/recommendations/recommendation-1");
  const memo = page.getByTestId("investment-memo");
  await expect(memo).toContainText("근거 상태 미확인"); await expect(memo).toContainText("보유 상태 미확인");
  const target = memo.locator("dl > div").filter({ has: page.locator("dt", { hasText: "모형 추정 가치" }) });
  await expect(target.locator("dd")).toHaveText("미측정");
  await expect(memo).toContainText("미지정"); await expect(memo).not.toContainText("0/0개 충족");
  await expect(page.locator("#recommendation-position-reality")).not.toContainText("미보유 계좌");
});

test("ETF memo does not reuse company target values or research claims", async ({ page, request }, info) => {
  await request.post("http://127.0.0.1:18765/__scenario", { data: { scenario: "memo-fund" } });
  await page.goto("/recommendations/recommendation-1");
  const memo = page.getByTestId("investment-memo");
  await expect(memo.getByRole("heading", { name: "ETF 구성과 비용을 어떻게 볼 것인가" })).toBeVisible();
  await expect(memo).toContainText("500개"); await expect(memo).toContainText("0.09%");
  await expect(memo).not.toContainText("모형 추정 가치"); await expect(memo).not.toContainText("서비스 매출");
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
  await memo.screenshot({ path: info.outputPath(`fund-memo-${info.project.name}.png`) });
});

test("source-blocked candidate stays restricted", async ({ page, request }) => {
  await request.post("http://127.0.0.1:18765/__scenario", { data: { scenario: "memo-source-blocked" } });
  await page.goto("/recommendations/recommendation-1");
  await expect(page.getByTestId("investment-memo").locator('[data-tone="blocked"]')).toContainText("원천 근거 제한");
});

test("missing next-review date stays unassigned", async ({ page, request }) => {
  await request.post("http://127.0.0.1:18765/__scenario", { data: { scenario: "memo-no-review" } });
  await page.goto("/recommendations/recommendation-1");
  await expect(page.getByTestId("investment-memo")).toContainText("미지정");
});
