import { describe, it, expect, vi } from 'vitest';
import { loadEvaluationHistory, validId, displayPercent, displayValue } from './evaluation-history';
const list = { contract_version: 'recommendation-eval-history-v1', source: 'live', read_only: true, history_basis: 'evaluation_time', runs: [{ eval_run_id: '9223372036854775807', snapshot_count: 0, snapshot_state: 'recorded_empty' }], pagination: { next_cursor: null, has_more: false, returned_count: 1 } };
describe('evaluation history reads', () => {
  it('preserves bigint IDs and zero/null without coercing missing data', async () => {
    const fetcher = vi.fn().mockResolvedValue(new Response(JSON.stringify(list)));
    const result = await loadEvaluationHistory({ fetcher });
    expect(result.history?.runs?.[0].eval_run_id).toBe('9223372036854775807');
    expect(displayPercent(0)).toBe('0.00%p'); expect(displayPercent(null)).toBe('미측정'); expect(displayValue(0)).toBe('0');
    expect(fetcher.mock.calls[0][1]).toMatchObject({ method: 'GET', cache: 'no-store', redirect: 'error' });
  });
  it('rejects malformed selectors before IO', async () => {
    const fetcher = vi.fn();
    for (const cursor of ['0', '01', '9223372036854775808', ['1','2'], '1/2']) expect((await loadEvaluationHistory({ cursor, fetcher })).issue).toBe('invalid');
    expect(fetcher).not.toHaveBeenCalled(); expect(validId('9223372036854775807')).toBe(true);
  });
  it('keeps API failures and absent history distinct', async () => {
    for (const [status, issue] of [[404,'not_found'],[503,'unavailable'],[401,'unavailable']] as const) {
      const result = await loadEvaluationHistory({ fetcher: vi.fn().mockResolvedValue(new Response('', { status })) });
      expect(result.issue).toBe(issue); expect(result.history).toBeNull();
    }
  });
  it('rejects wrong family, malformed paging and duplicate IDs', async () => {
    for (const raw of [{...list, source:'fixture'}, {...list, runs:[list.runs[0],list.runs[0]]}, {...list,pagination:{...list.pagination,has_more:true}}]) {
      expect((await loadEvaluationHistory({ fetcher: vi.fn().mockResolvedValue(new Response(JSON.stringify(raw))) })).issue).toBe('unavailable');
    }
  });
  it('bounds even an uncooperative fetcher', async () => {
    expect((await loadEvaluationHistory({ fetcher: vi.fn().mockReturnValue(new Promise(()=>{})), timeoutMs: 10 })).issue).toBe('unavailable');
  });
});
