import { identifier } from './research-reader-model';
import { parseCompany, parseInterpretation, parseNeighborhood, stockSymbol, type CompanyData, type Interpretation, type Neighborhood } from './company-evidence-model';
export type DetailIssue = 'identifier' | 'not-found' | 'http' | 'network' | 'invalid' | 'timeout';
export type DetailResult<T> = { data: T | null; issue: DetailIssue | null };
export type ReadOptions = { fetcher?: typeof fetch; timeoutMs?: number };
/** No operational/broker writes; deadline includes JSON body consumption. */
async function read<T>(path: string, parse: (payload: unknown) => T, options: ReadOptions = {}): Promise<DetailResult<T>> {
  const base = (process.env.STOCKANALYSIS_FRONTEND_API_BASE_URL ?? 'http://127.0.0.1:8765').replace(/\/$/, '');
  const token = process.env.STOCKANALYSIS_FRONTEND_API_READ_TOKEN;
  const controller = new AbortController();
  let issue: DetailIssue = 'network';
  let timer: ReturnType<typeof setTimeout> | undefined;
  const deadline = new Promise<never>((_, reject) => {
    timer = setTimeout(() => { issue = 'timeout'; controller.abort(); reject(new Error('deadline')); }, options.timeoutMs ?? 5000);
  });
  try {
    const load = async () => {
      const response = await (options.fetcher ?? fetch)(`${base}${path}`, { method: 'GET', cache: 'no-store', redirect: 'error', signal: controller.signal,
        headers: { Accept: 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) } });
      if (!response.ok) { issue = response.status === 404 ? 'not-found' : 'http'; throw new Error('unavailable'); }
      try { return parse(await response.json()); }
      catch { if (issue !== 'timeout') issue = 'invalid'; throw new Error('invalid payload'); }
    };
    return { data: await Promise.race([load(), deadline]), issue: null };
  } catch { return { data: null, issue }; }
  finally { clearTimeout(timer); }
}
export function loadCompany(symbol: string, options?: ReadOptions): Promise<DetailResult<CompanyData>> {
  const canonical = stockSymbol(symbol);
  return canonical ? read(`/api/stocks/${encodeURIComponent(canonical)}`, payload => parseCompany(payload, canonical), options)
    : Promise.resolve({ data: null, issue: 'identifier' });
}
export function loadInterpretation(id: string, options?: ReadOptions): Promise<DetailResult<Interpretation>> {
  return identifier(id) ? read(`/api/ai-evidence/${encodeURIComponent(id)}`, payload => parseInterpretation(payload, id), options)
    : Promise.resolve({ data: null, issue: 'identifier' });
}
export function loadCompanyNeighborhood(symbol: string, instrumentId: string, options?: ReadOptions): Promise<DetailResult<Neighborhood>> {
  const canonical = stockSymbol(symbol);
  return canonical && identifier(instrumentId) ? read(`/api/ai/evidence-neighborhoods/${encodeURIComponent(canonical)}`, payload => parseNeighborhood(payload, canonical, instrumentId), { timeoutMs: 3000, ...options })
    : Promise.resolve({ data: null, issue: 'identifier' });
}
