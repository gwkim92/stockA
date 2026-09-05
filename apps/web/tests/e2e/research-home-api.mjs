// Isolated localhost fixture API for SSR browser tests. Never connects to a database.
import { createServer } from "node:http";
import { readFileSync } from "node:fs";
const memoFixture = JSON.parse(readFileSync(new URL('./recommendation-memo-fixture.json', import.meta.url), 'utf8'));
let scenario = "healthy";
const server = createServer(async (request, response) => {
  const path = new URL(request.url, "http://127.0.0.1").pathname;
  const send = (status, value) => { response.writeHead(status, { "Content-Type": "application/json" }); response.end(JSON.stringify(value)); };
  if (path === "/__health") return send(200, { ok: true });
  if (path === "/__scenario" && request.method === "POST") {
    let body = ""; for await (const chunk of request) body += chunk;
    scenario = JSON.parse(body).scenario; return send(200, { scenario });
  }
  if (request.headers.authorization !== "Bearer ci-only-read-token") return send(401, { error: "fixture auth required" });
  if (scenario === "all-down" || (scenario === "news-down" && path.includes("news-clusters"))) {
    return send(503, { error: { message: "test-internal-token-must-not-render" } });
  }
  if (scenario === "slow-body" && path.includes("news-clusters")) {
    response.writeHead(200, { "Content-Type": "application/json" }); response.write('{"data":');
    const timer = setTimeout(() => response.end("{}}"), 30_000);
    response.on("close", () => clearTimeout(timer)); return;
  }
  if (path === "/api/recommendations/recommendation-1" || path === "/api/theses/thesis-1") {
    const sample = structuredClone(memoFixture);
    if (path.startsWith("/api/theses/")) {
      if (scenario === "memo-thesis-down") return send(503, { error: { message: "secret-thesis-password" } });
      if (scenario === "memo-thesis-mismatch") { sample.thesis.instrument_id = "wrong-instrument"; sample.thesis.summary = "ALIEN-CLAIM"; }
      if (scenario === "memo-no-review") sample.thesis.latest_review.next_review_date = "";
      if (scenario === "memo-thesis-slow") {
        response.writeHead(200, { "Content-Type": "application/json" }); response.write('{"data":');
        const timer = setTimeout(() => response.end("{}}"), 30_000); response.on("close", () => clearTimeout(timer)); return;
      }
    }
    const data = sample.recommendation;
    if (scenario === "memo-source-blocked") { data.professional_evidence_audit.source_blocker.blocked = true; data.professional_evidence_audit.source_blocker.summary = "정기 재무 원천이 없어 투자 판단을 보류합니다."; }
    if (scenario === "memo-unknown") {
      data.linked_thesis_id = ""; data.equity_research = null;
      data.professional_evidence_audit.status = "not_available";
      data.professional_evidence_audit.available_layer_count = 0; data.professional_evidence_audit.expected_layer_count = 0;
      data.valuation_target_range.status = "unavailable"; data.valuation_target_range.target_base = null; data.valuation_target_range.methods = [];
      for (const p of [data.position_context, data.position_context.broker_reference]) { p.status = "unknown"; p.quantity = null; p.average_cost = null; p.cost_basis_native = null; }
    }
    if (scenario === "memo-fund") {
      data.symbol = "SPY"; data.instrument_id = "instrument-2"; data.linked_thesis_id = "";
      data.professional_evidence_audit.product_type = "fund_or_etf";
      data.fund_instrument_analysis = {
        status: "available", analysis_type: "fund", symbol: "SPY", summary: "지수 노출과 비용·추적 품질을 검토합니다.", benchmark_code: "S&P 500", benchmark_source: "fixture", source_type: "fixture", source_as_of_date: "2026-09-04",
        holding_count: 500, holdings_coverage_weight: 0.99, average_holding_confidence: 0.9, top_holdings: [],
        portfolio_role: { portfolio_name: "Long Term Paper", current_weight: null, recommended_weight: null, role: "core", rationale: "지수 노출" },
        tracking_error: { status: "missing", value: null, metric_type: "tracking_difference", tracking_difference_value: null, source_name: "", source_as_of_date: "", source_url: "", measurement_window: "", measurement_basis: "", benchmark_name: "S&P 500", fund_return: null, benchmark_return: null, summary: "추적 자료 대기" },
        expense_ratio: { status: "collected", value: 0.0009, source_name: "fixture", source_as_of_date: "2026-09-03", source_url: "", summary: "검증용 비용률" },
        liquidity: { status: "missing", source_name: "", source_as_of_date: "", observation_count: 0, latest_volume: null, average_daily_volume: null, average_daily_dollar_volume: null, summary: "유동성 자료 대기" },
        nav_premium_discount: { status: "missing", nav_per_share: null, nav_as_of_date: "", bid_ask_midpoint: null, closing_price: null, market_price_as_of_date: "", premium_discount_to_nav: null, premium_discount_as_of_date: "", source_name: "", source_url: "", summary: "NAV 자료 대기" },
        limitations: ["지수 구성 집중 위험"], score_policy: "recommendation_weights_unchanged", automatic_order_allowed: false, broker_submit_allowed: false, order_boundary: "read_only_no_order",
      };
    }
    return send(200, { contract_version: "frontend-api-v0.1", generated_at: new Date().toISOString(), data: path.startsWith("/api/theses/") ? sample.thesis : data, links: {} });
  }
  const today = new Date().toISOString().slice(0, 10);
  const asOf = scenario === "historical" ? "2001-01-01" : today;
  const data = {
    "/api/cycles": { as_of_date: asOf, cycle_states: [
      { theme_key: "semiconductor", theme_name: "반도체", state: "expanding", previous_state: "forming", instrument_count: 12, confidence: 0.81 },
      { theme_key: "power_infrastructure", theme_name: "전력 인프라", state: "confirming", previous_state: "expanding", instrument_count: 6, confidence: 0.76 },
    ] },
    "/api/recommendations": { as_of_date: asOf, recommendations: [
      { recommendation_id: "recommendation-1", symbol: "AAPL", name: "Apple", rank_position: 1, score: 0.82, linked_thesis_id: "thesis-1",
        evidence_quality: { title: "현금흐름과 서비스 성장 검토", summary: "서비스 매출과 현금흐름을 확인하고 성장 둔화 가능성을 비교합니다.", source_blocker: { blocked: false } },
        decision_boundary: { paper_validation_input_allowed: true, reason: "실거래가 아닌 페이퍼 검토 입력입니다." } },
      { recommendation_id: "recommendation-2", symbol: "EROK", name: "EROK", rank_position: 2, score: 0.63, linked_thesis_id: "",
        evidence_quality: { title: "정기 재무 공시 확인 필요", summary: "원천 공시가 충분하지 않아 전문 판단에 사용하지 않습니다.", source_blocker: { blocked: true } },
        decision_boundary: { paper_validation_input_allowed: true, reason: "원천 제한 상태를 우선 확인합니다." } },
    ] },
    "/api/ai/news-clusters": { as_of_date: asOf, clusters: [
      { evidence_id: "evidence-1", theme_name: "반도체", symbols: ["AAPL", "NVDA"], title: "반도체 설비 투자 확대", story_label: "반도체 설비 투자 확대", event_count: 3, confidence: 0.8 },
    ] },
    "/api/dashboard/today": { as_of_date: asOf, attention_summary: { failed_pipeline_count: 0, open_ticket_count: 1 }, latest_metrics: { weight_coverage_ratio: 0.82 }, top_actions: [
      { rank: 1, symbol: "TSLA", action: "reduce_review", reason: "집중 노출과 기존 투자 논리를 다시 확인합니다.", risk_level: "high" },
    ] },
  }[path];
  if (!data) return send(404, { error: "fixture endpoint unavailable" });
  if (scenario === "missing-counts" && path.includes("dashboard")) { data.attention_summary = {}; data.latest_metrics = {}; }
  if (scenario === "empty") for (const key of ["cycle_states", "recommendations", "clusters", "top_actions"]) if (key in data) data[key] = [];
  send(200, { contract_version: "frontend-api-v0.1", generated_at: new Date().toISOString(), data, links: {} });
});
server.listen(18765, "127.0.0.1");
process.on("SIGTERM", () => server.close(() => process.exit(0)));
