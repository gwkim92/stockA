// Isolated synthetic reports based on saved contracts. No database or financial writes.
import { createServer } from "node:http";
import { readFileSync } from "node:fs";
const sample = name => JSON.parse(readFileSync(new URL(`../../../../docs/api/frontend/examples/${name}.json`, import.meta.url), "utf8"));
let scenario = "healthy", requests = [];
const server = createServer(async (req, res) => {
  const url = new URL(req.url, "http://127.0.0.1"), path = url.pathname;
  const send = (status, value) => { res.writeHead(status, { "Content-Type": "application/json" }); res.end(JSON.stringify(value)); };
  if (path === "/__health") return send(200, { ok: true });
  if (path === "/__requests") return send(200, requests);
  if (path === "/__scenario" && req.method === "POST") { let body = ""; for await (const chunk of req) body += chunk; scenario = JSON.parse(body).scenario; requests = []; return send(200, { scenario }); }
  requests.push({ path, query: url.search, method: req.method });
  if (req.headers.authorization !== "Bearer review-test-only") return send(401, { error: "fixture authentication" });
  if (scenario === "all-down") return send(503, { error: "do-not-expose-private-error" });
  if (path === "/api/trading-readiness") return send(200, sample("trading-readiness"));
  const isPortfolio = path === "/api/portfolio/Long%20Term%20Paper/coverage", isPerformance = path === "/api/performance/Long%20Term%20Paper/outcomes";
  if (!isPortfolio && !isPerformance) return send(404, { error: "fixture endpoint unavailable" });
  const date = url.searchParams.get(isPortfolio ? "asOfDate" : "measurementEndDate") || new Date().toISOString().slice(0, 10);
  const envelope = sample(isPortfolio ? "portfolio-coverage" : "performance-outcomes"), data = envelope.data;
  if (scenario === "legacy") return send(200, envelope);
  if (isPortfolio) {
    data.as_of_date = date; data.base_currency = "USD";
    data.positions = [
      { symbol: "AAPL", instrument_id: "i1", weight: 0.15, base_currency: "USD", market_value: 1200, cost_basis: 1000, unrealized_pnl: 200, active_thesis_id: "thesis-1", coverage_status: "covered", outcome_status: "measured", action: "monitor", position_size_status: "within_limit" },
      { symbol: "SPY", instrument_id: "i2", weight: 0.25, base_currency: "USD", market_value: 1900, cost_basis: 2000, unrealized_pnl: -100, active_thesis_id: null, coverage_status: "missing_thesis", outcome_status: "not_applicable", action: "needs_thesis_review" },
      { symbol: "EROK", instrument_id: "i3", weight: 0.1, base_currency: "USD", market_value: null, cost_basis: null, unrealized_pnl: null, outcome_status: "missing_outcome", action: "needs_thesis_review" },
      { symbol: "005930", instrument_id: "i4", weight: 0.1, base_currency: "KRW", market_value: 500000, cost_basis: 400000, unrealized_pnl: 100000, active_thesis_id: "thesis-kr", outcome_status: "measured", action: "monitor" },
    ];
    data.summary = { position_count: 4, missing_thesis_count: 1, missing_outcome_count: 1, missing_thesis_weight: 0.25, cash_weight: 0.4, weight_coverage_ratio: 0.5 };
    data.risk_budget = {
      status: "needs_position_review", over_single_position_limit_count: 1, concentration: { over_limit_count: null },
      review_decision_history: { eval_run_id: "review-10", portfolio_name: "Long Term Paper", as_of_date: date, latest_decisions: [{ symbol: "SPY", decision_label: "보유 논리 확인", rationale: "지수 노출 목적과 기존 보유 이유를 검토합니다.", next_review_action: "다음 분기 보유 목적 확인", related_thesis_id: "thesis-spy" }] },
      review_decision_feedback: { eval_run_id: "feedback-20", portfolio_name: "Long Term Paper", source_history_eval_run_id: "review-10", as_of_date: date, feedback_status: "too_early", too_early_count: 1, contradicted_count: 0, latest_items: [] },
    };
    if (scenario === "feedback-mismatch") { data.risk_budget.review_decision_feedback.source_history_eval_run_id = "review-999"; data.risk_budget.review_decision_feedback.too_early_count = 999; }
    if (scenario === "valuation-missing") { delete data.base_currency; for (const p of data.positions) delete p.base_currency; }
  } else {
    const base = data.outcomes[0];
    data.measurement_end_date = date; data.measurement_start_date = "2025-01-01";
    data.outcomes = [
      { ...base, outcome_id: "o1", recommendation_id: "recommendation-1", thesis_id: "thesis-1", symbol: "AAPL", horizon_days: 90, absolute_return: 0.1, benchmark_return: 0.04, alpha: 0.06 },
      { ...base, outcome_id: "o2", recommendation_id: "recommendation-2", thesis_id: null, symbol: "SPY", horizon_days: 365, absolute_return: 0.02, benchmark_return: 0.04, alpha: -0.02, label: "underperform", security_contribution_bps: -20 },
      { ...base, outcome_id: "o3", recommendation_id: null, thesis_id: null, symbol: "EROK", horizon_days: null, absolute_return: null, benchmark_return: null, alpha: null, security_contribution_bps: null, label: "not_available" },
    ];
    data.summary.measured_recommendation_count = 2; data.summary.average_alpha = 0.02; data.summary.hit_rate = 0.5;
    data.quality_evaluation = { status: "insufficient_sample", sample_size_status: "insufficient_sample", review_outcome_mismatch_count: 0, checks: [{ label: "표본 관찰", status: "watch", detail: "합성 테스트 표본입니다. 투자 성능 검증 자료가 아닙니다.", next_step: "관찰 기간별 측정 확인" }] };
    if (scenario === "summary-missing") { delete data.summary; delete data.quality_evaluation; }
  }
  if (scenario === "empty") { data[isPortfolio ? "positions" : "outcomes"] = []; if (!isPortfolio) data.summary.measured_recommendation_count = 0; }
  if (scenario === "wrong-portfolio") data.portfolio_name = "Other account";
  envelope.generated_at = new Date().toISOString(); return send(200, envelope);
});
server.listen(18766, "127.0.0.1");
process.on("SIGTERM", () => server.close(() => process.exit(0)));
