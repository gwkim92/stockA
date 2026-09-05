// Local synthetic browser fixtures only. No account or market data access.
import { createServer } from 'node:http';
import { readFileSync } from 'node:fs';
const example = name => JSON.parse(readFileSync(new URL(`../../../../docs/api/frontend/examples/${name}.json`, import.meta.url), 'utf8'));
const memo = JSON.parse(readFileSync(new URL('./recommendation-memo-fixture.json', import.meta.url), 'utf8'));
let scenario = 'healthy', requests = [];
const server = createServer(async (req, res) => {
  const path = new URL(req.url, 'http://127.0.0.1').pathname;
  const send = (status, data) => { res.writeHead(status, { 'Content-Type': 'application/json' }); res.end(JSON.stringify(data)); };
  if (path === '/__health') return send(200, { ok: true });
  if (path === '/__requests') return send(200, requests);
  if (path === '/__scenario' && req.method === 'POST') { let body = ''; for await (const part of req) body += part; scenario = JSON.parse(body).scenario; requests = []; return send(200, { scenario }); }
  requests.push({ path, method: req.method });
  if (req.headers.authorization !== 'Bearer company-fixture-only') return send(401, { error: 'fixture authentication' });
  if (scenario === 'all-down') return send(503, { error: 'private-error-must-not-render' });
  if (scenario === 'missing') return send(404, { error: 'missing' });
  const envelope = data => ({ contract_version: 'frontend-api-v0.1', generated_at: new Date().toISOString(), data, links: {} });
  if (path === '/api/stocks/AAPL' || path === '/api/stocks/SPY') {
    const p = example('stock-detail'), d = p.data;
    const fund = path.endsWith('/SPY'); d.symbol = fund ? 'SPY' : 'AAPL'; d.name = fund ? 'SPDR S&P 500 ETF' : 'Apple Inc.';
    d.as_of_date = '2026-09-05'; d.latest_price.trade_date = '2026-09-04'; d.latest_price.change_pct = null;
    d.recommendation = { recommendation_id: 'recommendation-1', linked_thesis_id: 'thesis-1', score: 0.78, status: 'active' };
    d.position.linked_thesis_id = 'thesis-1';
    d.price_bars = Array.from({ length: 45 }, (_, index) => ({ trade_date: new Date(Date.UTC(2026, 6, 20 + index)).toISOString().slice(0, 10), close: index === 30 ? null : 290 + index / 4 + Math.sin(index) * 3 }));
    d.equity_research = { title: 'Apple 기업 리서치', artifact_id: 'research-1', provider: 'fixture', model_name: 'fixture', source_document_ids: [], as_of_date: '2026-09-03', korean_summary: '서비스의 반복 매출과 현금흐름을 함께 살펴보는 검증용 투자 가설입니다.', key_points: ['매출 성장과 고객 유지율의 관계를 확인한다.'], catalysts: ['다음 실적 발표에서 서비스 매출과 마진을 검토한다.'], risks: ['규제 비용과 고객 유지율 하락 가능성'], invalidation_conditions: ['현금흐름이 비용 증가를 흡수하지 못할 때 재검토한다.'], valuation_sensitivity: {} };
    d.financial_statement_model = structuredClone(memo.recommendation.financial_statement_model);
    d.valuation_target_range = structuredClone(memo.recommendation.valuation_target_range);
    d.professional_source_guardrail = { blocked: false, status: 'available', summary: '검증용 원천 판정입니다. 실거래 주문은 생성하지 않습니다.' };
    d.market_data_provider = { analysis_price_source: { provider: 'fixture', freshness_status: 'fresh', used_for_scoring: false } };
    d.recent_events = [{ event_id: 'event-1', ai_evidence_id: 'ai-evidence-1', title: 'Service revenue and risks', korean_title: '서비스 매출과 사업 위험', event_at: '2026-09-03T00:00:00Z', impact_direction: 'mixed', source_document_id: 'source-document-1' }];
    if (fund) { d.fund_instrument_analysis = { analysis_type: 'fund', symbol: 'SPY', status: 'available', summary: '지수 노출과 비용을 검토하는 테스트용 펀드 기록입니다.', benchmark_code: 'S&P 500', holding_count: 500, source_as_of_date: '2026-09-03', expense_ratio: { value: 0.0009, source_as_of_date: '2026-09-03', source_name: 'fixture' }, top_holdings: [{ symbol: 'AAPL', name: 'Apple', target_weight: 0.06 }], limitations: ['구성 종목 집중 위험'] }; }
    if (scenario === 'stock-unknown') { delete d.currency_code; delete d.recommendation; delete d.position; delete d.latest_price; delete d.price_bars; }
    if (scenario === 'stock-wrong') d.symbol = 'MSFT';
    if (scenario === 'blocked') d.professional_source_guardrail = { blocked: true, summary: '정기 공시 자료 부족', blocker_label: '재무 원천 보완 필요' };
    return send(200, p);
  }
  if (path.startsWith('/api/ai/evidence-neighborhoods/')) {
    if (scenario === 'context-down') return send(503, { error: 'optional-private-error' });
    if (scenario === 'context-slow') { res.writeHead(200, { 'Content-Type': 'application/json' }); res.write('{"data":'); const timer = setTimeout(() => res.end('{} }'), 30000); res.on('close', () => clearTimeout(timer)); return; }
    const symbol = path.split('/').pop();
    return send(200, envelope({ symbol: scenario === 'context-wrong' ? 'MSFT' : symbol, as_of_date: '2026-09-03', instrument: { symbol, instrument_id: 'instrument-501', found: true }, themes: [{ theme_key: 'consumer_platform', theme_name: '소비자 플랫폼', membership_type: 'direct', confidence: 0.7 }], events: [], theses: [{ thesis_id: 'unrelated-first-thesis' }] }));
  }
  if (path === '/api/recommendations/recommendation-1') return send(200, envelope(structuredClone(memo.recommendation)));
  if (path === '/api/theses/thesis-1') { const p = example('thesis-detail'); p.data.thesis_id = 'thesis-1'; return send(200, p); }
  if (path.startsWith('/api/ai-evidence/')) {
    const p = example('ai-evidence-detail'), d = p.data; d.evidence_id = 'ai-evidence-1';
    d.korean_title = '서비스 성장 해석과 원천 대조'; delete d.korean_summary;
    d.source_document_id = 'source-document-1'; p.links.source_document = '/api/source-documents/source-document-1'; p.links.ai_evidence = path;
    d.visibility_trace = { validator: { blocked: false, decision_ko: '사람의 검토가 필요한 추출 기록입니다.', reasons_ko: ['추출값과 실제 발췌를 대조하세요.'] } };
    d.extracted_fields[0].source_chunk_id = 'chunk-mdna-services';
    d.source_chunks[0].summary = 'Title: Service revenue. Summary: Customer retention and recurring revenue must be reviewed together. This is a synthetic excerpt summary.';
    if (scenario === 'blocked') { d.evidence_type = 'news_event_candidate_rejected'; d.extraction_run.quality_gate = 'ai_review_passed'; d.visibility_trace.validator.blocked = true; d.visibility_trace.validator.reasons_ko = ['출처가 부족하여 입력에서 제외']; d.news_candidate = { event_summary: '검증용 후보 요약', uncertainty_notes: '실적과 매출의 인과관계는 확인되지 않았습니다.', instrument_impacts: [{ target: 'AAPL', rationale: '검증용 가설', confidence: 0.5 }], theme_impacts: [] }; }
    if (scenario === 'cluster') { d.source_document_id = ''; delete p.links.source_document; d.cluster_summary = { theme_name: '서비스 플랫폼', story_label: '반복 매출 관련 묶음', as_of_date: '2026-09-03', event_count: 2 }; d.cluster_events = [{ title: '묶음 이벤트 하나', source_document_id: 'source-document-1' }, { title: '묶음 이벤트 둘', source_document_id: 'source-document-2' }]; }
    if (scenario === 'chunk-missing') d.extracted_fields[0].source_chunk_id = 'missing-chunk';
    if (scenario === 'evidence-wrong') d.evidence_id = 'ai-evidence-999';
    if (scenario === 'source-mismatch') p.links.source_document = '/api/source-documents/other-document';
    if (scenario === 'literal-markup') d.source_chunks[0].summary = '<script>window.compromised=true</script> stored literal text';
    return send(200, p);
  }
  if (path.startsWith('/api/source-documents/')) {
    const p = example('source-document-detail'); p.data.document_id = path.split('/').pop(); return send(200, p);
  }
  return send(404, { error: 'fixture route unavailable' });
});
server.listen(18768, '127.0.0.1');
process.on('SIGTERM', () => server.close(() => process.exit(0)));
