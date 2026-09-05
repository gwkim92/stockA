import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test.beforeEach(async ({ request }) => {
  await request.post("http://127.0.0.1:18765/__scenario", { data: { scenario: "healthy" } });
});

test("investor journey renders with evidence links on desktop and mobile", async ({ page }, info) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  const response = await page.goto("/");
  expect(response?.status()).toBe(200);
  const home = page.getByTestId("research-home");
  await expect(home.getByRole("heading", { name: "시장 변화에서 투자 판단까지" })).toBeVisible();
  await expect(home.getByRole("link", { name: "투자 판단서 읽기" }).first()).toHaveAttribute("href", "/recommendations/recommendation-1");
  await expect(home.getByRole("link", { name: "테마 근거 보기" }).first()).toHaveAttribute("href", "/themes/semiconductor");
  await expect(home.getByText("반도체 설비 투자 확대", { exact: true })).toBeVisible();
  await expect(home.getByText("2위 · 원천 제한", { exact: true })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1)).toBe(true);
  const accessibility = await new AxeBuilder({ page }).include('[data-testid="research-home"]').analyze();
  expect(accessibility.violations).toEqual([]);
  await expect(home.getByRole("link", { name: "지난 판단의 수익률·벤치마크 대비 성과 확인" })).toHaveAttribute("href", "/performance");
  await expect(home.locator("details")).not.toHaveAttribute("open", "");
  expect(errors).toEqual([]);
  await page.screenshot({ path: info.outputPath(`research-home-${info.project.name}.png`), fullPage: true });
});

for (const scenario of ["news-down", "slow-body"]) {
  test(`news failure does not hide recommendations: ${scenario}`, async ({ page, request }) => {
    await request.post("http://127.0.0.1:18765/__scenario", { data: { scenario } });
    await page.goto("/");
    const home = page.getByTestId("research-home");
    await expect(home.getByText("현금흐름과 서비스 성장 검토", { exact: true })).toBeVisible();
    await expect(home.getByText(scenario === "slow-body" ? /응답 지연 · 이 영역만/ : /연결 확인 필요 · 이 영역만/).first()).toBeVisible();
    await expect(home).not.toContainText("test-internal-token-must-not-render");
    await expect(home).not.toContainText("조회된 뉴스 근거 목록이 비어 있습니다");
  });
}

test("all sources unavailable retains navigation and unknown metrics", async ({ page, request }) => {
  await request.post("http://127.0.0.1:18765/__scenario", { data: { scenario: "all-down" } });
  const response = await page.goto("/");
  expect(response?.status()).toBe(200);
  const home = page.getByTestId("research-home");
  await expect(home.getByRole("navigation", { name: "투자 판단 경로" })).toBeVisible();
  await expect(home).toContainText("분석 데이터 연결을 확인해 주세요");
  await expect(home).toContainText("미확인");
  await expect(home).not.toContainText("최근 자동 작업 정상");
  await expect(home).not.toContainText("조회된 투자 후보 목록이 비어 있습니다");
});

test("fresh HTTP response cannot conceal historical evidence", async ({ page, request }) => {
  await request.post("http://127.0.0.1:18765/__scenario", { data: { scenario: "historical" } });
  await page.goto("/");
  const home = page.getByTestId("research-home");
  await expect(home.getByText(/과거 기준 · 2001-01-01/).first()).toBeVisible();
  await expect(home).not.toContainText("페이퍼 검토 입력 허용");
});

test("missing counts are not healthy zeros", async ({ page, request }) => {
  await request.post("http://127.0.0.1:18765/__scenario", { data: { scenario: "missing-counts" } });
  await page.goto("/");
  await expect(page.getByTestId("research-home")).toContainText("작업 상태 미확인");
  await expect(page.getByTestId("research-home")).toContainText("미확인 보완 항목");
});

test("empty successful feeds render different copy from failures", async ({ page, request }) => {
  await request.post("http://127.0.0.1:18765/__scenario", { data: { scenario: "empty" } });
  await page.goto("/");
  await expect(page.getByTestId("research-home")).toContainText("조회된 투자 후보 목록이 비어 있습니다");
  await expect(page.getByTestId("research-home")).not.toContainText("이 영역만 불러오지 못했습니다");
});
