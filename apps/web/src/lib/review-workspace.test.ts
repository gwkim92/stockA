// @vitest-environment node
import { readFileSync } from "node:fs";
import { afterEach, describe, expect, it, vi } from "vitest";
import { loadReviewReport } from "./review-workspace-data";
import { filterHoldings, filterOutcomes, holding, money, outcome, parseReviewReport, percent, performanceHeadline, portfolioProjection, recordedReview, selectedDate, type ReviewKind } from "./review-workspace-model";
const sample = (name: string) => JSON.parse(readFileSync(`../../docs/api/frontend/examples/${name}.json`, "utf8"));
const date = "2026-09-05", now = new Date(`${date}T12:00:00Z`);
afterEach(() => { vi.useRealTimers(); vi.unstubAllEnvs(); });
const rawPosition = { instrument_id: "i1", symbol: "AAPL", base_currency: "USD", market_value: 120, cost_basis: 100, unrealized_pnl: 20, active_thesis_id: "t1" };
function portfolio(positions = [rawPosition]) { return parseReviewReport("portfolio", { data: { portfolio_name: "Long Term Paper", base_currency: "USD", positions } }); }
describe("existing contracts and account/date identity", () => {
  it.each([["portfolio", "portfolio-coverage"], ["performance", "performance-outcomes"]])("reads the saved %s contract without modifying it", (kind, file) => {
    const data = sample(file), before = JSON.stringify(data);
    expect(parseReviewReport(kind as ReviewKind, data).rows.length).toBeGreaterThan(0);
    expect(JSON.stringify(data)).toBe(before);
  });
  it("rejects another portfolio instead of displaying the wrong account", () => {
    const data = sample("portfolio-coverage"); data.data.portfolio_name = "Other Account";
    expect(() => parseReviewReport("portfolio", data)).toThrow();
  });
  it.each([undefined, null, {}, [null], [{}]])("rejects absent or malformed primary data %s", positions => {
    expect(() => parseReviewReport("portfolio", { data: { portfolio_name: "Long Term Paper", positions } })).toThrow();
  });
  it("keeps an explicitly empty list available", () => expect(portfolio([]).rows).toEqual([]));
  it("rejects duplicate identities", () => expect(() => portfolio([rawPosition, rawPosition])).toThrow());
  it.each(["2026-02-30", "2027-01-01", [date], "", "2026-09-05junk"])("does not silently replace invalid date %s with today", value => expect(selectedDate(value, date)).toBeNull());
  it("defaults only an absent date and accepts valid past dates", () => {
    expect(selectedDate(undefined, date)).toBe(date); expect(selectedDate("2025-12-31", date)).toBe("2025-12-31");
  });
});
describe("holdings have explicit valuation and evidence limits", () => {
  it("uses the existing stored P&L and return calculations", () => {
    const result = portfolioProjection(portfolio()); expect(result.valuation).toMatchObject({ marketValue: 120, costBasis: 100, unrealizedPnl: 20, returnPct: 0.2, measuredPositionCount: 1 });
  });
  it("never adds mixed currencies or substitutes native values", () => {
    const other = { ...rawPosition, instrument_id: "i2", base_currency: "KRW", market_value: 500000, cost_basis: 400000 };
    const native = { ...rawPosition, instrument_id: "i3", market_value: null, cost_basis: null, market_value_native: 999999 };
    const result = portfolioProjection(portfolio([rawPosition, other, native] as never));
    expect(result.valuation.marketValue).toBe(120); expect(result.excluded).toBe(2);
  });
  it.each([null, 0, -1, NaN, undefined])("unknown or nonpositive cost %s cannot produce an eligible subtotal", value => {
    expect(holding({ ...rawPosition, cost_basis: value }, "USD").amountVerified).toBe(false);
  });
  it("a measured zero market value is not missing", () => {
    const row = holding({ ...rawPosition, market_value: 0, unrealized_pnl: -100 }, "USD");
    expect(row.amountVerified).toBe(true); expect(row.returnPct).toBe(-1);
  });
  it("no eligible rows stays unmeasured, not zero P&L", () => {
    const result = portfolioProjection(portfolio([{ ...rawPosition, base_currency: "" }]));
    expect(result.valuation.marketValue).toBeNull(); expect(result.valuation.returnPct).toBeNull();
  });
  it("missing thesis field differs from explicit null", () => {
    expect(holding({ ...rawPosition, active_thesis_id: undefined }, "USD").thesisState).toBe("unknown");
    expect(holding({ ...rawPosition, active_thesis_id: null }, "USD").thesisState).toBe("missing");
    expect(holding(rawPosition, "USD").thesisState).toBe("linked");
  });
  it("projects only displayed position fields, not arbitrary server extras", () => {
    expect(JSON.stringify(holding({ ...rawPosition, debug_secret: "not-client-data" }, "USD"))).not.toContain("not-client-data");
  });
  it("filters without mutating order or amounts", () => {
    const rows = [holding(rawPosition, "USD"), holding({ ...rawPosition, instrument_id: "i2", symbol: "SPY", active_thesis_id: null }, "USD")];
    const before = JSON.stringify(rows);
    expect(filterHoldings(rows, "", "thesis").map(r => r.symbol)).toEqual(["SPY"]);
    expect(filterHoldings(rows, "aapl", "all")).toHaveLength(1); expect(JSON.stringify(rows)).toBe(before);
  });
});
describe("measured performance is not an invented strategy total", () => {
  it("uses percent for returns and percentage points for alpha", () => {
    expect(percent(0.06, true)).toBe("+6%p"); expect(percent(0.1)).toBe("+10%"); expect(percent(null)).toBe("미측정"); expect(percent(0, true)).toBe("0%p");
  });
  it("an empty/zero-sample report cannot show 100% hit rate", () => {
    const data = sample("performance-outcomes"); data.data.outcomes = []; data.data.summary.measured_recommendation_count = 0;
    expect(performanceHeadline(parseReviewReport("performance", data))).toMatchObject({ alpha: null, hitRate: null });
  });
  it("missing whole-report summary values are not computed from a filtered subset", () => {
    const data = sample("performance-outcomes"); delete data.data.summary;
    expect(performanceHeadline(parseReviewReport("performance", data))).toMatchObject({ measured: null, alpha: null, hitRate: null });
  });
  it("keeps unknown and zero alpha distinct", () => {
    const rows = [{ outcome_id: "a", symbol: "AAPL", alpha: 0.1, horizon_days: 90 }, { outcome_id: "b", symbol: "SPY", alpha: -0.02, horizon_days: 365 }, { outcome_id: "c", symbol: "META", alpha: 0, horizon_days: 90 }, { outcome_id: "d", symbol: "NVDA", alpha: null }].map(outcome);
    expect(filterOutcomes(rows, "", "positive", "90").map(r => r.symbol)).toEqual(["AAPL"]);
    expect(filterOutcomes(rows, "", "unknown", "").map(r => r.symbol)).toEqual(["NVDA"]);
    expect(filterOutcomes(rows, "", "all", "90").map(r => r.symbol)).toEqual(["AAPL", "META"]);
  });
  it("does not fabricate missing horizons and unsafe currency labels", () => {
    expect(outcome({ horizon_days: -1 }).horizon).toBeNull(); expect(money(100, null)).toBe("통화 미확인"); expect(money(null, "USD")).toBe("미측정");
  });
});
describe("recorded review lineage", () => {
  function reviewed(reference = "history-1") {
    const report = portfolio();
    report.raw.risk_budget = { review_decision_history: { eval_run_id: "history-1", portfolio_name: "Long Term Paper", latest_decisions: [] }, review_decision_feedback: { eval_run_id: "feedback-1", portfolio_name: "Long Term Paper", source_history_eval_run_id: reference, latest_items: [] } };
    return report;
  }
  it("joins feedback only to the exact stored history", () => {
    expect(recordedReview(reviewed()).feedbackLinked).toBe(true); expect(recordedReview(reviewed("history-999")).items).toBeNull();
  });
  it("keeps missing history missing", () => expect(recordedReview(portfolio()).decisions).toBeNull());
});
describe("read-only bounded report transport", () => {
  it("rejects invalid dates before any API access", async () => {
    const fetcher = vi.fn(); const result = await loadReviewReport("portfolio", "2026-02-30", { now, fetcher });
    expect(result.issue).toBe("date"); expect(fetcher).not.toHaveBeenCalled();
  });
  it("requests the selected date and never trading readiness for primary holdings", async () => {
    const fetcher = vi.fn(async () => Response.json(sample("portfolio-coverage"))) as typeof fetch;
    const result = await loadReviewReport("portfolio", "2025-01-15", { now, fetcher });
    expect(result.issue).toBeNull(); expect(fetcher).toHaveBeenCalledTimes(1);
    expect(fetcher).toHaveBeenCalledWith(expect.stringContaining("coverage?asOfDate=2025-01-15"), expect.objectContaining({ method: "GET", redirect: "error", cache: "no-store" }));
  });
  it("does not leak error bodies or read credentials", async () => {
    vi.stubEnv("STOCKANALYSIS_FRONTEND_API_READ_TOKEN", "private-token");
    const fetcher = vi.fn(async () => new Response("password=db-secret", { status: 503 })) as typeof fetch;
    const result = await loadReviewReport("performance", undefined, { now, fetcher });
    expect(result.issue).toBe("http"); expect(JSON.stringify(result)).not.toMatch(/password|private-token|db-secret/);
  });
  it("classifies invalid JSON without replacing it with a synthetic report", async () => {
    const fetcher = vi.fn(async () => new Response("not-json")) as typeof fetch;
    expect((await loadReviewReport("portfolio", undefined, { now, fetcher })).issue).toBe("invalid");
  });
  it("includes the response body in the deadline", async () => {
    vi.useFakeTimers(); let signal: AbortSignal | null | undefined;
    const fetcher = vi.fn(async (_url, init) => { signal = init?.signal; return { ok: true, json: () => new Promise(() => {}) }; }) as unknown as typeof fetch;
    const pending = loadReviewReport("performance", undefined, { now, fetcher, timeoutMs: 20 }); await vi.advanceTimersByTimeAsync(21);
    expect((await pending).issue).toBe("timeout"); expect(signal).toMatchObject({ aborted: true }); expect(vi.getTimerCount()).toBe(0);
  });
});
