/** Read-only presentation: source values, not investment decisions or inferred translations. */
import { count, dateOnly, identifier, knownSymbol, numeric, object, recordedDate, route, rows, safeApiLink, strings, text, type Row } from './research-reader-model';
export { count, object, rows, strings, text };
export const fraction = (value: unknown) => {
  const n = numeric(value);
  return n !== null && n >= 0 && n <= 1 ? n : null;
};
export const decimal = (value: unknown) => numeric(value) === null ? '미측정' : numeric(value)!.toLocaleString('ko-KR', { maximumFractionDigits: 3 });
export const percentage = (value: unknown) => numeric(value) === null ? '미측정' : `${(numeric(value)! * 100).toLocaleString('ko-KR', { maximumFractionDigits: 2 })}%`;
export const measuredConfidence = (value: unknown) => fraction(value) === null ? '미측정' : percentage(value);
export function stockSymbol(value: unknown): string | null {
  return typeof value === 'string' && /^[A-Za-z0-9][A-Za-z0-9.-]{0,19}$/.test(value) && knownSymbol(value) ? value.toUpperCase() : null;
}
export type PricePoint = { date: string; close: number | null };
export function priceObservations(value: unknown, asOf: string | null) {
  const input = rows(value);
  if (!input) return { points: null, excluded: null };
  const dates = input.map(row => dateOnly(row.trade_date));
  const counts = new Map<string, number>();
  for (const date of dates) if (date) counts.set(date, (counts.get(date) ?? 0) + 1);
  let excluded = 0;
  const ambiguous = new Set<string>();
  const points: PricePoint[] = [];
  input.forEach((row, index) => {
    const date = dates[index];
    if (!date || (asOf && date > asOf)) { excluded++; return; }
    if (counts.get(date)! > 1) {
      excluded++;
      if (!ambiguous.has(date)) { points.push({ date, close: null }); ambiguous.add(date); }
      return;
    }
    const close = numeric(row.close);
    points.push({ date, close: close !== null && close > 0 ? close : null });
  });
  return { points: points.sort((a, b) => a.date.localeCompare(b.date)), excluded };
}
export type CompanyData = {
  symbol: string; id: string; name: string; market: string; currency: string | null; asOf: string | null;
  price: number | null; priceDate: string | null; daily: number | null; points: PricePoint[] | null; excludedPrices: number | null;
  recommendation: Row | null; recommendationState: 'linked' | 'none' | 'unknown'; thesisHref: string | null;
  position: Row | null; positionState: 'held' | 'none' | 'unknown';
  research: Row; financial: Row; valuation: Row; industry: Row; fund: Row | null; fundKind: boolean;
  guard: Row; blocked: boolean; provider: Row; broker: Row;
  events: Row[] | null; macro: Row[] | null; correlations: Row[] | null;
};
export function parseCompany(payload: unknown, requested: string): CompanyData {
  const raw = object(object(payload).data), symbol = stockSymbol(raw.symbol);
  if (!symbol || symbol !== stockSymbol(requested) || !identifier(raw.instrument_id) || raw.instrument_id === 'instrument-unknown') throw new Error('company identity mismatch');
  const asOf = dateOnly(raw.as_of_date), price = object(raw.latest_price), recommendation = object(raw.recommendation), position = object(raw.position);
  const observations = priceObservations(raw.price_bars, asOf);
  const recommendationId = identifier(recommendation.recommendation_id);
  const qty = numeric(position.quantity);
  const guard = object(raw.professional_source_guardrail);
  const fund = Object.keys(object(raw.fund_instrument_analysis)).length ? object(raw.fund_instrument_analysis) : null;
  return {
    symbol, id: raw.instrument_id as string, name: text(raw.name, symbol), market: text(raw.market_code),
    currency: /^[A-Z]{3}$/.test(text(raw.currency_code, '')) ? raw.currency_code as string : null,
    asOf, price: numeric(price.close) !== null && Number(price.close) > 0 ? Number(price.close) : null,
    priceDate: dateOnly(price.trade_date), daily: dateOnly(price.trade_date) ? numeric(price.change_pct) : null,
    points: observations.points, excludedPrices: observations.excluded,
    recommendation: recommendationId ? recommendation : null,
    recommendationState: recommendationId ? 'linked' : raw.recommendation === null ? 'none' : 'unknown',
    // Only use an explicitly linked record, never the first thesis in a neighborhood.
    thesisHref: route('theses', recommendation.linked_thesis_id) ?? route('theses', position.linked_thesis_id),
    position: Object.keys(position).length ? position : null,
    positionState: qty !== null && qty !== 0 ? 'held' : raw.position === null || qty === 0 ? 'none' : 'unknown',
    research: object(raw.equity_research), financial: object(raw.financial_statement_model), valuation: object(raw.valuation_target_range),
    industry: object(raw.industry_competitive_position), fund,
    fundKind: !!fund || guard.status === 'fund_or_etf_company_model_not_applicable',
    guard, blocked: guard.blocked === true || ['blocked', 'source_blocked', 'blocked_source'].includes(text(guard.status, '')),
    provider: object(object(raw.market_data_provider).analysis_price_source), broker: object(raw.toss_provider_evidence),
    events: rows(raw.recent_events), macro: rows(raw.macro_flow_impacts), correlations: rows(raw.market_correlations),
  };
}
export type Neighborhood = { asOf: string | null; themes: Row[] | null; events: Row[] | null };
export function parseNeighborhood(payload: unknown, symbol: string, instrumentId: string): Neighborhood {
  const raw = object(object(payload).data), instrument = object(raw.instrument);
  if (stockSymbol(raw.symbol) !== symbol || stockSymbol(instrument.symbol) !== symbol || instrument.instrument_id !== instrumentId || instrument.found !== true) throw new Error('neighborhood identity mismatch');
  return { asOf: dateOnly(raw.as_of_date), themes: rows(raw.themes), events: rows(raw.events) };
}
export type Interpretation = {
  id: string; requested: string; alias: boolean; title: string; originalTitle: string; summary: string | null; eventAt: string | null;
  symbol: string | null; classification: Row; run: Row; candidate: Row | null; cluster: Row | null;
  fields: Row[] | null; chunks: Row[] | null; clusterEvents: Row[] | null; validator: Row;
  blocked: boolean; reviewLabel: string; sourceHref: string | null; sourceMismatch: boolean;
  thesisHref: string | null; recommendationHref: string | null; context: Row; trace: Row; notes: string[] | null;
};
export function parseInterpretation(payload: unknown, requested: string): Interpretation {
  const envelope = object(payload), raw = object(envelope.data), links = object(envelope.links);
  const id = identifier(raw.evidence_id);
  const numericAlias = /^\d+$/.test(requested) && id === `ai-evidence-${requested}`;
  const resolverAlias = !requested.startsWith('ai-evidence-') && /^ai-evidence-\d+$/.test(id ?? '')
    && safeApiLink(links.ai_evidence, 'ai-evidence') === route('ai-evidence', requested);
  if (!id || id === 'ai-evidence-unknown' || (id !== requested && !numericAlias && !resolverAlias) || !text(raw.title, '')) throw new Error('evidence identity mismatch');
  const chunks = rows(raw.source_chunks);
  if (chunks && (chunks.some(row => !identifier(row.chunk_id)) || new Set(chunks.map(row => row.chunk_id)).size !== chunks.length)) throw new Error('ambiguous source chunks');
  const run = object(raw.extraction_run), trace = object(raw.visibility_trace), validator = object(trace.validator);
  const blocked = raw.evidence_type === 'news_event_candidate_rejected' || run.quality_gate === 'validator_blocked' || validator.blocked === true;
  const sourceId = identifier(raw.source_document_id);
  const direct = sourceId && sourceId !== 'source-document-unknown' ? route('source-documents', sourceId) : null;
  const sourceLink = safeApiLink(links.source_document, 'source-documents');
  const sourceMismatch = !!direct && !!sourceLink && direct !== sourceLink;
  return {
    id, requested, alias: id !== requested, title: text(raw.korean_title, text(raw.title)), originalTitle: text(raw.title),
    summary: text(raw.korean_summary, '') || null, eventAt: recordedDate(raw.event_at), symbol: knownSymbol(object(raw.instrument).symbol),
    classification: object(raw.classification), run, validator, blocked,
    reviewLabel: blocked ? '추천 입력 제외 · 차단 기록' : run.quality_gate === 'ai_review_passed' ? '원천 판정: AI 검토 통과' : '사용 전 검토 필요',
    candidate: Object.keys(object(raw.news_candidate)).length ? object(raw.news_candidate) : null,
    cluster: Object.keys(object(raw.cluster_summary)).length ? object(raw.cluster_summary) : null,
    fields: rows(raw.extracted_fields), chunks, clusterEvents: rows(raw.cluster_events), sourceMismatch,
    sourceHref: sourceMismatch ? null : direct,
    thesisHref: safeApiLink(links.thesis, 'theses'), recommendationHref: safeApiLink(links.recommendation, 'recommendations'),
    context: object(raw.retrieval_context_summary), trace, notes: strings(raw.audit_notes),
  };
}
/** Links only to an exact returned chunk, never a keyword-based substitute. */
export function chunkTarget(chunks: Row[] | null, requested: unknown): string | null {
  if (!identifier(requested)) return null;
  const index = chunks?.findIndex(chunk => chunk.chunk_id === requested) ?? -1;
  return index < 0 ? null : `#evidence-chunk-${index}`;
}
