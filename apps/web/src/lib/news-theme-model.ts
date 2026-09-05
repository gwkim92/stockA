import { dateOnly, identifier, numeric, object, recordedDate, rows, strings, text, type Row } from './research-reader-model';

export type SearchInput = Record<string, string | string[] | undefined>;
export type NewsQuery = { date: string; symbol: string; theme: string; cursor: string };
export const NEWS_SCOPES = [['all', '전체'], ['evidence', '해석 미연결'], ['source', '원천 미연결'], ['restricted', '차단·보류']] as const;
export type NewsScope = typeof NEWS_SCOPES[number][0];
export const fraction = (v: unknown): number | null => {
  const n = numeric(v);
  return n !== null && n >= 0 && n <= 1 ? n : null;
};
export const scoreText = (v: unknown) => numeric(v) === null ? '미측정' : numeric(v)!.toLocaleString('ko-KR', { maximumFractionDigits: 3 });
export const ratioText = (v: unknown) => fraction(v) === null ? '미측정' : `${(fraction(v)! * 100).toLocaleString('ko-KR', { maximumFractionDigits: 1 })}%`;
export function resourceId(value: unknown): string | null {
  const id = identifier(value);
  return id && !/^(?:unknown|unclassified|missing|unavailable|(?:event|source-document|ai-evidence|instrument|thesis|recommendation)-unknown)$/i.test(id) ? id : null;
}
export function symbolCode(value: unknown): string | null {
  const id = resourceId(value);
  return id && /^[a-z0-9][a-z0-9.-]{0,19}$/i.test(id) ? id.toUpperCase() : null;
}
export function cursorValue(value: unknown): string | null {
  return typeof value === 'string' && /^[A-Za-z0-9_-]{1,512}={0,2}$/.test(value) ? value : null;
}
export function requestDate(value: unknown, today: string): string | null {
  if (value === undefined) return today;
  const date = dateOnly(value);
  return date && date <= today ? date : null;
}
export function parseNewsQuery(input: SearchInput, today: string): NewsQuery | null {
  const date = requestDate(input.date, today);
  if (!date) return null;
  const symbol = input.symbol === undefined || input.symbol === '' ? '' : symbolCode(input.symbol);
  const theme = input.theme === undefined || input.theme === '' ? '' : resourceId(input.theme);
  const cursor = input.cursor === undefined || input.cursor === '' ? '' : cursorValue(input.cursor);
  return symbol === null || theme === null || cursor === null ? null : { date, symbol, theme, cursor };
}
export function newsHref(query: NewsQuery, options: { q?: string; scope?: string; cursor?: string } = {}): string {
  const params = new URLSearchParams({ date: query.date });
  if (query.symbol) params.set('symbol', query.symbol);
  if (query.theme) params.set('theme', query.theme);
  const cursor = options.cursor ?? query.cursor;
  if (cursor) params.set('cursor', cursor);
  if (options.q) params.set('q', options.q.slice(0, 100));
  if (options.scope && options.scope !== 'all') params.set('scope', options.scope);
  return `/events?${params}`;
}
export function themeHref(key: unknown, date: string): string | null {
  const id = resourceId(key);
  return id ? `/themes/${encodeURIComponent(id)}?${new URLSearchParams({ date })}` : null;
}
export function recordHref(resource: 'stocks' | 'theses' | 'recommendations' | 'ai-evidence' | 'source-documents', value: unknown): string | null {
  const id = resource === 'stocks' ? symbolCode(value) : resourceId(value);
  return id ? `/${resource}/${encodeURIComponent(id)}` : null;
}
export function isRestricted(row: Row): boolean {
  return row.ai_evidence_type === 'news_event_candidate_rejected'
    || ['validator_blocked', 'low_signal_suppressed', 'blocked', 'rejected'].includes(text(row.quality_gate, ''));
}
export type NewsItem = {
  id: string; title: string; originalTitle: string; summary: string | null; at: string | null;
  symbol: string | null; theme: string | null; themeName: string; type: string; direction: string;
  score: number | null; confidence: number | null; gate: string; restricted: boolean;
  evidence: string | null; source: string | null;
  related: { id: string | null; title: string; reason: string; relation: string }[] | null;
};
function newsItem(row: Row): NewsItem {
  const id = resourceId(row.event_id);
  if (!id) throw new Error('event identity unavailable');
  return {
    id, title: text(row.korean_title, text(row.title, '제목 미제공')), originalTitle: text(row.title, '원제 미제공'),
    summary: text(row.korean_summary, '') || null, at: recordedDate(row.event_at),
    symbol: symbolCode(row.symbol), theme: resourceId(row.theme_key), themeName: text(row.theme_name, text(row.theme_key, '테마 미분류')),
    type: text(row.event_type, '미분류'), direction: text(row.impact_direction, '미확인'),
    score: numeric(row.impact_score), confidence: fraction(row.ai_evidence_confidence), gate: text(row.quality_gate, '미확인'),
    restricted: isRestricted(row), evidence: resourceId(row.ai_evidence_id), source: resourceId(row.source_document_id),
    related: rows(row.related_events)?.map(item => ({ id: resourceId(item.event_id), title: text(item.korean_title, text(item.title, '제목 미제공')), reason: text(item.reason, '관계 설명 미제공'), relation: text(item.relation_type, '미분류') })) ?? null,
  };
}
export type NewsPage = { asOf: string | null; items: NewsItem[]; hasMore: boolean | null; nextCursor: string | null; pagingIssue: boolean };
export function parseNewsPage(payload: unknown, query: NewsQuery): NewsPage {
  const envelope = object(payload), raw = object(envelope.data), records = rows(raw.events), filters = object(raw.filters);
  if (!records) throw new Error('event list unavailable');
  if ((query.symbol && symbolCode(filters.symbol) !== query.symbol) || (query.theme && filters.theme_key !== query.theme)) throw new Error('event filter mismatch');
  const pagination = object(envelope.pagination);
  const hasMore = typeof pagination.has_more === 'boolean' ? pagination.has_more : null;
  const returnedCursor = cursorValue(pagination.next_cursor);
  const nextCursor = hasMore === true && returnedCursor !== query.cursor ? returnedCursor : null;
  // Rows can repeat an event with another instrument/source relation. Preserve them.
  return { asOf: dateOnly(raw.as_of_date), items: records.map(newsItem), hasMore, nextCursor,
    pagingIssue: hasMore === null || (hasMore === true && !nextCursor) };
}
export function filterNews(items: readonly NewsItem[], query: string, scope: string): NewsItem[] {
  const q = query.trim().toLocaleLowerCase();
  return items.filter(item => [item.title, item.originalTitle, item.summary, item.symbol, item.themeName, item.id].join(' ').toLocaleLowerCase().includes(q)
    && (scope === 'restricted' ? item.restricted : scope === 'evidence' ? !item.evidence : scope === 'source' ? !item.source : true));
}
export type ThemeCompany = { id: string; symbol: string | null; strength: number | null; thesis: string | null; recommendation: string | null };
export type ThemeData = {
  key: string; name: string; asOf: string | null; strategy: string; horizon: string;
  state: string | null; previous: string | null; score: number | null; confidence: number | null;
  features: { key: string; name: string; value: number | null }[];
  history: { date: string | null; state: string | null; confidence: number | null }[] | null;
  companies: ThemeCompany[] | null; events: NewsItem[] | null; notes: string[] | null;
};
function stateValue(value: unknown): string | null {
  const state = text(value, '');
  return state && !['unknown', 'unavailable', 'missing', 'not_available'].includes(state.toLowerCase()) ? state : null;
}
export function parseTheme(payload: unknown, requested: string): ThemeData {
  const raw = object(object(payload).data);
  if (!resourceId(requested) || raw.theme_key !== requested) throw new Error('theme identity mismatch');
  const companies = rows(raw.linked_instruments);
  if (companies?.some(row => !resourceId(row.instrument_id))) throw new Error('theme company identity unavailable');
  return {
    key: requested, name: text(raw.theme_name, requested), asOf: dateOnly(raw.as_of_date), strategy: text(raw.strategy_name), horizon: text(raw.horizon_type),
    state: stateValue(raw.state), previous: stateValue(raw.previous_state), score: numeric(raw.cycle_score), confidence: fraction(raw.confidence),
    features: [['event_intensity', '뉴스 특징'], ['price_momentum', '가격 특징'], ['fundamental_quality', '기업 품질 특징']].map(([key, name]) => ({ key, name, value: fraction(object(raw.features)[key]) })),
    history: rows(raw.cycle_history)?.map(row => ({ date: dateOnly(row.as_of_date), state: stateValue(row.state), confidence: fraction(row.confidence) })) ?? null,
    companies: companies?.map(row => ({ id: row.instrument_id as string, symbol: symbolCode(row.symbol), strength: fraction(row.membership_strength), thesis: resourceId(row.active_thesis_id), recommendation: resourceId(row.latest_recommendation_id) })) ?? null,
    events: rows(raw.supporting_events)?.map(newsItem) ?? null, notes: strings(raw.operator_notes),
  };
}
export function filterCompanies(companies: readonly ThemeCompany[], query: string, missingOnly: boolean): ThemeCompany[] {
  const needle = query.trim().toUpperCase();
  return companies.filter(row => (row.symbol ?? '').includes(needle) && (!missingOnly || !row.thesis));
}
