// @vitest-environment node
import { readFileSync } from 'node:fs';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { chunkTarget, parseCompany, parseInterpretation, parseNeighborhood, priceObservations, stockSymbol } from './company-evidence-model';
import { loadCompany, loadCompanyNeighborhood, loadInterpretation } from './company-evidence-data';
const example = (name: string) => JSON.parse(readFileSync(`../../docs/api/frontend/examples/${name}.json`, 'utf8'));
afterEach(() => { vi.useRealTimers(); vi.unstubAllEnvs(); });
describe('saved company contracts and honest observations', () => {
  it('preserves source data and never infers a daily return from sparse bars', () => {
    const payload = example('stock-detail'), before = JSON.stringify(payload);
    const view = parseCompany(payload, 'aapl');
    expect(view.symbol).toBe('AAPL'); expect(view.daily).toBeNull();
    expect(view.points).toHaveLength(payload.data.price_bars.length);
    expect(JSON.stringify(payload)).toBe(before);
  });
  it('keeps explicitly reported zero daily change', () => {
    const payload = example('stock-detail'); payload.data.latest_price.change_pct = 0;
    expect(parseCompany(payload, 'AAPL').daily).toBe(0);
  });
  it.each([null, {}, { change_pct: 0.1 }, { trade_date: '2026-02-30', change_pct: 0.1 }])('cannot label an undated price change as observed', price => {
    const payload = example('stock-detail'); payload.data.latest_price = price;
    expect(parseCompany(payload, 'AAPL').daily).toBeNull();
  });
  it.each(['MSFT', '', 'UNKNOWN'])('refuses a mismatching or absent company identity %s', symbol => {
    const payload = example('stock-detail'); payload.data.symbol = symbol;
    expect(() => parseCompany(payload, 'AAPL')).toThrow();
  });
  it('does not turn a missing position into confirmed non-holdings', () => {
    const payload = example('stock-detail'); delete payload.data.position;
    expect(parseCompany(payload, 'AAPL').positionState).toBe('unknown');
    payload.data.position = null; expect(parseCompany(payload, 'AAPL').positionState).toBe('none');
    payload.data.position = { quantity: 0 }; expect(parseCompany(payload, 'AAPL').positionState).toBe('none');
  });
  it('keeps missing currency, risk, provider and recommendation data unknown', () => {
    const payload = example('stock-detail'); delete payload.data.currency_code; delete payload.data.recommendation;
    const view = parseCompany(payload, 'AAPL');
    expect(view.currency).toBeNull(); expect(view.recommendationState).toBe('unknown');
    expect(view.guard.blocked).toBeUndefined(); expect(view.provider.used_for_scoring).toBeUndefined();
  });
  it('a source blocker is not overridden by a linked recommendation', () => {
    const payload = example('stock-detail'); payload.data.professional_source_guardrail = { blocked: true };
    expect(parseCompany(payload, 'AAPL')).toMatchObject({ blocked: true, recommendationState: 'linked' });
  });
  it('does not select an unrelated first neighborhood thesis', () => {
    const payload = example('stock-detail'); delete payload.data.recommendation; delete payload.data.position;
    payload.data.neighborhood = { theses: [{ thesis_id: 'wrong-thesis' }] };
    expect(parseCompany(payload, 'AAPL').thesisHref).toBeNull();
  });
  it('uses explicit fund evidence instead of a ticker-name guess', () => {
    const payload = example('stock-detail'); payload.data.fund_instrument_analysis = { analysis_type: 'fund', symbol: 'AAPL' };
    expect(parseCompany(payload, 'AAPL').fundKind).toBe(true);
  });
  it('preserves null price gaps and excludes ambiguous dates', () => {
    const observations = [
      { trade_date: '2026-09-01', close: 100 }, { trade_date: '2026-09-02', close: null },
      { trade_date: '2026-09-03', close: 103 }, { trade_date: '2026-09-03', close: 104 },
      { trade_date: '2026-09-04', close: 105 }, { trade_date: '2026-09-07', close: 106 },
    ];
    const before = JSON.stringify(observations), result = priceObservations(observations, '2026-09-05');
    expect(result.points).toEqual([{ date: '2026-09-01', close: 100 }, { date: '2026-09-02', close: null }, { date: '2026-09-03', close: null }, { date: '2026-09-04', close: 105 }]);
    expect(result.excluded).toBe(3); expect(JSON.stringify(observations)).toBe(before);
  });
  it('does not replace close by adjusted close, zero, or a fabricated observation', () => {
    expect(priceObservations([{ trade_date: '2026-09-01', adjusted_close: 100, close: 0 }], null).points?.[0].close).toBeNull();
    expect(priceObservations(null, null).points).toBeNull();
    expect(priceObservations([], null).points).toEqual([]);
  });
});
describe('neighborhood ownership', () => {
  const payload = () => ({ data: { symbol: 'AAPL', instrument: { symbol: 'AAPL', instrument_id: 'i1', found: true }, themes: [], events: [] } });
  it('requires both symbol and instrument identity before presenting context', () => {
    expect(parseNeighborhood(payload(), 'AAPL', 'i1').themes).toEqual([]);
    expect(() => parseNeighborhood(payload(), 'AAPL', 'i2')).toThrow();
    expect(() => parseNeighborhood(payload(), 'MSFT', 'i1')).toThrow();
  });
  it('does not export unrelated theses or arbitrary internal fields', () => {
    const p = payload(); Object.assign(p.data, { storage_uri: 'internal', theses: [{ thesis_id: 'unrelated' }] });
    expect(JSON.stringify(parseNeighborhood(p, 'AAPL', 'i1'))).not.toMatch(/storage_uri|unrelated/);
  });
});
describe('evidence, rejection and exact chunk links', () => {
  it('preserves saved English source content without translation guesses', () => {
    const p = example('ai-evidence-detail'), before = JSON.stringify(p);
    const view = parseInterpretation(p, p.data.evidence_id);
    expect(view.summary).toBeNull(); expect(view.chunks?.[0].summary).toBe(p.data.source_chunks[0].summary);
    expect(JSON.stringify(p)).toBe(before);
  });
  it('execution success is not quality approval', () => {
    const p = example('ai-evidence-detail'); p.data.extraction_run = { status: 'succeeded' };
    expect(parseInterpretation(p, p.data.evidence_id).reviewLabel).toBe('사용 전 검토 필요');
  });
  it.each(['type', 'gate', 'validator'])('rejection via %s overrides another passed flag', mechanism => {
    const p = example('ai-evidence-detail'); p.data.extraction_run.quality_gate = 'ai_review_passed';
    if (mechanism === 'type') p.data.evidence_type = 'news_event_candidate_rejected';
    if (mechanism === 'gate') p.data.extraction_run.quality_gate = 'validator_blocked';
    if (mechanism === 'validator') p.data.visibility_trace = { validator: { blocked: true } };
    expect(parseInterpretation(p, p.data.evidence_id)).toMatchObject({ blocked: true, reviewLabel: '추천 입력 제외 · 차단 기록' });
  });
  it('resolves only exact, unambiguous source chunk IDs', () => {
    const p = example('ai-evidence-detail'), view = parseInterpretation(p, p.data.evidence_id);
    expect(chunkTarget(view.chunks, 'chunk-mdna-services')).toBe('#evidence-chunk-1');
    expect(chunkTarget(view.chunks, 'services')).toBeNull();
    p.data.source_chunks.push(p.data.source_chunks[0]); expect(() => parseInterpretation(p, p.data.evidence_id)).toThrow();
  });
  it('conflicting source id and supplied link are not joined', () => {
    const p = example('ai-evidence-detail'); p.links.source_document = '/api/source-documents/different-document';
    expect(parseInterpretation(p, p.data.evidence_id)).toMatchObject({ sourceMismatch: true, sourceHref: null });
  });
  it('canonical evidence mismatch fails even when a self-link echoes the request', () => {
    const p = example('ai-evidence-detail'); p.data.evidence_id = 'ai-evidence-9'; p.links.ai_evidence = '/api/ai-evidence/ai-evidence-1';
    expect(() => parseInterpretation(p, 'ai-evidence-1')).toThrow();
  });
  it('keeps numeric and backend-confirmed event aliases explicit', () => {
    const p = example('ai-evidence-detail'); p.data.evidence_id = 'ai-evidence-9'; p.links.ai_evidence = '/api/ai-evidence/event-1';
    expect(parseInterpretation(p, '9').alias).toBe(true); expect(parseInterpretation(p, 'event-1').alias).toBe(true);
    delete p.links.ai_evidence; expect(() => parseInterpretation(p, 'event-1')).toThrow();
  });
  it.each(['../a', 'AAPL?x=1', 'AAPL/path', 'AAPL%2f', ' AAPL', 'UNKNOWN'])('rejects unsafe company navigation %s', value => expect(stockSymbol(value)).toBeNull());
});
describe('bounded read transport', () => {
  it('invalid path fails before network access', async () => {
    const fetcher = vi.fn(); expect((await loadCompany('../admin', { fetcher })).issue).toBe('identifier'); expect(fetcher).not.toHaveBeenCalled();
  });
  it.each([404, 403, 503])('HTTP %s cannot return synthetic company data or disclose error bodies', async status => {
    const result = await loadCompany('AAPL', { fetcher: vi.fn(async () => new Response('private-error-secret', { status })) as typeof fetch });
    expect(result.issue).toBe(status === 404 ? 'not-found' : 'http'); expect(result.data).toBeNull(); expect(JSON.stringify(result)).not.toContain('private-error-secret');
  });
  it('sends server-side read credentials, blocks redirects and avoids recommendation enrichment', async () => {
    vi.stubEnv('STOCKANALYSIS_FRONTEND_API_READ_TOKEN', 'private-read');
    const fetcher = vi.fn(async () => Response.json(example('stock-detail'))) as typeof fetch;
    const result = await loadCompany('AAPL', { fetcher });
    expect(result.issue).toBeNull(); expect(fetcher).toHaveBeenCalledTimes(1);
    expect(fetcher).toHaveBeenCalledWith(expect.stringContaining('/api/stocks/AAPL'), expect.objectContaining({ method: 'GET', redirect: 'error', cache: 'no-store' }));
    expect(JSON.stringify(result)).not.toContain('private-read');
  });
  it('optional context failure remains separate from primary analysis', async () => {
    const context = await loadCompanyNeighborhood('AAPL', 'instrument-501', { fetcher: vi.fn(async () => new Response('', { status: 503 })) as typeof fetch });
    expect(context.issue).toBe('http');
    expect((await loadCompany('AAPL', { fetcher: vi.fn(async () => Response.json(example('stock-detail'))) as typeof fetch })).data?.symbol).toBe('AAPL');
  });
  it('response-body stalls are aborted and leave no active timers', async () => {
    vi.useFakeTimers(); let signal: AbortSignal | null | undefined;
    const fetcher = vi.fn(async (_url, init) => { signal = init?.signal; return { ok: true, json: () => new Promise(() => {}) }; }) as unknown as typeof fetch;
    const promise = loadInterpretation('event-1', { fetcher, timeoutMs: 20 }); await vi.advanceTimersByTimeAsync(21);
    expect((await promise).issue).toBe('timeout'); expect(signal?.aborted).toBe(true); expect(vi.getTimerCount()).toBe(0);
  });
});
