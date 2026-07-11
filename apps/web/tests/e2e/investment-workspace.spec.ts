import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

const investorRoutes = [
  ["/", "오늘"],
  ["/market-map", "시장"],
  ["/cycle-map", "흐름"],
  ["/intelligence", "뉴스"],
  ["/stocks", "종목"],
  ["/recommendations", "추천"],
  ["/portfolio/coverage", "포트폴리오"],
  ["/paper-trading", "가상 매매"],
] as const;

const detailRoutes = [
  ["/stocks/AAPL", "AAPL"],
  ["/stocks/SPY", "SPY"],
  ["/recommendations/AAPL-2024-11-01", "AAPL"],
  ["/recommendations/AAPL-professional-2026-06-25", "AAPL"],
  ["/ai-evidence/sec-event-aapl-10k-20240928", "근거"],
] as const;

const operationsRoutes = [
  ["/data-health", "운영 관리 · 데이터 상태"],
  ["/admin/ai-agents", "운영 관리 · AI 운영"],
  ["/trading-readiness", "운영 관리 · 거래 안전"],
  ["/remediation", "운영 관리 · 보완 작업"],
] as const;

const investorInternalCopyPattern =
  /\b(?:pipeline|runner|artifact|fallback|canonical|shadow|missing|not available|wait|read-only|bootstrap-v1|monitor_or_accumulate|needs_thesis_review|missing_thesis|raw_[a-z0-9_]+|[a-z]+_[a-z0-9_]+)\b|CHINA ADR COVERAGE|coverage status|검토 가능|확인한다|봐야 한다|미수집/i;
const rawStatusCodePattern =
  /\b(?:monitor_or_accumulate|needs_thesis_review|missing_thesis|equity_research|missing_api_key|admin_key_missing)\b|CHINA ADR COVERAGE/i;

async function isSummaryRecommendationRecord(page: Page): Promise<boolean> {
  const main = page.locator("#main-content");
  await expect(main).toContainText("추천");
  const mainText = await main.innerText();
  return /요약형\s*(?:추천\s*)?기록|최신 전문 분석 항목이 붙기 전 생성된 추천/.test(mainText);
}

test.describe("professional investment workspace", () => {
  for (const [route, headingText] of investorRoutes) {
    test(`${route} renders without horizontal overflow`, async ({ page }) => {
      await page.goto(route);
      await expect(page.locator("#main-content")).toContainText(headingText);

      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
      expect(overflow).toBeLessThanOrEqual(1);

      const bodyText = await page.locator("body").innerText();
      expect(bodyText).not.toMatch(investorInternalCopyPattern);
      expect(bodyText).not.toMatch(rawStatusCodePattern);
    });
  }

  for (const [route, expectedText] of detailRoutes) {
    test(`${route} keeps the research detail readable`, async ({ page }) => {
      await page.goto(route);
      await expect(page.locator("#main-content")).toContainText(expectedText);
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
      expect(overflow).toBeLessThanOrEqual(1);
      const bodyText = await page.locator("body").innerText();
      expect(bodyText).not.toMatch(investorInternalCopyPattern);
      expect(bodyText).not.toMatch(rawStatusCodePattern);
    });
  }

  test("mobile stock audit keeps the execution boundary fully visible", async ({ page }) => {
    test.skip((page.viewportSize()?.width ?? 0) > 560, "Mobile-only execution-boundary regression check.");
    await page.goto("/stocks/AAPL");

    const audit = page.getByRole("region", { name: "종목 전문 근거 감사", exact: true });
    const rail = audit.locator(".decision-boundary-rail");
    const executionStatus = rail.locator(".rail-status-value");
    await expect(executionStatus).toHaveText("읽기 전용, 주문 차단");

    const layout = await rail.evaluate((element) => getComputedStyle(element).gridTemplateColumns);
    expect(layout.trim().split(/\s+/)).toHaveLength(1);
    const isContained = await executionStatus.evaluate((element) => {
      const value = element.getBoundingClientRect();
      const cell = element.parentElement?.getBoundingClientRect();
      return Boolean(cell && value.left >= cell.left && value.right <= cell.right);
    });
    expect(isContained).toBe(true);
  });

  test("tablet summary and price layouts do not leave unassigned grid cells", async ({ page }) => {
    const viewportWidth = page.viewportSize()?.width ?? 0;
    test.skip(viewportWidth <= 640 || viewportWidth > 1024, "Tablet-only grid-fill regression check.");

    await page.goto("/recommendations/AAPL-2024-11-01");
    const commandGrid = page.locator(".workspace-command-grid");
    const executionCard = commandGrid.locator(".decision-card").last();
    await expect(commandGrid).toBeVisible();
    const commandGridBox = await commandGrid.boundingBox();
    const executionCardBox = await executionCard.boundingBox();
    expect(commandGridBox).not.toBeNull();
    expect(executionCardBox).not.toBeNull();
    expect(Math.abs((commandGridBox?.width ?? 0) - (executionCardBox?.width ?? 0))).toBeLessThanOrEqual(1);

    await page.goto("/stocks/AAPL");
    const priceGrid = page.locator("#stock-price-data");
    const priceSummary = priceGrid.locator(":scope > article").nth(1);
    await expect(priceGrid).toBeVisible();
    const priceGridBox = await priceGrid.boundingBox();
    const priceSummaryBox = await priceSummary.boundingBox();
    expect(priceGridBox).not.toBeNull();
    expect(priceSummaryBox).not.toBeNull();
    expect(Math.abs((priceGridBox?.width ?? 0) - (priceSummaryBox?.width ?? 0))).toBeLessThanOrEqual(2);
  });

  test("live recommendation detail keeps internal terms out of the investor view", async ({ page }) => {
    await page.goto("/recommendations");
    const firstRecommendation = page.locator('a[href^="/recommendations/"]').first();
    const href = await firstRecommendation.getAttribute("href");
    if (!href) {
      test.skip(true, "No live recommendation link is visible on the recommendation list.");
      return;
    }

    await page.goto(href);
    await expect(page.locator("#main-content")).toContainText("추천");
    const bodyText = await page.locator("body").innerText();
    expect(bodyText).not.toMatch(investorInternalCopyPattern);
    expect(bodyText).not.toMatch(rawStatusCodePattern);
  });

  test("summary recommendation record stays compact and links to the right follow-up screens", async ({ page }) => {
    await page.goto("/recommendations/AAPL-2024-11-01");
    expect(await isSummaryRecommendationRecord(page)).toBe(true);
    await expect(page.getByRole("region", { name: "AAPL 추천 판단서" })).toBeVisible();
    await expect(page.locator("#main-content")).toContainText("최신 전문 분석 항목이 붙기 전 생성된 추천");
    await expect(page.getByRole("link", { name: /종목 리서치/ })).toHaveAttribute("href", "/stocks/AAPL");
    await expect(page.getByRole("link", { name: /가상 매매/ })).toHaveAttribute("href", "/paper-trading");
  });

  test("professional recommendation detail keeps deep evidence collapsed by default", async ({ page }) => {
    await page.goto("/recommendations/AAPL-professional-2026-06-25");
    expect(await isSummaryRecommendationRecord(page)).toBe(false);
    const disclosures = page.locator(
      [
        "#recommendation-professional-flow",
        "#recommendation-financial-model",
        "#recommendation-valuation",
        "#recommendation-equity-research",
        "#recommendation-evidence-review",
      ].join(", "),
    );
    await expect(disclosures.first()).toBeVisible();
    expect(await disclosures.count()).toBeGreaterThanOrEqual(4);
    const openStates = await disclosures.evaluateAll((items) =>
      items.map((item) => item instanceof HTMLDetailsElement && item.open),
    );
    expect(openStates.every((isOpen) => !isOpen)).toBe(true);
    await expect(page.locator("#recommendation-evidence-review")).toContainText("펼치기");
  });

  test("professional recommendation detail top half uses a compact decision board", async ({ page }) => {
    await page.goto("/recommendations/AAPL-professional-2026-06-25");
    await expect(page.locator(".recommendation-focus-panel")).toHaveCount(0);
    expect(await isSummaryRecommendationRecord(page)).toBe(false);
    await expect(page.locator('[aria-label="추천 상세 핵심 판단"]')).toBeVisible();
    await expect(page.locator('[aria-label="포지션 요약"]')).toBeVisible();
    await expect(page.locator(".recommendation-waterfall-card").first()).toContainText("다음 확인");
    await expect(page.locator("body")).not.toContainText("UNKNOWN");
  });

  for (const [route, expectedText] of operationsRoutes) {
    test(`${route} is visibly separated as operations`, async ({ page }) => {
      await page.goto(route);
      await expect(page.locator("#main-content")).toContainText(expectedText);
      const bodyText = await page.locator("body").innerText();
      expect(bodyText).not.toMatch(rawStatusCodePattern);
    });
  }

  test("primary navigation exposes working investor destinations", async ({ page }) => {
    await page.goto("/");
    const navigation = page.getByRole("navigation", { name: "투자 리서치 주요 메뉴" });
    for (const [route, label] of [
      ["/market-map", "시장"],
      ["/intelligence", "리서치"],
      ["/stocks", "종목"],
      ["/recommendations", "추천"],
      ["/portfolio/coverage", "포트폴리오"],
    ] as const) {
      const link = navigation.getByRole("link", { name: label });
      await expect(link).toHaveAttribute("href", route);
    }
  });

  test("AI operations page exposes status without browser mutation controls", async ({ page }) => {
    await page.goto("/admin/ai-agents");
    const statusPanel = page.getByRole("region", { name: "예비 AI 연결 상태" });
    await expect(statusPanel).toBeVisible();
    await expect(statusPanel).toContainText("상태 조회 전용");
    await expect(statusPanel).toContainText("서버 CLI/SSH 전용");
    await expect(statusPanel.locator("button, form")).toHaveCount(0);
    await expect(statusPanel.locator('a[href^="http"]')).toHaveCount(0);
    const text = await statusPanel.innerText();
    expect(text).not.toMatch(/auth_url|user_code|device_auth_pid|status_path|\/opt\/|admin action token/i);
  });

  test("investor and operations pages have no serious accessibility violations", async ({ page }) => {
    for (const [route] of [...investorRoutes, ...operationsRoutes]) {
      await page.goto(route);
      const result = await new AxeBuilder({ page }).analyze();
      const serious = result.violations.filter(
        (violation) => violation.impact === "critical" || violation.impact === "serious",
      );
      expect(serious, `${route}: ${serious.map((violation) => violation.id).join(", ")}`).toEqual([]);
    }
  });
});
