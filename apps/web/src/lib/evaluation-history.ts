export type RecordValue = Record<string, unknown>;
export type EvalRun = { eval_run_id: string; as_of_date?: string | null; created_at?: string; horizon_days?: number | null; snapshot_count: number; snapshot_state: string; stored_score?: RecordValue };
export type Snapshot = { snapshot_id: string; primary_symbol: string; source_recommendation_id: string; recommendation_action: string; recommendation_total_score: number; snapshot_json: RecordValue };
export type PageInfo = { next_cursor: string | null; has_more: boolean; returned_count: number };
export type History = { runs?: EvalRun[]; run?: EvalRun; snapshots?: Snapshot[]; pagination: PageInfo; history_basis: string };
export type Comparison = { snapshot_id: string; integrity: string; status: string; changes: { field: string; recorded: unknown; current: unknown }[]; later_outcome: RecordValue | null };
export type EvaluationResult = { history: History | null; comparisons: Comparison[]; comparedAt?: string; issue: 'invalid' | 'unavailable' | 'not_found' | null };
export const record = (value: unknown): RecordValue => value !== null && typeof value === 'object' && !Array.isArray(value) ? value as RecordValue : {};
export function validId(value: unknown): value is string {
  return typeof value === 'string' && /^[1-9][0-9]{0,18}$/.test(value) && BigInt(value) <= 9223372036854775807n;
}
export const stateLabel = (value: string) => ({ recorded: '기록 있음', recorded_empty: '평가 대상 없음', legacy_unavailable: '과거 상세 기록 없음', count_mismatch: '기록 수 불일치', changed: '현재 자료 변경', unchanged: '비교 항목 동일', source_missing: '현재 추천 없음', source_identity_mismatch: '종목 연결 불일치', unavailable: '현재 자료 조회 불가', untrusted_history: '기록 확인 필요', verified: '저장 내용 일치', mismatch: '저장 내용 불일치', unverifiable: '저장 내용 검증 불가' }[value] ?? '확인 필요');
export function displayValue(value: unknown): string {
  if (value === null || value === undefined) return '미확인';
  if (typeof value === 'string') return value || '빈 값';
  if (typeof value === 'number') return Number.isFinite(value) ? String(value) : '미확인';
  if (Array.isArray(value)) return value.length ? value.map(displayValue).join(' · ') : '없음';
  return JSON.stringify(value);
}
export function displayPercent(value: unknown): string {
  return typeof value === 'number' && Number.isFinite(value) ? `${value > 0 ? '+' : ''}${(value * 100).toFixed(2)}%p` : '미측정';
}
function validateHistory(raw: unknown, detail: boolean): History {
  const h = record(raw), page = record(h.pagination);
  if (h.contract_version !== 'recommendation-eval-history-v1' || h.source !== 'live' || h.read_only !== true ||
      typeof h.history_basis !== 'string' || typeof page.has_more !== 'boolean' ||
      (page.next_cursor !== null && !validId(page.next_cursor)) || page.has_more !== (page.next_cursor !== null)) throw Error('invalid history');
  const rows = detail ? h.snapshots : h.runs;
  if (!Array.isArray(rows) || rows.length > 25 || page.returned_count !== rows.length) throw Error('invalid page');
  const checkRun = (value: unknown) => { const r = record(value); return validId(r.eval_run_id) && Number.isSafeInteger(r.snapshot_count) && (r.snapshot_count as number) >= 0 && ['recorded','recorded_empty','legacy_unavailable','count_mismatch'].includes(String(r.snapshot_state)); };
  if (detail && !checkRun(h.run)) throw Error('invalid run');
  const ids = new Set<string>();
  for (const rawRow of rows) {
    const row = record(rawRow), id = detail ? row.snapshot_id : row.eval_run_id;
    if (!validId(id) || ids.has(id)) throw Error('invalid row identity');
    ids.add(id);
    if (detail ? (!validId(row.source_recommendation_id) || typeof row.primary_symbol !== 'string' || typeof row.recommendation_action !== 'string' || !row.snapshot_json || typeof row.snapshot_json !== 'object') : !checkRun(row)) throw Error('invalid row');
  }
  return h as unknown as History;
}

export async function loadEvaluationHistory(options: { runId?: unknown; cursor?: unknown; fetcher?: typeof fetch; timeoutMs?: number } = {}): Promise<EvaluationResult> {
  const detail = options.runId !== undefined;
  if ((detail && !validId(options.runId)) || (options.cursor !== undefined && !validId(options.cursor))) return { history: null, comparisons: [], issue: 'invalid' };
  const path = detail ? `/api/recommendation-evaluation-comparisons/eval-run-${options.runId}` : '/api/recommendation-evaluations';
  const query = `?limit=25${options.cursor ? `&${detail ? 'after' : 'before'}=${options.cursor}` : ''}`;
  const base = (process.env.STOCKANALYSIS_FRONTEND_API_BASE_URL ?? 'http://127.0.0.1:8765').replace(/\/$/, '');
  const token = process.env.STOCKANALYSIS_FRONTEND_API_READ_TOKEN;
  const controller = new AbortController();
  let timer: ReturnType<typeof setTimeout> | undefined;
  try {
    const deadline = new Promise<never>((_, reject) => { timer = setTimeout(() => { controller.abort(); reject(Error('timeout')); }, options.timeoutMs ?? 8000); });
    const read = async (): Promise<EvaluationResult> => {
      const response = await (options.fetcher ?? fetch)(base + path + query, { method: 'GET', cache: 'no-store', redirect: 'error', signal: controller.signal, headers: { Accept: 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) } });
      if (!response.ok) return { history: null, comparisons: [], issue: response.status === 404 ? 'not_found' : 'unavailable' };
      const raw = record(await response.json());
      if (detail && (raw.contract_version !== 'recommendation-eval-comparison-v1' || raw.read_only !== true || !Array.isArray(raw.comparisons))) throw Error('invalid comparison');
      const history = validateHistory(detail ? raw.history : raw, detail);
      if (detail && history.run?.eval_run_id !== options.runId) throw Error('wrong run');
      const comparisons = detail ? raw.comparisons as Comparison[] : [];
      if (detail && (comparisons.length !== history.snapshots?.length || comparisons.some((r, i) => r.snapshot_id !== history.snapshots?.[i].snapshot_id || !Array.isArray(r.changes) || r.changes.some(c => !c || typeof c.field !== 'string') || (r.later_outcome !== null && (typeof r.later_outcome !== 'object' || Array.isArray(r.later_outcome))) || !['verified','mismatch','unverifiable'].includes(r.integrity) || !['changed','unchanged','source_missing','source_identity_mismatch','unavailable','untrusted_history'].includes(r.status)))) throw Error('invalid comparisons');
      return { history, comparisons, comparedAt: typeof raw.compared_at === 'string' ? raw.compared_at : undefined, issue: null };
    };
    return await Promise.race([read(), deadline]);
  } catch { return { history: null, comparisons: [], issue: 'unavailable' }; }
  finally { clearTimeout(timer); }
}
