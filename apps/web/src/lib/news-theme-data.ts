import { parseNewsPage, parseNewsQuery, parseTheme, requestDate, resourceId, type NewsPage, type NewsQuery, type SearchInput, type ThemeData } from './news-theme-model';

export type SignalIssue = 'query' | 'identifier' | 'not-found' | 'http' | 'network' | 'invalid' | 'timeout';
export type SignalResult<T> = { data: T | null; issue: SignalIssue | null; today: string; requestedDate: string };
type Options = { now?: Date; timeoutMs?: number; fetcher?: typeof fetch };
async function read<T>(path: string, parse: (payload: unknown) => T, options: Options): Promise<{ data: T | null; issue: SignalIssue | null }> {
  const base = (process.env.STOCKANALYSIS_FRONTEND_API_BASE_URL ?? 'http://127.0.0.1:8765').replace(/\/$/, '');
  const token = process.env.STOCKANALYSIS_FRONTEND_API_READ_TOKEN;
  const controller = new AbortController();
  let issue: SignalIssue = 'network';
  let timer: ReturnType<typeof setTimeout> | undefined;
  const deadline = new Promise<never>((_, reject) => {
    timer = setTimeout(() => { issue = 'timeout'; controller.abort(); reject(new Error('deadline')); }, options.timeoutMs ?? 5000);
  });
  try {
    const request = async () => {
      const response = await (options.fetcher ?? fetch)(`${base}${path}`, {
        method: 'GET', cache: 'no-store', redirect: 'error', signal: controller.signal,
        headers: { Accept: 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      });
      if (!response.ok) { issue = response.status === 404 ? 'not-found' : 'http'; throw new Error('unavailable'); }
      try { return parse(await response.json()); }
      catch { if (issue !== 'timeout') issue = 'invalid'; throw new Error('invalid payload'); }
    };
    return { data: await Promise.race([request(), deadline]), issue: null };
  } catch { return { data: null, issue }; }
  finally { clearTimeout(timer); }
}
export async function loadNews(input: SearchInput, options: Options = {}): Promise<SignalResult<NewsPage> & { query: NewsQuery | null }> {
  const today = (options.now ?? new Date()).toISOString().slice(0, 10);
  const query = parseNewsQuery(input, today);
  if (!query) return { data: null, query: null, issue: 'query', today, requestedDate: today };
  const params = new URLSearchParams({ asOfDate: query.date, eventType: 'all', evidenceType: 'all', limit: '50' });
  if (query.symbol) params.set('symbol', query.symbol);
  if (query.theme) params.set('themeKey', query.theme);
  if (query.cursor) params.set('cursor', query.cursor);
  return { ...await read(`/api/events?${params}`, payload => parseNewsPage(payload, query), options), query, today, requestedDate: query.date };
}
export async function loadTheme(key: string, input: SearchInput, options: Options = {}): Promise<SignalResult<ThemeData>> {
  const today = (options.now ?? new Date()).toISOString().slice(0, 10);
  const date = requestDate(input.date, today);
  if (!resourceId(key) || !date) return { data: null, issue: !resourceId(key) ? 'identifier' : 'query', today, requestedDate: today };
  return { ...await read(`/api/themes/${encodeURIComponent(key)}?${new URLSearchParams({ asOfDate: date })}`, payload => parseTheme(payload, key), options), today, requestedDate: date };
}
