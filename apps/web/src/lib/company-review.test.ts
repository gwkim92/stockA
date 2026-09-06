// @vitest-environment node
import { readFileSync } from 'node:fs';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { parseCompany } from './company-evidence-model';
import { CHECKS, draftKey, emptyDraft, exportReview, parseDraft, reviewModel, selectReviewSource } from './company-review-model';
import { loadReviewSource, reviewSnapshot } from './company-review-data';
const example = (name: string) => JSON.parse(readFileSync(`../../docs/api/frontend/examples/${name}.json`, 'utf8'));
const company = () => parseCompany(example('stock-detail'), 'AAPL');
const model = () => reviewModel(company());
const saved = () => ({ ...emptyDraft(model(), reviewSnapshot(model())), savedAt: '2026-09-06T12:00:00Z' });
afterEach(() => { vi.useRealTimers(); vi.unstubAllEnvs(); });
describe('stored research review projection', () => {
  it('uses the saved contract without inventing a research summary or claims', () => {
    const input=company(), before=JSON.stringify(input), view=reviewModel(input);
    expect(view.groups[0].items).toBeNull(); expect(view.summary).toBe('저장된 리서치 요약이 없습니다.');
    expect(view.sources[0].id).toBe(input.events![0].source_document_id); expect(JSON.stringify(input)).toBe(before);
  });
  it('keeps exact source IDs but never turns a news event ID into a document', () => {
    const input=company(); input.events=[{ event_id:'event-1', title:'No document' }]; input.macro=null;
    expect(reviewModel(input).sources).toEqual([]);
  });
  it('preserves model claims and explicitly labels fixture results separately', () => {
    const input=company(); input.research={ provider:'fixture', korean_summary:'stored summary', key_points:['literal claim'], risks:[] };
    const view=reviewModel(input); expect(view.groups[0].items).toEqual(['literal claim']); expect(view.groups[1].items).toEqual([]);
    expect(view.origin).toContain('규칙 기반'); expect(view.summary).toBe('stored summary');
  });
  it('deduplicates document inventory while preserving research/direct/background context', () => {
    const input=company(); input.research.source_document_ids=['doc-1','source-document-unknown','../evil'];
    input.events=[{ source_document_id:'doc-1', title:'Source 1' }]; input.macro=[{ source_document_id:'doc-2', title:'Background' }];
    const sources=reviewModel(input).sources; expect(sources).toHaveLength(2); expect(sources[0].context).toContain('리서치 입력');
    expect(sources[1].context).toBe('시장 배경 연결');
  });
  it('funds use stored exposure/cost/limits rather than company claims and targets', () => {
    const view=reviewModel(parseCompany(example('stock-detail-spy'),'SPY'));
    expect(view.fund).toBe(true); expect(view.groups.map(g=>g.key)).toEqual(['exposure','cost','limits']);
    expect(JSON.stringify(view)).not.toContain('target_base');
  });
  it('omits private adapter extras and keeps explicit source restrictions', () => {
    const input=company(); input.research.debug_token='private-value'; input.blocked=true;
    const view=reviewModel(input); expect(JSON.stringify(view)).not.toContain('private-value'); expect(view.blocked).toBe(true);
  });
  it('changes the bundle fingerprint when a claim, date or linked source changes', () => {
    const a=model(); for(const mutate of [(v:typeof a)=>{v.summary='new'},(v:typeof a)=>{v.asOf='2026-09-06'},(v:typeof a)=>{v.sources=[]}]) {
      const b=structuredClone(a);mutate(b);expect(reviewSnapshot(a)).not.toBe(reviewSnapshot(b));
    }
    expect(reviewSnapshot(a)).toBe(reviewSnapshot(structuredClone(a)));
  });
  it.each(['other-document','../private',['doc-1'],null,''].map(value=>({value})))('refuses unlinked/duplicate source selection $value', ({value}) => {
    expect(selectReviewSource(model(),value)).toEqual({id:null,invalid:true});
  });
  it('chooses a default only when no source was requested', () => {
    const view=model(); expect(selectReviewSource(view,undefined).id).toBe(view.sources[0].id);
    expect(selectReviewSource(view,view.sources[0].id).invalid).toBe(false);
  });
});
describe('browser-local draft contract', () => {
  it('round trips human notes and explicit checkboxes without injecting a conclusion', () => {
    const draft={...saved(),note:'Need more evidence',checks:[CHECKS[0][0]],nextDate:'2026-09-20'};
    expect(parseDraft(JSON.stringify(draft),model())).toEqual(draft);
  });
  it.each([{version:2},{symbol:'MSFT'},{instrumentId:'other'},{snapshot:'fake'},{savedAt:'bad'},
    {asOf:'2026-02-30'},{nextDate:'2026-02-30'},{note:7},{note:'x'.repeat(4001)},
    {checks:['approved']},{checks:['numbers','numbers']},{broker_submit_allowed:true}])('refuses invalid or foreign draft %s', patch => {
    expect(parseDraft(JSON.stringify({...saved(),...patch}),model())).toBeNull();
  });
  it('rejects malformed JSON and oversized blobs without turning them into empty drafts', () => {
    expect(parseDraft('not-json',model())).toBeNull();expect(parseDraft('x'.repeat(25000),model())).toBeNull();
  });
  it('separates drafts by company instrument and symbol', () => {
    expect(draftKey(model())).not.toBe(draftKey({...model(),instrumentId:'other'}));
    expect(draftKey(model())).not.toBe(draftKey({...model(),symbol:'MSFT'}));
  });
  it('old bundle drafts remain readable but are not current matches', () => {
    const draft=saved(), next={...model(),summary:'new narrative'};
    const restored=parseDraft(JSON.stringify(draft),next)!;
    expect(restored.snapshot).not.toBe(reviewSnapshot(next));
  });
  it('stale export excludes current claims and source inventory', () => {
    const text=exportReview({...saved(),snapshot:'a'.repeat(64),note:'old note'}, {...model(),summary:'new-secret-claim'}, reviewSnapshot(model()));
    expect(text).toContain('old note');expect(text).not.toContain('new-secret-claim');expect(text).not.toContain(model().sources[0].id);
  });
  it('exports user markup as literal indented text and separates source inventory from proof', () => {
    const text=exportReview({...saved(),note:'<script>bad()</script>\n# invented heading'},model(),reviewSnapshot(model()));
    expect(text).toContain('    <script>bad()</script>\n    # invented heading');
    expect(text).toContain('개별 주장을 입증하는 인용 목록이 아님');expect(text).toContain('알림 없음');
  });
});
describe('bounded source retrieval', () => {
  it('does no IO for a source not in the company inventory', async () => {
    const fetcher=vi.fn();const result=await loadReviewSource(model(),'private-document',{fetcher});
    expect(result.invalid).toBe(true);expect(fetcher).not.toHaveBeenCalled();
  });
  it('reads only the selected explicit source using existing authenticated GET', async () => {
    const view=model(), selected=view.sources[0].id;
    const data=example('source-document-detail');data.data.document_id=selected;
    vi.stubEnv('STOCKANALYSIS_FRONTEND_API_READ_TOKEN','private-test-token');
    const fetcher=vi.fn(async()=>Response.json(data)) as typeof fetch;
    const result=await loadReviewSource(view,selected,{fetcher});
    expect(result.data?.id).toBe(selected);expect(fetcher).toHaveBeenCalledTimes(1);
    expect(String(vi.mocked(fetcher).mock.calls[0][0])).toContain(encodeURIComponent(selected));
    expect(vi.mocked(fetcher).mock.calls[0][1]).toMatchObject({method:'GET',cache:'no-store',redirect:'error'});
    expect(JSON.stringify(result)).not.toContain('private-test-token');
  });
  it('failed source does not replace the company projection or return raw errors', async () => {
    const view=model(),before=JSON.stringify(view);
    const result=await loadReviewSource(view,undefined,{fetcher:vi.fn(async()=>new Response('secret',{status:503})) as typeof fetch});
    expect(result.issue).toBe('http');expect(result.data).toBeNull();expect(JSON.stringify(view)).toBe(before);
    expect(JSON.stringify(result)).not.toContain('secret');
  });
  it('source response body deadline is bounded and aborted', async () => {
    vi.useFakeTimers();let signal: AbortSignal | null | undefined;
    const fetcher=vi.fn(async(_url,init)=>{signal=init?.signal;return {ok:true,json:()=>new Promise(()=>{})};}) as unknown as typeof fetch;
    const task=loadReviewSource(model(),undefined,{fetcher,timeoutMs:20});await vi.advanceTimersByTimeAsync(21);
    expect((await task).issue).toBe('timeout');expect(signal?.aborted).toBe(true);expect(vi.getTimerCount()).toBe(0);
  });
});
