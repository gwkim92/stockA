/** Stored research and human notes; no inferred claim/source approval. */
import { dateOnly, recordedDate, object, rows, strings, text } from './research-reader-model';
import { resourceId, recordHref } from './news-theme-model';
import type { CompanyData } from './company-evidence-model';
import { researchDisplayIssue, type ResearchDisplayIssue } from './research-display-contract';
export type ReviewSource = { id: string; title: string; context: string };
export type ReviewGroup = { key: string; title: string; items: string[] | null };
export type ReviewModel = {
  symbol: string; instrumentId: string; name: string; asOf: string | null; researchDate: string | null;
  artifactId: string | null; summary: string; origin: string; fund: boolean; blocked: boolean;
  groups: ReviewGroup[]; sources: ReviewSource[]; sourcesKnown: boolean;
  thesisHref: string | null; recommendationHref: string | null; researchIssue?: ResearchDisplayIssue;
};
export function reviewModel(company: CompanyData): ReviewModel {
  const r = company.research, fund = company.fund;
  const issue = company.fundKind ? null : researchDisplayIssue(r);
  const researchIds = strings(r.source_document_ids);
  const sources = new Map<string, ReviewSource>();
  for (const raw of researchIds ?? []) {
    const id = resourceId(raw);
    if (id) sources.set(id, { id, title: id, context: '리서치 입력 문서' });
  }
  for (const [events, context] of [[company.events, '기업 직접 연결'], [company.macro, '시장 배경 연결']] as const) {
    for (const event of events ?? []) {
      const id = resourceId(event.source_document_id);
      if (!id) continue;
      const prior = sources.get(id);
      sources.set(id, { id, title: text(event.korean_title, text(event.title, id)), context: prior ? `${prior.context} · ${context}` : context });
    }
  }
  const fallback = r.provider === 'fixture' || r.provider === 'local_rules';
  return {
    symbol: company.symbol, instrumentId: company.id, name: company.name, asOf: company.asOf,
    researchDate: dateOnly(company.fundKind ? fund?.source_as_of_date : r.as_of_date),
    artifactId: resourceId(r.artifact_id), fund: company.fundKind, blocked: company.blocked,
    summary: text(company.fundKind ? fund?.summary : r.korean_summary, '저장된 리서치 요약이 없습니다.'),
    origin: company.fundKind ? '펀드 분석 기록' : fallback ? '규칙 기반·검증용 제공자 기록' : r.provider === 'codex_oauth' || r.provider === 'agents_sdk_openai' ? '저장된 모델 해석' : '생성 방식 미확인',
    groups: company.fundKind ? [
      { key: 'exposure', title: '상품이 제공하는 노출', items: typeof fund?.summary === 'string' ? [fund.summary] : null },
      { key: 'cost', title: '구성과 비용의 기록', items: [text(object(fund?.expense_ratio).summary, ''), text(object(fund?.tracking_error).summary, '')].filter(Boolean) },
      { key: 'limits', title: '제한 사항', items: strings(fund?.limitations) },
    ] : [
      { key: 'claims', title: '핵심 주장', items: strings(r.key_points) },
      { key: 'risks', title: '반대 근거·위험', items: strings(r.risks) },
      { key: 'conditions', title: '판단을 바꿀 조건', items: strings(r.invalidation_conditions) },
      { key: 'catalysts', title: '다음 촉매', items: strings(r.catalysts) },
    ],
    sources: [...sources.values()], sourcesKnown: researchIds !== null || company.events !== null || company.macro !== null,
    thesisHref: company.thesisHref, recommendationHref: recordHref('recommendations', company.recommendation?.recommendation_id),
    ...(issue ? { researchIssue: issue } : {}),
  };
}
/** Selector is an allowlist, not a general document lookup. Never replace bad requests with another source. */
export function selectReviewSource(model: ReviewModel, requested: unknown): { id: string | null; invalid: boolean } {
  if (requested === undefined) return { id: model.sources[0]?.id ?? null, invalid: false };
  const id = resourceId(requested);
  return id && model.sources.some(s => s.id === id) ? { id, invalid: false } : { id: null, invalid: true };
}
export const CHECKS = [['numbers', '숫자·통화·기간을 원천과 대조했다'], ['opposition', '반대 근거와 빠진 자료를 검토했다'], ['conditions', '판단을 바꿀 조건을 확인했다']] as const;
export type CheckKey = typeof CHECKS[number][0];
export type Draft = {
  version: 1; symbol: string; instrumentId: string; snapshot: string; asOf: string | null;
  savedAt: string; note: string; opposition: string; nextAction: string; nextDate: string;
  checks: CheckKey[];
};
export const draftKey = (model: Pick<ReviewModel, 'symbol' | 'instrumentId'>) => `stocka:company-review:v1:${encodeURIComponent(model.symbol)}:${encodeURIComponent(model.instrumentId)}`;
export function emptyDraft(model: ReviewModel, snapshot: string): Draft {
  return { version: 1, symbol: model.symbol, instrumentId: model.instrumentId, snapshot, asOf: model.asOf,
    savedAt: '', note: '', opposition: '', nextAction: '', nextDate: '', checks: [] };
}
const keys = ['version','symbol','instrumentId','snapshot','asOf','savedAt','note','opposition','nextAction','nextDate','checks'].sort().join(',');
export function parseDraft(raw: string, model: Pick<ReviewModel, 'symbol' | 'instrumentId'>): Draft | null {
  if (raw.length > 24000) return null;
  try {
    const d = object(JSON.parse(raw));
    if (Object.keys(d).sort().join(',') !== keys || d.version !== 1 || d.symbol !== model.symbol || d.instrumentId !== model.instrumentId
      || typeof d.snapshot !== 'string' || !/^[a-f0-9]{64}$/.test(d.snapshot)
      || (d.asOf !== null && !dateOnly(d.asOf)) || !recordedDate(d.savedAt)
      || typeof d.note !== 'string' || d.note.length > 4000 || typeof d.opposition !== 'string' || d.opposition.length > 3000
      || typeof d.nextAction !== 'string' || d.nextAction.length > 2000 || typeof d.nextDate !== 'string'
      || (d.nextDate !== '' && !dateOnly(d.nextDate)) || !Array.isArray(d.checks)
      || d.checks.some(k => !CHECKS.some(([key]) => key === k)) || new Set(d.checks).size !== d.checks.length) return null;
    return d as Draft;
  } catch { return null; }
}
/** User/source strings remain indented literal text in Markdown, never executable markup or authored links. */
export function exportReview(draft: Draft, model: ReviewModel, currentSnapshot: string): string {
  const literal = (v: string) => v.split(/\r?\n/).map(line => `    ${line}`).join('\n');
  const current = draft.snapshot === currentSnapshot;
  const parts = ['# stockA 개인 검토 초안', literal(`${model.symbol} · ${model.name}`),
    '이 파일은 사람이 작성한 초안입니다. 추천·주문·검증 승인·일정 알림이 아닙니다.',
    literal(`기업 ID: ${draft.instrumentId}\n초안 분석 기준: ${draft.asOf ?? '미확인'}\n저장 시각: ${draft.savedAt || '미저장'}\n초안 스냅샷: ${draft.snapshot}`),
    current ? '현재 화면의 분석 묶음과 초안 기준이 일치합니다. 원천 본문 불변성이나 주장 검증을 뜻하지 않습니다.' : '이전 분석 기준의 초안입니다. 현재 화면의 분석·원천을 이 초안의 근거로 합치지 않았습니다.',
    '## 내 검토 메모', literal(draft.note || '미작성'), '## 반대 근거와 남은 의문', literal(draft.opposition || '미작성'),
    '## 다음 확인 사항', literal(draft.nextAction || '미작성'), literal(`직접 정한 날짜: ${draft.nextDate || '미지정'} (알림 없음)`),
    '## 사람의 체크 표시', literal(CHECKS.map(([key,label]) => `${draft.checks.includes(key) ? '[x]' : '[ ]'} ${label}`).join('\n'))];
  if (current) {
    parts.push('## 화면에 저장된 분석 — 개인 메모와 별개', literal(model.origin), literal(model.summary));
    for (const group of model.groups) parts.push(`### ${group.title}`, literal(group.items === null ? '목록 미제공' : group.items.length ? group.items.join('\n\n') : '반환된 목록이 비어 있음'));
    parts.push('## 연결 문서 목록 — 개별 주장을 입증하는 인용 목록이 아님', literal(model.sources.map(s => `${s.title}\nID: ${s.id}\n/source-documents/${encodeURIComponent(s.id)}`).join('\n\n') || '연결 문서 미제공'));
  }
  return parts.join('\n\n') + '\n';
}
