/** Reading/export copy only. Never add these derived values to the saved review model. */
import type { ReviewGroup, ReviewModel } from './company-review-model';
import { RESEARCH_FIELD_LABELS, type ResearchField } from './research-display-contract';

const groupFields: Record<string, ResearchField | undefined> = {
  claims: 'key_points', risks: 'risks', conditions: 'invalidation_conditions', catalysts: 'catalysts',
};

export function reviewFieldProblem(model: ReviewModel, field: ResearchField): string | null {
  const issue = model.fund ? undefined : model.researchIssue;
  if (!issue) return null;
  const label = RESEARCH_FIELD_LABELS[field];
  if (issue.metadataInvalid) return `${label}: 데이터 상태를 확인할 수 없어 표시하지 않았습니다.`;
  if (issue.invalid.includes(field)) return `${label}: 형식 오류로 표시하지 않았습니다.`;
  if (issue.unavailable.includes(field)) return `${label}: 자료 미제공. 빈 목록이나 문제가 없다는 뜻은 아닙니다.`;
  return null;
}

export function reviewSummaryText(model: ReviewModel): string {
  return reviewFieldProblem(model, 'korean_summary') ?? model.summary;
}

/** A null message means the stored items can be rendered, not that their claims are true. */
export function reviewGroupMessage(model: ReviewModel, group: ReviewGroup): string | null {
  const field = Object.hasOwn(groupFields, group.key) ? groupFields[group.key] : undefined;
  const problem = field ? reviewFieldProblem(model, field) : null;
  if (problem) return problem;
  if (group.items === null) return '목록 미제공. 근거가 충분하다는 뜻은 아닙니다.';
  return group.items.length ? null : '반환된 목록이 비어 있습니다. 근거가 충분하다는 뜻은 아닙니다.';
}

export function reviewSourcePresentation(model: ReviewModel): { badge: string; notice: string | null; empty: string } {
  const problem = reviewFieldProblem(model, 'source_document_ids');
  if (problem) {
    return {
      badge: model.sources.length ? `현재 표시 ${model.sources.length}개` : '문서 수 미확인',
      notice: model.sources.length
        ? `${problem} 아래 기업·시장 연결 문서는 별도 연결 자료이며, 사용할 수 없는 리서치 입력 문서 목록을 대신하지 않습니다.`
        : null,
      empty: `${problem} 연결 문서가 없다고 단정할 수 없습니다.`,
    };
  }
  return {
    badge: model.sourcesKnown ? `${model.sources.length}개 연결 문서` : '문서 수 미확인',
    notice: null,
    empty: model.sourcesKnown ? '반환된 연결 문서가 없습니다.' : '원천 문서 목록 미제공. 연결 문서가 없다고 단정할 수 없습니다.',
  };
}

/** Canonical labels only; never echo arbitrary producer metadata into a portable file. */
export function reviewQualityMessages(model: ReviewModel): string[] {
  const issue = model.fund ? undefined : model.researchIssue;
  if (!issue) return [];
  const messages: string[] = [];
  if (issue.metadataInvalid) {
    messages.push('리서치 데이터 상태를 확인할 수 없습니다. 해당 분석 필드와 리서치 입력 문서 목록을 표시하지 않았습니다.');
  } else {
    const fields = Object.keys(RESEARCH_FIELD_LABELS) as ResearchField[];
    const invalid = fields.filter(field => issue.invalid.includes(field));
    const unavailable = fields.filter(field => issue.unavailable.includes(field));
    if (invalid.length) messages.push(`형식 오류: ${invalid.map(field => RESEARCH_FIELD_LABELS[field]).join(' · ')}. 잘못된 값을 분석 문장이나 원천 링크로 바꾸지 않았습니다.`);
    if (unavailable.length) messages.push(`미제공: ${unavailable.map(field => RESEARCH_FIELD_LABELS[field]).join(' · ')}. 빈 목록이나 위험이 없다는 의미가 아닙니다.`);
  }
  if (messages.length) messages.push('데이터 형식 확인은 분석의 사실성·투자 판단 검증과 별개입니다.');
  return messages;
}
