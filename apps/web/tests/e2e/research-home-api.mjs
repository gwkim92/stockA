// Isolated localhost fixture API for SSR browser tests. Never connects to a database.
import { createServer } from "node:http";
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
  const today = new Date().toISOString().slice(0, 10);
  const asOf = scenario === "historical" ? "2001-01-01" : today;
  const data = {
    "/api/cycles": { as_of_date: asOf, cycle_states: [
      { theme_key: "semiconductor", state: "expanding", previous_state: "forming", instrument_count: 12, confidence: 0.81 },
      { theme_key: "power_infrastructure", state: "confirming", previous_state: "expanding", instrument_count: 6, confidence: 0.76 },
    ] },
    "/api/recommendations": { as_of_date: asOf, recommendations: [
      { recommendation_id: "recommendation-1", symbol: "AAPL", name: "Apple", rank_position: 1,
        evidence_quality: { title: "현금흐름과 서비스 성장 검토", summary: "서비스 매출과 현금흐름을 확인하고 성장 둔화 가능성을 비교합니다.", source_blocker: { blocked: false } },
        decision_boundary: { paper_validation_input_allowed: true, reason: "실거래가 아닌 페이퍼 검토 입력입니다." } },
      { recommendation_id: "recommendation-2", symbol: "EROK", name: "EROK", rank_position: 2,
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
