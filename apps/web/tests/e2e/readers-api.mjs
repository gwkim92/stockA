// Synthetic read-only browser fixtures. This server never reaches a database.
import { createServer } from "node:http";
import { readFileSync } from "node:fs";
const example = name => JSON.parse(readFileSync(new URL(`../../../../docs/api/frontend/examples/${name}.json`, import.meta.url), "utf8"));
const memo = JSON.parse(readFileSync(new URL("./recommendation-memo-fixture.json", import.meta.url), "utf8"));
let scenario = "healthy";
let requests = [];
const server = createServer(async (req, res) => {
  const url = new URL(req.url, "http://127.0.0.1"), path = url.pathname;
  const send = (status, value) => { res.writeHead(status, { "Content-Type": "application/json" }); res.end(JSON.stringify(value)); };
  if (path === "/__health") return send(200, { ok: true });
  if (path === "/__requests") return send(200, requests);
  if (path === "/__scenario" && req.method === "POST") {
    let body = ""; for await (const part of req) body += part;
    scenario = JSON.parse(body).scenario; requests = []; return send(200, { scenario });
  }
  requests.push({ path, method: req.method });
  if (req.headers.authorization !== "Bearer reader-test-only") return send(401, { error: "fixture authentication required" });
  if (scenario === "all-down") return send(503, { error: "private-error-must-not-render" });
  if (scenario === "missing") return send(404, { error: "missing record" });
  const isSource = path.startsWith("/api/source-documents/");
  const isThesis = path.startsWith("/api/theses/");
  if (scenario === "slow-body" && isSource) {
    res.writeHead(200, { "Content-Type": "application/json" }); res.write('{"data":');
    const timer = setTimeout(() => res.end("{}}"), 30000);
    res.on("close", () => clearTimeout(timer)); return;
  }
  const envelope = data => ({ contract_version: "frontend-api-v0.1", generated_at: new Date().toISOString(), data, links: {} });
  if (path === "/api/stocks/AAPL") {
    const payload = example("stock-detail");
    payload.data.recommendation.recommendation_id = "recommendation-1";
    payload.data.recommendation.linked_thesis_id = "thesis-1";
    return send(200, payload);
  }
  if (path === "/api/recommendations/recommendation-1") return send(200, envelope(structuredClone(memo.recommendation)));
  // The existing legacy adapters explicitly support a 404 neighborhood response.
  if (path === "/api/ai/evidence-neighborhoods/AAPL") return send(404, { error: "fixture has no optional neighborhood" });
  if (path === "/api/ai-evidence/event-1") {
    const payload = example("ai-evidence-detail");
    payload.data.evidence_id = "event-1";
    payload.data.source_document_id = "source-document-1";
    payload.links.source_document = "/api/source-documents/source-document-1";
    return send(200, payload);
  }
  if (isThesis) {
    const payload = example("thesis-detail"), data = payload.data;
    data.thesis_id = "thesis-1"; data.created_from_recommendation_id = "recommendation-1";
    data.summary = "서비스의 반복 매출이 현금흐름을 뒷받침한다는 저장된 투자 가설입니다. 이는 화면 동작 확인용 기록입니다.";
    data.core_claims = ["서비스 매출의 반복성과 고객 유지율을 함께 검토한다.", "가격 상승이 아니라 현금흐름의 지속성을 확인한다."];
    data.lifecycle = {
      source: "thesis_record", buy_case: { summary: data.summary, core_claims: data.core_claims },
      catalysts: ["다음 실적 발표에서 서비스 매출과 마진을 확인한다."],
      risks: ["고객 유지율 하락과 규제 비용 증가가 가설을 약화할 수 있다."],
      invalidation_conditions: [{ condition: "서비스 성장률의 둔화가 지속되는 경우", current_status: "not_triggered" }, { condition: "현금흐름이 원가 상승을 흡수하지 못하는 경우", current_status: "unknown" }],
      valuation: { base_case: "성장률·할인율을 별도 확인하는 검증용 시나리오" },
      readiness: { status: "needs_detail", missing_items: ["valuation_sensitivity"] },
    };
    data.latest_review = { review_id: "review-1", reviewed_at: "2026-09-04T12:00:00Z", action: "monitor", risk_level: "medium", summary: "성장 근거를 다시 확인하는 검토 기록입니다.", change_notes: "원문 검토 기록: 현금흐름과 수익성 가정을 다음 실적에서 대조한다.", next_review_date: "2026-10-20" };
    data.evidence = [{ evidence_id: "event-1", type: "source_document_event", title: "서비스 매출과 사업 위험 발췌", observed_at: "2026-09-03T09:00:00Z" }];
    data.valuation_target_range = structuredClone(memo.recommendation.valuation_target_range);
    data.professional_lifecycle_gates = { status: "warning", gate_count: 1, pass_count: 0, blocked_count: 0, gates: [{ gate_key: "valuation_assumptions", title: "저장된 가치평가 가정 확인", status: "warning", decision: "원천과 평가 가정을 분리해서 확인한다.", detail: "테스트용 가정이며 투자 성능 검증 결과가 아닙니다.", next_step: "다음 공시와 가정을 대조한다.", facts: [{ label: "저장 근거", value: "검증용 가정 2개" }] }] };
    payload.links.recommendation = "/api/recommendations/recommendation-1";
    if (scenario === "triggered") data.lifecycle.invalidation_conditions[0].current_status = "triggered";
    if (scenario === "unknown") { delete data.latest_review; delete data.professional_lifecycle_gates; delete data.valuation_target_range.currency_code; }
    if (scenario === "wrong-id") data.thesis_id = "thesis-999";
    if (scenario === "unsafe-link") { data.created_from_recommendation_id = "bad?id"; payload.links.recommendation = "https://untrusted.invalid/private"; }
    return send(200, payload);
  }
  if (isSource) {
    const payload = example("source-document-detail"), data = payload.data;
    data.document_id = "source-document-1";
    data.title = "Business overview and service revenue — synthetic filing excerpt";
    data.korean_title = "서비스 매출과 사업 위험 · 원천 발췌";
    data.korean_summary = "저장된 요약: 반복 매출과 비용 구조를 확인하는 검증용 문서입니다.";
    data.storage_uri = "artifact://private-bucket/do-not-show-source-location";
    data.excerpts = [
      { chunk_id: "chunk-services", section: "Service revenue", locator: "Item 7 · page 12", summary: "Recurring service revenue is reviewed alongside customer retention. This is synthetic text for interface testing, not a live filing quotation." },
      { chunk_id: "chunk-risk", section: "Risk factors", locator: "Item 1A · page 24", summary: "Customer churn and regulatory costs may affect future cash flows. This stored excerpt summary is not a complete source document." },
    ];
    data.linked_evidence = [{ evidence_id: "event-1", evidence_type: "source_document_event", title: "서비스 사업에 관한 연결 해석" }];
    payload.links.source_document = path;
    payload.links.thesis = "/api/theses/thesis-1";
    if (scenario === "alias") data.document_id = "external-filing-aapl";
    if (scenario === "untranslated") { delete data.korean_summary; delete data.korean_title; }
    if (scenario === "unknown") { delete data.filed_at; delete data.retrieval.fetched_at; delete data.access_policy; delete data.excerpts; }
    if (scenario === "empty") data.excerpts = [];
    if (scenario === "download-flag") data.access_policy.browser_download_enabled = true;
    if (scenario === "literal-markup") data.excerpts[0].summary = '<script>window.readerInjection=true</script> Stored text, not executable markup.';
    if (scenario === "wrong-id") { data.document_id = "unrelated-document"; delete payload.links.source_document; }
    return send(200, payload);
  }
  return send(404, { error: "unknown fixture route" });
});
server.listen(18767, "127.0.0.1");
process.on("SIGTERM", () => server.close(() => process.exit(0)));
