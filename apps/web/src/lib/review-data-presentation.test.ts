// @vitest-environment node
import { execFileSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { parseCompany } from './company-evidence-model';
import { emptyDraft, exportReview, reviewModel, selectReviewSource, type ReviewModel } from './company-review-model';
import { reviewSnapshot } from './company-review-data';
import { reviewGroupMessage, reviewQualityMessages, reviewSourcePresentation, reviewSummaryText } from './review-data-presentation';

const produced = JSON.parse(execFileSync('python3', ['tests/contracts/research-producer.py'], {
  encoding: 'utf8', timeout: 15000, maxBuffer: 1000000,
}));
const example = JSON.parse(readFileSync('../../docs/api/frontend/examples/stock-detail.json', 'utf8'));
function model(research: unknown): ReviewModel {
  return reviewModel(parseCompany({ ...example, data: { ...example.data, equity_research: research, recent_events: [], macro_flow_impacts: [] } }, 'AAPL'));
}
function exported(view: ReviewModel): string {
  const snapshot = reviewSnapshot(view);
  return exportReview(emptyDraft(view, snapshot), view, snapshot);
}

describe('reading and portable-export state continuity', () => {
  it('retains valid claims and source identities without inventing validation', () => {
    const view = model(produced.valid);
    expect(reviewGroupMessage(view, view.groups[0])).toBeNull();
    expect(reviewQualityMessages(view)).toEqual([]);
    expect(reviewSourcePresentation(view).badge).toBe('2개 연결 문서');
    expect(exported(view)).toContain('정상 주장');
    expect(exported(view)).toContain('연결 경로: 리서치 입력 문서');
    expect(exported(view)).not.toContain('## 리서치 데이터 상태');
  });
  it('keeps invalid claims distinct from missing claims in the reading position and export', () => {
    const view = model(produced.malformed), output = exported(view);
    expect(reviewGroupMessage(view, view.groups[0])).toContain('형식 오류');
    expect(output).toContain('형식 오류: 핵심 주장 · 리서치 입력 문서');
    expect(output).not.toContain('synthetic-object');
    expect(output).not.toContain('valid fragment');
    expect(output).not.toContain('source-document-7001');
  });
  it('keeps missing risk data different from a genuinely empty list', () => {
    const view = model(produced.partial), group = view.groups.find(g => g.key === 'risks')!;
    expect(reviewGroupMessage(view, group)).toContain('자료 미제공');
    expect(exported(view)).toContain('미제공: 반대 근거·위험');
    expect(reviewGroupMessage(view, view.groups.find(g => g.key === 'catalysts')!)).toContain('반환된 목록이 비어');
  });
  it.each(['malformed', 'missing-sources'])('never reports a rejected or missing inventory as known zero: %s', name => {
    const view = model(produced[name]);
    expect(reviewSourcePresentation(view).badge).toBe('문서 수 미확인');
    expect(exported(view)).not.toContain('0개 연결 문서');
    expect(selectReviewSource(view, undefined).id).toBeNull();
  });
  it('preserves explicit empty inventories and their explanation in the export', () => {
    const view = model(produced.empty);
    expect(reviewSourcePresentation(view).badge).toBe('0개 연결 문서');
    expect(exported(view)).toContain('반환된 연결 문서가 없습니다.');
    expect(exported(view)).not.toContain('## 리서치 데이터 상태');
  });
  it('retains independent source contexts without restoring invalid research inputs', () => {
    const input = parseCompany({ ...example, data: { ...example.data, equity_research: produced.malformed,
      recent_events: [{ source_document_id: 'source-document-31', title: 'Event source' }],
      macro_flow_impacts: [{ source_document_id: 'source-document-32', title: 'Market background' }],
    } }, 'AAPL');
    const view = reviewModel(input), output = exported(view);
    expect(reviewSourcePresentation(view).badge).toBe('현재 표시 2개');
    expect(reviewSourcePresentation(view).notice).toContain('대신하지 않습니다');
    expect(output).toContain('연결 경로: 기업 직접 연결');
    expect(output).toContain('연결 경로: 시장 배경 연결');
    expect(output).not.toContain('연결 경로: 리서치 입력 문서');
    expect(selectReviewSource(view, 'source-document-31')).toEqual({ id: 'source-document-31', invalid: false });
    expect(selectReviewSource(view, 'source-document-7001')).toEqual({ id: null, invalid: true });
  });
  it('explains rejected summaries without replacing unrelated valid claims', () => {
    const view = model(produced['bad-summary']);
    expect(reviewSummaryText(view)).toContain('요약: 형식 오류');
    expect(exported(view)).toContain('정상 주장');
    expect(exported(view)).not.toContain('synthetic-summary');
  });
  it('does not echo corrupt metadata and distinguishes unknown status from a known field error', () => {
    const view = model({ ...produced.valid, data_quality: { policy: 'unexpected-private-metadata' } });
    const output = exported(view);
    expect(output).toContain('데이터 상태를 확인할 수 없습니다');
    expect(reviewGroupMessage(view, view.groups[0])).toContain('데이터 상태를 확인할 수 없어');
    expect(output).not.toContain('unexpected-private-metadata');
    expect(output).not.toContain('정상 주장');
    expect(output).not.toContain('source-document-7001');
  });
  it.each(['valid', 'malformed', 'partial', 'empty', 'missing-sources', 'bad-summary'])('does not mutate a model or invalidate its saved fingerprint: %s', name => {
    const view = model(produced[name]), before = JSON.stringify(view), snapshot = reviewSnapshot(view);
    Object.freeze(view.groups); Object.freeze(view.sources); Object.freeze(view);
    reviewSummaryText(view); view.groups.forEach(group => reviewGroupMessage(view, group));
    reviewSourcePresentation(view); reviewQualityMessages(view); exported(view);
    expect(JSON.stringify(view)).toBe(before);
    expect(reviewSnapshot(view)).toBe(snapshot);
  });
  it('never appends current quality warnings or independent sources to a stale-basis draft', () => {
    const old = model(produced.valid), next = model(produced.malformed);
    const draft = { ...emptyDraft(old, reviewSnapshot(old)), note: 'Old private note' };
    next.sources.push({ id: 'source-document-99', title: 'New source', context: '기업 직접 연결' });
    const output = exportReview(draft, next, reviewSnapshot(next));
    expect(output).toContain('Old private note');
    expect(output).toContain('이전 분석 기준의 초안');
    expect(output).not.toContain('## 리서치 데이터 상태');
    expect(output).not.toContain('형식 오류');
    expect(output).not.toContain('source-document-99');
  });
  it('keeps source titles and relationship context literal in Markdown', () => {
    const view = model(produced.valid);
    view.sources[0].title = '# not a heading\n<script>not executed</script>';
    view.sources[0].context = '[not a link](javascript:alert(1))';
    expect(exported(view)).toContain('    # not a heading\n    <script>not executed</script>');
    expect(exported(view)).toContain('    연결 경로: [not a link](javascript:alert(1))');
  });
  it('legacy unknown inventory is not a zero and does not acquire producer-validation claims', () => {
    const research = { ...produced.valid }; delete research.data_quality;
    const view = { ...model(research), sources: [], sourcesKnown: false };
    expect(reviewSourcePresentation(view).badge).toBe('문서 수 미확인');
    expect(reviewSourcePresentation(view).empty).toContain('원천 문서 목록 미제공');
    expect(reviewQualityMessages(view)).toEqual([]);
  });
  it('fund analysis does not inherit equity field warnings', () => {
    const view = { ...model(produced.malformed), fund: true, summary: 'Fund exposure',
      groups: [{ key: 'limits', title: '제한 사항', items: ['Stored fund limitation'] }] };
    expect(reviewQualityMessages(view)).toEqual([]);
    expect(reviewSummaryText(view)).toBe('Fund exposure');
    expect(reviewGroupMessage(view, view.groups[0])).toBeNull();
    expect(exported(view)).toContain('Stored fund limitation');
  });
});
