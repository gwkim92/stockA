import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

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
  ["/recommendations/AAPL-2024-11-01", "AAPL"],
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

  test("recommendation detail keeps deep evidence collapsed by default", async ({ page }) => {
    await page.goto("/recommendations/AAPL-2024-11-01");
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
