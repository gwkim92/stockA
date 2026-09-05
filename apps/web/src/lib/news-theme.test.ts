// @vitest-environment node
import { readFileSync } from 'node:fs';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { cursorValue, filterCompanies, filterNews, isRestricted, newsHref, parseNewsPage, parseNewsQuery, parseTheme, ratioText, recordHref, requestDate, themeHref, type NewsQuery } from './news-theme-model';
import { loadNews, loadTheme } from './news-theme-data';
const sample = (name: string) => JSON.parse(readFileSync(`../../docs/api/frontend/examples/${name}.json`, 'utf8'));
const today = '2026-09-05';
const query: NewsQuery = { date: today, symbol: '', theme: '', cursor: '' };
const now = new Date(`${today}T12:00:00Z`);
afterEach(() => { vi.useRealTimers(); vi.unstubAllEnvs(); });

describe('saved API contracts without invented interpretation', () => {
  it('reads the event example, preserves originals and does not use fetch time', () => {
    const input = sample('event-list'), before = JSON.stringify(input), data = parseNewsPage(input, query);
    expect(data.items).toHaveLength(2); expect(data.items[0].title).toBe(input.data.events[0].title);
    expect(data.items[0].summary).toBeNull(); expect(data.asOf).toBe('2024-11-01');
    expect(JSON.stringify(input)).toBe(before);
  });
  it('reads the complete saved theme without changing its values', () => {
    const input = sample('theme-detail'), before = JSON.stringify(input), data = parseTheme(input, 'ANNUAL_REPORTING');
    expect(data.companies?.[0].symbol).toBe('AAPL'); expect(data.score).toBe(0.74);
    expect(data.history).toHaveLength(2); expect(JSON.stringify(input)).toBe(before);
  });
  it.each([undefined, null, {}, [null], [{}]].map(events => ({ events })))('missing/malformed primary events are not an empty success: $events', ({ events }) => {
    expect(() => parseNewsPage({ data: { events } }, query)).toThrow();
  });
  it('distinguishes empty primary events, missing optional theme data and measured zero', () => {
    expect(parseNewsPage({ data: { events: [] } }, query).items).toEqual([]);
    const t = parseTheme({ data: { theme_key: 'semiconductor', features: { event_intensity: 0 } } }, 'semiconductor');
    expect(t.events).toBeNull(); expect(t.companies).toBeNull(); expect(t.history).toBeNull();
    expect(t.features.map(f => f.value)).toEqual([0, null, null]); expect(t.confidence).toBeNull();
    expect(ratioText(0)).toBe('0%'); expect(ratioText(null)).toBe('미측정');
  });
  it('keeps different source relations for the same event instead of dropping one', () => {
    const input = sample('event-list'); input.data.events.push({ ...input.data.events[0], source_document_id: 'another-source' });
    expect(parseNewsPage(input, query).items).toHaveLength(3);
  });
  it('does not export unneeded internal fields to a client projection', () => {
    const input = sample('event-list'); Object.assign(input.data.events[0], { storage_uri: 'internal-only', debug_token: 'private-token' });
    expect(JSON.stringify(parseNewsPage(input, query))).not.toMatch(/internal-only|private-token/);
  });
  it('a Korean title does not imply a stored Korean summary', () => {
    const input = sample('event-list'); input.data.events[0].korean_title = '저장 제목';
    const row = parseNewsPage(input, query).items[0];
    expect(row.title).toBe('저장 제목'); expect(row.summary).toBeNull(); expect(row.originalTitle).toBe(input.data.events[0].title);
  });
  it('rejected type overrides a passed quality flag', () => {
    expect(isRestricted({ ai_evidence_type: 'news_event_candidate_rejected', quality_gate: 'ai_review_passed' })).toBe(true);
    expect(isRestricted({ quality_gate: 'low_signal_suppressed' })).toBe(true); expect(isRestricted({})).toBe(false);
  });
  it('requires the exact theme identity', () => expect(() => parseTheme(sample('theme-detail'), 'different-theme')).toThrow());
  it('does not synthesize state transitions or discard ambiguous history', () => {
    const input = sample('theme-detail'); input.data.previous_state = 'unknown';
    input.data.cycle_history.push({ as_of_date: '2024-11-01', state: 'unknown', confidence: null }, { as_of_date: '2026-02-30', state: 'forming', confidence: 3 });
    const t = parseTheme(input, 'ANNUAL_REPORTING');
    expect(t.previous).toBeNull(); expect(t.history).toHaveLength(4);
    expect(t.history?.[2].state).toBeNull(); expect(t.history?.[3]).toMatchObject({ date: null, confidence: null });
    expect(t).not.toHaveProperty('transitionCount');
  });
});

describe('query and source-bounded navigation', () => {
  it.each(['2026-02-30', '2026-09-06', '', ['2026-09-01', today], `${today}junk`].map(date => ({ date })))('rejects invalid or duplicate date $date', ({ date }) => expect(requestDate(date, today)).toBeNull());
  it('defaults only an absent date and preserves a valid historical cutoff', () => {
    expect(requestDate(undefined, today)).toBe(today); expect(requestDate('2024-11-01', today)).toBe('2024-11-01');
  });
  it.each([{ symbol: ['AAPL', 'MSFT'] }, { theme: '../private' }, { symbol: 'AAPL?x=1' }, { cursor: 'https://example.org' }, { date: [today] }])('rejects unsafe or repeated server input %s', input => expect(parseNewsQuery(input, today)).toBeNull());
  it('uses the server-returned cursor only, with local filters and date retained', () => {
    const href = newsHref({ ...query, symbol: 'AAPL', theme: 'ANNUAL_REPORTING', cursor: 'old' }, { cursor: 'next', q: 'cash flow', scope: 'source' });
    const p = new URL(href, 'https://local.test').searchParams;
    expect(p.get('date')).toBe(today); expect(p.get('cursor')).toBe('next'); expect(p.get('q')).toBe('cash flow');
    expect(new URL(newsHref(query, { cursor: '' }), 'https://local.test').searchParams.has('cursor')).toBe(false);
  });
  it.each(['a/b', 'a?x=1', 'x'.repeat(515), '', 7])('cannot use an unsafe next cursor %s', value => expect(cursorValue(value)).toBeNull());
  it('a missing or repeated next cursor is incomplete paging, not the last page', () => {
    const input = sample('event-list'); input.pagination.has_more = true; input.pagination.next_cursor = null;
    expect(parseNewsPage(input, query)).toMatchObject({ hasMore: true, nextCursor: null, pagingIssue: true });
    input.pagination.next_cursor = 'repeat'; expect(parseNewsPage(input, { ...query, cursor: 'repeat' }).pagingIssue).toBe(true);
    delete input.pagination; expect(parseNewsPage(input, query)).toMatchObject({ hasMore: null, pagingIssue: true });
  });
  it('server filter mismatch cannot silently show an unrelated page', () => {
    expect(() => parseNewsPage(sample('event-list'), { ...query, symbol: 'MSFT' })).toThrow();
    expect(() => parseNewsPage(sample('event-list'), { ...query, theme: 'other' })).toThrow();
  });
  it('builds only existing explicit resource links, preserving the date on themes', () => {
    expect(themeHref('ANNUAL_REPORTING', '2024-11-01')).toBe('/themes/ANNUAL_REPORTING?date=2024-11-01');
    expect(recordHref('stocks', 'aapl')).toBe('/stocks/AAPL'); expect(recordHref('ai-evidence', 'ai-evidence-unknown')).toBeNull();
    expect(recordHref('source-documents', 'doc?token=secret')).toBeNull(); expect(themeHref('UNCLASSIFIED', today)).toBeNull();
  });
  it('literal text and triage filters preserve source order and input values', () => {
    const data = parseNewsPage(sample('event-list'), query), before = JSON.stringify(data);
    expect(filterNews(data.items, 'aapl', 'all')).toHaveLength(1);
    expect(filterNews(data.items, '', 'evidence').map(row => row.symbol)).toEqual(['BABA']);
    expect(filterNews(data.items, '.*', 'all')).toHaveLength(0); expect(JSON.stringify(data)).toBe(before);
  });
  it('connected company filters do not create a missing thesis', () => {
    const data = parseTheme(sample('theme-detail'), 'ANNUAL_REPORTING');
    expect(filterCompanies(data.companies!, 'AAPL', false)).toHaveLength(1); expect(filterCompanies(data.companies!, '', true)).toHaveLength(0);
  });
});

describe('read-only date and paging transport', () => {
  it('rejects bad queries before IO', async () => {
    const fetcher = vi.fn(); const result = await loadNews({ date: '2026-02-30' }, { now, fetcher });
    expect(result.issue).toBe('query'); expect(fetcher).not.toHaveBeenCalled();
  });
  it('sends actual date, symbol, theme and returned cursor in a single GET', async () => {
    const input = sample('event-list'); input.data.filters = { symbol: 'AAPL', theme_key: 'ANNUAL_REPORTING' };
    vi.stubEnv('STOCKANALYSIS_FRONTEND_API_READ_TOKEN', 'private-read-token');
    const fetcher = vi.fn(async () => Response.json(input)) as typeof fetch;
    const result = await loadNews({ date: '2024-11-01', symbol: 'aapl', theme: 'ANNUAL_REPORTING', cursor: 'YWJj' }, { now, fetcher });
    expect(result.issue).toBeNull(); expect(fetcher).toHaveBeenCalledTimes(1);
    const [url, init] = vi.mocked(fetcher).mock.calls[0]; const params = new URL(String(url)).searchParams;
    expect(Object.fromEntries(params)).toMatchObject({ asOfDate: '2024-11-01', symbol: 'AAPL', themeKey: 'ANNUAL_REPORTING', cursor: 'YWJj', limit: '50' });
    expect(init).toMatchObject({ method: 'GET', cache: 'no-store', redirect: 'error', headers: { Authorization: 'Bearer private-read-token' } });
    expect(JSON.stringify(result)).not.toContain('private-read-token');
  });
  it.each([404, 403, 503])('HTTP %s remains a sanitized failure', async status => {
    const result = await loadNews({}, { now, fetcher: vi.fn(async () => new Response('private-error', { status })) as typeof fetch });
    expect(result.data).toBeNull(); expect(result.issue).toBe(status === 404 ? 'not-found' : 'http'); expect(JSON.stringify(result)).not.toContain('private-error');
  });
  it('malformed JSON and invalid theme IDs do not produce a fallback theme', async () => {
    const fetcher = vi.fn(async () => new Response('not-json')) as typeof fetch;
    expect((await loadTheme('ANNUAL_REPORTING', {}, { now, fetcher })).issue).toBe('invalid');
    expect((await loadTheme('../other', {}, { now, fetcher })).issue).toBe('identifier'); expect(fetcher).toHaveBeenCalledTimes(1);
  });
  it('stalled response bodies are aborted and the deadline is cleaned up', async () => {
    vi.useFakeTimers(); let signal: AbortSignal | null | undefined;
    const fetcher = vi.fn(async (_url, init) => { signal = init?.signal; return { ok: true, json: () => new Promise(() => {}) }; }) as unknown as typeof fetch;
    const pending = loadNews({}, { now, fetcher, timeoutMs: 20 }); await vi.advanceTimersByTimeAsync(21);
    expect((await pending).issue).toBe('timeout'); expect(signal?.aborted).toBe(true); expect(vi.getTimerCount()).toBe(0);
  });
});
