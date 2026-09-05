import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
test.beforeEach(async ({ request }) => {
  await request.post("http://127.0.0.1:18767/__scenario", { data: { scenario: "healthy" } });
});
for (const [path, title, kind] of [["/theses/thesis-1", "AAPL 투자 논리", "thesis"], ["/source-documents/source-document-1", "서비스 매출과 사업 위험 · 원천 발췌", "source"]]) {
  test(`${kind} reader is accessible and shows real reading content early`, async ({ page }, info) => {
    const errors: string[] = []; page.on("pageerror", error => errors.push(error.message));
    await page.goto(path); const reader = page.getByTestId("research-reader");
    await expect(reader.getByRole("heading", { level: 1, name: title })).toBeVisible();
    const first = reader.locator("#thesis-claims > p, [data-testid=source-excerpts] article").first();
    await expect(first).toBeVisible(); expect((await first.boundingBox())!.y).toBeLessThan(700);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
    const axe = await new AxeBuilder({ page }).analyze(); expect(axe.violations).toEqual([]);
    expect(errors).toEqual([]);
    await page.screenshot({ path: info.outputPath(`reader-${kind}-${info.project.name}.png`), fullPage: true, animations: "disabled" });
    await page.screenshot({ path: info.outputPath(`reader-${kind}-${info.project.name}-viewport.png`), animations: "disabled" });
  });
}
test("real company to thesis to interpretation to source navigation works", async ({ page, request }) => {
  await page.goto("/stocks/AAPL");
  await page.getByRole("link", { name: "투자 논리 열기", exact: true }).first().click();
  await expect(page).toHaveURL(/\/theses\/thesis-1$/);
  await page.getByTestId("research-reader").getByRole("link", { name: "연결 해석 보기 →", exact: true }).click();
  await expect(page).toHaveURL(/\/ai-evidence\/event-1$/);
  await page.getByRole("link", { name: "원천 문서 열기", exact: true }).first().click();
  await expect(page).toHaveURL(/\/source-documents\/source-document-1$/);
  await expect(page.getByTestId("source-excerpts")).toContainText("Recurring service revenue");
  await page.getByRole("link", { name: "연결 투자 논리 →", exact: true }).click();
  await expect(page).toHaveURL(/\/theses\/thesis-1$/);
  const requests: { path: string; method: string }[] = await (await request.get("http://127.0.0.1:18767/__requests")).json();
  for (const expected of ["/api/stocks/AAPL", "/api/theses/thesis-1", "/api/ai-evidence/event-1", "/api/source-documents/source-document-1"]) expect(requests.some(row => row.path === expected)).toBe(true);
  expect(requests.every(row => row.method === "GET")).toBe(true);
});
test("excerpt search persists across reload and literal text stays readable", async ({ page }) => {
  await page.goto("/source-documents/source-document-1"); const excerpts = page.getByTestId("source-excerpts");
  await excerpts.getByRole("textbox", { name: "발췌 검색" }).fill("customer churn");
  await expect(excerpts.getByRole("article")).toHaveCount(1); await expect(page).toHaveURL(/q=customer/);
  await page.reload(); await expect(excerpts.getByRole("textbox")).toHaveValue("customer churn");
  await expect(excerpts.getByRole("article")).toHaveCount(1);
  await excerpts.getByRole("textbox").fill(".*"); await expect(excerpts).toContainText("검색어와 일치하는 발췌가 없습니다");
  await excerpts.getByRole("button", { name: "검색 초기화" }).click(); await expect(excerpts.getByRole("article")).toHaveCount(2);
  await expect(page.getByTestId("research-reader")).not.toContainText("do-not-show-source-location");
  await expect(page.getByTestId("research-reader")).not.toContainText("reader-test-only");
});
test("unknown invalidation is not counted as triggered and missing review is not monitor", async ({ page, request }) => {
  await request.post("http://127.0.0.1:18767/__scenario", { data: { scenario: "unknown" } });
  await page.goto("/theses/thesis-1"); const reader = page.getByTestId("research-reader");
  await expect(reader.locator("#thesis-conditions")).toContainText("발동 기록 0개");
  await expect(reader.locator("#thesis-conditions")).toContainText("판정 미확인 1개");
  await expect(reader.locator("#thesis-review")).toContainText("식별자와 검토일이 확인된 기록이 없습니다");
  await expect(reader.getByRole("complementary")).toContainText("미지정");
  await expect(reader.locator("#thesis-valuation")).toContainText("통화 미확인");
});
test("explicit trigger is shown without replacing it by a ready state", async ({ page, request }) => {
  await request.post("http://127.0.0.1:18767/__scenario", { data: { scenario: "triggered" } });
  await page.goto("/theses/thesis-1");
  await expect(page.getByTestId("research-reader")).toContainText("발동·차단 기록 확인");
  await expect(page.locator("#thesis-conditions")).toContainText("발동 기록 1개");
});
test("chapter links resolve and existing detailed valuation remains readable", async ({ page }) => {
  await page.goto("/theses/thesis-1"); const reader = page.getByTestId("research-reader");
  const nav = reader.getByRole("navigation", { name: "문서 목차" });
  for (const link of await nav.getByRole("link").all()) await expect(page.locator((await link.getAttribute("href"))!)).toHaveCount(1);
  await nav.getByRole("link", { name: "촉매·무효화", exact: true }).click();
  await expect(page.locator("#thesis-conditions")).toBeInViewport();
  const disclosure = reader.locator("details").filter({ has: page.locator("summary", { hasText: "기존 전문 가치평가·사업부 모델 전체 보기" }) });
  await disclosure.locator("summary").first().click();
  await expect(disclosure).toContainText("매출 성장률"); await expect(disclosure).toContainText("할인율");
});
test("missing translation does not invent a Korean market interpretation", async ({ page, request }) => {
  await request.post("http://127.0.0.1:18767/__scenario", { data: { scenario: "untranslated" } });
  await page.goto("/source-documents/source-document-1"); const reader = page.getByTestId("research-reader");
  await expect(reader).toContainText("저장된 한국어 요약이 없습니다");
  await expect(reader.getByRole("heading", { level: 1 })).toHaveText("Business overview and service revenue — synthetic filing excerpt");
  await expect(reader).not.toContainText("시장 뉴스 흐름 문서다");
});
test("a permission flag alone never creates a raw download action", async ({ page, request }) => {
  await request.post("http://127.0.0.1:18767/__scenario", { data: { scenario: "download-flag" } });
  await page.goto("/source-documents/source-document-1");
  await expect(page.getByTestId("research-reader")).toContainText("원문 전달 경로 미제공");
  expect(await page.getByTestId("research-reader").locator('a[href^="artifact:"], a[download]').count()).toBe(0);
});
test("stored markup is literal text and cannot execute", async ({ page, request }) => {
  await request.post("http://127.0.0.1:18767/__scenario", { data: { scenario: "literal-markup" } });
  await page.goto("/source-documents/source-document-1");
  await expect(page.getByTestId("source-excerpts")).toContainText("<script>window.readerInjection=true</script>");
  expect(await page.evaluate(() => (window as unknown as { readerInjection?: boolean }).readerInjection)).toBeUndefined();
});
test("existing aliases are visible rather than silently re-labeled exact", async ({ page, request }) => {
  await page.goto("/theses/AAPL-bootstrap-v1");
  await expect(page.getByTestId("research-reader")).toContainText("기존 API 별칭 해석");
  await request.post("http://127.0.0.1:18767/__scenario", { data: { scenario: "alias" } });
  await page.goto("/source-documents/source-document-7");
  await expect(page.getByTestId("research-reader")).toContainText("기존 API 별칭 해석");
  await expect(page.getByTestId("research-reader")).toContainText("external-filing-aapl");
});
for (const [scenario, expected] of [["empty", "이 문서에 공개된 발췌가 없습니다"], ["unknown", "발췌 자료를 확인할 수 없습니다"], ["wrong-id", "요청한 자료와 응답을 대조해야 합니다"], ["all-down", "자료를 불러오지 못했습니다"], ["slow-body", "자료 응답이 지연되고 있습니다"], ["missing", "찾는 화면이 없습니다"]]) {
  test(`${scenario} never renders a fake complete source`, async ({ page, request }) => {
    await request.post("http://127.0.0.1:18767/__scenario", { data: { scenario } });
    await page.goto("/source-documents/source-document-1");
    await expect(page.locator("main")).toContainText(expected);
    await expect(page.locator("main")).not.toContainText("private-error-must-not-render");
  });
}
