// Isolated HTTP fixtures. All text and prices are synthetic, not live investment inputs.
import { createServer } from 'node:http';
import { readFileSync } from 'node:fs';
const example = name => JSON.parse(readFileSync(new URL(`../../../../docs/api/frontend/examples/${name}.json`, import.meta.url), 'utf8'));
let scenario = 'healthy', requests = [];
const cursor = offset => Buffer.from(JSON.stringify({ offset, v: 1 })).toString('base64url');
const day = (date, delta) => new Date(Date.parse(`${date}T12:00:00Z`) + delta * 86400000).toISOString().slice(0, 10);
const server = createServer(async (req, res) => {
  const url = new URL(req.url, 'http://127.0.0.1'), path = url.pathname;
  const send = (status, payload) => { res.writeHead(status, { 'Content-Type': 'application/json' }); res.end(JSON.stringify(payload)); };
  if (path === '/__health') return send(200, { ok: true });
  if (path === '/__requests') return send(200, requests);
  if (path === '/__scenario' && req.method === 'POST') { let body = ''; for await (const part of req) body += part; scenario = JSON.parse(body).scenario; requests = []; return send(200, { scenario }); }
  requests.push({ path, query: url.search, method: req.method });
  if (req.headers.authorization !== 'Bearer news-theme-fixture') return send(401, { error: 'fixture auth' });
  if (scenario === 'all-down') return send(503, { error: 'private-fixture-error' });
  if (scenario === 'missing') return send(404, { error: 'missing' });
  if (scenario === 'slow-body' && path === '/api/events') { res.writeHead(200, { 'Content-Type': 'application/json' }); res.write('{"data":'); const timer = setTimeout(() => res.end('{} }'), 30000); res.on('close', () => clearTimeout(timer)); return; }
  const date = url.searchParams.get('asOfDate') || new Date().toISOString().slice(0, 10);
  const event = (id, symbol, extra = {}) => ({ event_id: id, title: `Stored source for ${symbol}`, korean_title: `${symbol} 설비 투자와 수요 변화`, korean_summary: '검증용 뉴스입니다. 공급 계획과 실제 수요를 원천 자료에서 대조합니다.', event_type: 'news_rss_item', event_at: `${day(date, -1)}T09:00:00Z`, symbol, instrument_id: `instrument-${symbol}`, theme_key: 'semiconductor', theme_name: '반도체', impact_direction: 'mixed', impact_score: 0.7, ai_evidence_id: 'ai-evidence-1', source_document_id: 'source-document-1', quality_gate: 'human_review_required', related_events: [], ...extra });
  if (path === '/api/events') {
    const p = example('event-list');
    let records = [event('event-1', 'AAPL'), event('event-2', 'MSFT', { ai_evidence_id: null, korean_title: '기업 수요 변화 · 해석 연결 대기' }), event('event-3', 'UNKNOWN', { source_document_id: null, ai_evidence_id: null, theme_key: 'UNCLASSIFIED', korean_title: '시장 배경 자료 · 원천 확인 필요' }), event('event-4', 'NVDA', { ai_evidence_type: 'news_event_candidate_rejected', quality_gate: 'ai_review_passed', korean_title: '근거가 부족하여 입력에서 제외된 뉴스' })];
    if (scenario === 'paged') records = [...records, ...Array.from({ length: 46 }, (_, i) => event(`event-page-${i}`, 'TEST')), event('event-tail-1', 'AAPL', { korean_title: '다음 페이지 AAPL 뉴스' }), event('event-tail-2', 'MSFT')];
    const symbol = url.searchParams.get('symbol'), theme = url.searchParams.get('themeKey');
    if (symbol) records = records.filter(row => row.symbol === symbol);
    if (theme) records = records.filter(row => row.theme_key === theme);
    const incoming = url.searchParams.get('cursor');
    const offset = incoming ? JSON.parse(Buffer.from(incoming, 'base64url').toString()).offset : 0;
    const limit = Number(url.searchParams.get('limit') || 50);
    p.data.events = scenario === 'empty' ? [] : records.slice(offset, offset + limit);
    p.data.as_of_date = date;
    p.data.filters = { symbol, theme_key: theme, event_type: 'all', evidence_type: 'all' };
    p.pagination = { limit, cursor: incoming, item_count: p.data.events.length, has_more: offset + limit < records.length, next_cursor: offset + limit < records.length ? cursor(offset + limit) : null };
    if (scenario === 'bad-paging') { p.pagination.has_more = true; p.pagination.next_cursor = null; }
    if (scenario === 'unknown') { delete p.data.as_of_date; delete p.pagination; delete p.data.events[0].event_at; delete p.data.events[0].quality_gate; }
    if (scenario === 'mismatch') p.data.filters.symbol = 'OTHER';
    if (scenario === 'literal') p.data.events[0].korean_summary = '<script>window.newsInjection=true</script> literal source text';
    return send(200, p);
  }
  if (path.startsWith('/api/themes/')) {
    const p = example('theme-detail'), d = p.data;
    Object.assign(d, { theme_key: decodeURIComponent(path.split('/').pop()), theme_name: '반도체', as_of_date: date, state: 'expanding', previous_state: 'unknown', confidence: 0.72, cycle_score: 0.74, features: { event_intensity: 0, price_momentum: 0.61, fundamental_quality: null } });
    d.cycle_history = [{ as_of_date: day(date, -10), state: 'forming', confidence: 0.6 }, { as_of_date: day(date, -5), state: 'unknown', confidence: null }, { as_of_date: date, state: 'expanding', confidence: 0.72 }];
    d.linked_instruments = [{ symbol: 'AAPL', instrument_id: 'instrument-aapl', membership_strength: 0.86, active_thesis_id: 'thesis-1', latest_recommendation_id: null }, { symbol: 'MSFT', instrument_id: 'instrument-msft', membership_strength: null, active_thesis_id: null, latest_recommendation_id: null }];
    d.supporting_events = [event('event-1', 'AAPL'), event('event-4', 'NVDA', { quality_gate: 'validator_blocked' })];
    d.operator_notes = ['합성 테스트 기록이며 실제 투자 정보가 아닙니다.'];
    if (scenario === 'unknown') { delete d.state; delete d.previous_state; delete d.cycle_score; delete d.confidence; delete d.cycle_history; delete d.supporting_events; delete d.linked_instruments; }
    if (scenario === 'duplicate') { d.cycle_history.push({ as_of_date: date, state: 'cooling', confidence: 0.3 }); d.supporting_events.push({ ...d.supporting_events[0], source_document_id: 'source-document-2' }); }
    if (scenario === 'mismatch') d.theme_key = 'wrong-theme';
    return send(200, p);
  }
  if (path === '/api/stocks/AAPL') return send(200, example('stock-detail'));
  if (path.startsWith('/api/ai/evidence-neighborhoods/')) return send(404, { error: 'no optional neighborhood' });
  if (path === '/api/theses/thesis-1') { const p = example('thesis-detail'); p.data.thesis_id = 'thesis-1'; return send(200, p); }
  if (path === '/api/ai-evidence/ai-evidence-1') { const p = example('ai-evidence-detail'); p.data.evidence_id = 'ai-evidence-1'; p.data.source_document_id = 'source-document-1'; p.links.source_document = '/api/source-documents/source-document-1'; return send(200, p); }
  if (path.startsWith('/api/source-documents/')) { const p = example('source-document-detail'); p.data.document_id = path.split('/').pop(); return send(200, p); }
  return send(404, { error: 'fixture route unavailable' });
});
server.listen(18769, '127.0.0.1');
process.on('SIGTERM', () => server.close(() => process.exit(0)));
